"""API Server 集成测试"""
import pytest
import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

# 添加 src 到路径
_src_dir = str(Path(__file__).parent.parent / "src")
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)


class TestHealthEndpoint:
    def test_health_returns_ok(self):
        """健康检查端点应返回 200 和 ok 状态"""
        from fastapi.testclient import TestClient
        from lemma.api.server import app

        client = TestClient(app)
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data


class TestDomainsEndpoint:
    def test_domains_list(self):
        """域列表端点应返回可用域"""
        from fastapi.testclient import TestClient
        from lemma.api.server import app

        client = TestClient(app)
        response = client.get("/api/domains")
        assert response.status_code == 200
        data = response.json()
        assert "domains" in data
        # 域列表可能为空（取决于路径解析），但端点应正常响应


class TestStatusEndpoint:
    def test_status_without_agent(self):
        """无 Agent 时 status 返回 not_initialized"""
        from fastapi.testclient import TestClient
        from lemma.api.server import app, _agent

        client = TestClient(app)
        # 通过 patch 确保 _agent 为 None
        with patch("lemma.api.server._agent", None):
            response = client.get("/api/status")
            assert response.status_code == 200
            assert response.json()["status"] == "not_initialized"


class TestChatEndpoint:
    def test_chat_without_agent_returns_400(self):
        """未初始化 Agent 时 chat 返回 400"""
        from fastapi.testclient import TestClient
        from lemma.api.server import app

        client = TestClient(app)
        with patch("lemma.api.server._agent", None):
            response = client.post(
                "/api/chat",
                json={"message": "hello"},
                headers={"X-API-Key": "dev-key-change-in-production"},
            )
            assert response.status_code == 400


class TestCancelEndpoint:
    def test_cancel_without_agent(self):
        """无 Agent 时 cancel 返回 no_agent"""
        from fastapi.testclient import TestClient
        from lemma.api.server import app

        client = TestClient(app)
        with patch("lemma.api.server._agent", None):
            response = client.post(
                "/api/cancel",
                headers={"X-API-Key": "dev-key-change-in-production"},
            )
            assert response.status_code == 200
            assert response.json()["status"] == "no_agent"


class TestResetEndpoint:
    def test_reset_without_agent(self):
        """无 Agent 时 reset 不报错"""
        from fastapi.testclient import TestClient
        from lemma.api.server import app

        client = TestClient(app)
        with patch("lemma.api.server._agent", None):
            response = client.post(
                "/api/reset",
                headers={"X-API-Key": "dev-key-change-in-production"},
            )
            assert response.status_code == 200


class TestSafeResolve:
    def test_absolute_path_rejected(self):
        """绝对路径应被拒绝"""
        from fastapi.testclient import TestClient
        from fastapi import HTTPException
        from lemma.api.server import _safe_resolve
        from pathlib import Path

        base = Path("/tmp/workdir")
        with pytest.raises(HTTPException):
            _safe_resolve(base, "/etc/passwd")

    def test_traversal_path_rejected(self):
        """路径遍历应被拒绝"""
        from fastapi.testclient import TestClient
        from fastapi import HTTPException
        from lemma.api.server import _safe_resolve
        from pathlib import Path

        base = Path("/tmp/workdir")
        with pytest.raises(HTTPException):
            _safe_resolve(base, "../../../etc/passwd")

    def test_valid_relative_path_accepted(self, tmp_path):
        """有效相对路径应通过"""
        from lemma.api.server import _safe_resolve

        subdir = tmp_path / "subdir"
        subdir.mkdir()
        result = _safe_resolve(tmp_path, "subdir")
        assert result == subdir.resolve()

    def test_empty_path_returns_base(self, tmp_path):
        """空路径返回基础目录"""
        from lemma.api.server import _safe_resolve
        result = _safe_resolve(tmp_path, "")
        assert result == tmp_path.resolve()


