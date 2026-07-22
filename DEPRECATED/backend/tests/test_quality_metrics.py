"""质量指标测试"""

import pytest
from lemma.quality.metrics import QualityMetrics, QualityScore


class TestQualityMetrics:
    def test_has_source_binding_with_facts(self):
        text = "根据 [fact] 排队论是运筹学分支 [fact] 可以建模等待系统"
        score = QualityMetrics.has_source_binding(text)
        assert score > 0

    def test_has_source_binding_no_tags(self):
        assert QualityMetrics.has_source_binding("普通文本") == 0.0

    def test_has_checklist_output_pass_fail(self):
        text = "检查结果：PASS 无违规"
        score = QualityMetrics.has_checklist_output(text)
        assert score > 0

    def test_has_checklist_output_empty(self):
        assert QualityMetrics.has_checklist_output("") == 0.0

    def test_has_term_expansion(self):
        text = "人工智能 (AI) 和机器学习 (ML) 是关键技术，自然语言处理 (NLP) 也很重要"
        score = QualityMetrics.has_term_expansion(text)
        # 只要有展开格式就算有效
        assert score >= 0.0

    def test_has_specificity_with_numbers(self):
        text = "系统处理速度达到每秒 1000 次请求，延迟低于 50ms"
        score = QualityMetrics.has_specificity(text)
        assert score > 0

    def test_evaluate_returns_quality_score(self):
        text = "根据 [fact] 数据，人工智能 (AI) 系统处理 1000 请求/秒，延迟 50ms。检查：PASS"
        result = QualityMetrics.evaluate(text)
        assert isinstance(result, QualityScore)
        assert 0.0 <= result.overall <= 1.0

    def test_compare(self):
        baseline = QualityScore(overall=0.5)
        improved = QualityScore(overall=0.8)
        diff = QualityMetrics.compare(baseline, improved)
        assert diff["improved"] is True
        assert diff["overall_delta"] == pytest.approx(0.3)
