"""结构化日志配置 — JSON Lines 格式"""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime


class JsonLineFormatter(logging.Formatter):
    """JSON Lines 格式的日志格式化器"""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # 附加额外字段
        if hasattr(record, "trace_id"):
            log_entry["trace_id"] = record.trace_id
        if hasattr(record, "span_id"):
            log_entry["span_id"] = record.span_id
        if record.exc_info and record.exc_info[1]:
            log_entry["exception"] = str(record.exc_info[1])

        return json.dumps(log_entry, ensure_ascii=False)


def setup_json_logging(level: str = "INFO") -> None:
    """设置 JSON Lines 格式的日志"""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonLineFormatter())

    root = logging.getLogger("ultramath")
    root.setLevel(getattr(logging, level.upper(), logging.INFO))
    root.addHandler(handler)