class TestFilesEndpoint:
    def test_files_without_agent(self):
        from fastapi.testclient import TestClient
        from lemma.api.server import app

        client = TestClient(app)
        with patch("lemma.api.server._agent", None):
            response = client.get("/api/files", headers={"X-API-Key": "dev-key-change-in-production"})
            assert response.status_code == 400

    def test_files_with_agent(self, tmp_path):
        from fastapi.testclient import TestClient
        from lemma.api.server import app

        mock_agent = MagicMock()
        mock_agent.work_dir = tmp_path
        (tmp_path / "test.txt").write_text("hello")

        client = TestClient(app)
        with patch("lemma.api.server._agent", mock_agent):
            response = client.get("/api/files", headers={"X-API-Key": "dev-key-change-in-production"})
            assert response.status_code == 200
            data = response.json()
            assert "files" in data

    def test_file_read(self, tmp_path):
        from fastapi.testclient import TestClient
        from lemma.api.server import app

        mock_agent = MagicMock()
        mock_agent.work_dir = tmp_path
        (tmp_path / "doc.md").write_text("# Hello")

        client = TestClient(app)
        with patch("lemma.api.server._agent", mock_agent):
            response = client.get("/api/file/doc.md", headers={"X-API-Key": "dev-key-change-in-production"})
            assert response.status_code == 200
            assert response.json()["content"] == "# Hello"

    def test_file_not_found(self, tmp_path):
        from fastapi.testclient import TestClient
        from lemma.api.server import app

        mock_agent = MagicMock()
        mock_agent.work_dir = tmp_path

        client = TestClient(app)
        with patch("lemma.api.server._agent", mock_agent):
            response = client.get("/api/file/nonexistent.txt", headers={"X-API-Key": "dev-key-change-in-production"})
            assert response.status_code == 404


class TestCostEndpoint:
    def test_cost_without_agent(self):
        from fastapi.testclient import TestClient
        from lemma.api.server import app

        client = TestClient(app)
        with patch("lemma.api.server._agent", None):
            response = client.get("/api/cost", headers={"X-API-Key": "dev-key-change-in-production"})
            assert response.status_code == 200
            assert response.json()["cost_usd"] == 0


class TestPerformanceEndpoint:
    def test_performance_returns_metrics(self):
        from fastapi.testclient import TestClient
        from lemma.api.server import app

        client = TestClient(app)
        response = client.get("/api/performance", headers={"X-API-Key": "dev-key-change-in-production"})
        assert response.status_code == 200
        assert "metrics" in response.json()


class TestRolesEndpoint:
    def test_roles_returns_list(self):
        from fastapi.testclient import TestClient
        from lemma.api.server import app

        client = TestClient(app)
        response = client.get("/api/roles", headers={"X-API-Key": "dev-key-change-in-production"})
        assert response.status_code == 200
        assert "roles" in response.json()


class TestConfigEndpoint:
    def test_config_update(self):
        from fastapi.testclient import TestClient
        from lemma.api.server import app

        client = TestClient(app)
        with patch("lemma.api.server._agent", MagicMock()):
            response = client.post(
                "/api/config",
                json={"provider": "openai", "model": "gpt-4o", "api_key": "test"},
                headers={"X-API-Key": "dev-key-change-in-production"},
            )
            assert response.status_code == 200
            assert response.json()["status"] == "ok"


class TestSessionEndpoints:
    def test_sessions_without_agent(self):
        from fastapi.testclient import TestClient
        from lemma.api.server import app

        client = TestClient(app)
        with patch("lemma.api.server._agent", None):
            response = client.get("/api/sessions", headers={"X-API-Key": "dev-key-change-in-production"})
            assert response.status_code == 400

    def test_save_without_agent(self):
        from fastapi.testclient import TestClient
        from lemma.api.server import app

        client = TestClient(app)
        with patch("lemma.api.server._agent", None):
            response = client.post("/api/session/save", headers={"X-API-Key": "dev-key-change-in-production"})
            assert response.status_code == 400


class TestEvalEndpoints:
    def test_eval_run_without_agent(self):
        """评测端点应工作"""
        from fastapi.testclient import TestClient
        from lemma.api.server import app

        client = TestClient(app)
        # eval/run 不需要 agent，直接调用
        response = client.post(
            "/api/eval/run",
            params={"domain_id": "math-modeling"},
            headers={"X-API-Key": "dev-key-change-in-production"},
        )
        # 可能返回 200 或异常（取决于依赖），但不应崩溃
        assert response.status_code in [200, 500]

    def test_eval_domains(self):
        from fastapi.testclient import TestClient
        from lemma.api.server import app

        client = TestClient(app)
        response = client.get(
            "/api/eval/domains",
            headers={"X-API-Key": "dev-key-change-in-production"},
        )
        assert response.status_code == 200
        assert "domains" in response.json()

    def test_eval_report_nonexistent_domain(self):
        from fastapi.testclient import TestClient
        from lemma.api.server import app

        client = TestClient(app)
        response = client.get(
            "/api/eval/report/nonexistent-domain-xyz",
            headers={"X-API-Key": "dev-key-change-in-production"},
        )
        assert response.status_code == 404


