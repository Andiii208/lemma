"""多 Agent 拓扑测试"""

import asyncio
import pytest
from lemma.orchestration.topology import (
    TopologyType,
    TopologyExecutor,
    TopologyResult,
    AgentNode,
)


class TestTopologyExecutor:
    @pytest.mark.asyncio
    async def test_sequential(self):
        calls = []

        async def caller(role_id: str, msg: str) -> str:
            calls.append(role_id)
            return f"[{role_id}] {msg}"

        executor = TopologyExecutor(caller)
        agents = [AgentNode("a", "A"), AgentNode("b", "B")]
        result = await executor.execute(TopologyType.SEQUENTIAL, agents, "input")

        assert result.topology == "sequential"
        assert calls == ["a", "b"]
        assert "b" in result.final_output

    @pytest.mark.asyncio
    async def test_parallel(self):
        async def caller(role_id: str, msg: str) -> str:
            return f"response from {role_id}"

        executor = TopologyExecutor(caller)
        agents = [AgentNode("x"), AgentNode("y")]
        result = await executor.execute(TopologyType.PARALLEL, agents, "input")

        assert result.topology == "parallel"
        assert "x" in result.outputs
        assert "y" in result.outputs

    @pytest.mark.asyncio
    async def test_debate(self):
        async def caller(role_id: str, msg: str) -> str:
            if role_id == "lead":
                return "选择方案 A"
            return f"方案 {role_id}"

        executor = TopologyExecutor(caller)
        agents = [AgentNode("a"), AgentNode("b"), AgentNode("lead")]
        result = await executor.execute(TopologyType.DEBATE, agents, "问题")

        assert result.topology == "debate"
        assert len(result.outputs) == 3
        assert "方案" in result.final_output or "选择" in result.final_output

    @pytest.mark.asyncio
    async def test_committee(self):
        async def caller(role_id: str, msg: str) -> str:
            return f"投票 {role_id}"

        executor = TopologyExecutor(caller)
        agents = [AgentNode("p1"), AgentNode("p2"), AgentNode("p3")]
        result = await executor.execute(TopologyType.COMMITTEE, agents, "问题")

        assert result.topology == "committee"
        assert len(result.outputs) == 3

    @pytest.mark.asyncio
    async def test_critic_actor(self):
        call_count = 0

        async def caller(role_id: str, msg: str) -> str:
            nonlocal call_count
            call_count += 1
            if role_id == "critic":
                if call_count >= 4:
                    return "通过，质量合格"
                return "需要改进：请增加更多细节"
            return "改进后的内容"

        executor = TopologyExecutor(caller)
        agents = [AgentNode("actor"), AgentNode("critic")]
        result = await executor.execute(
            TopologyType.CRITIC_ACTOR, agents, "任务", max_rounds=3
        )

        assert result.topology == "critic_actor"
        assert len(result.final_output) > 0

    @pytest.mark.asyncio
    async def test_debate_fallback_to_parallel(self):
        """不足 3 个 agent 时 debate 应 fallback 到 parallel"""
        async def caller(role_id: str, msg: str) -> str:
            return f"response {role_id}"

        executor = TopologyExecutor(caller)
        agents = [AgentNode("a"), AgentNode("b")]  # 只有 2 个
        result = await executor.execute(TopologyType.DEBATE, agents, "问题")
        assert result.topology == "parallel"
