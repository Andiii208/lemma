"""多 Agent 拓扑 — 支持可配置的协作模式

拓扑类型:
- sequential: 串行执行（默认）
- parallel: 并行执行所有角色
- debate: 辩论 + 裁决
- committee: 投票委员会
- critic_actor: critic 反馈循环
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable


class TopologyType(str, Enum):
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    DEBATE = "debate"
    COMMITTEE = "committee"
    CRITIC_ACTOR = "critic_actor"


@dataclass
class AgentNode:
    """Agent 节点"""

    role_id: str
    name: str = ""
    temperature: float = 0.7


@dataclass
class TopologyResult:
    """拓扑执行结果"""

    topology: str = ""
    outputs: dict[str, str] = field(default_factory=dict)
    final_output: str = ""
    votes: dict[str, int] = field(default_factory=dict)


class TopologyExecutor:
    """拓扑执行器 — 根据拓扑类型编排多 Agent"""

    def __init__(self, agent_caller: Callable):
        """
        Args:
            agent_caller: async def(role_id: str, message: str) -> str
        """
        self.agent_caller = agent_caller

    async def execute(
        self,
        topology: TopologyType,
        agents: list[AgentNode],
        input_text: str,
        **kwargs: Any,
    ) -> TopologyResult:
        """执行拓扑"""
        if topology == TopologyType.SEQUENTIAL:
            return await self._sequential(agents, input_text)
        elif topology == TopologyType.PARALLEL:
            return await self._parallel(agents, input_text)
        elif topology == TopologyType.DEBATE:
            return await self._debate(agents, input_text, **kwargs)
        elif topology == TopologyType.COMMITTEE:
            return await self._committee(agents, input_text)
        elif topology == TopologyType.CRITIC_ACTOR:
            return await self._critic_actor(agents, input_text, **kwargs)
        else:
            raise ValueError(f"Unknown topology: {topology}")

    async def _sequential(
        self, agents: list[AgentNode], input_text: str
    ) -> TopologyResult:
        """串行执行：每个 Agent 的输出作为下一个的输入"""
        outputs: dict[str, str] = {}
        current_input = input_text

        for agent in agents:
            output = await self.agent_caller(agent.role_id, current_input)
            outputs[agent.role_id] = output
            current_input = output

        return TopologyResult(
            topology="sequential",
            outputs=outputs,
            final_output=current_input,
        )

    async def _parallel(
        self, agents: list[AgentNode], input_text: str
    ) -> TopologyResult:
        """并行执行：所有 Agent 同时处理"""
        tasks = [
            self.agent_caller(agent.role_id, input_text) for agent in agents
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        outputs: dict[str, str] = {}
        for agent, result in zip(agents, results):
            if isinstance(result, Exception):
                outputs[agent.role_id] = f"[错误: {result}]"
            else:
                outputs[agent.role_id] = result

        # 合并所有输出
        combined = "\n\n---\n\n".join(
            f"## {outputs[role_id]}\n{outputs[role_id]}" for role_id in outputs
        )

        return TopologyResult(
            topology="parallel",
            outputs=outputs,
            final_output=combined,
        )

    async def _debate(
        self, agents: list[AgentNode], input_text: str, rounds: int = 2, **kwargs
    ) -> TopologyResult:
        """辩论拓扑：两个角色独立回答，lead 裁决"""
        if len(agents) < 3:
            # 不足 3 个 agent，fallback 到 parallel
            return await self._parallel(agents, input_text)

        agent_a, agent_b, lead = agents[0], agents[1], agents[2]
        outputs: dict[str, str] = {}

        # 各自独立回答
        answer_a = await self.agent_caller(agent_a.role_id, input_text)
        answer_b = await self.agent_caller(agent_b.role_id, input_text)

        outputs[agent_a.role_id] = answer_a
        outputs[agent_b.role_id] = answer_b

        # Lead 裁决
        judge_prompt = f"""请比较以下两种方案，选择更优的方案并说明理由。

## 方案 A ({agent_a.name})
{answer_a[:2000]}

## 方案 B ({agent_b.name})
{answer_b[:2000]}

请选择更优方案，并综合两者的优点给出最终建议。"""

        final = await self.agent_caller(lead.role_id, judge_prompt)
        outputs[lead.role_id] = final

        return TopologyResult(
            topology="debate",
            outputs=outputs,
            final_output=final,
        )

    async def _committee(
        self, agents: list[AgentNode], input_text: str
    ) -> TopologyResult:
        """投票委员会：所有 Agent 投票，取多数意见"""
        tasks = [
            self.agent_caller(agent.role_id, input_text) for agent in agents
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        outputs: dict[str, str] = {}
        for agent, result in zip(agents, results):
            outputs[agent.role_id] = str(result) if not isinstance(result, Exception) else "弃权"

        # 简单投票：取最长的输出作为"最详细"的方案
        best_role = max(outputs, key=lambda r: len(outputs[r]))

        return TopologyResult(
            topology="committee",
            outputs=outputs,
            final_output=outputs[best_role],
        )

    async def _critic_actor(
        self, agents: list[AgentNode], input_text: str, max_rounds: int = 3, **kwargs
    ) -> TopologyResult:
        """Critic-Actor 循环：Actor 产出，Critic 反馈，迭代改进"""
        if len(agents) < 2:
            return await self._sequential(agents, input_text)

        actor, critic = agents[0], agents[1]
        outputs: dict[str, str] = {}

        current_output = await self.agent_caller(actor.role_id, input_text)

        for round_num in range(max_rounds):
            # Critic 评审
            critique = await self.agent_caller(
                critic.role_id,
                f"请评审以下内容，指出问题并给出改进建议：\n\n{current_output[:3000]}",
            )

            # 检查是否通过
            if "通过" in critique or "合格" in critique or "无问题" in critique:
                outputs[f"{actor.role_id}_final"] = current_output
                outputs[f"{critic.role_id}_final"] = critique
                break

            # Actor 改进
            current_output = await self.agent_caller(
                actor.role_id,
                f"根据以下反馈改进你的内容：\n\n原内容：\n{current_output[:2000]}\n\n反馈：\n{critique[:1000]}",
            )

        outputs[f"{actor.role_id}_final"] = current_output

        return TopologyResult(
            topology="critic_actor",
            outputs=outputs,
            final_output=current_output,
        )
