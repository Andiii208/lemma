"""Human-in-the-Loop — 关键节点暂停等待人类确认"""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from uuid import uuid4


@dataclass
class ConfirmationRequest:
    """确认请求"""

    request_id: str = field(default_factory=lambda: uuid4().hex[:8])
    phase_id: str = ""
    message: str = ""
    options: list[str] = field(default_factory=lambda: ["approve", "reject", "edit"])
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    response: str = ""
    responded_at: str = ""

    @property
    def is_pending(self) -> bool:
        return not self.response

    @property
    def is_approved(self) -> bool:
        return self.response == "approve"


class HITLManager:
    """Human-in-the-Loop 管理器 — 管理确认请求与响应"""

    def __init__(self, persist_dir: str | None = None):
        self._pending: dict[str, ConfirmationRequest] = {}
        self._events: dict[str, asyncio.Event] = {}
        self._history: list[ConfirmationRequest] = []
        self._persist_dir = Path(persist_dir) if persist_dir else None

        if self._persist_dir:
            self._persist_dir.mkdir(parents=True, exist_ok=True)

    def create_request(
        self, phase_id: str, message: str, options: list[str] | None = None
    ) -> ConfirmationRequest:
        """创建确认请求"""
        req = ConfirmationRequest(
            phase_id=phase_id,
            message=message,
            options=options or ["approve", "reject", "edit"],
        )
        self._pending[req.request_id] = req
        self._events[req.request_id] = asyncio.Event()

        if self._persist_dir:
            self._save_request(req)

        return req

    def respond(self, request_id: str, response: str) -> bool:
        """响应确认请求"""
        req = self._pending.get(request_id)
        if not req:
            return False

        req.response = response
        req.responded_at = datetime.now().isoformat()

        # 触发等待事件
        if request_id in self._events:
            self._events[request_id].set()

        # 移到历史
        self._history.append(req)
        self._pending.pop(request_id, None)
        self._events.pop(request_id, None)

        if self._persist_dir:
            self._save_request(req)

        return True

    async def wait_for_response(
        self, request_id: str, timeout: float = 300.0
    ) -> ConfirmationRequest | None:
        """等待确认响应"""
        req = self._pending.get(request_id)
        if not req:
            return None

        event = self._events.get(request_id)
        if not event:
            return None

        try:
            await asyncio.wait_for(event.wait(), timeout=timeout)
            return req
        except asyncio.TimeoutError:
            req.response = "timeout"
            req.responded_at = datetime.now().isoformat()
            self._history.append(req)
            self._pending.pop(request_id, None)
            self._events.pop(request_id, None)
            return req

    def get_pending(self) -> list[ConfirmationRequest]:
        """获取所有待确认请求"""
        return list(self._pending.values())

    def get_history(self) -> list[ConfirmationRequest]:
        """获取历史确认记录"""
        return list(self._history)

    def _save_request(self, req: ConfirmationRequest) -> None:
        """持久化确认请求"""
        if not self._persist_dir:
            return
        path = self._persist_dir / f"hitl_{req.request_id}.json"
        path.write_text(
            json.dumps({
                "request_id": req.request_id,
                "phase_id": req.phase_id,
                "message": req.message,
                "options": req.options,
                "response": req.response,
                "created_at": req.created_at,
                "responded_at": req.responded_at,
            }, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
