"""WebSocket 全消息类型测试 — 覆盖所有消息类型的正常和异常路径"""
import json
import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

_src_dir = str(Path(__file__).parent.parent / "src")
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)


@pytest.fixture
def client():
    from fastapi.testclient import TestClient
    from lemma.api.server import app
    return TestClient(app)


class TestConnection:
    """无需初始化的基础消息测试"""

    def test_ping_pong(self, client):
        with client.websocket_connect("/ws") as ws:
            ws.send_json({"type": "ping"})
            r = ws.receive_json()
            assert r["type"] == "pong"

    def test_invalid_json(self, client):
        with client.websocket_connect("/ws") as ws:
            ws.send_text("bad json{{{")
            r = ws.receive_json()
            assert r["type"] == "error"
            assert "JSON" in r.get("message", "")

    def test_chat_no_init(self, client):
        with client.websocket_connect("/ws") as ws:
            ws.send_json({"type": "chat", "message": "hello"})
            r = ws.receive_json()
            assert r["type"] == "error"
            assert "未初始化" in r.get("message", "")

    def test_stream_chat_no_init(self, client):
        with client.websocket_connect("/ws") as ws:
            ws.send_json({"type": "stream_chat", "message": "hello"})
            r = ws.receive_json()
            assert r["type"] == "error"
            assert "未初始化" in r.get("message", "")

    def test_chat_empty(self, client):
        with client.websocket_connect("/ws") as ws:
            ws.send_json({"type": "chat", "message": ""})
            r = ws.receive_json()
            assert r["type"] == "error"

    def test_chat_too_long(self, client):
        with client.websocket_connect("/ws") as ws:
            ws.send_json({"type": "chat", "message": "x" * 100001})
            r = ws.receive_json()
            assert r["type"] == "error"

    def test_init_no_workdir(self, client):
        with client.websocket_connect("/ws") as ws:
            ws.send_json({"type": "init"})
            r = ws.receive_json()
            assert r["type"] == "error"
            assert "工作目录" in r.get("message", "")

    def test_cancel_no_init(self, client):
        with client.websocket_connect("/ws") as ws:
            ws.send_json({"type": "cancel"})

    def test_unknown_type(self, client):
        with client.websocket_connect("/ws") as ws:
            ws.send_json({"type": "foo_bar_baz"})

    def test_reconnect(self, client):
        with client.websocket_connect("/ws") as ws1:
            assert ws1 is not None
        with client.websocket_connect("/ws") as ws2:
            ws2.send_json({"type": "ping"})
            r = ws2.receive_json()
            assert r["type"] == "pong"


class TestWithMockedAgent:
    """设置 _agent 后的消息测试"""

    def _setup(self):
        import lemma.api.server as server
        agent = MagicMock()
        agent.domain.id = "math-modeling"
        agent.domain.name = "数学建模"
        agent.domain.phases = [MagicMock(id="a", name="A")]
        agent.domain.roles = [MagicMock(id="r1", name="R1")]
        agent.domain.get_role_by_id = MagicMock(return_value=MagicMock())
        agent.switch_role = MagicMock()
        agent.get_current_role = MagicMock()
        agent.get_current_role.return_value = MagicMock()
        agent.get_current_role.return_value.name = "数学家"
        agent.current_role_id = "lead"
        agent.cancel = MagicMock()
        agent.get_status = MagicMock(return_value={"state": {"phase": "idle"}})
        agent.chat = MagicMock()
        server._agent = agent
        server._ws_connections.clear()
        return server, agent

    def _teardown(self, server):
        server._agent = None
        server._ws_connections.clear()

    def test_connection_sends_status(self, client):
        """agent 存在时连接后应自动收到 status 消息"""
        server, _ = self._setup()
        try:
            with client.websocket_connect("/ws") as ws:
                r = ws.receive_json()
                assert r["type"] == "status"
        finally:
            self._teardown(server)

    def test_cancel_calls_agent_cancel(self, client):
        """cancel 应调用 agent.cancel()"""
        server, agent = self._setup()
        try:
            with client.websocket_connect("/ws") as ws:
                _ = ws.receive_json()
                ws.send_json({"type": "cancel"})
                assert agent.cancel.called
        finally:
            self._teardown(server)

    def test_chat_does_not_crash(self, client):
        """chat 不应崩溃"""
        server, _ = self._setup()
        try:
            with client.websocket_connect("/ws") as ws:
                _ = ws.receive_json()
                ws.send_json({"type": "chat", "message": "hi"})
        finally:
            self._teardown(server)

    def test_auto_run_does_not_crash(self, client):
        """auto_run 不应崩溃"""
        server, _ = self._setup()
        try:
            with client.websocket_connect("/ws") as ws:
                _ = ws.receive_json()
                ws.send_json({"type": "auto_run", "problem_text": "test"})
        finally:
            self._teardown(server)

    def test_stream_chat_does_not_crash(self, client):
        """stream_chat 不应崩溃"""
        server, _ = self._setup()
        try:
            with client.websocket_connect("/ws") as ws:
                _ = ws.receive_json()
                ws.send_json({"type": "stream_chat", "message": "hi"})
        finally:
            self._teardown(server)

    def test_init_with_mocked_create_agent(self, client, tmp_path):
        """init + mock create_agent 应返回 initialized"""
        server, agent = self._setup()
        server._agent = None
        try:
            with patch("lemma.api.server.create_agent", return_value=agent):
                with client.websocket_connect("/ws") as ws:
                    ws.send_json({
                        "type": "init",
                        "work_dir": str(tmp_path),
                        "domain_id": "math-modeling",
                    })
                    r = ws.receive_json()
                    assert r["type"] == "initialized"
        finally:
            self._teardown(server)
