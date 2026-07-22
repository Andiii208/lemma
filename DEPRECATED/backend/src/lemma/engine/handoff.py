"""结构化交接协议 — 跨 Agent 通信的标准化摘要"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum


class Confidence(Enum):
    """置信度等级"""
    GREEN = "green"     # 高置信，可下游使用
    YELLOW = "yellow"   # 中等置信，需标注不确定
    RED = "red"         # 低置信，仅供参考


@dataclass
class HandoffSummary:
    """标准交接摘要表"""
    agent_role: str
    agent_name: str
    conclusion: str                     # 一句话结论
    confidence: Confidence
    unresolved_disagreements: list[str] = field(default_factory=list)
    key_data_referenced: list[str] = field(default_factory=list)
    downstream_warnings: list[str] = field(default_factory=list)
    artifacts_produced: dict[str, str] = field(default_factory=dict)

    def to_context_block(self) -> str:
        """渲染为可以注入下游 Agent context 的文本块"""
        lines = [
            f"## {self.agent_name} ({self.agent_role}) 交接",
        ]
        # 渲染表格
        rows = [
            ("结论", self.conclusion),
            ("置信度", self.confidence.value),
        ]
        if self.unresolved_disagreements:
            rows.append(("未解决分歧", "; ".join(self.unresolved_disagreements)))
        if self.key_data_referenced:
            rows.append(("关键数据引用", "; ".join(self.key_data_referenced)))
        if self.downstream_warnings:
            rows.append(("下游警告", "; ".join(self.downstream_warnings)))
        if self.artifacts_produced:
            rows.append(("产出物", "; ".join(f"{k}={v}" for k, v in self.artifacts_produced.items())))

        lines.append("| 字段 | 内容 |")
        lines.append("|------|------|")
        for key, value in rows:
            lines.append(f"| {key} | {value} |")

        return "\n".join(lines)


# 字段名 → 属性名的映射（用于解析）
_FIELD_MAP: dict[str, str] = {
    "结论": "conclusion",
    "置信度": "confidence",
    "未解决分歧": "unresolved_disagreements",
    "关键数据引用": "key_data_referenced",
    "下游警告": "downstream_warnings",
    "产出物": "artifacts_produced",
}


def parse_handoff_from_text(text: str) -> HandoffSummary | None:
    """尝试从 LLM 输出中解析交接表（Markdown 表格格式）"""
    table_match = re.search(
        r'\| 字段 \| 内容 \|.*?(?=\n\n|\Z)', text, re.DOTALL
    )
    if not table_match:
        return None

    table_text = table_match.group(0)
    fields: dict[str, str] = {}
    for line in table_text.split('\n'):
        m = re.match(r'\|\s*(.+?)\s*\|\s*(.+?)\s*\|', line)
        if m and m.group(1) not in ("字段", "---"):
            fields[m.group(1)] = m.group(2)

    if "结论" not in fields:
        return None

    raw_confidence = fields.get("置信度", "green").lower()
    if "red" in raw_confidence:
        conf = Confidence.RED
    elif "yellow" in raw_confidence:
        conf = Confidence.YELLOW
    else:
        conf = Confidence.GREEN

    return HandoffSummary(
        agent_role="unknown",
        agent_name="unknown",
        conclusion=fields.get("结论", ""),
        confidence=conf,
        unresolved_disagreements=_split_field(fields.get("未解决分歧", "")),
        key_data_referenced=_split_field(fields.get("关键数据引用", "")),
        downstream_warnings=_split_field(fields.get("下游警告", "")),
    )


def _split_field(value: str) -> list[str]:
    """拆分字段值（支持分号或逗号分割）"""
    if not value:
        return []
    parts = re.split(r'[;；,，]', value)
    return [p.strip() for p in parts if p.strip()]
