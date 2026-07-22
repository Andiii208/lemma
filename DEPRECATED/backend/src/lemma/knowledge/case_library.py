"""案例库 — 存储高质量历史产出，支持相似度检索用于 few-shot 注入"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Case:
    """案例"""

    case_id: str = ""
    domain_id: str = ""
    phase_id: str = ""
    input_summary: str = ""
    output_preview: str = ""
    quality_score: float = 0.0
    tags: list[str] = field(default_factory=list)
    created_at: str = ""


class CaseLibrary:
    """案例库"""

    def __init__(self, library_dir: str):
        self.library_dir = Path(library_dir)
        self.library_dir.mkdir(parents=True, exist_ok=True)
        self._index_file = self.library_dir / "index.jsonl"
        self._cases: list[Case] = []
        self._load_index()

    def _load_index(self) -> None:
        if not self._index_file.exists():
            return
        for line in self._index_file.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                data = json.loads(line)
                self._cases.append(Case(**data))
            except (json.JSONDecodeError, TypeError):
                continue

    def add_case(self, case: Case, output_content: str = "") -> None:
        """添加案例"""
        self._cases.append(case)

        # 追加到索引
        with open(self._index_file, "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "case_id": case.case_id,
                "domain_id": case.domain_id,
                "phase_id": case.phase_id,
                "input_summary": case.input_summary[:200],
                "output_preview": case.output_preview[:200],
                "quality_score": case.quality_score,
                "tags": case.tags,
                "created_at": case.created_at,
            }, ensure_ascii=False) + "\n")

        # 保存完整输出
        if output_content:
            case_file = self.library_dir / f"{case.case_id}.md"
            case_file.write_text(output_content, encoding="utf-8")

    def search(
        self,
        domain_id: str | None = None,
        phase_id: str | None = None,
        min_score: float = 0.0,
        limit: int = 5,
    ) -> list[Case]:
        """搜索案例"""
        results = []
        for case in self._cases:
            if domain_id and case.domain_id != domain_id:
                continue
            if phase_id and case.phase_id != phase_id:
                continue
            if case.quality_score < min_score:
                continue
            results.append(case)

        results.sort(key=lambda c: c.quality_score, reverse=True)
        return results[:limit]

    def get_case_content(self, case_id: str) -> str | None:
        """获取案例完整内容"""
        case_file = self.library_dir / f"{case_id}.md"
        if case_file.exists():
            return case_file.read_text(encoding="utf-8")
        return None

    @property
    def count(self) -> int:
        return len(self._cases)
