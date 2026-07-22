"""失败模式库 — 收集和管理失败案例，用于回归测试"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class FailureMode:
    """失败模式"""

    mode_id: str = ""
    category: str = ""  # sandbox_escape | tool_error | llm_hallucination | eval_regression
    description: str = ""
    example_input: str = ""
    expected_behavior: str = ""
    actual_behavior: str = ""
    severity: str = "medium"  # low | medium | high | critical
    discovered_at: str = ""
    fixed: bool = False


class FailureModeLibrary:
    """失败模式库"""

    def __init__(self, library_path: str):
        self.library_path = Path(library_path)
        self._modes: list[FailureMode] = []
        self._load()

    def _load(self) -> None:
        if not self.library_path.exists():
            return
        for line in self.library_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                data = json.loads(line)
                self._modes.append(FailureMode(**data))
            except (json.JSONDecodeError, TypeError):
                continue

    def add(self, mode: FailureMode) -> None:
        """添加失败模式"""
        self._modes.append(mode)
        self.library_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.library_path, "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "mode_id": mode.mode_id,
                "category": mode.category,
                "description": mode.description,
                "example_input": mode.example_input[:500],
                "expected_behavior": mode.expected_behavior,
                "actual_behavior": mode.actual_behavior,
                "severity": mode.severity,
                "discovered_at": mode.discovered_at,
                "fixed": mode.fixed,
            }, ensure_ascii=False) + "\n")

    def search(
        self,
        category: str | None = None,
        severity: str | None = None,
        unfixed_only: bool = False,
    ) -> list[FailureMode]:
        """搜索失败模式"""
        results = []
        for mode in self._modes:
            if category and mode.category != category:
                continue
            if severity and mode.severity != severity:
                continue
            if unfixed_only and mode.fixed:
                continue
            results.append(mode)
        return results

    def mark_fixed(self, mode_id: str) -> bool:
        """标记为已修复"""
        for mode in self._modes:
            if mode.mode_id == mode_id:
                mode.fixed = True
                self._save_all()
                return True
        return False

    def _save_all(self) -> None:
        self.library_path.write_text(
            "\n".join(
                json.dumps({
                    "mode_id": m.mode_id,
                    "category": m.category,
                    "description": m.description,
                    "example_input": m.example_input[:500],
                    "expected_behavior": m.expected_behavior,
                    "actual_behavior": m.actual_behavior,
                    "severity": m.severity,
                    "discovered_at": m.discovered_at,
                    "fixed": m.fixed,
                }, ensure_ascii=False)
                for m in self._modes
            ),
            encoding="utf-8",
        )

    @property
    def count(self) -> int:
        return len(self._modes)

    @property
    def unfixed_count(self) -> int:
        return sum(1 for m in self._modes if not m.fixed)
