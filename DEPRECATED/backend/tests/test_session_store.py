"""会话持久化测试"""

import json
import pytest
from unittest.mock import MagicMock
from lemma.memory.session_store import SessionStore


class TestSessionStore:
    @pytest.fixture
    def mock_agent(self):
        agent = MagicMock()
        agent.memory.get_raw_messages.return_value = [
            MagicMock(role="user", content="hello"),
            MagicMock(role="assistant", content="hi"),
        ]
        agent.memory.get_messages.return_value = [
            {"role": "user", "content": "hello"},
            {"role": "assistant", "content": "hi"},
        ]
        agent.get_status.return_value = {"state": {"progress": 50}}
        agent.domain.id = "test"
        agent.state.current_phase = "analysis"
        agent.state.progress = 50
        agent.memory.length = 2
        return agent

    def test_save_creates_session(self, tmp_path, mock_agent):
        store = SessionStore(str(tmp_path))
        session_id = store.save(mock_agent)
        assert session_id is not None
        assert len(session_id) > 0

    def test_list_sessions(self, tmp_path, mock_agent):
        store = SessionStore(str(tmp_path))
        store.save(mock_agent)
        sessions = store.list_sessions()
        assert len(sessions) == 1

    def test_load_session(self, tmp_path, mock_agent):
        store = SessionStore(str(tmp_path))
        session_id = store.save(mock_agent)

        mock_agent.memory = MagicMock()
        ok = store.load(session_id, mock_agent)
        assert ok is True

    def test_load_nonexistent(self, tmp_path, mock_agent):
        store = SessionStore(str(tmp_path))
        ok = store.load("nonexistent", mock_agent)
        assert ok is False

    def test_delete_session(self, tmp_path, mock_agent):
        store = SessionStore(str(tmp_path))
        session_id = store.save(mock_agent)
        assert store.delete_session(session_id) is True
        assert store.get_session_count() == 0

    def test_get_session_count(self, tmp_path, mock_agent):
        store = SessionStore(str(tmp_path))
        assert store.get_session_count() == 0
        store.save(mock_agent)
        assert store.get_session_count() == 1
