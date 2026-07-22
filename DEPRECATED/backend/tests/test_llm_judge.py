"""LLM Judge 单元测试 — 覆盖缓存、评分、边界条件"""

import pytest
from unittest.mock import AsyncMock, patch
from lemma.eval.llm_judge import LLMJudge, _cache_key
from lemma.eval.scorers import ScoreResult


class TestCacheKey:
    def test_cache_key_deterministic(self):
        key1 = _cache_key("output text", "criteria text")
        key2 = _cache_key("output text", "criteria text")
        assert key1 == key2

    def test_cache_key_different_output(self):
        key1 = _cache_key("output A", "criteria")
        key2 = _cache_key("output B", "criteria")
        assert key1 != key2


class TestLLMJudge:
    def test_judge_creation(self):
        judge = LLMJudge()
        assert judge.model == "gpt-4o-mini"
        assert judge._cache_hits == 0
        assert judge._cache_misses == 0

    def test_judge_with_cache_dir(self, tmp_path):
        judge = LLMJudge(cache_dir=str(tmp_path))
        assert judge._cache_dir is not None

    def test_cache_miss_returns_none(self, tmp_path):
        judge = LLMJudge(cache_dir=str(tmp_path))
        result = judge._get_cached("nonexistent_key")
        assert result is None

    def test_cache_set_and_get(self, tmp_path):
        judge = LLMJudge(cache_dir=str(tmp_path))
        result = ScoreResult(name="test", score=8.0, passed=True, detail="好")
        judge._set_cache("test_key", result)

        cached = judge._get_cached("test_key")
        assert cached is not None
        assert cached.score == 8.0
        assert cached.passed is True
        assert cached.name == "test"

    def test_cache_hit_counter(self, tmp_path):
        judge = LLMJudge(cache_dir=str(tmp_path))
        result = ScoreResult(name="hit", score=9.0, passed=True, detail="h")
        judge._set_cache("hit_key", result)
        judge._get_cached("hit_key")
        assert judge._cache_hits == 1

    def test_memory_cache_faster_than_disk(self, tmp_path):
        judge = LLMJudge(cache_dir=str(tmp_path))
        result = ScoreResult(name="mem", score=7.0, passed=True, detail="mem")
        judge._set_cache("mem_key", result)
        judge._get_cached("mem_key")
        judge._get_cached("mem_key")
        assert judge._cache_hits == 2

    @pytest.mark.asyncio
    async def test_score_with_cache(self, tmp_path):
        """相同产出再次评分应命中缓存"""
        judge = LLMJudge(cache_dir=str(tmp_path))

        mock_response = AsyncMock()
        mock_response.content = '{"score": 0.85, "reason": "逻辑清晰"}'

        with patch("lemma.llm.backend.LLMBackend") as mock_cls:
            instance = mock_cls.return_value
            instance.generate = AsyncMock(return_value=mock_response)

            result1 = await judge.score("测试输出", "清晰度")
            assert result1.score == 0.85
            assert result1.passed is True

            # 相同内容再次评分应命中缓存
            result2 = await judge.score("测试输出", "清晰度")
            assert result2.score == 0.85
            assert judge._cache_hits >= 1

    @pytest.mark.asyncio
    async def test_score_with_different_inputs(self, tmp_path):
        """不同输入不共享缓存"""
        judge = LLMJudge(cache_dir=str(tmp_path))

        mock_response = AsyncMock()
        mock_response.content = '{"score": 0.5, "reason": ""}'

        with patch("lemma.llm.backend.LLMBackend") as mock_cls:
            instance = mock_cls.return_value
            instance.generate = AsyncMock(return_value=mock_response)

            await judge.score("输出A", "标准1")
            await judge.score("输出B", "标准2")

            assert judge._cache_misses == 2

    def test_cache_stats(self, tmp_path):
        judge = LLMJudge(cache_dir=str(tmp_path))
        stats = judge.cache_stats
        assert "hits" in stats
        assert "misses" in stats
        assert "memory_size" in stats