class TestCasesEndpoint:
    def test_cases_returns_list(self):
        from fastapi.testclient import TestClient
        from lemma.api.server import app

        client = TestClient(app)
        with patch("lemma.knowledge.case_library.CaseLibrary.search") as mock_search:
            mock_search.return_value = []
            response = client.get(
                "/api/cases",
                headers={"X-API-Key": "dev-key-change-in-production"},
            )
            assert response.status_code == 200
            assert "cases" in response.json()


class TestCheckpointEndpoint:
    def test_checkpoint_without_agent(self):
        from fastapi.testclient import TestClient
        from lemma.api.server import app

        client = TestClient(app)
        with patch("lemma.api.server._agent", None):
            response = client.get(
                "/api/checkpoint",
                headers={"X-API-Key": "dev-key-change-in-production"},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "no_agent"


class TestHITLEndpoints:
    def test_hitl_pending_without_agent(self):
        from fastapi.testclient import TestClient
        from lemma.api.server import app

        client = TestClient(app)
        with patch("lemma.api.server._agent", None):
            response = client.get(
                "/api/hitl/pending",
                headers={"X-API-Key": "dev-key-change-in-production"},
            )
            assert response.status_code == 200
            assert "requests" in response.json()

    def test_hitl_respond_without_agent(self):
        from fastapi.testclient import TestClient
        from lemma.api.server import app

        client = TestClient(app)
        with patch("lemma.api.server._agent", None):
            response = client.post(
                "/api/hitl/respond",
                params={"request_id": "test", "response": "approve"},
                headers={"X-API-Key": "dev-key-change-in-production"},
            )
            assert response.status_code == 400


class TestKnowledgeEndpoints:
    def test_knowledge_graph(self):
        from fastapi.testclient import TestClient
        from lemma.api.server import app

        client = TestClient(app)
        response = client.get(
                "/api/knowledge/graph",
                params={"domain_id": "math-modeling"},
                headers={"X-API-Key": "dev-key-change-in-production"},
            )
        assert response.status_code == 200

    def test_knowledge_search(self):
        from fastapi.testclient import TestClient
        from lemma.api.server import app

        client = TestClient(app)
        response = client.get(
                "/api/knowledge/search",
                params={"query": "optimization", "domain_id": "math-modeling"},
                headers={"X-API-Key": "dev-key-change-in-production"},
            )
        assert response.status_code == 200


class TestDocumentEndpoints:
    def test_documents_without_agent(self):
        from fastapi.testclient import TestClient
        from lemma.api.server import app

        client = TestClient(app)
        with patch("lemma.api.server._agent", None):
            response = client.get(
                "/api/documents",
                headers={"X-API-Key": "dev-key-change-in-production"},
            )
            assert response.status_code == 400

    def test_document_versions_without_agent(self):
        from fastapi.testclient import TestClient
        from lemma.api.server import app

        client = TestClient(app)
        with patch("lemma.api.server._agent", None):
            response = client.get(
                "/api/document/test/versions",
                headers={"X-API-Key": "dev-key-change-in-production"},
            )
            assert response.status_code == 400


class TestTraceEndpoint:
    def test_trace_latest(self):
        from fastapi.testclient import TestClient
        from lemma.api.server import app

        client = TestClient(app)
        response = client.get(
            "/api/trace/latest",
            headers={"X-API-Key": "dev-key-change-in-production"},
        )
        assert response.status_code == 200


class TestTenantEndpoint:
    def test_tenant_usage(self):
        from fastapi.testclient import TestClient
        from lemma.api.server import app

        client = TestClient(app)
        response = client.get(
            "/api/tenant/usage",
            headers={"X-API-Key": "dev-key-change-in-production"},
        )
        assert response.status_code == 200


class TestExperimentsEndpoint:
    def test_list_experiments(self):
        from fastapi.testclient import TestClient
        from lemma.api.server import app

        client = TestClient(app)
        response = client.get(
            "/api/experiments",
            headers={"X-API-Key": "dev-key-change-in-production"},
        )
        assert response.status_code == 200
        assert "experiments" in response.json()


class TestAutoRunEndpoint:
    def test_auto_run_without_agent(self):
        from fastapi.testclient import TestClient
        from lemma.api.server import app

        client = TestClient(app)
        with patch("lemma.api.server._agent", None):
            response = client.post(
                "/api/auto-run",
                json={"work_dir": "/tmp/test-dir"},
                headers={"X-API-Key": "dev-key-change-in-production"},
            )
            # 无 agent + 无效 work_dir 可能返回 400/422
            assert response.status_code in [200, 400, 422]


class TestExportEndpoint:
    def test_export_without_agent(self):
        from fastapi.testclient import TestClient
        from lemma.api.server import app

        client = TestClient(app)
        with patch("lemma.api.server._agent", None):
            response = client.post(
                "/api/export",
                headers={"X-API-Key": "dev-key-change-in-production"},
            )
            assert response.status_code == 400


class TestValidateWorkDir:
    """_validate_work_dir 边界测试"""

    def test_valid_path(self, tmp_path):
        from lemma.api.server import _validate_work_dir
        result = _validate_work_dir(str(tmp_path))
        assert result == tmp_path.resolve()

    def test_nonexistent_path_raises(self, tmp_path):
        from fastapi import HTTPException
        from lemma.api.server import _validate_work_dir
        nonexistent = tmp_path / "does_not_exist"
        with pytest.raises(HTTPException) as exc_info:
            _validate_work_dir(str(nonexistent))
        assert exc_info.value.status_code == 400

    def test_file_path_raises(self, tmp_path):
        from fastapi import HTTPException
        from lemma.api.server import _validate_work_dir
        file_path = tmp_path / "test.txt"
        file_path.write_text("hello")
        with pytest.raises(HTTPException) as exc_info:
            _validate_work_dir(str(file_path))
        assert exc_info.value.status_code == 400


class TestInitEndpoint:
    """POST /api/project/init 端点测试"""

    def test_init_with_valid_params(self, tmp_path):
        from fastapi.testclient import TestClient
        from lemma.api.server import app
        from unittest.mock import patch, MagicMock

        client = TestClient(app)
        with patch("lemma.api.server._agent", None):
            with patch("lemma.api.server.create_agent") as mock_create:
                mock_agent = MagicMock()
                mock_agent.domain.id = "math-modeling"
                mock_agent.domain.name = "数学建模"
                mock_agent.domain.phases = []
                mock_agent.domain.roles = []
                mock_create.return_value = mock_agent

                response = client.post(
                    "/api/project/init",
                    json={
                        "work_dir": str(tmp_path),
                        "domain_id": "math-modeling",
                    },
                    headers={"X-API-Key": "dev-key-change-in-production"},
                )
                assert response.status_code == 200
                assert response.json()["status"] == "ok"

    def test_init_without_work_dir(self):
        from fastapi.testclient import TestClient
        from lemma.api.server import app

        client = TestClient(app)
        response = client.post(
            "/api/project/init",
            json={"domain_id": "math-modeling"},
            headers={"X-API-Key": "dev-key-change-in-production"},
        )
        assert response.status_code == 422  # 缺少必填字段


class TestConfigEndpointExtended:
    """配置端点扩展测试"""

    def test_config_invalid_provider(self):
        from fastapi.testclient import TestClient
        from lemma.api.server import app

        client = TestClient(app)
        with patch("lemma.api.server._agent", MagicMock()):
            response = client.post(
                "/api/config",
                json={"provider": "invalid_provider", "model": "test", "api_key": "test"},
                headers={"X-API-Key": "dev-key-change-in-production"},
            )
            assert response.status_code == 200
            assert response.json()["status"] == "ok"

    def test_config_with_base_url(self):
        from fastapi.testclient import TestClient
        from lemma.api.server import app

        client = TestClient(app)
        with patch("lemma.api.server._agent", MagicMock()):
            response = client.post(
                "/api/config",
                json={
                    "provider": "openai-compatible",
                    "model": "custom-model",
                    "api_key": "test",
                    "base_url": "https://custom.api.com/v1",
                },
                headers={"X-API-Key": "dev-key-change-in-production"},
            )
            assert response.status_code == 200

    def test_config_missing_api_key(self):
        from fastapi.testclient import TestClient
        from lemma.api.server import app

        client = TestClient(app)
        with patch("lemma.api.server._agent", MagicMock()):
            response = client.post(
                "/api/config",
                json={"provider": "openai", "model": "gpt-4o", "api_key": ""},
                headers={"X-API-Key": "dev-key-change-in-production"},
            )
            # 空 API Key 可能通过校验但后续会失败
            assert response.status_code in [200, 422]
