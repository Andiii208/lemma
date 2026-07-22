"""可观测性模块 — 轻量级 trace + 结构化日志"""

from .tracer import Span, TraceCollector, get_current_trace, trace_span

__all__ = ["trace_span", "Span", "TraceCollector", "get_current_trace"]
