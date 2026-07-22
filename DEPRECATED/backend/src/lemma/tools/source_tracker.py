"""来源追踪工具 — 引用纪律的来源绑定系统"""
from __future__ import annotations

import json
from pathlib import Path

from .base import Tool, ToolResult


class SourceTrackerTool(Tool):
    """管理研究来源，强制执行引用纪律。每个事实性断言必须绑定一个已注册的来源。"""

    name = "source_tracker"
    description = "注册、查询和验证研究来源。每个事实性断言必须绑定一个已注册的来源。提供 register（注册来源）、bind（绑定断言）、audit（审计来源质量）、list（列表查询）四种操作。"
    category = "research"

    def __init__(self, work_dir: str = "."):
        self.sources_file = Path(work_dir) / ".ultraagent" / "sources.json"
        self.sources_file.parent.mkdir(parents=True, exist_ok=True)

    def _load(self) -> dict:
        if self.sources_file.exists():
            result: dict = json.loads(self.sources_file.read_text(encoding="utf-8"))
            return result
        return {"sources": {}, "claims": []}

    def _save(self, data: dict) -> None:
        self.sources_file.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    async def execute(self, action: str = "list", **kwargs) -> ToolResult:
        data = self._load()

        if action == "register":
            source_id = kwargs.get("source_id", "")
            source_type = kwargs.get("source_type", "unknown")
            url = kwargs.get("url", "")
            description = kwargs.get("description", "")

            if not source_id:
                return ToolResult.fail("注册来源必须提供 source_id")

            data["sources"][source_id] = {
                "type": source_type,
                "url": url,
                "description": description,
                "quality": {
                    "tier": "一手" if source_type == "primary"
                            else "二手" if source_type == "secondary"
                            else "三手",
                    "independent": bool(url),
                },
                "created_at": __import__("datetime").datetime.now().isoformat(),
            }
            self._save(data)
            return ToolResult.ok(f"来源已注册: {source_id} ({source_type})")

        elif action == "bind":
            claim = kwargs.get("claim", "")
            source_id = kwargs.get("source_id", "")

            if not claim or not source_id:
                return ToolResult.fail("bind 需要 claim 和 source_id 参数")
            if source_id not in data["sources"]:
                return ToolResult.fail(f"来源 {source_id} 未注册，请先 register")

            source = data["sources"][source_id]
            label = "fact" if source["quality"]["independent"] else "inference"

            data["claims"].append({
                "claim": claim[:500],
                "source_id": source_id,
                "label": label,
                "bound_at": __import__("datetime").datetime.now().isoformat(),
            })
            self._save(data)
            return ToolResult.ok(f"断言已绑定来源 {source_id}，标签: {label}")

        elif action == "audit":
            total = len(data["claims"])
            facts = sum(1 for c in data["claims"] if c["label"] == "fact")
            inferences = total - facts
            orphans = [
                c["claim"][:80]
                for c in data["claims"]
                if c["source_id"] not in data["sources"]
            ]
            lines = [
                f"## 来源审计",
                f"总断言: {total}, fact: {facts}, inference: {inferences}",
            ]
            if total > 0:
                ratio = facts / total * 100
                lines.append(f"Fact/总比例: {ratio:.0f}%")
            if orphans:
                lines.append(f"\n⚠️ 孤立断言（来源已删除但断言仍存在）: {len(orphans)}")
                for o in orphans[:5]:
                    lines.append(f"  - {o}...")
            if facts > 0 and facts == total:
                lines.append("\n✅ 全部断言为 fact——来源纪律优秀")
            return ToolResult.ok("\n".join(lines))

        elif action == "list":
            return ToolResult.ok(json.dumps(data, ensure_ascii=False, indent=2))

        elif action == "stats":
            num_sources = len(data["sources"])
            num_claims = len(data["claims"])
            type_counts: dict[str, int] = {}
            for s in data["sources"].values():
                t = s.get("type", "unknown")
                type_counts[t] = type_counts.get(t, 0) + 1
            return ToolResult.ok(
                f"来源: {num_sources} 个 ({', '.join(f'{t}={c}' for t, c in type_counts.items())}), "
                f"断言: {num_claims} 条"
            )

        return ToolResult.fail(f"未知 action: {action}")

    def _get_parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["register", "bind", "audit", "list", "stats"],
                    "description": "操作类型：register=注册来源, bind=绑定断言, audit=审计, list=列出全部, stats=统计",
                },
                "source_id": {
                    "type": "string",
                    "description": "来源唯一标识（如 'ref_01' 或文件名）",
                },
                "source_type": {
                    "type": "string",
                    "enum": ["primary", "secondary", "tertiary"],
                    "description": "来源等级：primary=一手, secondary=二手, tertiary=三手",
                },
                "url": {
                    "type": "string",
                    "description": "可独立验证的 URL、DOI 或文件路径",
                },
                "description": {
                    "type": "string",
                    "description": "来源的简要描述",
                },
                "claim": {
                    "type": "string",
                    "description": "要绑定来源的事实性断言",
                },
            },
            "required": ["action"],
        }
