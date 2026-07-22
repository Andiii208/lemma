"""E2E 测试：lab-report 领域全流程（Mock LLM）"""
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


def make_mock_response(content: str = "实验设计完成。") -> LLMResponse:
    return LLMResponse(
        content=content,
        model="mock-model",
        usage={"prompt_tokens": 80, "completion_tokens": 40},
        finish_reason="stop",
    )


@pytest.fixture
def lab_domain():
    return DomainProfile.from_directory(os.path.join(DOMAINS_DIR, "lab-report"))


@pytest.fixture
def mock_router():
    config = LLMConfig(api_key="test", model="gpt-4o")
    router = ModelRouter.from_single_config(config)
    backend = MagicMock()
    backend.generate = AsyncMock(return_value=make_mock_response(
        "## 实验设计\n自变量：温度\n因变量：反应速率\n\n| 字段 | 内容 |\n|------|------|\n| 结论 | 实验方案确定 |\n| 置信度 | green |"
    ))
    router.get_default_backend = MagicMock(return_value=backend)
    router.backends = {"default": backend}
    return router


class TestLabReportPipeline:
    @pytest.mark.asyncio
    async def test_agent_creation_with_lab_domain(self, tmp_path, lab_domain):
        """实验报告领域 Agent 应能正确创建"""
        router = ModelRouter.from_single_config(LLMConfig(api_key="test", model="gpt-4o"))
        tools = ToolRegistry()
        agent = AcademicAgent(
            work_dir=str(tmp_path / "workspace"),
            domain=lab_domain,
            llm_router=router,
            tool_registry=tools,
        )
        assert agent.domain.id == "lab-report"
        assert len(agent.domain.phases) >= 4

    @pytest.mark.asyncio
    async def test_domain_phases_have_handlers(self, lab_domain):
        """所有非 idle/done 阶段都应有 phase_handler"""
        for phase in lab_domain.phases:
            if phase.id in ("idle", "done"):
                continue
            assert phase.id in lab_domain.phase_handlers, f"Phase {phase.id} missing handler"

    @pytest.mark.asyncio
    async def test_run_auto_yields_events(self, tmp_path, lab_domain, mock_router):
        """run_auto 应产出事件"""
        tools = ToolRegistry()
        agent = AcademicAgent(
            work_dir=str(tmp_path / "workspace"),
            domain=lab_domain,
            llm_router=mock_router,
            tool_registry=tools,
        )
        events = []
        async for event in agent.run_auto("实验目标：测试温度对反应速率的影响"):
            events.append(event)
            if len(events) > 20:
                break

        event_types = [e["type"] for e in events]
        assert "start" in event_types
        assert "phase_start" in event_types

    @pytest.mark.asyncio
    async def test_domain_roles_have_prompts(self, lab_domain):
        """所有角色都应有 system_prompt"""
        for role in lab_domain.roles:
            assert role.system_prompt, f"Role {role.id} missing system_prompt"
