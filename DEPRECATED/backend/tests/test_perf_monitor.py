"""性能监控测试"""

import pytest
from lemma.utils.perf_monitor import PerformanceMonitor, get_monitor, track_performance


class TestPerformanceMonitor:
    def test_record_and_get_stats(self):
        monitor = PerformanceMonitor()
        monitor.record("test_op", 0.5)
        monitor.record("test_op", 1.0)
        stats = monitor.get_stats("test_op")
        assert stats["count"] == 2
        assert stats["avg"] == pytest.approx(0.75)
        assert stats["min"] == 0.5
        assert stats["max"] == 1.0

    def test_get_stats_empty(self):
        monitor = PerformanceMonitor()
        stats = monitor.get_stats("nonexistent")
        assert stats["count"] == 0

    def test_get_all_stats(self):
        monitor = PerformanceMonitor()
        monitor.record("op1", 0.1)
        monitor.record("op2", 0.2)
        all_stats = monitor.get_all_stats()
        assert "op1" in all_stats
        assert "op2" in all_stats

    def test_reset(self):
        monitor = PerformanceMonitor()
        monitor.record("test", 0.5)
        monitor.reset()
        assert monitor.get_stats("test")["count"] == 0

    def test_get_monitor_singleton(self):
        m1 = get_monitor()
        m2 = get_monitor()
        assert m1 is m2


class TestTrackPerformanceDecorator:
    def test_sync_function(self):
        @track_performance("sync_test")
        def my_func():
            return 42

        result = my_func()
        assert result == 42
        monitor = get_monitor()
        assert monitor.get_stats("sync_test")["count"] >= 1

    @pytest.mark.asyncio
    async def test_async_function(self):
        @track_performance("async_test")
        async def my_async_func():
            return "hello"

        result = await my_async_func()
        assert result == "hello"
        monitor = get_monitor()
        assert monitor.get_stats("async_test")["count"] >= 1
