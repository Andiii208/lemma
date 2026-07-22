"""Multi-Agent 辩论机制测试"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from lemma.engine.debate import AgentDebate


class TestAgentDebate:
    @pytest.fixture
    def mock_agent(self):
        agent = MagicMock()
        agent.chat = AsyncMock(side_effect=["方案A回答", "方案B回答", "综合裁决"])
        agent.switch_role = MagicMock()
        agent.current_role_id = "lead"
        return agent

    @pytest.mark.asyncio
    async def test_debate_returns_synthesis(self, mock_agent):
        debate = AgentDebate(mock_agent)
        result = await debate.debate("测试问题", "math", "engineer", rounds=1)
        assert result == "综合裁决"
        assert mock_agent.chat.call_count == 3

    @pytest.mark.asyncio
    async def test_debate_switches_roles(self, mock_agent):
        debate = AgentDebate(mock_agent)
        await debate.debate("问题", "math", "engineer")
        roles_called = [call.args[0] for call in mock_agent.switch_role.call_args_list]
        assert "math" in roles_called
        assert "engineer" in roles_called
        assert "lead" in roles_called

    @pytest.mark.asyncio
    async def test_debate_restores_original_role(self, mock_agent):
        mock_agent.current_role_id = "writer"
        debate = AgentDebate(mock_agent)
        await debate.debate("问题", "math", "engineer")
        # 最后一次 switch_role 应该恢复原始角色
        last_role = mock_agent.switch_role.call_args_list[-1].args[0]
        assert last_role == "writer"

    def test_build_synthesis_prompt(self):
        responses = [
            {"role": "math", "response": "使用排队论"},
            {"role": "engineer", "response": "使用模拟方法"},
        ]
        prompt = AgentDebate._build_synthesis_prompt(responses)
        assert "math" in prompt
        assert "排队论" in prompt
        assert "模拟方法" in prompt

    def test_build_synthesis_prompt_truncates_long_response(self):
        responses = [{"role": "a", "response": "x" * 5000}]
        prompt = AgentDebate._build_synthesis_prompt(responses)
        assert len(prompt) < 5000  # 应该被截断
