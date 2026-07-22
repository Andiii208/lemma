"""E2E 测试：WebSocket 连接和消息流"""
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient


class TestWebSocketE2E:
    def test_ws_connect_and_ping(self):
        """WebSocket 连接后发送 ping 应收到 pong"""
        from lemma.api.server import app

        client = TestClient(app)
        with client.websocket_connect("/ws") as ws:
            ws.send_json({"type": "ping"})
            response = ws.receive_json()
            assert response["type"] == "pong"

    def test_ws_chat_without_agent_returns_error(self):
        """未初始化 Agent 时发送 chat 应返回错误"""
        from lemma.api.server import app

        client = TestClient(app)
        with patch("lemma.api.server._agent", None):
            with client.websocket_connect("/ws") as ws:
                ws.send_json({"type": "chat", "message": "hello"})
                response = ws.receive_json()
                assert response["type"] == "error"
                assert "未初始化" in response["message"]

    def test_ws_invalid_json_returns_error(self):
        """发送无效 JSON 应返回错误"""
        from lemma.api.server import app

        client = TestClient(app)
        with client.websocket_connect("/ws") as ws:
            ws.send_text("not valid json {{{")
            response = ws.receive_json()
            assert response["type"] == "error"
            assert "JSON" in response["message"]
