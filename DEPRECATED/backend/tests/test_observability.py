"""可观测性模块测试"""

import asyncio
import pytest
from lemma.observability.tracer import (
    Span,
    Trace,
    TraceCollector,
    trace_span,
    start_trace,
    finish_trace,
    get_current_trace,
    get_collector,
)


class TestSpan:
    def test_span_creation(self):
        span = Span(name="test")
        assert span.name == "test"
        assert span.status == "ok"
        assert span.duration_ms >= 0

    def test_span_finish(self):
        span = Span(name="test")
        span.finish("ok")
        assert span.end_time > 0
        assert span.status == "ok"

    def test_span_to_dict(self):
        span = Span(name="test", attributes={"key": "value"})
        d = span.to_dict()
        assert d["name"] == "test"
        assert d["attributes"]["key"] == "value"
        assert "duration_ms" in d


class TestTrace:
    def test_trace_creation(self):
        trace = Trace(name="test_trace")
        assert trace.name == "test_trace"
        assert trace.root_span.name == "test_trace"

    def test_trace_save_and_load(self, tmp_path):
        trace = Trace(name="test")
        trace.root_span.finish()
        path = str(tmp_path / "trace.json")
        trace.save(path)

        import json
        data = json.loads((tmp_path / "trace.json").read_text())
        assert data["name"] == "test"
        assert "trace_id" in data


class TestTraceCollector:
    def test_start_and_finish_trace(self):
        collector = TraceCollector()
        trace = collector.start_trace("test")
        assert collector.get_trace(trace.trace_id) is not None

        collector.finish_trace(trace)
        assert collector.get_trace(trace.trace_id) is None
        assert len(collector.get_completed()) == 1

    def test_clear(self):
        collector = TraceCollector()
        collector.start_trace("t1")
        collector.clear()
        assert len(collector.get_completed()) == 0


class TestTraceSpanDecorator:
    @pytest.mark.asyncio
    async def test_async_decorator(self):
        @trace_span("async_operation", component="test")
        async def my_async_func(x: int) -> int:
            return x * 2

        # 需要在一个 trace 上下文中运行
        trace = start_trace("test_trace")
        result = await my_async_func(5)
        finish_trace(trace)

        assert result == 10
        assert len(trace.root_span.children) == 1
        assert trace.root_span.children[0].name == "async_operation"
        assert trace.root_span.children[0].attributes["component"] == "test"

    def test_sync_decorator(self):
        @trace_span("sync_operation")
        def my_sync_func(x: int) -> int:
            return x + 1

        trace = start_trace("test_trace")
        result = my_sync_func(5)
        finish_trace(trace)

        assert result == 6
        assert len(trace.root_span.children) == 1

    @pytest.mark.asyncio
    async def test_nested_spans(self):
        @trace_span("outer")
        async def outer():
            inner()

        @trace_span("inner")
        def inner():
            pass

        trace = start_trace("test_trace")
        await outer()
        finish_trace(trace)

        outer_span = trace.root_span.children[0]
        assert outer_span.name == "outer"
        assert len(outer_span.children) == 1
        assert outer_span.children[0].name == "inner"

    @pytest.mark.asyncio
    async def test_error_recorded_in_span(self):
        @trace_span("failing_op")
        async def failing():
            raise ValueError("test error")

        trace = start_trace("test_trace")
        with pytest.raises(ValueError):
            await failing()
        finish_trace(trace)

        span = trace.root_span.children[0]
        assert span.status == "error"
        assert span.attributes["error"] == "test error"
