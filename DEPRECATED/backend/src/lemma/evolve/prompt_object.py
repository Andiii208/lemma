"""可优化 Prompt 对象 — 将 prompt 视为可变异的优化目标"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class OptimizablePrompt:
    """可优化的 Prompt — 包含模板和可变异插槽"""

    name: str = ""
    template: str = ""
    slots: dict[str, str] = field(default_factory=dict)
    version: int = 0
    score: float = 0.0
    parent_id: str = ""

    @property
    def prompt_id(self) -> str:
        """基于内容的唯一 ID"""
        content = f"{self.template}||{self.slots}"
        return hashlib.sha256(content.encode()).hexdigest()[:10]

    @property
    def rendered(self) -> str:
        """渲染后的完整 prompt"""
        result = self.template
        for key, value in self.slots.items():
            result = result.replace(f"{{{key}}}", value)
        return result

    def save(self, path: str) -> None:
        """保存到文件"""
        Path(path).write_text(self.rendered, encoding="utf-8")

    @classmethod
    def from_file(cls, path: str, name: str = "") -> OptimizablePrompt:
        """从文件加载"""
        content = Path(path).read_text(encoding="utf-8")
        return cls(
            name=name or Path(path).stem,
            template=content,
        )

    def clone(self) -> OptimizablePrompt:
        """深拷贝"""
        return OptimizablePrompt(
            name=self.name,
            template=self.template,
            slots=dict(self.slots),
            version=self.version,
            score=self.score,
            parent_id=self.prompt_id,
        )
