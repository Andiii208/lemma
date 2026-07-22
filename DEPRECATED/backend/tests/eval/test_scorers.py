"""评测评分器测试"""

import pytest
from lemma.eval.scorers import (
    KeywordScorer,
    LengthScorer,
    LaTeXScorer,
    StructureScorer,
    CompositeScorer,
    ScoreResult,
)


class TestKeywordScorer:
    def test_all_hit(self):
        s = KeywordScorer(required=["排队论", "灵敏度分析"])
        result = s.score("本文使用排队论，并做了灵敏度分析")
        assert result.score == 1.0
        assert result.passed is True

    def test_partial(self):
        s = KeywordScorer(required=["排队论", "马尔可夫"])
        r = s.score("只提了排队论")
        assert 0.4 < r.score < 0.6
        assert r.passed is False

    def test_no_keywords(self):
        s = KeywordScorer(required=[])
        r = s.score("任何文本")
        assert r.score == 1.0
        assert r.passed is True

    def test_custom_threshold(self):
        s = KeywordScorer(required=["a", "b", "c"], threshold=0.3)
        r = s.score("a")
        assert r.passed is True  # 1/3 >= 0.3


class TestLengthScorer:
    def test_below_min(self):
        s = LengthScorer(min_length=100)
        r = s.score("短")
        assert r.score < 0.5
        assert r.passed is False

    def test_above_optimal(self):
        s = LengthScorer(min_length=100, optimal_length=200)
        r = s.score("x" * 300)
        assert r.score == 1.0
        assert r.passed is True

    def test_between_min_and_optimal(self):
        s = LengthScorer(min_length=100, optimal_length=200)
        r = s.score("x" * 150)
        assert 0.5 < r.score < 1.0
        assert r.passed is True


class TestStructureScorer:
    def test_all_sections_present(self):
        s = StructureScorer(required_sections=["摘要", "问题重述", "模型"])
        text = "## 摘要\n...\n## 问题重述\n...\n## 模型建立\n..."
        r = s.score(text)
        assert r.passed is True
        assert r.score == 1.0

    def test_partial_sections(self):
        s = StructureScorer(required_sections=["摘要", "问题重述", "模型"])
        text = "## 摘要\n...\n## 模型\n..."
        r = s.score(text)
        assert r.score < 1.0

    def test_no_sections(self):
        s = StructureScorer(required_sections=[])
        r = s.score("任何文本")
        assert r.score == 1.0


class TestLaTeXScorer:
    def test_balanced_braces(self):
        s = LaTeXScorer()
        r = s.score("\\begin{equation} x = y \\end{equation}")
        assert r.passed is True

    def test_unbalanced_braces(self):
        s = LaTeXScorer()
        r = s.score("\\begin{equation x = y \\end{equation}}}}}}}}}}}}}")
        assert r.passed is False

    def test_balanced_dollars(self):
        s = LaTeXScorer()
        r = s.score("公式 $x = y$ 和 $z = w$")
        assert r.passed is True

    def test_unbalanced_dollars(self):
        s = LaTeXScorer()
        r = s.score("公式 $x = y 和 z = w")
        assert r.passed is False


class TestCompositeScorer:
    def test_weighted_average(self):
        s1 = KeywordScorer(required=["关键词"])
        s2 = LengthScorer(min_length=10)
        composite = CompositeScorer([(s1, 1.0), (s2, 1.0)])
        text = "这里包含关键词，而且文本足够长超过十个字符"
        total, results = composite.score(text)
        assert total > 0.6
        assert len(results) == 2

    def test_normalized_weights(self):
        s1 = KeywordScorer(required=["x"])
        s2 = LengthScorer(min_length=1)
        composite = CompositeScorer([(s1, 3.0), (s2, 1.0)])
        total, results = composite.score("x" * 100)
        assert total > 0.7
