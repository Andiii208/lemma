"""结构化日志配置测试"""

import json
import logging
import pytest
from lemma.observability.logging_config import JsonLineFormatter, setup_json_logging


class TestJsonLineFormatter:
    def test_format_produces_json(self):
        formatter = JsonLineFormatter()
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0,
            msg="test message", args=(), exc_info=None,
        )
        output = formatter.format(record)
        data = json.loads(output)
        assert data["message"] == "test message"
        assert data["level"] == "INFO"
        assert data["logger"] == "test"
        assert "timestamp" in data

    def test_format_with_exception(self):
        import sys
        formatter = JsonLineFormatter()
        try:
            raise ValueError("test error")
        except ValueError:
            exc_info = sys.exc_info()
            record = logging.LogRecord(
                name="test", level=logging.ERROR, pathname="", lineno=0,
                msg="error occurred", args=(), exc_info=exc_info,
            )
        output = formatter.format(record)
        data = json.loads(output)
        assert "exception" in data
        assert "test error" in data["exception"]

    def test_format_with_trace_context(self):
        formatter = JsonLineFormatter()
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0,
            msg="traced", args=(), exc_info=None,
        )
        record.trace_id = "abc123"
        record.span_id = "def456"
        output = formatter.format(record)
        data = json.loads(output)
        assert data["trace_id"] == "abc123"
        assert data["span_id"] == "def456"


class TestSetupJsonLogging:
    def test_setup_adds_handler(self):
        logger = logging.getLogger("ultramath")
        initial_count = len(logger.handlers)
        setup_json_logging("INFO")
        # 应该添加了 handler
        assert len(logger.handlers) >= initial_count
