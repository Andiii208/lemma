"""LLM 调用成本追踪"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


# 各模型价格（USD / 1M tokens）
MODEL_PRICING: dict[str, dict[str, float]] = {
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4-turbo": {"input": 10.00, "output": 30.00},
    "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
    "deepseek-chat": {"input": 0.14, "output": 0.28},
    "deepseek-reasoner": {"input": 0.55, "output": 2.19},
}


class CostTracker:
    """追踪 LLM API 调用成本"""

    def __init__(self, work_dir: str):
        self.log_path = Path(work_dir) / ".ultraagent" / "costs.jsonl"
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self.session_cost: float = 0.0
        self.session_tokens: dict[str, int] = {"input": 0, "output": 0}

    def record(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """记录一次调用成本，返回本次费用"""
        pricing = MODEL_PRICING.get(model, {"input": 1.0, "output": 4.0})
        cost = (input_tokens / 1_000_000) * pricing["input"] + \
               (output_tokens / 1_000_000) * pricing["output"]
        self.session_cost += cost
        self.session_tokens["input"] += input_tokens
        self.session_tokens["output"] += output_tokens

        entry = {
            "timestamp": datetime.now().isoformat(),
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost_usd": round(cost, 6),
            "cumulative_usd": round(self.session_cost, 6),
        }

        try:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        except OSError as e:
            import logging
            logging.getLogger(__name__).warning(f"Failed to write cost log: {e}")

        return cost

    def get_session_cost(self) -> float:
        """获取本次会话总费用"""
        return round(self.session_cost, 4)

    def get_session_tokens(self) -> dict[str, int]:
        """获取本次会话 token 使用量"""
        return dict(self.session_tokens)

    def get_summary(self) -> dict:
        """获取成本摘要"""
        return {
            "session_cost_usd": self.get_session_cost(),
            "session_tokens": self.get_session_tokens(),
            "log_path": str(self.log_path),
        }

    def get_history(self, limit: int = 50) -> list[dict]:
        """获取最近的调用历史"""
        if not self.log_path.exists():
            return []

        lines = self.log_path.read_text(encoding="utf-8").strip().split("\n")
        entries = []
        for line in lines[-limit:]:
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return entries

    @staticmethod
    def estimate_run_cost(
        model: str,
        num_phases: int,
        avg_input_tokens: int = 8000,
        avg_output_tokens: int = 4000,
    ) -> float:
        """预估一次 auto_run 的成本
        
        Args:
            model: 模型名称
            num_phases: 阶段数量
            avg_input_tokens: 平均每阶段输入 token 数
            avg_output_tokens: 平均每阶段输出 token 数
            
        Returns:
            预估成本（USD）
        """
        pricing = MODEL_PRICING.get(model, {"input": 1.0, "output": 4.0})
        total_input = num_phases * avg_input_tokens
        total_output = num_phases * avg_output_tokens
        cost = (total_input / 1_000_000) * pricing["input"] + \
               (total_output / 1_000_000) * pricing["output"]
        return round(cost, 4)
