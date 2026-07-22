"""E2E 测试：math-modeling 领域全流程（Mock LLM）"""
import pytest
import asyncio
import os
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from lemma.engine.agent import AcademicAgent
from lemma.engine.domain import DomainProfile
from lemma.llm.router import ModelRouter
from lemma.llm.backend import LLMConfig, LLMResponse
from lemma.tools.registry import ToolRegistry
from lemma.tools.file_manager import FileManagerTool
from lemma.tools.code_executor import CodeExecutorTool

DOMAINS_DIR = str(Path(__file__).parent.parent.parent.parent / "domains")


def make_mock_response(content: str = "分析完成。") -> LLMResponse:
    return LLMResponse(
        content=content,
        model="mock-model",
        usage={"prompt_tokens": 100, "completion_tokens": 50},
        finish_reason="stop",
    )


@pytest.fixture
def math_domain():
    return DomainProfile.from_directory(os.path.join(DOMAINS_DIR, "math-modeling"))


@pytest.fixture
def mock_router():
    config = LLMConfig(api_key="test", model="gpt-4o")
    router = ModelRouter.from_single_config(config)
    backend = MagicMock()
    backend.generate = AsyncMock(return_value=make_mock_response(
        "## 题目分析\n这是一个优化问题。\n\n| 字段 | 内容 |\n|------|------|\n| 结论 | 线性规划模型 |\n| 置信度 | green |"
    ))
    backend.generate_stream = AsyncMock(return_value=iter(["分析", "完成"]))
    router.get_default_backend = MagicMock(return_value=backend)
    router.backends = {"default": backend}
    return router


class TestMathModelingPipeline:
    @pytest.mark.asyncio
    async def test_agent_creation_with_math_domain(self, tmp_path, math_domain):
        """数学建模领域 Agent 应能正确创建"""
        router = ModelRouter.from_single_config(LLMConfig(api_key="test", model="gpt-4o"))
        tools = ToolRegistry()
        agent = AcademicAgent(
            work_dir=str(tmp_path / "workspace"),
            domain=math_domain,
            llm_router=router,
            tool_registry=tools,
        )
        assert agent.domain.id == "math-modeling"
        assert len(agent.domain.phases) >= 6

    @pytest.mark.asyncio
    async def test_run_auto_yields_phase_events(self, tmp_path, math_domain, mock_router):
        """run_auto 应产出 phase_start 和 phase_end 事件"""
        tools = ToolRegistry()
        tools.register(FileManagerTool(str(tmp_path)))
        agent = AcademicAgent(
            work_dir=str(tmp_path / "workspace"),
            domain=math_domain,
            llm_router=mock_router,
            tool_registry=tools,
        )

        events = []
        async for event in agent.run_auto("测试题目内容"):
            events.append(event)
            if len(events) > 30:
                break

        event_types = [e["type"] for e in events]
        assert "start" in event_types
        assert "phase_start" in event_types
        # 应有 phase_end 或 phase_error
        assert any(t in event_types for t in ("phase_end", "phase_error", "complete"))

    @pytest.mark.asyncio
    async def test_chat_returns_response(self, tmp_path, math_domain, mock_router):
        """chat 接口应返回 LLM 响应"""
        tools = ToolRegistry()
        agent = AcademicAgent(
            work_dir=str(tmp_path / "workspace"),
            domain=math_domain,
            llm_router=mock_router,
            tool_registry=tools,
        )
        response = await agent.chat("这是一个测试问题")
        assert len(response) > 0
        assert isinstance(response, str)

    @pytest.mark.asyncio
    async def test_domain_phases_have_handlers(self, math_domain):
        """所有非 idle/done 阶段都应有 phase_handler"""
        for phase in math_domain.phases:
            if phase.id in ("idle", "done"):
                continue
            assert phase.id in math_domain.phase_handlers, f"Phase {phase.id} missing handler"

    @pytest.mark.asyncio
    async def test_domain_roles_have_prompts(self, math_domain):
        """所有角色都应有 system_prompt"""
        for role in math_domain.roles:
            assert role.system_prompt, f"Role {role.id} missing system_prompt"
