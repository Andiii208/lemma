"""Prompt 变异策略 — 生成 prompt 变体"""

from __future__ import annotations

import random
import re

from .prompt_object import OptimizablePrompt


class Mutator:
    """默认变异策略"""

    def __init__(self, mutation_rate: float = 0.3):
        self.mutation_rate = mutation_rate

    def mutate(self, prompt: OptimizablePrompt) -> OptimizablePrompt:
        """对 prompt 进行随机变异"""
        variant = prompt.clone()
        variant.parent_id = prompt.prompt_id

        # 随机选择变异策略
        strategies = [
            self._add_instruction,
            self._remove_redundancy,
            self._reorder_sections,
            self._emphasize_keywords,
            self._add_examples_hint,
        ]

        chosen = random.choice(strategies)
        variant.template = chosen(variant.template)

        return variant

    def _add_instruction(self, text: str) -> str:
        """添加强化指令"""
        additions = [
            "请确保输出结构清晰，包含章节标题。",
            "请使用学术论文的写作风格。",
            "请在每个步骤提供详细的推理过程。",
            "请确保所有公式使用 LaTeX 格式。",
            "请在结论部分总结关键发现。",
        ]
        addition = random.choice(additions)
        return text + "\n\n" + addition

    def _remove_redundancy(self, text: str) -> str:
        """去除冗余内容"""
        # 移除连续空行
        text = re.sub(r"\n{3,}", "\n\n", text)
        # 移除重复的分隔线
        text = re.sub(r"(---\n){2,}", "---\n", text)
        return text.strip()

    def _reorder_sections(self, text: str) -> str:
        """随机交换两个段落"""
        paragraphs = text.split("\n\n")
        if len(paragraphs) >= 3:
            i = random.randint(1, len(paragraphs) - 2)
            j = random.randint(1, len(paragraphs) - 2)
            if i != j:
                paragraphs[i], paragraphs[j] = paragraphs[j], paragraphs[i]
        return "\n\n".join(paragraphs)

    def _emphasize_keywords(self, text: str) -> str:
        """在关键位置强调关键词"""
        emphasis = [
            ("请分析", "**请详细分析**"),
            ("请建立", "**请建立**"),
            ("请设计", "**请设计**"),
            ("求解", "**求解**"),
        ]
        for old, new in emphasis:
            if old in text and random.random() < 0.5:
                text = text.replace(old, new, 1)
                break
        return text

    def _add_examples_hint(self, text: str) -> str:
        """添加示例提示"""
        hints = [
            "\n\n参考示例格式：\n- 问题描述 → 数学建模 → 求解 → 验证",
            "\n\n输出要求：包含 LaTeX 公式、图表、代码实现。",
            "\n\n质量要求：逻辑严谨、数据准确、结论明确。",
        ]
        return text + random.choice(hints)
