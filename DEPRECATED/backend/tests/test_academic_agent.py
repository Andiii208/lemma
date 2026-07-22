"""AcademicAgent 单元测试"""
import pytest
from unittest.mock import AsyncMock
from pathlib import Path

from lemma.engine.domain import DomainProfile
from lemma.engine.agent import AcademicAgent
from lemma.llm.router import ModelRouter
from lemma.llm.backend import LLMConfig
from lemma.tools.registry import ToolRegistry


@pytest.fixture
def sample_domain(tmp_path):
    domain_dir = tmp_path / "test-domain"
    domain_dir.mkdir()
    (domain_dir / "domain.yaml").write_text("""
id: test
name: 测试领域
phases:
  - id: idle
    name: 空闲
    order: -1
    progress: 0
    transition: {pass: init}
  - id: init
    name: 初始化
    order: 0
    progress: 50
    transition: {pass: done}
  - id: done
    name: 完成
    order: 1
    progress: 100
roles:
  - id: lead
    name: Lead
    temperature: 0.5
    tools: []
directories:
  output: output
""", encoding="utf-8")
    return DomainProfile.from_directory(str(domain_dir))


@pytest.fixture
def sample_domain_with_handler(tmp_path):
    domain_dir = tmp_path / "test-domain-2"
    domain_dir.mkdir()
    prompts_dir = domain_dir / "prompts"
    prompts_dir.mkdir()
    (prompts_dir / "agent_lead.md").write_text("You are a test assistant.", encoding="utf-8")
    (prompts_dir / "phase_init.md").write_text("执行初始化，输入：{input_text}", encoding="utf-8")
    (domain_dir / "domain.yaml").write_text("""
id: test2
name: 测试领域2
phases:
  - id: idle
    name: 空闲
    order: -1
    progress: 0
    transition: {pass: init}
  - id: init
    name: 初始化
    order: 0
    progress: 50
    transition: {pass: done}
  - id: done
    name: 完成
    order: 1
    progress: 100
roles:
  - id: lead
    name: Lead
    temperature: 0.5
    tools: []
directories:
  output: output
""", encoding="utf-8")
    return DomainProfile.from_directory(str(domain_dir))


class TestAcademicAgent:
    def test_agent_creation(self, tmp_path, sample_domain):
        config = LLMConfig(api_key="test", model="gpt-4o")
        router = ModelRouter.from_single_config(config)
        tools = ToolRegistry()
        agent = AcademicAgent(
            work_dir=str(tmp_path / "workspace"),
            domain=sample_domain,
            llm_router=router,
            tool_registry=tools,
        )
        assert agent.domain.id == "test"
        assert agent.state.current_phase == "idle"
        assert agent.current_role_id == "lead"
        assert (tmp_path / "workspace" / "output").exists()

    def test_switch_role(self, tmp_path, sample_domain):
        config = LLMConfig(api_key="test", model="gpt-4o")
        router = ModelRouter.from_single_config(config)
        agent = AcademicAgent(
            work_dir=str(tmp_path / "workspace"),
            domain=sample_domain,
            llm_router=router,
            tool_registry=ToolRegistry(),
        )
        assert agent.current_role_id == "lead"
        agent.switch_role("nonexistent")
        assert agent.current_role_id == "lead"  # 无效角色不应切换

    def test_reset(self, tmp_path, sample_domain):
        config = LLMConfig(api_key="test", model="gpt-4o")
        router = ModelRouter.from_single_config(config)
        agent = AcademicAgent(
            work_dir=str(tmp_path / "workspace"),
            domain=sample_domain,
            llm_router=router,
            tool_registry=ToolRegistry(),
        )
        agent.reset()
        assert agent.state.current_phase == "idle"

    def test_get_status(self, tmp_path, sample_domain):
        config = LLMConfig(api_key="test", model="gpt-4o")
        router = ModelRouter.from_single_config(config)
        agent = AcademicAgent(
            work_dir=str(tmp_path / "workspace"),
            domain=sample_domain,
            llm_router=router,
            tool_registry=ToolRegistry(),
        )
        status = agent.get_status()
        assert "state" in status
        assert "current_role" in status
        assert status["current_role_name"] == "Lead"

    def test_run_auto_yields_events(self, tmp_path, sample_domain_with_handler):
        """带 handler 的 domain 应能执行 run_auto"""
        config = LLMConfig(api_key="test", model="gpt-4o")
        router = ModelRouter.from_single_config(config)
        tools = ToolRegistry()
        agent = AcademicAgent(
            work_dir=str(tmp_path / "workspace"),
            domain=sample_domain_with_handler,
            llm_router=router,
            tool_registry=tools,
        )

        async def run():
            events = []
            async for event in agent.run_auto("test input"):
                events.append(event)
            return events

        import asyncio
        events = asyncio.run(run())
        # 即使 LLM 调用失败，也应产生 start 和 phase_start 事件
        event_types = [e["type"] for e in events]
        assert "start" in event_types
        assert "phase_start" in event_types
        assert "phase_end" in event_types or "phase_error" in event_types or "error" in event_types
