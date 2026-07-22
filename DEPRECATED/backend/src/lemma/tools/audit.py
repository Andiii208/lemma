"""审计日志系统 — 记录所有工具调用与 Agent 操作"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from uuid import uuid4


@dataclass
class AuditEvent:
    """审计事件"""

    event_id: str = field(default_factory=lambda: uuid4().hex[:12])
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    event_type: str = ""  # tool_call | chat | phase_change | config_change
    actor: str = ""  # user | agent | system
    action: str = ""
    details: dict = field(default_factory=dict)
    success: bool = True
    error: str = ""


class AuditLogger:
    """审计日志记录器 — JSONL 格式追加写入"""

    def __init__(self, log_dir: str):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self._current_file: Path | None = None

    def _get_log_file(self) -> Path:
        """获取当日审计日志文件"""
        today = datetime.now().strftime("%Y-%m-%d")
        path = self.log_dir / f"audit_{today}.jsonl"
        if path != self._current_file:
            self._current_file = path
        return path

    def log(self, event: AuditEvent) -> None:
        """记录审计事件"""
        path = self._get_log_file()
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(event), ensure_ascii=False) + "\n")

    def log_tool_call(
        self, tool_name: str, arguments: dict, result: dict, success: bool
    ) -> None:
        """记录工具调用"""
        self.log(AuditEvent(
            event_type="tool_call",
            actor="agent",
            action=tool_name,
            details={"arguments": arguments, "result_preview": str(result)[:500]},
            success=success,
        ))

    def log_chat(self, role: str, content_preview: str) -> None:
        """记录对话"""
        self.log(AuditEvent(
            event_type="chat",
            actor=role,
            action="message",
            details={"content_preview": content_preview[:200]},
        ))

    def log_phase_change(self, phase_id: str, status: str) -> None:
        """记录阶段变更"""
        self.log(AuditEvent(
            event_type="phase_change",
            actor="system",
            action=f"phase_{status}",
            details={"phase_id": phase_id},
        ))

    def log_config_change(self, key: str, old_value: str, new_value: str) -> None:
        """记录配置变更"""
        self.log(AuditEvent(
            event_type="config_change",
            actor="user",
            action="update_config",
            details={"key": key, "old": old_value, "new": new_value},
        ))

    def query(
        self,
        date: str | None = None,
        event_type: str | None = None,
        limit: int = 100,
    ) -> list[AuditEvent]:
        """查询审计事件"""
        if date:
            path = self.log_dir / f"audit_{date}.jsonl"
            files = [path] if path.exists() else []
        else:
            files = sorted(self.log_dir.glob("audit_*.jsonl"), reverse=True)

        events: list[AuditEvent] = []
        for f in files:
            for line in f.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                    if event_type and data.get("event_type") != event_type:
                        continue
                    events.append(AuditEvent(**data))
                except (json.JSONDecodeError, TypeError):
                    continue
                if len(events) >= limit:
                    return events
        return events
