"""Multi-Agent 辩论 — 两个角色独立回答，lead 裁决合并"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .agent import AcademicAgent

logger = logging.getLogger(__name__)


class AgentDebate:
    """Multi-Agent 辩论机制
    
    在关键决策阶段，调用两个不同角色对同一问题给出独立回答，
    然后由 lead 角色裁决合并，提升输出质量。
    """

    def __init__(self, agent: AcademicAgent):
        self.agent = agent

    async def debate(
        self,
        question: str,
        role_a: str,
        role_b: str,
        rounds: int = 1,
    ) -> str:
        """两个角色辩论，最多 rounds 轮，lead 最终裁决
        
        Args:
            question: 需要辩论的问题
            role_a: 第一个角色 ID
            role_b: 第二个角色 ID
            rounds: 辩论轮数（默认 1 轮）
            
        Returns:
            整合后的最终答案
        """
        original_role = self.agent.current_role_id

        # 收集两个角色的独立回答
        responses = []
        for role_id in [role_a, role_b]:
            self.agent.switch_role(role_id)
            resp = await self.agent.chat(question)
            responses.append({"role": role_id, "response": resp})
            logger.info(f"Debate: {role_id} answered ({len(resp)} chars)")

        # 仲裁
        self.agent.switch_role("lead")
        synthesis_prompt = self._build_synthesis_prompt(responses)
        final: str = await self.agent.chat(synthesis_prompt)

        # 恢复原角色
        self.agent.switch_role(original_role)
        logger.info(f"Debate completed: {len(final)} chars")

        return final

    @staticmethod
    def _build_synthesis_prompt(responses: list[dict]) -> str:
        """构建裁决提示词"""
        parts = ["以下是两个专家的独立分析，请整合两者观点给出最终结论：\n"]

        for i, resp in enumerate(responses, 65):  # A=65, B=66
            role_label = chr(i)
            parts.append(f"## 角色 {role_label} ({resp['role']})")
            parts.append(resp["response"][:3000])
            parts.append("")

        parts.append("## 裁决要求")
        parts.append("请整合两者的最佳观点，突出：")
        parts.append("1. 双方一致的部分（共识）")
        parts.append("2. 双方分歧的部分及你的裁决理由")
        parts.append("3. 整合后的最终答案")

        return "\n".join(parts)
