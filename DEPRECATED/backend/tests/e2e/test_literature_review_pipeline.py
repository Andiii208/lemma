"""E2E 测试：literature-review 领域全流程（Mock LLM）"""
import pytest
import os
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from lemma.engine.agent import AcademicAgent
from lemma.engine.domain import DomainProfile
from lemma.llm.router import ModelRouter
from lemma.llm.backend import LLMConfig, LLMResponse
from lemma.tools.registry import ToolRegistry

DOMAINS_DIR = str(Path(__file__).parent.parent.parent.parent / "domains")


def make_mock_response(content: str = "文献检索完成。") -> LLMResponse:
    return LLMResponse(
        content=content,
        model="mock-model",
        usage={"prompt_tokens": 90, "completion_tokens": 45},
        finish_reason="stop",
    )


@pytest.fixture
def lit_domain():
    return DomainProfile.from_directory(os.path.join(DOMAINS_DIR, "literature-review"))


@pytest.fixture
def mock_router():
    config = LLMConfig(api_key="test", model="gpt-4o")
    router = ModelRouter.from_single_config(config)
    backend = MagicMock()
    backend.generate = AsyncMock(return_value=make_mock_response(
        "## 检索策略\n关键词：transformer, time series\n数据库：Web of Science\n\n| 字段 | 内容 |\n|------|------|\n| 结论 | 检索策略确定 |\n| 置信度 | green |"
    ))
    router.get_default_backend = MagicMock(return_value=backend)
    router.backends = {"default": backend}
    return router


class TestLiteratureReviewPipeline:
    @pytest.mark.asyncio
    async def test_agent_creation_with_lit_domain(self, tmp_path, lit_domain):
        """文献综述领域 Agent 应能正确创建"""
        router = ModelRouter.from_single_config(LLMConfig(api_key="test", model="gpt-4o"))
        tools = ToolRegistry()
        agent = AcademicAgent(
            work_dir=str(tmp_path / "workspace"),
            domain=lit_domain,
            llm_router=router,
            tool_registry=tools,
        )
        assert agent.domain.id == "literature-review"
        assert len(agent.domain.phases) >= 5

    @pytest.mark.asyncio
    async def test_five_roles_exist(self, lit_domain):
        """文献综述应有 5 个角色（lead/researcher/analyst/synthesizer/editor）"""
        role_ids = [r.id for r in lit_domain.roles]
        assert "lead" in role_ids
        assert "researcher" in role_ids
        assert "analyst" in role_ids
        assert "synthesizer" in role_ids
        assert "editor" in role_ids

    @pytest.mark.asyncio
    async def test_domain_phases_have_handlers(self, lit_domain):
        """所有非 idle/done 阶段都应有 phase_handler"""
        for phase in lit_domain.phases:
            if phase.id in ("idle", "done"):
                continue
            assert phase.id in lit_domain.phase_handlers, f"Phase {phase.id} missing handler"

    @pytest.mark.asyncio
    async def test_run_auto_yields_events(self, tmp_path, lit_domain, mock_router):
        """run_auto 应产出事件"""
        tools = ToolRegistry()
        agent = AcademicAgent(
            work_dir=str(tmp_path / "workspace"),
            domain=lit_domain,
            llm_router=mock_router,
            tool_registry=tools,
        )
        events = []
        async for event in agent.run_auto("综述主题：Transformer 在时间序列预测中的应用"):
            events.append(event)
            if len(events) > 20:
                break

        event_types = [e["type"] for e in events]
        assert "start" in event_types
        assert "phase_start" in event_types

    @pytest.mark.asyncio
    async def test_domain_roles_have_prompts(self, lit_domain):
        """所有角色都应有 system_prompt"""
        for role in lit_domain.roles:
            assert role.system_prompt, f"Role {role.id} missing system_prompt"
