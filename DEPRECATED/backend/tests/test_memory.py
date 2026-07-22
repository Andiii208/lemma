"""记忆系统单元测试"""
import pytest
from lemma.memory.short_term import ShortTermMemory, Message


class TestShortTermMemory:
    def test_add_and_retrieve(self):
        mem = ShortTermMemory(max_tokens=1000)
        mem.add("user", "hello")
        messages = mem.get_messages()
        assert len(messages) == 1
        assert messages[0]["content"] == "hello"
        assert messages[0]["role"] == "user"

    def test_multiple_messages(self):
        mem = ShortTermMemory(max_tokens=10000)
        mem.add("user", "hello")
        mem.add("assistant", "hi there")
        mem.add("user", "how are you")
        assert mem.length == 3

    def test_sliding_window_trims_old(self):
        mem = ShortTermMemory(max_tokens=50)
        for i in range(20):
            mem.add("user", f"message {i} " * 5)
        messages = mem.get_messages()
        assert len(messages) < 20

    def test_system_messages_preserved(self):
        mem = ShortTermMemory(max_tokens=50)
        mem.add("system", "you are helpful")
        for i in range(20):
            mem.add("user", f"message {i} " * 5)
        messages = mem.get_messages()
        system_msgs = [m for m in messages if m["role"] == "system"]
        assert len(system_msgs) >= 1

    def test_clear(self):
        mem = ShortTermMemory()
        mem.add("user", "test")
        mem.clear(keep_system=False)
        assert len(mem.get_messages()) == 0

    def test_clear_keep_system(self):
        mem = ShortTermMemory()
        mem.add("system", "system msg")
        mem.add("user", "user msg")
        mem.clear(keep_system=True)
        messages = mem.get_messages()
        assert len(messages) == 1
        assert messages[0]["role"] == "system"

    def test_get_raw_messages(self):
        mem = ShortTermMemory()
        mem.add("user", "hello")
        raw = mem.get_raw_messages()
        assert isinstance(raw[0], Message)
        assert raw[0].content == "hello"

    def test_token_counting(self):
        mem = ShortTermMemory()
        mem.add("user", "hello world")
        assert mem.get_token_count() > 0

    def test_get_last_n(self):
        mem = ShortTermMemory(max_tokens=10000)
        for i in range(10):
            mem.add("user", f"msg {i}")
        last3 = mem.get_last_n(3)
        assert len(last3) == 3
        assert last3[0]["content"] == "msg 7"

    def test_message_to_dict(self):
        msg = Message(role="assistant", content="test", tool_calls=[{"name": "foo"}])
        d = msg.to_dict()
        assert d["role"] == "assistant"
        assert d["tool_calls"] == [{"name": "foo"}]
