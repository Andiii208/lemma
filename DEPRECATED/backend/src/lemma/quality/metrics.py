"""输出质量评分 — 可对比 prompt 改进前后效果"""
from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class QualityScore:
    """单次输出的质量评分"""
    source_binding: float = 0.0      # [fact]/[inference] 标签比例
    checklist_output: float = 0.0    # 结构化审查清单
    term_expansion: float = 0.0      # 缩写首次展开
    specificity: float = 0.0         # 具体数值 vs 模糊量词
    overall: float = 0.0
    details: list[str] = field(default_factory=list)


class QualityMetrics:
    """评估 Agent 输出的质量维度"""

    @staticmethod
    def has_source_binding(text: str) -> float:
        """检查断言是否绑定来源（[fact] 标签比例）"""
        facts = text.count("[fact]")
        inferences = text.count("[inference]")
        total = facts + inferences
        return facts / total if total > 0 else 0.0

    @staticmethod
    def has_checklist_output(text: str) -> float:
        """检查是否输出结构化审查清单"""
        has_pass = "PASS" in text or "FAIL" in text
        has_violations = "VIOLATION" in text or "违规" in text
        has_target = "REVIEW_TARGET" in text or "审查对象" in text
        score = 0.0
        if has_pass:
            score += 0.4
        if has_violations:
            score += 0.3
        if has_target:
            score += 0.3
        return min(1.0, score)

    @staticmethod
    def has_term_expansion(text: str) -> float:
        """检查缩写首次出现时是否展开（全称+缩写格式）"""
        expanded = len(re.findall(r'[\u4e00-\u9fff\w]+（[A-Z]+）', text))
        raw_abbrev = len(re.findall(r'(?<!（)[A-Z]{2,}(?!）)', text))
        total = expanded + raw_abbrev
        return expanded / total if total > 0 else 1.0

    @staticmethod
    def has_specificity(text: str) -> float:
        """检查具体数值 vs 模糊量词"""
        vague = len(re.findall(r'许多|大量|显著|一些|若干|部分', text))
        specific = len(re.findall(r'\d+\.?\d*\s*(%|个|篇|次|倍|元)', text))
        total = vague + specific
        return specific / total if total > 0 else 0.5

    @classmethod
    def evaluate(cls, text: str) -> QualityScore:
        """综合评估一次输出的质量"""
        score = QualityScore()
        score.source_binding = cls.has_source_binding(text)
        score.checklist_output = cls.has_checklist_output(text)
        score.term_expansion = cls.has_term_expansion(text)
        score.specificity = cls.has_specificity(text)

        # 加权平均
        score.overall = (
            score.source_binding * 0.3 +
            score.checklist_output * 0.25 +
            score.term_expansion * 0.2 +
            score.specificity * 0.25
        )

        if score.source_binding < 0.5:
            score.details.append("来源绑定不足：缺少 [fact]/[inference] 标签")
        if score.checklist_output < 0.3:
            score.details.append("缺少结构化审查清单（PASS/FAIL）")
        if score.specificity < 0.3:
            score.details.append("模糊量词过多，缺少具体数值")

        return score

    @classmethod
    def compare(cls, baseline: QualityScore, improved: QualityScore) -> dict:
        """对比两次输出的质量差异"""
        return {
            "source_binding_delta": improved.source_binding - baseline.source_binding,
            "checklist_delta": improved.checklist_output - baseline.checklist_output,
            "term_expansion_delta": improved.term_expansion - baseline.term_expansion,
            "specificity_delta": improved.specificity - baseline.specificity,
            "overall_delta": improved.overall - baseline.overall,
            "improved": improved.overall > baseline.overall,
        }
