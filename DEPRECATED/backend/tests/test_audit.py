"""审计日志系统测试"""

import json
import pytest
from lemma.tools.audit import AuditLogger, AuditEvent


class TestAuditLogger:
    def test_log_and_query(self, tmp_path):
        logger = AuditLogger(str(tmp_path))
        logger.log_tool_call("test_tool", {"arg": 1}, {"result": "ok"}, True)

        events = logger.query()
        assert len(events) == 1
        assert events[0].event_type == "tool_call"
        assert events[0].action == "test_tool"
        assert events[0].success is True

    def test_log_chat(self, tmp_path):
        logger = AuditLogger(str(tmp_path))
        logger.log_chat("user", "Hello world")

        events = logger.query()
        assert len(events) == 1
        assert events[0].event_type == "chat"
        assert events[0].actor == "user"

    def test_log_phase_change(self, tmp_path):
        logger = AuditLogger(str(tmp_path))
        logger.log_phase_change("analysis", "completed")

        events = logger.query()
        assert events[0].details["phase_id"] == "analysis"

    def test_query_filter_by_type(self, tmp_path):
        logger = AuditLogger(str(tmp_path))
        logger.log_chat("user", "msg")
        logger.log_tool_call("tool", {}, {}, True)

        assert len(logger.query(event_type="chat")) == 1
        assert len(logger.query(event_type="tool_call")) == 1
        assert len(logger.query(event_type="nonexistent")) == 0

    def test_query_limit(self, tmp_path):
        logger = AuditLogger(str(tmp_path))
        for i in range(10):
            logger.log_chat("user", f"msg {i}")

        assert len(logger.query(limit=5)) == 5

    def test_jsonl_format(self, tmp_path):
        logger = AuditLogger(str(tmp_path))
        logger.log(AuditEvent(event_type="test", action="test"))

        files = list(tmp_path.glob("audit_*.jsonl"))
        assert len(files) == 1
        lines = files[0].read_text().strip().split("\n")
        assert len(lines) == 1
        data = json.loads(lines[0])
        assert data["event_type"] == "test"
