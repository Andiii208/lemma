"""轻量级 Trace 装饰器 — 不依赖 OpenTelemetry，纯 Python 实现

每个 run_auto 是一个 Trace，每个 phase/tool/LLM 调用是一个 Span。
Span 树可导出为 JSON，供前端 PipelinePanel 渲染时间轴。
"""

from __future__ import annotations

import asyncio
import json
import time
import uuid
from contextvars import ContextVar
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable


@dataclass
class Span:
    """单个 Trace Span"""

    span_id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    name: str = ""
    parent_id: str | None = None
    start_time: float = field(default_factory=time.time)
    end_time: float = 0.0
    attributes: dict[str, Any] = field(default_factory=dict)
    children: list[Span] = field(default_factory=list)
    status: str = "ok"  # ok | error

    @property
    def duration_ms(self) -> float:
        end = self.end_time if self.end_time > 0 else time.time()
        return (end - self.start_time) * 1000

    def finish(self, status: str = "ok") -> None:
        self.end_time = time.time()
        self.status = status

    def to_dict(self) -> dict:
        return {
            "span_id": self.span_id,
            "name": self.name,
            "parent_id": self.parent_id,
            "duration_ms": round(self.duration_ms, 2),
            "attributes": self.attributes,
            "status": self.status,
            "children": [c.to_dict() for c in self.children],
        }


@dataclass
class Trace:
    """一次完整的执行 Trace"""

    trace_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    name: str = ""
    root_span: Span = field(default_factory=Span)
    start_time: float = field(default_factory=time.time)

    def __post_init__(self):
        if self.name and not self.root_span.name:
            self.root_span.name = self.name

    def to_dict(self) -> dict:
        return {
            "trace_id": self.trace_id,
            "name": self.name,
            "duration_ms": round(self.root_span.duration_ms, 2),
            "root_span": self.root_span.to_dict(),
        }

    def save(self, path: str) -> None:
        Path(path).write_text(
            json.dumps(self.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


class TraceCollector:
    """Trace 收集器 — 管理当前活跃的 Trace"""

    def __init__(self):
        self._traces: dict[str, Trace] = {}
        self._completed: list[Trace] = []

    def start_trace(self, name: str) -> Trace:
        trace = Trace(name=name)
        if not trace.root_span.name:
            trace.root_span.name = name
        self._traces[trace.trace_id] = trace
        return trace

    def finish_trace(self, trace: Trace) -> None:
        trace.root_span.finish()
        self._traces.pop(trace.trace_id, None)
        self._completed.append(trace)

    def get_trace(self, trace_id: str) -> Trace | None:
        return self._traces.get(trace_id)

    def get_completed(self) -> list[Trace]:
        return list(self._completed)

    def clear(self) -> None:
        self._traces.clear()
        self._completed.clear()


# 全局收集器
_collector = TraceCollector()

# 当前 Span 的上下文变量
_current_span: ContextVar[Span | None] = ContextVar("current_span", default=None)
_current_trace: ContextVar[Trace | None] = ContextVar("current_trace", default=None)


def get_current_trace() -> Trace | None:
    """获取当前活跃的 Trace"""
    return _current_trace.get()


def get_current_span() -> Span | None:
    """获取当前活跃的 Span"""
    return _current_span.get()


def get_collector() -> TraceCollector:
    """获取全局 Trace 收集器"""
    return _collector


def trace_span(name: str, **extra_attrs: Any) -> Callable:
    """装饰器 — 为函数创建 trace span

    支持同步和异步函数。
    """

    def decorator(func: Callable) -> Callable:
        if asyncio.iscoroutinefunction(func):

            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                return await _run_with_span(name, func, extra_attrs, args, kwargs)

            return async_wrapper
        else:

            def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                return _run_with_span_sync(name, func, extra_attrs, args, kwargs)

            return sync_wrapper

    return decorator


async def _run_with_span(
    name: str, func: Callable, extra_attrs: dict, args: tuple, kwargs: dict
) -> Any:
    """异步 span 执行"""
    span = _create_child_span(name, extra_attrs)
    token = _current_span.set(span)
    try:
        result = await func(*args, **kwargs)
        span.finish("ok")
        return result
    except Exception as e:
        span.attributes["error"] = str(e)
        span.finish("error")
        raise
    finally:
        _current_span.reset(token)


def _run_with_span_sync(
    name: str, func: Callable, extra_attrs: dict, args: tuple, kwargs: dict
) -> Any:
    """同步 span 执行"""
    span = _create_child_span(name, extra_attrs)
    token = _current_span.set(span)
    try:
        result = func(*args, **kwargs)
        span.finish("ok")
        return result
    except Exception as e:
        span.attributes["error"] = str(e)
        span.finish("error")
        raise
    finally:
        _current_span.reset(token)


def _create_child_span(name: str, extra_attrs: dict) -> Span:
    """创建子 span（挂到当前 span 或 trace root 下）"""
    parent = _current_span.get()
    trace = _current_trace.get()

    span = Span(name=name, attributes=dict(extra_attrs))

    if parent:
        span.parent_id = parent.span_id
        parent.children.append(span)
    elif trace:
        span.parent_id = trace.root_span.span_id
        trace.root_span.children.append(span)

    return span


def start_trace(name: str) -> Trace:
    """开始一个新的 Trace（设置上下文）"""
    trace = _collector.start_trace(name)
    _current_trace.set(trace)
    return trace


def finish_trace(trace: Trace) -> None:
    """结束 Trace（清理上下文）"""
    _collector.finish_trace(trace)
    _current_trace.set(None)
