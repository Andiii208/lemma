"""路由器单元测试"""
import pytest
from lemma.llm.router import ModelRouter, TaskType
from lemma.llm.backend import LLMConfig


class TestModelRouter:
    def test_from_single_config(self):
        config = LLMConfig(api_key="test", model="gpt-4o")
        router = ModelRouter.from_single_config(config)
        backend = router.get_default_backend()
        assert backend.model == "gpt-4o"

    def test_get_backend_returns_default_for_unknown(self):
        config = LLMConfig(api_key="test", model="gpt-4o")
        router = ModelRouter.from_single_config(config)
        backend = router.get_backend(TaskType.MATH_REASONING)
        assert backend.model == "gpt-4o"

    def test_all_task_types_routed(self):
        config = LLMConfig(api_key="test", model="gpt-4o")
        router = ModelRouter.from_single_config(config)
        for task_type in TaskType:
            backend = router.get_backend(task_type)
            assert backend is not None
