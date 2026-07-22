"""固化模式 — 将成功的 ad-hoc 运行转化为永久领域预设"""
from __future__ import annotations

import json
from pathlib import Path


def solidify_session(
    source_work_dir: str,
    target_domain_name: str,
    domains_base_dir: str,
) -> str:
    """将一次成功运行的产出固化到新的领域预设目录

    Args:
        source_work_dir: 已完成的工作目录
        target_domain_name: 新领域名称
        domains_base_dir: domains 根目录

    Returns:
        新领域的完整路径
    """
    source = Path(source_work_dir)
    target = Path(domains_base_dir) / target_domain_name

    if target.exists():
        raise FileExistsError(f"领域 '{target_domain_name}' 已存在: {target}")

    # 创建领域目录结构
    target.mkdir(parents=True)
    (target / "prompts").mkdir(exist_ok=True)
    (target / "knowledge").mkdir(exist_ok=True)
    (target / "templates").mkdir(exist_ok=True)

    # 从上下文构建 domain.yaml
    context_file = source / "agent-context.json"
    context_data = None
    if context_file.exists():
        context_data = json.loads(context_file.read_text(encoding="utf-8"))

    phases = _build_phases_from_context(context_data) if context_data else _default_phases()

    domain_cfg = {
        "id": target_domain_name,
        "name": target_domain_name,
        "description": f"固化于 {source}",
        "version": "1.0",
        "phases": phases,
        "roles": [
            {"id": "lead", "name": "主编", "temperature": 0.5, "tools": ["file_manager"]},
        ],
        "directories": {"output": "output"},
    }
    (target / "domain.yaml").write_text(
        _yaml_dump(domain_cfg), encoding="utf-8",
    )

    # 复制 prompts（如果有）
    prompts_source = source / "agent_prompts"
    if prompts_source.exists():
        import shutil
        shutil.copytree(prompts_source, target / "prompts", dirs_exist_ok=True)

    return str(target)


def _build_phases_from_context(context_data: dict) -> list[dict]:
    """从上下文中提取阶段定义"""
    phases = []
    raw_phases = context_data.get("phases", {})
    sorted_keys = sorted(raw_phases.keys(), key=lambda k: int(k) if k.isdigit() else 0)

    total = len(sorted_keys)
    for i, phase_key in enumerate(sorted_keys):
        info = raw_phases[phase_key]
        phases.append({
            "id": phase_key,
            "name": info.get("phase_name", f"阶段 {phase_key}"),
            "order": i,
            "progress": int((i + 1) / max(total, 1) * 100),
            "transition": {
                "pass": sorted_keys[i + 1] if i + 1 < total else "done",
                "fail": phase_key,
            },
        })

    # 添加 idle 和 done
    if not any(p["id"] == "idle" for p in phases):
        phases.insert(0, {
            "id": "idle", "name": "空闲", "order": -1,
            "progress": 0, "transition": {"pass": phases[0]["id"] if phases else "done"},
        })
    phases.append({
        "id": "done", "name": "完成", "order": len(phases),
        "progress": 100,
    })
    return phases


def _default_phases() -> list[dict]:
    """返回默认的阶段配置"""
    return [
        {"id": "idle", "name": "空闲", "order": -1, "progress": 0,
         "transition": {"pass": "init"}},
        {"id": "init", "name": "初始化", "order": 0, "progress": 20,
         "transition": {"pass": "draft"}},
        {"id": "draft", "name": "草稿", "order": 1, "progress": 60,
         "transition": {"pass": "done", "fail": "draft"}},
        {"id": "done", "name": "完成", "order": 2, "progress": 100},
    ]


def _yaml_dump(data: dict) -> str:
    """简单 YAML 序列化（不需要 yaml 库依赖）"""
    lines = []
    for key, value in data.items():
        if isinstance(value, list):
            lines.append(f"{_yaml_key(key)}:")
            for item in value:
                if isinstance(item, dict):
                    lines.append("  -")
                    for sk, sv in item.items():
                        if isinstance(sv, dict):
                            lines.append(f"    {_yaml_key(sk)}:")
                            for ssk, ssv in sv.items():
                                lines.append(f"      {_yaml_key(ssk)}: {_yaml_val(ssv)}")
                        else:
                            lines.append(f"    {_yaml_key(sk)}: {_yaml_val(sv)}")
                else:
                    lines.append(f"  - {_yaml_val(item)}")
        elif isinstance(value, dict):
            lines.append(f"{_yaml_key(key)}:")
            for sk, sv in value.items():
                lines.append(f"  {_yaml_key(sk)}: {_yaml_val(sv)}")
        else:
            lines.append(f"{_yaml_key(key)}: {_yaml_val(value)}")
    return "\n".join(lines)


def _yaml_key(key: str) -> str:
    return key


def _yaml_val(val: object) -> str:
    value_str = str(val)
    if isinstance(val, str) and (" " in value_str or value_str.startswith("{")):
        return f'"{value_str}"'
    return value_str
