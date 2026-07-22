"""级联模型路由测试"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from lemma.llm.cascade import CascadeRouter


class TestCascadeRouter:
    def test_create_router(self):
        stages = [
            {"model": "gpt-4o-mini", "quality_threshold": 0.7},
            {"model": "gpt-4o", "quality_threshold": 0.95},
        ]
        router = CascadeRouter(stages)
        assert router is not None

    def test_backends_property(self):
        stages = [{"model": "gpt-4o-mini"}, {"model": "gpt-4o"}]
        router = CascadeRouter(stages)
        assert isinstance(router.backends, dict)

    def test_estimate_quality_empty(self):
        assert CascadeRouter._estimate_quality("") == 0.0

    def test_estimate_quality_short(self):
        assert CascadeRouter._estimate_quality("hi") == 0.0

    def test_estimate_quality_good_text(self):
        text = "## 分析\n\n这是一个详细的分析。\n\n| 项目 | 值 |\n|------|-----|\n| A | 1 |\n\n```python\nx = 1\n```"
        score = CascadeRouter._estimate_quality(text)
        assert score > 0.5

    def test_estimate_quality_with_chinese_punctuation(self):
        text = "这是一个包含中文标点的长文本，用于测试质量评估。模型应该给出合理的分数，需要超过五十个字符才能被评分。"
        score = CascadeRouter._estimate_quality(text)
        assert score > 0.0


class TestCascadeLLMJudge:
    @pytest.mark.asyncio
    async def test_llm_judge_fallback_on_none_backend(self):
        """无 backend 时应回退到启发式"""
        quality = await CascadeRouter._llm_judge_quality("## 高质量文本\n\n有结构的回答。", backend=None)
        # 应为启发式评分
        assert 0.0 <= quality <= 1.0

    @pytest.mark.asyncio
    async def test_llm_judge_returns_number(self):
        """LLM Judge 应返回 0-1 之间的浮点数"""
        mock_backend = AsyncMock()
        mock_backend.generate = AsyncMock()
        mock_backend.generate.return_value.content = '{"逻辑性": 2, "完整性": 2, "清晰度": 2, "实用性": 2, "创新性": 1}'

        quality = await CascadeRouter._llm_judge_quality("这是一段测试文本。需要至少三十个字符才能被处理。这里补充一些内容。", backend=mock_backend)
        assert isinstance(quality, float)
        assert 0.0 <= quality <= 1.0

    @pytest.mark.asyncio
    async def test_llm_judge_malformed_json_fallback(self):
        """JSON 解析失败应回退到启发式"""
        mock_backend = AsyncMock()
        mock_backend.generate = AsyncMock()
        mock_backend.generate.return_value.content = "不是 JSON 格式的响应"

        quality = await CascadeRouter._llm_judge_quality("这是一段测试文本，用于验证。需要五十个字符才能触发评分。因此这里补充足够的内容以确保能够正常运作。", backend=mock_backend)
        # 应触发回退
        assert isinstance(quality, float)
        assert 0.0 <= quality <= 1.0

    @pytest.mark.asyncio
    async def test_llm_judge_empty_text(self):
        """空文本应返回 0.0"""
        mock_backend = AsyncMock()
        quality = await CascadeRouter._llm_judge_quality("", backend=mock_backend)
        assert quality == 0.0

    @pytest.mark.asyncio
    async def test_generate_with_fallback_llm_judge_mode(self):
        """use_llm_judge=True 时 LLM Judge 应被调用"""
        stages = [
            {"model": "tiny-model", "quality_threshold": 0.5},
        ]
        router = CascadeRouter(stages)

        # Mock 第一个阶段的 backend
        tiny_backend = AsyncMock()
        tiny_backend.generate.return_value.content = "## 测试\n\n有一定质量的回答内容。"
        router._backends["tiny-model"] = tiny_backend

        # 设置同模型作为 judge
        result = await router.generate_with_fallback(
            [{"role": "user", "content": "test"}],
            use_llm_judge=True,
        )
        assert result is not None
        assert result.content == tiny_backend.generate.return_value.content
