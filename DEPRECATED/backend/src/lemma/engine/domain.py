"""Domain Profile — 领域配置文件加载与验证"""
from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, Field

# ==================== 核心模型 ====================


class PhaseConfig(BaseModel):
    """阶段配置"""
    id: str
    name: str
    order: int
    progress: float = 0.0
    transition: dict[str, str] = Field(default_factory=dict)
    handler_prompt: str = ""


class RoleConfig(BaseModel):
    """角色配置"""
    id: str
    name: str
    emoji: str = "🤖"
    temperature: float = 0.5
    tools: list[str] = Field(default_factory=list)
    system_prompt: str = ""


class ValidatorConfig(BaseModel):
    """验证器配置"""
    phase: str
    check: str
    path: str = ""
    glob: str = ""


class DomainProfile(BaseModel):
    """完整的领域配置"""

    id: str
    name: str
    description: str = ""
    version: str = "1.0"

    phases: list[PhaseConfig]
    roles: list[RoleConfig]
    directories: dict[str, str] = Field(default_factory=dict)
    phase_handlers: dict[str, str] = Field(default_factory=dict)
    validators: list[ValidatorConfig] = Field(default_factory=list)

    # --- 持久化 ---

    @classmethod
    def from_directory(cls, dir_path: str | Path) -> DomainProfile:
        """从领域目录加载配置"""
        dir_path = Path(dir_path)
        yaml_path = dir_path / "domain.yaml"
        if not yaml_path.exists():
            raise FileNotFoundError(f"domain.yaml not found in {dir_path}")

        with open(yaml_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        profile = cls(**data)

        # 自动加载 prompts 目录中的 .md 文件作为角色的 system_prompt
        prompts_dir = dir_path / "prompts"
        if prompts_dir.exists():
            for role_cfg in profile.roles:
                prompt_file = prompts_dir / f"agent_{role_cfg.id}.md"
                if prompt_file.exists():
                    role_cfg.system_prompt = prompt_file.read_text(encoding="utf-8")

        # 自动加载 phase_handlers 从 prompts/*.md（如果 domain.yaml 中未指定）
        if prompts_dir.exists() and not profile.phase_handlers:
            for phase in profile.phases:
                handler_file = prompts_dir / f"phase_{phase.id}.md"
                if handler_file.exists():
                    profile.phase_handlers[phase.id] = handler_file.read_text(encoding="utf-8")

        return profile

    @classmethod
    def list_domains(cls, base_dir: str | Path) -> list[dict]:
        """列出所有可用领域"""
        domains_path = Path(base_dir)
        if not domains_path.exists():
            return []

        domains = []
        for d in sorted(domains_path.iterdir()):
            if d.is_dir() and (d / "domain.yaml").exists():
                try:
                    with open(d / "domain.yaml", encoding="utf-8") as f:
                        data = yaml.safe_load(f)
                    domains.append({
                        "id": data.get("id", d.name),
                        "name": data.get("name", d.name),
                        "description": data.get("description", ""),
                        "version": data.get("version", "1.0"),
                    })
                except Exception:
                    continue
        return domains

    # --- 查询 ---

    def get_phase_by_id(self, phase_id: str) -> PhaseConfig | None:
        for p in self.phases:
            if p.id == phase_id:
                return p
        return None

    def get_role_by_id(self, role_id: str) -> RoleConfig | None:
        for r in self.roles:
            if r.id == role_id:
                return r
        return None

    def get_phase_ids(self) -> list[str]:
        return [p.id for p in sorted(self.phases, key=lambda x: x.order)]

    def get_transition(self, from_phase: str, success: bool) -> str:
        """根据当前阶段和结果获取下一阶段"""
        phase = self.get_phase_by_id(from_phase)
        if not phase:
            return from_phase
        key = "pass" if success else "fail"
        return phase.transition.get(key, from_phase)


# ==================== 阶段结果 ====================


class PhaseResult(BaseModel):
    """阶段执行结果"""
    phase_id: str
    success: bool = True
    summary: str = ""
    artifacts: dict[str, str] = {}
    issues: list[str] = []
    gate_passed: bool = True
    metrics: dict[str, float] = {}
    metadata: dict = Field(default_factory=dict)
