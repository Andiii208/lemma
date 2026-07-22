"""会话持久化系统 — JSON 格式保存/恢复完整会话状态"""
from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import TypedDict


class SessionMeta(TypedDict):
    session_id: str
    domain_id: str
    created_at: str
    updated_at: str
    phase: str
    progress: float
    message_count: int


class SessionStore:
    """会话持久化存储"""

    def __init__(self, work_dir: str):
        self.sessions_dir = Path(work_dir) / ".ultraagent" / "sessions"
        self.sessions_dir.mkdir(parents=True, exist_ok=True)

    def save(self, agent) -> str:
        """保存当前会话，返回 session_id"""
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_dir = self.sessions_dir / session_id
        session_dir.mkdir(parents=True, exist_ok=True)

        # 保存消息历史
        messages = []
        for msg in agent.memory.get_raw_messages():
            messages.append({
                "role": msg.role,
                "content": msg.content,
            })
        (session_dir / "messages.json").write_text(
            json.dumps(messages, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        # 保存状态
        state = agent.get_status()
        (session_dir / "state.json").write_text(
            json.dumps(state, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )

        # 保存元信息
        meta: SessionMeta = {
            "session_id": session_id,
            "domain_id": agent.domain.id,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "phase": state.get("state", {}).get("current_phase", ""),
            "progress": state.get("state", {}).get("progress", 0),
            "message_count": len(messages),
        }
        (session_dir / "meta.json").write_text(
            json.dumps(meta, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        return session_id

    def load(self, session_id: str, agent) -> bool:
        """恢复会话到 agent"""
        session_dir = self.sessions_dir / session_id
        if not session_dir.exists():
            return False

        # 恢复消息
        messages_file = session_dir / "messages.json"
        if messages_file.exists():
            messages = json.loads(messages_file.read_text(encoding="utf-8"))
            agent.memory.clear(keep_system=False)
            for msg in messages:
                agent.memory.add(msg["role"], msg["content"])

        return True

    def list_sessions(self) -> list[SessionMeta]:
        """列出所有已保存的会话"""
        sessions = []
        for session_dir in sorted(self.sessions_dir.iterdir(), reverse=True):
            meta_file = session_dir / "meta.json"
            if meta_file.exists():
                try:
                    meta = json.loads(meta_file.read_text(encoding="utf-8"))
                    sessions.append(meta)
                except Exception:
                    continue
        return sessions

    def delete_session(self, session_id: str) -> bool:
        """删除会话"""
        session_dir = self.sessions_dir / session_id
        if session_dir.exists():
            shutil.rmtree(session_dir)
            return True
        return False

    def get_session_count(self) -> int:
        """获取会话总数"""
        return len(list(self.sessions_dir.iterdir()))
