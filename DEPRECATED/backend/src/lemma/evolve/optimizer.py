"""Prompt 优化器 — 进化搜索自动优化 prompt

工作流程：
1. 从当前 prompt 生成 N 个变异体
2. 用评测系统（A1）对每个变异体评分
3. 保留 top-K 变异体
4. 重复直到收敛或达到迭代上限
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

from ..eval.report import EvalReport
from ..eval.runner import evaluate
from .prompt_object import OptimizablePrompt

logger = logging.getLogger("ultramath.evolve")


@dataclass
class OptimizationResult:
    """优化结果"""

    original: OptimizablePrompt
    best: OptimizablePrompt
    iterations: int = 0
    score_improvement: float = 0.0
    history: list[dict] = field(default_factory=list)


class PromptOptimizer:
    """Prompt 优化器 — 进化搜索"""

    def __init__(
        self,
        eval_domain_id: str,
        population_size: int = 5,
        max_iterations: int = 3,
        improvement_threshold: float = 0.02,
    ):
        self.eval_domain_id = eval_domain_id
        self.population_size = population_size
        self.max_iterations = max_iterations
        self.improvement_threshold = improvement_threshold

    async def optimize(
        self,
        prompt: OptimizablePrompt,
        mutator: "Mutator | None" = None,
        use_mock: bool = True,
    ) -> OptimizationResult:
        """优化 prompt

        Args:
            prompt: 初始 prompt
            mutator: 变异策略（默认使用内置）
            use_mock: 是否使用 mock 评测
        """
        from .mutator import Mutator

        if mutator is None:
            mutator = Mutator()

        current_best = prompt.clone()
        history: list[dict] = []

        # 基线评分
        baseline_score = await self._evaluate_prompt(current_best, use_mock)
        current_best.score = baseline_score
        logger.info(f"基线评分: {baseline_score:.3f}")

        for iteration in range(self.max_iterations):
            logger.info(f"迭代 {iteration + 1}/{self.max_iterations}")

            # 生成变异体
            variants = [mutator.mutate(current_best) for _ in range(self.population_size)]
            variants.append(current_best.clone())  # 保留当前最优

            # 评分
            scored = []
            for variant in variants:
                score = await self._evaluate_prompt(variant, use_mock)
                variant.score = score
                scored.append(variant)

            # 排序取 top-1
            scored.sort(key=lambda p: p.score, reverse=True)
            new_best = scored[0]

            improvement = new_best.score - current_best.score
            history.append({
                "iteration": iteration + 1,
                "best_score": new_best.score,
                "improvement": improvement,
                "population_scores": [s.score for s in scored],
            })

            logger.info(f"最优评分: {new_best.score:.3f} (提升: {improvement:+.3f})")

            if improvement < self.improvement_threshold:
                logger.info("收敛，停止优化")
                break

            current_best = new_best
            current_best.version += 1

        return OptimizationResult(
            original=prompt,
            best=current_best,
            iterations=len(history),
            score_improvement=current_best.score - baseline_score,
            history=history,
        )

    async def _evaluate_prompt(
        self, prompt: OptimizablePrompt, use_mock: bool
    ) -> float:
        """用评测系统对 prompt 评分"""
        from ..eval.dataset import GoldenDataset

        golden_path = (
            Path(__file__).parent.parent.parent.parent.parent
            / "domains"
            / self.eval_domain_id
            / "golden.jsonl"
        )
        if not golden_path.exists():
            logger.warning(f"Golden set 不存在: {golden_path}")
            return 0.0

        dataset = GoldenDataset.from_jsonl(str(golden_path))
        report = await evaluate(
            self.eval_domain_id, dataset, version=f"opt_{prompt.prompt_id}", use_mock=use_mock
        )
        return report.avg_score
