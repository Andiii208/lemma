"""证据地图工具 — 递归分解树的记录与查询"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from .base import Tool, ToolResult


class EvidenceMapTool(Tool):
    """维护研究问题的分解树和证据链。支持递归分解追踪、置信度审计。"""

    name = "evidence_map"
    description = "添加、查询研究分解树节点，维护证据链。支持递归分解（add_node）、子树查询（get_tree）、置信度审计（audit）、统计（stats）。"
    category = "research"

    def __init__(self, work_dir: str = "."):
        self.map_file = Path(work_dir) / ".ultraagent" / "evidence_map.json"
        self.map_file.parent.mkdir(parents=True, exist_ok=True)

    def _load(self) -> dict:
        if self.map_file.exists():
            result: dict = json.loads(self.map_file.read_text(encoding="utf-8"))
            return result
        return {"root_id": None, "nodes": {}, "created_at": datetime.now().isoformat()}

    def _save(self, data: dict) -> None:
        self.map_file.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def _extract_subtree(self, data: dict, node_id: str) -> dict:
        """递归提取子树"""
        node = data["nodes"].get(node_id, {})
        result = dict(node)
        result["children_detail"] = [
            self._extract_subtree(data, child_id)
            for child_id in node.get("children", [])
        ]
        return result

    async def execute(self, action: str = "stats", **kwargs) -> ToolResult:
        data = self._load()

        if action == "add_node":
            node_id = kwargs.get("node_id", "")
            parent_id = kwargs.get("parent_id", "")
            question = kwargs.get("question", "")
            answer = kwargs.get("answer", "")
            confidence = kwargs.get("confidence", "medium")
            sources = kwargs.get("sources", [])
            is_atomic = kwargs.get("is_atomic", False)

            if not node_id:
                return ToolResult.fail("add_node 必须提供 node_id")

            if data["root_id"] is None:
                data["root_id"] = node_id

            # 自动计算标签：High 置信度 + ≥2 来源 = fact
            label = "fact" if confidence in ("high", "medium") and len(sources) >= 2 else "inference"

            data["nodes"][node_id] = {
                "parent": parent_id or None,
                "question": question,
                "answer": answer,
                "confidence": confidence,
                "sources": sources,
                "is_atomic": is_atomic,
                "children": [],
                "label": label,
                "updated_at": datetime.now().isoformat(),
            }

            if parent_id and parent_id in data["nodes"]:
                if node_id not in data["nodes"][parent_id]["children"]:
                    data["nodes"][parent_id]["children"].append(node_id)

            self._save(data)
            node_type = "叶子（原子）" if is_atomic else "非叶子"
            return ToolResult.ok(f"节点 {node_id} ({node_type}) 已添加，标签={label}")

        elif action == "get_tree":
            node_id = kwargs.get("node_id", "")
            if node_id and node_id in data["nodes"]:
                subtree = self._extract_subtree(data, node_id)
                return ToolResult.ok(json.dumps(subtree, ensure_ascii=False, indent=2))
            return ToolResult.ok(json.dumps(data, ensure_ascii=False, indent=2))

        elif action == "audit":
            violations = []
            for nid, node in data["nodes"].items():
                conf = node.get("confidence", "low")
                src_count = len(node.get("sources", []))
                if conf == "high" and src_count < 2:
                    violations.append(f"- {nid}: High 置信度但只有 {src_count} 个来源（需 ≥2）")
                if conf == "medium" and src_count < 1:
                    violations.append(f"- {nid}: Medium 置信度但无来源")

            if violations:
                return ToolResult.fail("审计发现违规:\n" + "\n".join(violations))
            return ToolResult.ok("审计通过：所有置信度与证据量匹配")

        elif action == "stats":
            total = len(data["nodes"])
            atomic = sum(1 for n in data["nodes"].values() if n.get("is_atomic"))
            high = sum(1 for n in data["nodes"].values() if n.get("confidence") == "high")
            facts = sum(1 for n in data["nodes"].values() if n.get("label") == "fact")
            max_depth = self._compute_max_depth(data, data.get("root_id"))

            return ToolResult.ok(
                f"证据地图: {total} 节点, {atomic} 原子问题, "
                f"最大深度 {max_depth}, "
                f"High 置信度 {high} 个, fact 标签 {facts} 个"
            )

        return ToolResult.fail(f"未知 action: {action}")

    def _compute_max_depth(self, data: dict, root_id: str | None, depth: int = 0) -> int:
        """计算树的最大深度"""
        if root_id is None or root_id not in data["nodes"]:
            return depth
        node = data["nodes"][root_id]
        children = node.get("children", [])
        if not children:
            return depth
        return max(self._compute_max_depth(data, cid, depth + 1) for cid in children)

    def _get_parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["add_node", "get_tree", "audit", "stats"],
                    "description": "操作类型：add_node=添加节点, get_tree=查询子树, audit=置信度审计, stats=统计",
                },
                "node_id": {"type": "string", "description": "节点唯一标识"},
                "parent_id": {"type": "string", "description": "父节点 ID"},
                "question": {"type": "string", "description": "该节点研究的问题"},
                "answer": {"type": "string", "description": "基于证据的回答"},
                "confidence": {
                    "type": "string",
                    "enum": ["high", "medium", "low"],
                    "description": "置信度等级",
                },
                "sources": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "支撑来源的 ID 列表",
                },
                "is_atomic": {
                    "type": "boolean",
                    "description": "是否为原子问题（无需继续拆分）",
                },
            },
            "required": ["action"],
        }
