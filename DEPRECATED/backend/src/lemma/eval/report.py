"""评测报告 — 生成评测结果报告与版本对比"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from .scorers import ScoreResult


@dataclass
class CaseResult:
    """单条用例的评测结果"""

    case_id: str
    scores: list[ScoreResult]
    output_preview: str = ""

    @property
    def total_score(self) -> float:
        if not self.scores:
            return 0.0
        return sum(s.score for s in self.scores) / len(self.scores)

    @property
    def all_passed(self) -> bool:
        return all(s.passed for s in self.scores)


@dataclass
class EvalReport:
    """评测报告"""

    domain_id: str
    version: str = "unknown"
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    cases: list[CaseResult] = field(default_factory=list)

    @property
    def total_cases(self) -> int:
        return len(self.cases)

    @property
    def passed_cases(self) -> int:
        return sum(1 for c in self.cases if c.all_passed)

    @property
    def avg_score(self) -> float:
        if not self.cases:
            return 0.0
        return sum(c.total_score for c in self.cases) / len(self.cases)

    def score_by_dimension(self) -> dict[str, float]:
        """按维度汇总平均分"""
        dim_scores: dict[str, list[float]] = {}
        for case in self.cases:
            for s in case.scores:
                dim_scores.setdefault(s.name, []).append(s.score)
        return {name: sum(scores) / len(scores) for name, scores in dim_scores.items()}

    def to_markdown(self) -> str:
        """生成 Markdown 格式报告"""
        lines = [
            f"# 评测报告: {self.domain_id}",
            f"",
            f"**版本**: {self.version}  ",
            f"**时间**: {self.timestamp}  ",
            f"**用例数**: {self.total_cases}  ",
            f"**通过率**: {self.passed_cases}/{self.total_cases} ({self.passed_cases / max(1, self.total_cases) * 100:.0f}%)  ",
            f"**平均分**: {self.avg_score:.3f}",
            "",
            "## 各维度得分",
            "",
            "| 维度 | 得分 |",
            "|------|------|",
        ]
        for name, score in self.score_by_dimension().items():
            lines.append(f"| {name} | {score:.3f} |")

        lines.extend(["", "## 用例明细", ""])
        for case in self.cases:
            status = "✅" if case.all_passed else "❌"
            lines.append(f"### {status} {case.case_id} — {case.total_score:.3f}")
            for s in case.scores:
                passed = "✅" if s.passed else "❌"
                lines.append(f"- {passed} **{s.name}**: {s.score:.3f} — {s.detail}")
            lines.append("")

        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "domain_id": self.domain_id,
            "version": self.version,
            "timestamp": self.timestamp,
            "total_cases": self.total_cases,
            "passed_cases": self.passed_cases,
            "avg_score": self.avg_score,
            "score_by_dimension": self.score_by_dimension(),
            "cases": [
                {
                    "case_id": c.case_id,
                    "total_score": c.total_score,
                    "all_passed": c.all_passed,
                    "scores": [
                        {"name": s.name, "score": s.score, "passed": s.passed, "detail": s.detail}
                        for s in c.scores
                    ],
                }
                for c in self.cases
            ],
        }

    def save(self, path: str) -> None:
        """保存报告到 JSON 文件"""
        Path(path).write_text(
            json.dumps(self.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    @classmethod
    def load(cls, path: str) -> EvalReport:
        """从 JSON 文件加载报告"""
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        cases = []
        for c in data.get("cases", []):
            scores = [
                ScoreResult(s["name"], s["score"], s["passed"], s.get("detail", ""))
                for s in c.get("scores", [])
            ]
            cases.append(CaseResult(c["case_id"], scores, c.get("output_preview", "")))
        return cls(
            domain_id=data["domain_id"],
            version=data.get("version", "unknown"),
            timestamp=data.get("timestamp", ""),
            cases=cases,
        )

    def compare(self, old: EvalReport) -> dict:
        """与旧报告对比，返回 diff"""
        old_scores = {c.case_id: c.total_score for c in old.cases}
        new_scores = {c.case_id: c.total_score for c in self.cases}

        improved = []
        regressed = []
        unchanged = []

        for case_id in set(list(old_scores.keys()) + list(new_scores.keys())):
            old_s = old_scores.get(case_id, 0.0)
            new_s = new_scores.get(case_id, 0.0)
            diff = new_s - old_s
            if diff > 0.01:
                improved.append({"case_id": case_id, "old": old_s, "new": new_s, "diff": diff})
            elif diff < -0.01:
                regressed.append({"case_id": case_id, "old": old_s, "new": new_s, "diff": diff})
            else:
                unchanged.append(case_id)

        return {
            "improved": improved,
            "regressed": regressed,
            "unchanged": unchanged,
            "old_avg": old.avg_score,
            "new_avg": self.avg_score,
            "avg_diff": self.avg_score - old.avg_score,
        }
