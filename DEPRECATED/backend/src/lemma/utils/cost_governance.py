"""成本治理 — 预算上限、超额告警、自动降级"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger("ultramath.cost")


@dataclass
class BudgetPolicy:
    """预算策略"""

    max_cost_per_run: float = 5.0  # 单次运行最大成本 (USD)
    max_cost_per_day: float = 20.0  # 每日最大成本 (USD)
    warning_threshold: float = 0.8  # 80% 时告警
    auto_downgrade: bool = True  # 超限时自动降级模型


@dataclass
class CostRecord:
    """成本记录"""

    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    model: str = ""
    tokens_in: int = 0
    tokens_out: int = 0
    cost_usd: float = 0.0
    run_id: str = ""


class CostGovernor:
    """成本治理器"""

    def __init__(self, policy: BudgetPolicy | None = None):
        self.policy = policy or BudgetPolicy()
        self._records: list[CostRecord] = []
        self._daily_cost: float = 0.0
        self._run_cost: float = 0.0
        self._current_run_id: str = ""

    def start_run(self, run_id: str) -> None:
        """开始新的运行"""
        self._current_run_id = run_id
        self._run_cost = 0.0

    def record(self, model: str, tokens_in: int, tokens_out: int, cost_usd: float) -> None:
        """记录成本"""
        record = CostRecord(
            model=model,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            cost_usd=cost_usd,
            run_id=self._current_run_id,
        )
        self._records.append(record)
        self._daily_cost += cost_usd
        self._run_cost += cost_usd

    def check_budget(self) -> dict:
        """检查预算状态"""
        run_pct = self._run_cost / self.policy.max_cost_per_run if self.policy.max_cost_per_run > 0 else 0
        day_pct = self._daily_cost / self.policy.max_cost_per_day if self.policy.max_cost_per_day > 0 else 0

        warnings = []
        should_downgrade = False
        should_stop = False

        if run_pct >= 1.0:
            should_stop = True
            warnings.append(f"单次运行成本已达上限: ${self._run_cost:.2f}/${self.policy.max_cost_per_run:.2f}")
        elif run_pct >= self.policy.warning_threshold:
            warnings.append(f"单次运行成本接近上限: ${self._run_cost:.2f}/${self.policy.max_cost_per_run:.2f}")
            if self.policy.auto_downgrade:
                should_downgrade = True

        if day_pct >= 1.0:
            should_stop = True
            warnings.append(f"每日成本已达上限: ${self._daily_cost:.2f}/${self.policy.max_cost_per_day:.2f}")
        elif day_pct >= self.policy.warning_threshold:
            warnings.append(f"每日成本接近上限: ${self._daily_cost:.2f}/${self.policy.max_cost_per_day:.2f}")

        return {
            "run_cost": self._run_cost,
            "daily_cost": self._daily_cost,
            "run_pct": run_pct,
            "day_pct": day_pct,
            "warnings": warnings,
            "should_downgrade": should_downgrade,
            "should_stop": should_stop,
        }

    def get_summary(self) -> dict:
        """获取成本摘要"""
        return {
            "total_records": len(self._records),
            "daily_cost": self._daily_cost,
            "run_cost": self._run_cost,
            "policy": {
                "max_per_run": self.policy.max_cost_per_run,
                "max_per_day": self.policy.max_cost_per_day,
            },
        }
