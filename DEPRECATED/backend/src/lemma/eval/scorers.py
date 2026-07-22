"""评测评分器 — 多维度自动评分"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Protocol


@dataclass
class ScoreResult:
    """单维度评分结果"""

    name: str
    score: float  # 0.0-1.0
    passed: bool
    detail: str = ""


class Scorer(Protocol):
    """评分器协议"""

    def score(self, text: str) -> ScoreResult: ...


class KeywordScorer:
    """关键词命中率评分"""

    def __init__(self, required: list[str], threshold: float = 0.6):
        self.required = required
        self.threshold = threshold

    def score(self, text: str) -> ScoreResult:
        if not self.required:
            return ScoreResult("keyword", 1.0, True, detail="无关键词要求")
        hits = sum(1 for kw in self.required if kw in text)
        ratio = hits / len(self.required)
        return ScoreResult(
            "keyword",
            ratio,
            ratio >= self.threshold,
            detail=f"{hits}/{len(self.required)} 命中",
        )


class LengthScorer:
    """文本长度评分"""

    def __init__(self, min_length: int = 500, optimal_length: int = 3000):
        self.min_length = min_length
        self.optimal_length = optimal_length

    def score(self, text: str) -> ScoreResult:
        n = len(text)
        if n < self.min_length:
            score = n / self.min_length * 0.5
        elif n >= self.optimal_length:
            score = 1.0
        else:
            score = 0.5 + 0.5 * (n - self.min_length) / (self.optimal_length - self.min_length)
        return ScoreResult(
            "length",
            min(1.0, score),
            n >= self.min_length,
            detail=f"{n}/{self.min_length} 字符",
        )


class StructureScorer:
    """结构完整性评分 — 检查必需章节"""

    def __init__(self, required_sections: list[str], threshold: float = 0.6):
        self.required_sections = required_sections
        self.threshold = threshold

    def score(self, text: str) -> ScoreResult:
        if not self.required_sections:
            return ScoreResult("structure", 1.0, True, detail="无章节要求")
        hits = sum(1 for sec in self.required_sections if sec in text)
        ratio = hits / len(self.required_sections)
        return ScoreResult(
            "structure",
            ratio,
            ratio >= self.threshold,
            detail=f"{hits}/{len(self.required_sections)} 章节",
        )


class LaTeXScorer:
    """LaTeX 编译性评分 — 检查基本 LaTeX 语法"""

    REQUIRED_ENVS = ["document", "equation"]
    DANGEROUS_CMDS = ["\\\\input\\{", "\\\\write18"]

    def score(self, text: str) -> ScoreResult:
        errors: list[str] = []

        # 检查花括号配对
        brace_count = text.count("{") - text.count("}")
        if abs(brace_count) > 2:
            errors.append(f"花括号不配对: 差 {brace_count}")

        # 检查 $ 配对（简单计数，偶数则配对）
        dollar_count = text.count("$")
        if dollar_count % 2 != 0:
            errors.append("$ 符号不配对")

        # 检查危险命令
        for cmd in self.DANGEROUS_CMDS:
            if re.search(cmd, text):
                errors.append(f"包含危险命令: {cmd}")

        score = max(0.0, 1.0 - len(errors) * 0.3)
        return ScoreResult(
            "latex",
            score,
            len(errors) == 0,
            detail="; ".join(errors) if errors else "语法基本正确",
        )


class CompositeScorer:
    """组合评分器 — 加权汇总多维度"""

    def __init__(self, scorers: list[tuple[Scorer, float]]):
        """
        Args:
            scorers: [(scorer, weight), ...] 权重会自动归一化
        """
        self.scorers = scorers
        total_weight = sum(w for _, w in scorers)
        self._weights = [(s, w / total_weight) for s, w in scorers] if total_weight > 0 else []

    def score(self, text: str) -> tuple[float, list[ScoreResult]]:
        """返回 (加权总分, 各维度详情)"""
        results: list[ScoreResult] = []
        weighted_sum = 0.0
        for scorer, weight in self._weights:
            result = scorer.score(text)
            results.append(result)
            weighted_sum += result.score * weight
        return min(1.0, weighted_sum), results
