"""性能监控工具 — 追踪关键路径的执行时间"""
from __future__ import annotations

import functools
import logging
import time
from collections import defaultdict
from typing import Any, Callable

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """性能监控器 — 追踪函数执行时间"""

    def __init__(self):
        self.metrics: dict[str, list[float]] = defaultdict(list)

    def record(self, name: str, duration: float) -> None:
        """记录一次执行时间"""
        self.metrics[name].append(duration)
        if duration > 5.0:  # 超过 5 秒的慢操作记录警告
            logger.warning(f"Slow operation: {name} took {duration:.2f}s")

    def get_stats(self, name: str) -> dict[str, float]:
        """获取某操作的统计信息"""
        if name not in self.metrics:
            return {"count": 0}

        durations = self.metrics[name]
        return {
            "count": len(durations),
            "total": round(sum(durations), 3),
            "avg": round(sum(durations) / len(durations), 3),
            "min": round(min(durations), 3),
            "max": round(max(durations), 3),
            "p50": round(sorted(durations)[len(durations) // 2], 3),
        }

    def get_all_stats(self) -> dict[str, dict[str, float]]:
        """获取所有操作的统计信息"""
        return {name: self.get_stats(name) for name in self.metrics}

    def reset(self) -> None:
        """重置所有指标"""
        self.metrics.clear()


# 全局性能监控实例
_global_monitor = PerformanceMonitor()


def get_monitor() -> PerformanceMonitor:
    """获取全局性能监控实例"""
    return _global_monitor


def track_performance(name: str | None = None) -> Callable:
    """性能追踪装饰器

    Usage:
        @track_performance("llm_generate")
        async def generate(self, messages):
            ...
    """
    def decorator(func: Callable) -> Callable:
        operation_name = name or f"{func.__module__}.{func.__qualname__}"

        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            start = time.monotonic()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration = time.monotonic() - start
                _global_monitor.record(operation_name, duration)

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            start = time.monotonic()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.monotonic() - start
                _global_monitor.record(operation_name, duration)

        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator
