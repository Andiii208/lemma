"""自我反思器 — 让 Agent 审视自己的输出并改进"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


class SelfReflector:
    """自我反思与改进循环"""

    # 默认反思标准
    DEFAULT_CRITERIA = [
        "逻辑一致性：论证是否自洽，有无矛盾",
        "完整性：是否遗漏关键信息或步骤",
        "准确性：数据和引用是否正确",
        "清晰度：表达是否简洁易懂",
        "创新性：是否有独到见解或方法",
    ]

    def __init__(self, agent):
        self.agent = agent

    async def reflect_and_improve(
        self,
        original_response: str,
        criteria: list[str] | None = None,
        max_iterations: int = 1,
    ) -> str:
        """基于给定标准反思并改进回答"""
        if criteria is None:
            criteria = self.DEFAULT_CRITERIA

        current = original_response
        for iteration in range(max_iterations):
            reflection_prompt = f"""请以批判性眼光审视以下回答，然后给出改进版本。

## 评估标准
{chr(10).join(f'- {c}' for c in criteria)}

## 原始回答
{current[:5000]}

## 指令
1. 先指出原始回答的不足之处（简明扼要，3-5 条）
2. 然后给出改进后的完整回答

请按以下格式输出：
[反思]
不足之处：
1. ...
2. ...
[/反思]

[改进版]
(改进后的完整回答)
[/改进版]
"""
            self.agent.memory.add("user", reflection_prompt)
            improved = await self.agent._generate_with_tools()
            self.agent.memory.add("assistant", improved)

            # 尝试提取改进版
            if "[改进版]" in improved and "[/改进版]" in improved:
                start = improved.find("[改进版]") + len("[改进版]")
                end = improved.find("[/改进版]")
                extracted = improved[start:end].strip()
                if extracted:
                    current = extracted
                    logger.info(f"反思迭代 {iteration + 1}: 已提取改进版 ({len(current)} 字)")
            else:
                logger.warning(f"反思迭代 {iteration + 1}: 未能提取改进版，使用原始响应")
                break

        return current

    async def quick_reflect(self, response: str) -> str:
        """快速反思 — 只检查明显问题，不做深度改进"""
        prompt = f"""快速检查以下回答是否有明显错误或遗漏。如果有问题，直接给出修正后的版本；如果没问题，原样返回。

回答：
{response[:3000]}

直接返回修正版或原版，不要解释。"""
        self.agent.memory.add("user", prompt)
        result = await self.agent._generate_with_tools()
        self.agent.memory.add("assistant", result)
        return result if len(result) > len(response) * 0.5 else response
