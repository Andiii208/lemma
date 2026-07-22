"""用量计费 — token 计量 + 配额管理"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass
class UsageRecord:
    """用量记录"""

    tenant_id: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    tokens_in: int = 0
    tokens_out: int = 0
    cost_usd: float = 0.0
    model: str = ""
    run_id: str = ""


@dataclass
class Quota:
    """配额"""

    tenant_id: str = ""
    max_tokens_per_day: int = 100000
    max_cost_per_day: float = 5.0
    max_runs_per_day: int = 10


class BillingMeter:
    """计费计量器"""

    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._usage_file = self.data_dir / "usage.jsonl"
        self._records: list[UsageRecord] = []
        self._load()

    def _load(self) -> None:
        if not self._usage_file.exists():
            return
        for line in self._usage_file.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                self._records.append(UsageRecord(**json.loads(line)))
            except (json.JSONDecodeError, TypeError):
                continue

    def record(self, usage: UsageRecord) -> None:
        """记录用量"""
        self._records.append(usage)
        with open(self._usage_file, "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "tenant_id": usage.tenant_id,
                "timestamp": usage.timestamp,
                "tokens_in": usage.tokens_in,
                "tokens_out": usage.tokens_out,
                "cost_usd": usage.cost_usd,
                "model": usage.model,
                "run_id": usage.run_id,
            }, ensure_ascii=False) + "\n")

    def get_usage_today(self, tenant_id: str) -> dict:
        """获取今日用量"""
        today = datetime.now().strftime("%Y-%m-%d")
        total_tokens = 0
        total_cost = 0.0
        run_count = 0

        for r in self._records:
            if r.tenant_id == tenant_id and r.timestamp.startswith(today):
                total_tokens += r.tokens_in + r.tokens_out
                total_cost += r.cost_usd
                if r.run_id:
                    run_count += 1

        return {
            "tenant_id": tenant_id,
            "date": today,
            "total_tokens": total_tokens,
            "total_cost_usd": total_cost,
            "run_count": run_count,
        }

    def check_quota(self, tenant_id: str, quota: Quota) -> dict:
        """检查配额"""
        usage = self.get_usage_today(tenant_id)

        token_pct = usage["total_tokens"] / quota.max_tokens_per_day if quota.max_tokens_per_day > 0 else 0
        cost_pct = usage["total_cost_usd"] / quota.max_cost_per_day if quota.max_cost_per_day > 0 else 0
        run_pct = usage["run_count"] / quota.max_runs_per_day if quota.max_runs_per_day > 0 else 0

        exceeded = (
            (quota.max_tokens_per_day > 0 and usage["total_tokens"] >= quota.max_tokens_per_day)
            or (quota.max_cost_per_day > 0 and usage["total_cost_usd"] >= quota.max_cost_per_day)
            or (quota.max_runs_per_day > 0 and usage["run_count"] >= quota.max_runs_per_day)
        )

        return {
            **usage,
            "quota": {
                "max_tokens": quota.max_tokens_per_day,
                "max_cost": quota.max_cost_per_day,
                "max_runs": quota.max_runs_per_day,
            },
            "usage_pct": {
                "tokens": min(1.0, token_pct),
                "cost": min(1.0, cost_pct),
                "runs": min(1.0, run_pct),
            },
            "exceeded": exceeded,
        }

    def get_monthly_summary(self, tenant_id: str, year: int, month: int) -> dict:
        """获取月度汇总"""
        prefix = f"{year}-{month:02d}"
        total_tokens = 0
        total_cost = 0.0
        by_model: dict[str, float] = {}

        for r in self._records:
            if r.tenant_id == tenant_id and r.timestamp.startswith(prefix):
                total_tokens += r.tokens_in + r.tokens_out
                total_cost += r.cost_usd
                by_model[r.model] = by_model.get(r.model, 0) + r.cost_usd

        return {
            "tenant_id": tenant_id,
            "period": prefix,
            "total_tokens": total_tokens,
            "total_cost_usd": round(total_cost, 4),
            "by_model": by_model,
        }
