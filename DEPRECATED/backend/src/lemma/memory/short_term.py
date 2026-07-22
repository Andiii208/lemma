"""短期记忆 — 管理对话上下文窗口"""

from __future__ import annotations

import contextlib
from dataclasses import dataclass
from typing import Any

try:
    import tiktoken

    _HAS_TIKTOKEN = True
except ImportError:
    _HAS_TIKTOKEN = False


@dataclass
class Message:
    """对话消息"""

    role: str
    content: str
    name: str | None = None
    tool_call_id: str | None = None
    tool_calls: list[dict] | None = None
    token_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        """转换为 OpenAI 格式"""
        d: dict[str, Any] = {"role": self.role, "content": self.content}
        if self.name:
            d["name"] = self.name
        if self.tool_call_id:
            d["tool_call_id"] = self.tool_call_id
        if self.tool_calls:
            d["tool_calls"] = self.tool_calls
        return d


class ShortTermMemory:
    """短期记忆 — 滑动窗口上下文管理"""

    def __init__(self, max_tokens: int = 128000):
        self.max_tokens = max_tokens
        self.messages: list[Message] = []
        self._encoder = None
        if _HAS_TIKTOKEN:
            with contextlib.suppress(Exception):
                self._encoder = tiktoken.get_encoding("cl100k_base")

    def _count_tokens(self, text: str) -> int:
        """估算 token 数"""
        if self._encoder:
            return len(self._encoder.encode(text))
        # 粗略估算：1 token ≈ 4 字符（英文）或 2 字符（中文）
        return max(len(text) // 2, 1)

    def add(self, role: str, content: str, **kwargs) -> None:
        """添加消息"""
        token_count = self._count_tokens(content)
        msg = Message(role=role, content=content, token_count=token_count, **kwargs)
        self.messages.append(msg)
        self._trim()

    def add_message(self, msg: Message) -> None:
        """直接添加 Message 对象"""
        if msg.token_count == 0:
            msg.token_count = self._count_tokens(msg.content)
        self.messages.append(msg)
        self._trim()

    def get_messages(self) -> list[dict[str, Any]]:
        """获取所有消息（OpenAI 格式）"""
        return [m.to_dict() for m in self.messages]

    def get_raw_messages(self) -> list[Message]:
        """获取原始消息对象"""
        return list(self.messages)

    def get_token_count(self) -> int:
        """获取总 token 数"""
        return sum(m.token_count for m in self.messages)

    def get_last_n(self, n: int) -> list[dict[str, Any]]:
        """获取最近 n 条消息"""
        return [m.to_dict() for m in self.messages[-n:]]

    def clear(self, keep_system: bool = True) -> None:
        """清空记忆"""
        if keep_system:
            system_msgs = [m for m in self.messages if m.role == "system"]
            self.messages = system_msgs
        else:
            self.messages = []

    def _trim(self) -> None:
        """滑动窗口裁剪"""
        total = self.get_token_count()
        if total <= self.max_tokens:
            return

        system_msgs = [m for m in self.messages if m.role == "system"]
        other_msgs = [m for m in self.messages if m.role != "system"]

        system_tokens = sum(m.token_count for m in system_msgs)
        budget = self.max_tokens - system_tokens

        kept = []
        used = 0
        for msg in reversed(other_msgs):
            if used + msg.token_count > budget:
                break
            kept.append(msg)
            used += msg.token_count

        self.messages = system_msgs + list(reversed(kept))

    @property
    def length(self) -> int:
        return len(self.messages)
