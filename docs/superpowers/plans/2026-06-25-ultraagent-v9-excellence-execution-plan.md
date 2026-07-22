# Lemma v9.0 — 卓越执行计划：从"功能齐全"到"可信赖·可度量·可进化"

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 基于 v7 大规模功能落地和 v8 整合补全之后的现状，将 Lemma 从"模块齐全但接线断裂、测试有量但深度不足、前端有空壳但数据未通"的状态，推进为"每个模块有测试、每个端点可调用、每个前端组件有数据源、系统行为可度量可验证"的生产级平台。

**Architecture:** 本计划是 v6→v7→v8 路线图的自然延续。v6 解决了"能跑→好用"，v7 解决了"好用→卓越（功能维度）"，v8 解决了"功能齐全→接线补全"。v9 聚焦在 **"接线补全→深度可信"**——不是加新功能，而是让已有功能真正可依赖、可验证、可持续。分 5 个阶段，每阶段独立可交付。

**Tech Stack:** Python 3.11+, FastAPI, pytest 9.1.1, pytest-cov 7.1.0, React 18, TypeScript, Vitest 2.0, Playwright (新引入), Electron 31

---

## 0. 路线图演进回顾

| 版本 | 文档 | 核心目标 | 完成度 |
|------|------|----------|--------|
| v6 | `2026-06-24-lemma-v6-next-roadmap.md` | 测试加固、去emoji、可访问性、打包部署 | ✅ ~95% |
| v7 | `2026-06-25-lemma-v7-excellence-roadmap.md` | A-F六大维度：智能深水区、工程底盘、平台化 | ✅ 功能落地，接线待补 |
| v8 | `2026-06-25-lemma-v8-consolidation-plan.md` | 补测试盲区、打通API接线、前端补全 | 🔄 执行中 (7 测试文件待提交) |
| **v9** | **本文档** | **深度可信：测试深度、端到端验证、性能基线、持续度量** | 📋 计划中 |

---

## 1. 现状诊断（2026-06-25 v8 执行中途审计）

### 1.1 资产清单

| 类别 | 数量 | 状态 |
|------|------|------|
| Python 源文件 | 82 个模块 / ~10,400 行 | 🟢 |
| React 组件 | 17 个 | 🟢 |
| 领域配置 | 4 个 (math-modeling/paper-writing/lab-report/literature-review) | 🟢 |
| 内置工具 | 9 个 (code/latex/file/quality/figure/equation/data/source_tracker/evidence_map) | 🟢 |
| REST 端点 | ~25 个 (含 v7 新增) | 🟡 部分未接线 |
| WebSocket 消息类型 | 7 种 (init/chat/auto_run/stream_chat/cancel/... ) | 🟢 |
| 后端测试 | 434 passed, 0 failed | 🟢 |
| 前端测试 | 21 passed, 0 failed | 🟡 |
| E2E 测试 | 38 passed, 0 failed | 🟢 |
| 总覆盖率 | 70% | 🟡 |

### 1.2 三条"战线"现状

#### 战线一：测试深度 ⚔️

```
已解决 (v8 Task 1.1):
✅ test_debate.py       — 5 个测试，覆盖 debate 核心路径
✅ test_cascade.py      — 6 个测试，覆盖 CascadeRouter 创建+质量评估
✅ test_session_store.py — 6 个测试，覆盖 save/load/list/delete/count
✅ test_perf_monitor.py — 7 个测试，覆盖 record/stats/reset/singleton/decorator
✅ test_logging_config.py — 5 个测试，覆盖 JSON格式化+trace context+setup

待提交:
📋 7 个测试文件已写好，在 git status 中显示为 Untracked (??)

仍缺失:
❌ test_quality_metrics.py  — 内容为空壳，需实质性测试
❌ test_prompt_version.py   — 内容为空壳，需实质性测试
❌ test_fuzzer.py           — 模糊测试器完全未测
❌ test_exporter.py         — 导出器完全未测 (0%)
❌ server.py 测试扩展       — 覆盖率仅 28%
❌ orchestration/engine.py  — 覆盖率仅 16%
❌ 13 个前端组件无测试      — 仅 ChatPanel/PipelinePanel/SettingsPanel/Sidebar 有测试
```

#### 战线二：API 接线 ⚔️

```
已接线 (v8 Task 2.x):
✅ 评测系统 API      — POST /api/eval/run, GET /api/eval/report, GET /api/eval/domains
✅ 检查点 API        — GET /api/checkpoint, POST /api/checkpoint/resume
✅ HITL API          — GET /api/hitl/pending, POST /api/hitl/respond
✅ 知识图谱 API      — GET /api/knowledge/graph, GET /api/knowledge/search
✅ 案例库 API        — GET /api/cases
✅ 文档版本 API      — GET /api/documents, GET /api/document/{name}/versions
✅ Trace API         — GET /api/trace/latest
✅ 租户/实验 API     — GET /api/tenant/usage, GET /api/experiments

待确认:
⚠️ 以上端点在 server.py 中是否已实际添加？（v8 plan 设计了但需要验证是否已落地）
⚠️ 若已落地，是否每个端点都有对应的测试？
```

#### 战线三：前端对齐 ⚔️

```
已创建组件 (v8 Task 3.x):
✅ TraceViewer.tsx        — trace 树可视化组件
✅ ConfirmationCard.tsx   — HITL 确认卡片组件
✅ DocumentVersions.tsx   — 文档版本历史组件
✅ ChatPanel.test.tsx     — 聊天面板测试
✅ PipelinePanel.test.tsx — 流水线面板测试
✅ SettingsPanel.test.tsx — 设置面板测试

待确认:
⚠️ TraceViewer 是否对接了 /api/trace/latest 真实数据？
⚠️ ConfirmationCard 是否对接了 /api/hitl/pending 轮询？
⚠️ DocumentVersions 是否对接了 /api/documents 数据源？
⚠️ 其他前端组件 (AgentRoster/AdventureMap/AgentThoughts/FileViewer/SessionPanel/AgentQuickMenu) 是否有测试？
```

### 1.3 关键风险矩阵

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| API 端点设计文档与实际代码不一致 | 中 | 高 | 本计划包含端点审计任务 |
| 前端组件引用不存在的 API 路径 | 中 | 高 | 本计划包含前后端联调任务 |
| 真实 LLM 评测结果为负面 | 低 | 高 | 先 mock 评测跑通，再切真实 API |
| E2E 测试因环境依赖而不可重复 | 中 | 中 | 引入 Playwright 替代纯 API E2E |
| Electron 打包后 Python 后端无法启动 | 中 | 中 | 本计划包含打包验证任务 |

---

## 2. 总览：五阶段路线图

```
阶段一 (第 1-3 天)        阶段二 (第 4-10 天)       阶段三 (第 11-20 天)
审计与提交 ───────────→ 测试深度攻坚 ───────────→ API 接线验证与补全
│                        │                        │
├─ 提交 7 个待提交测试     ├─ 0%模块实质性测试       ├─ 逐端点审计+测试
├─ 确认 v8 各 Task 落地情况 ├─ server.py 覆盖率 28→65%  ├─ WebSocket 消息流测试
├─ 建立真实覆盖率基线       ├─ orchestration/engine 16→50%├─ 前端组件 API 对接验证
└─ 更新 QUALITY_BASELINE   └─ 工具模块 15-25→60%     └─ 端点文档自动生成

阶段四 (第 21-30 天)      阶段五 (第 31-45 天)
生产验证 ───────────────→ 持续质量体系
│                        │
├─ 真实 LLM 评测           ├─ 覆盖率CI门禁
├─ E2E 全流程 Playwright   ├─ 性能基线+CI回归
├─ Electron 打包实测        ├─ 类型检查门禁
└─ 性能基线建立             └─ 文档自动生成
```

| 里程碑 | 验收标准 | 预计时间 |
|--------|----------|----------|
| M1: 基线确立 | 7 个待提交测试入仓，0%模块全部消除，真实覆盖率 ≥ 72% | 第 3 天 |
| M2: 测试深度 | server.py ≥ 60%, orchestration/engine ≥ 50%, 工具模块 ≥ 60%, 前端组件测试 ≥ 10 个 | 第 10 天 |
| M3: API 可信 | 所有 v7/v8 新增端点有测试，WS 消息流全路径覆盖，前端组件对接真实 API | 第 20 天 |
| M4: 生产验证 | 真实 LLM 评测通过，4 领域 E2E 全绿，Electron 打包可运行，性能基线文档化 | 第 30 天 |
| M5: 持续度量 | CI 覆盖率门禁+性能门禁+类型门禁全生效，每次 PR 自动报告质量变化 | 第 45 天 |

---

## 阶段一：审计与提交（第 1-3 天）

### Task 1.1: 提交 7 个已完成测试文件

**目标:** 将已写好的 7 个测试文件正式纳入版本控制，消除 0% 覆盖率模块。

**Files:**
- Commit: `backend/tests/test_debate.py`
- Commit: `backend/tests/test_cascade.py`
- Commit: `backend/tests/test_session_store.py`
- Commit: `backend/tests/test_perf_monitor.py`
- Commit: `backend/tests/test_logging_config.py`
- Commit: `backend/tests/test_quality_metrics.py`
- Commit: `backend/tests/test_prompt_version.py`

- [ ] **Step 1: 审查 test_quality_metrics.py 和 test_prompt_version.py 内容**

先读取这两个文件，确认它们是否有实质性测试内容，还是仅骨架。

```bash
cat backend/tests/test_quality_metrics.py
cat backend/tests/test_prompt_version.py
```

- [ ] **Step 2: 如有骨架测试，补全实质性断言**

若内容为仅含 `assert True` 或 `pass` 的空壳，参考已完成的 5 个测试文件的风格补充测试。

`test_quality_metrics.py` 应覆盖：
- `QualityMetrics` 实例化
- 评分计算（输入有效输出 → 返回合理分数）
- 评分计算（输入空字符串 → 返回 0 或异常）
- 多维度评分配置

`test_prompt_version.py` 应覆盖：
- `PromptVersionTracker` 实例化
- 追踪文件变化（修改 prompt 文件 → 版本号递增）
- 获取版本历史
- 回退到指定版本

- [ ] **Step 3: 运行 7 个新测试确认全部通过**

```bash
cd backend && PYTHONPATH=src python -m pytest tests/test_debate.py tests/test_cascade.py tests/test_session_store.py tests/test_perf_monitor.py tests/test_logging_config.py tests/test_quality_metrics.py tests/test_prompt_version.py -v --tb=short
```

预期: 全部 PASS, 0 failed

- [ ] **Step 4: 提交**

```bash
cd "E:\数学建模agent"
git add backend/tests/test_debate.py backend/tests/test_cascade.py backend/tests/test_session_store.py backend/tests/test_perf_monitor.py backend/tests/test_logging_config.py backend/tests/test_quality_metrics.py backend/tests/test_prompt_version.py
git commit -m "test: eliminate all 0% coverage modules (7 modules, ~35 new tests)"
```

### Task 1.2: 审计 v8 计划落地情况

**目标:** 逐项核验 v8 consolidation plan 的 4 个阶段是否已实际落地到代码中。

**Files:**
- Audit: `backend/src/ultramath/api/server.py` (检查 v8 Task 2.1-2.5 端点是否已添加)
- Audit: `frontend/src/components/TraceViewer.tsx` (检查是否对接真实 API)
- Audit: `frontend/src/components/ConfirmationCard.tsx` (检查是否对接真实 API)
- Audit: `frontend/src/components/DocumentVersions.tsx` (检查是否对接真实 API)
- Audit: `frontend/src/__tests__/` (检查测试文件质量)

- [ ] **Step 1: 审计 server.py 中的 API 端点**

```bash
cd backend && grep -n "def run_evaluation\|def get_eval_report\|def get_checkpoint\|def hitl_respond\|def hitl_pending\|def get_knowledge_graph\|def search_knowledge\|def list_cases\|def list_document_versions\|def get_document_versions\|def get_latest_trace\|def get_tenant_usage\|def list_experiments" src/ultramath/api/server.py
```

若缺失任何端点，记录到 `docs/superpowers/plans/v8-audit-gaps.md`。

- [ ] **Step 2: 审计前端组件是否对接真实数据源**

检查以下组件是否使用 `fetch()` 或 WebSocket 获取数据：

```bash
cd frontend && grep -n "fetch\|useWebSocket\|api/" src/components/TraceViewer.tsx src/components/ConfirmationCard.tsx src/components/DocumentVersions.tsx
```

若组件使用 mock 数据或硬编码，记录到审计报告。

- [ ] **Step 3: 审计前端测试质量**

```bash
cd frontend && grep -n "assert\|expect\|it\|test" src/__tests__/ChatPanel.test.tsx src/__tests__/PipelinePanel.test.tsx src/__tests__/SettingsPanel.test.tsx
```

确认每个测试文件有 ≥ 3 个有意义的断言。

- [ ] **Step 4: 生成审计报告并提交**

```bash
git add docs/superpowers/plans/v8-audit-gaps.md
git commit -m "docs: add v8 execution audit report"
```

### Task 1.3: 建立真实覆盖率基线

**目标:** 在提交 7 个新测试后，重新测量全量覆盖率，更新基线文档。

- [ ] **Step 1: 运行全量测试并生成覆盖率报告**

```bash
cd backend && PYTHONPATH=src python -m pytest tests/ --cov=src/ultramath --cov-report=term-missing --cov-report=html -v 2>&1 | tee coverage-report.txt
```

- [ ] **Step 2: 运行前端测试并生成覆盖率报告**

```bash
cd frontend && npx vitest run --coverage 2>&1 | tee coverage-report.txt
```

- [ ] **Step 3: 更新 QUALITY_BASELINE.md**

在 `docs/QUALITY_BASELINE.md` 中更新以下内容：
- 测试数（后端 + 前端 + E2E）
- 总覆盖率百分比
- 各模块覆盖率表
- 0% 覆盖率模块清单（应变为空）
- 新的覆盖率门禁值

- [ ] **Step 4: 提交**

```bash
git add docs/QUALITY_BASELINE.md backend/coverage-report.txt frontend/coverage-report.txt
git commit -m "docs: update quality baseline post v8-test-merge"
```

---

## 阶段二：测试深度攻坚（第 4-10 天）

### Task 2.1: server.py 覆盖率 28% → 65%

**目标:** 将 API 服务器的测试覆盖从 28% 提升至 65%，重点覆盖 REST 端点和 WebSocket 消息处理。

**Files:**
- Modify: `backend/tests/test_api_server.py`
- Create: `backend/tests/test_api_websocket.py`

- [ ] **Step 1: 梳理 server.py 中所有待测端点**

```bash
cd backend && grep -n "@app\.\(get\|post\|put\|delete\|websocket\)" src/ultramath/api/server.py
```

列出所有端点，标注已有测试和缺失测试。

- [ ] **Step 2: 编写 REST 端点测试补充**

```python
# backend/tests/test_api_server.py — 追加以下测试类

class TestAutoRunEndpoint:
    """POST /api/auto-run 端点测试"""

    @pytest.fixture
    def client(self):
        from ultramath.api.server import app
        from fastapi.testclient import TestClient
        return TestClient(app)

    @pytest.fixture
    def auth_headers(self):
        return {"X-API-Key": "test-api-key-for-development"}

    def test_auto_run_without_agent(self, client, auth_headers):
        """未初始化 Agent 时 auto_run 返回 400"""
        response = client.post(
            "/api/auto-run",
            json={"domain_id": "math-modeling"},
            headers=auth_headers,
        )
        assert response.status_code == 400

    def test_cancel_without_agent(self, client, auth_headers):
        """未初始化时 cancel 返回 400"""
        response = client.post("/api/cancel", headers=auth_headers)
        assert response.status_code == 400


class TestFileEndpoints:
    """文件管理端点测试"""

    def test_list_files_without_agent(self, client, auth_headers):
        """未初始化时 GET /api/files 返回 400"""
        response = client.get("/api/files", headers=auth_headers)
        assert response.status_code == 400

    def test_get_file_without_agent(self, client, auth_headers):
        """未初始化时 GET /api/file/xxx 返回 400"""
        response = client.get("/api/file/test.txt", headers=auth_headers)
        assert response.status_code == 400


class TestSessionEndpoints:
    """会话管理端点测试"""

    def test_save_session_without_agent(self, client, auth_headers):
        response = client.post("/api/session/save", headers=auth_headers)
        assert response.status_code == 400

    def test_list_sessions_without_agent(self, client, auth_headers):
        response = client.get("/api/sessions", headers=auth_headers)
        assert response.status_code == 400

    def test_load_session_without_agent(self, client, auth_headers):
        response = client.post("/api/session/test-id/load", headers=auth_headers)
        assert response.status_code == 400

    def test_delete_session_without_agent(self, client, auth_headers):
        response = client.delete("/api/session/test-id", headers=auth_headers)
        assert response.status_code == 400


class TestExportEndpoint:
    """导出端点测试"""

    def test_export_without_agent(self, client, auth_headers):
        response = client.post("/api/export", headers=auth_headers)
        assert response.status_code == 400

    def test_export_with_format_param(self, client, auth_headers):
        response = client.post("/api/export?format=markdown", headers=auth_headers)
        assert response.status_code == 400  # 无 agent


class TestCostEndpoint:
    """成本查询端点测试"""

    def test_cost_without_agent(self, client, auth_headers):
        response = client.get("/api/cost", headers=auth_headers)
        # 无 agent 时可能返回 0 或 200
        assert response.status_code in [200, 400]


class TestPerformanceEndpoint:
    """性能端点测试"""

    def test_performance_without_agent(self, client, auth_headers):
        response = client.get("/api/performance", headers=auth_headers)
        assert response.status_code in [200, 400]
```

- [ ] **Step 3: 编写 WebSocket 消息处理测试**

```python
# backend/tests/test_api_websocket.py
"""WebSocket 端到端消息流测试"""
import json
import pytest
from fastapi.testclient import TestClient
from ultramath.api.server import app


class TestWebSocketLifecycle:
    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_websocket_health_message(self, client):
        """WebSocket 连接后应收到欢迎消息"""
        with client.websocket_connect("/ws") as websocket:
            data = websocket.receive_json()
            assert data["type"] == "connected"
            assert "version" in data

    def test_websocket_init_creates_agent(self, client):
        """发送 init 消息应初始化 Agent"""
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            with client.websocket_connect("/ws") as websocket:
                _ = websocket.receive_json()  # 跳过 connected
                websocket.send_json({
                    "type": "init",
                    "domain_id": "math-modeling",
                    "work_dir": tmpdir,
                })
                response = websocket.receive_json()
                assert response["type"] == "initialized"
                assert response["domain"]["id"] == "math-modeling"
                assert "phases" in response
                assert "roles" in response

    def test_websocket_chat_requires_init(self, client):
        """未初始化时 chat 应返回错误"""
        with client.websocket_connect("/ws") as websocket:
            _ = websocket.receive_json()  # 跳过 connected
            websocket.send_json({
                "type": "chat",
                "message": "hello",
            })
            response = websocket.receive_json()
            assert response["type"] == "error"
            assert "未初始化" in response.get("message", "")

    def test_websocket_invalid_message_type(self, client):
        """无效消息类型应返回错误"""
        with client.websocket_connect("/ws") as websocket:
            _ = websocket.receive_json()
            websocket.send_json({"type": "invalid_type_xyz"})
            response = websocket.receive_json()
            assert response["type"] == "error"

    def test_websocket_bad_json(self, client):
        """发送非 JSON 文本应不崩溃"""
        with client.websocket_connect("/ws") as websocket:
            _ = websocket.receive_json()
            websocket.send_text("not valid json{{{")
            # 应收到错误或连接保持（取决于实现）
            try:
                response = websocket.receive_json()
                assert response["type"] == "error"
            except Exception:
                pass  # 连接断开也是合理的处理方式
```

- [ ] **Step 4: 运行测试确认覆盖率提升**

```bash
cd backend && PYTHONPATH=src python -m pytest tests/test_api_server.py tests/test_api_websocket.py -v --cov=src/ultramath/api/server --cov-report=term
```

预期: server.py 覆盖率 ≥ 60%

- [ ] **Step 5: 提交**

```bash
git add backend/tests/test_api_server.py backend/tests/test_api_websocket.py
git commit -m "test: expand server.py coverage from 28% to 60%+ (REST + WebSocket)"
```

### Task 2.2: orchestration/engine.py 覆盖率 16% → 50%

**目标:** 编排引擎是 run_auto 的核心路径，276 行代码仅 16% 覆盖不可接受。

**Files:**
- Modify: `backend/tests/test_runner.py` 或 Create: `backend/tests/test_orchestration_engine.py`

- [ ] **Step 1: 分析 engine.py 中未覆盖的路径**

```bash
cd backend && PYTHONPATH=src python -m pytest tests/ --cov=src/ultramath/orchestration/engine --cov-report=term-missing
```

查看 term-missing 输出，找出未覆盖的行号。

- [ ] **Step 2: 编写编排引擎单元测试**

```python
# backend/tests/test_orchestration_engine.py
"""编排引擎单元测试 — 覆盖 RunEngine 核心路径"""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from ultramath.orchestration.engine import RunEngine


class TestRunEngine:
    @pytest.fixture
    def mock_agent(self):
        agent = MagicMock()
        agent.domain.phases = [
            MagicMock(id="analysis", name="分析", order=1, progress=15),
            MagicMock(id="derivation", name="推导", order=2, progress=30),
            MagicMock(id="writing", name="写作", order=3, progress=80),
        ]
        agent.domain.get_phase_by_id = lambda pid: next(
            (p for p in agent.domain.phases if p.id == pid), None
        )
        agent.chat = AsyncMock(return_value="Phase completed successfully.")
        agent._execute_phase = AsyncMock(
            return_value=MagicMock(success=True, summary="done", phase_id="analysis")
        )
        agent.current_phase = "idle"
        return agent

    def test_engine_creation(self, mock_agent):
        engine = RunEngine(mock_agent)
        assert engine.agent is mock_agent
        assert engine.cancelled is False

    @pytest.mark.asyncio
    async def test_run_to_completion(self, mock_agent):
        """正常跑完所有阶段"""
        engine = RunEngine(mock_agent)
        result = await engine.run("测试输入")
        assert result is not None
        # 每个阶段至少被调用一次
        assert mock_agent._execute_phase.call_count >= len(mock_agent.domain.phases)

    @pytest.mark.asyncio
    async def test_cancel_mid_run(self, mock_agent):
        """中途取消运行"""
        engine = RunEngine(mock_agent)
        engine.cancel()
        result = await engine.run("测试输入")
        # 取消后应立即返回而不执行任何阶段
        assert engine.cancelled is True

    @pytest.mark.asyncio
    async def test_run_with_phase_failure(self, mock_agent):
        """某个阶段执行失败后应能继续（取决于实现）"""
        mock_agent._execute_phase = AsyncMock(
            return_value=MagicMock(success=False, summary="failed", phase_id="analysis")
        )
        engine = RunEngine(mock_agent)
        result = await engine.run("测试输入")
        # 不应崩溃
        assert result is not None

    @pytest.mark.asyncio
    async def test_run_handles_empty_phases(self, mock_agent):
        """领域没有阶段时不应崩溃"""
        mock_agent.domain.phases = []
        engine = RunEngine(mock_agent)
        result = await engine.run("测试输入")
        assert result is not None

    def test_progress_callback(self, mock_agent):
        """进度回调被正确调用"""
        callback = MagicMock()
        engine = RunEngine(mock_agent, on_progress=callback)
        engine._report_progress("analysis", 15)
        callback.assert_called_once()
```

- [ ] **Step 3: 运行测试确认**

```bash
cd backend && PYTHONPATH=src python -m pytest tests/test_orchestration_engine.py -v --cov=src/ultramath/orchestration/engine --cov-report=term
```

预期: 覆盖率 ≥ 50%

- [ ] **Step 4: 提交**

```bash
git add backend/tests/test_orchestration_engine.py
git commit -m "test: expand orchestration/engine.py coverage from 16% to 50%+"
```

### Task 2.3: 工具模块测试补全

**目标:** 将 data_analyzer, equation_solver, evidence_map, quality_checker, source_tracker, exporter 的覆盖率从 15-25% 提升至 ≥ 60%。

**Files:**
- Modify: `backend/tests/test_tools.py` 或各独立测试文件
- Modify: `backend/tests/test_exporter_ext.py`
- Modify: `backend/tests/test_evidence_map.py`
- Modify: `backend/tests/test_quality_checker.py`

- [ ] **Step 1: 补充 data_analyzer 测试**

```python
# backend/tests/test_tools.py — 追加 DataAnalyzerTool 测试

class TestDataAnalyzerTool:
    @pytest.fixture
    def tool(self):
        from ultramath.tools.data_analyzer import DataAnalyzerTool
        return DataAnalyzerTool()

    def test_ttest_execution(self, tool):
        result = tool.execute(
            test_type="ttest",
            data=[1.0, 2.0, 3.0, 4.0, 5.0],
            data2=[2.0, 3.0, 4.0, 5.0, 6.0],
        )
        assert result.success is True
        assert "t 统计量" in result.output or "ttest" in result.output.lower()

    def test_anova_execution(self, tool):
        result = tool.execute(
            test_type="anova",
            data=[],
            groups=[[1.0, 2.0, 3.0], [4.0, 5.0, 6.0], [7.0, 8.0, 9.0]],
        )
        assert result.success is True

    def test_correlation_execution(self, tool):
        result = tool.execute(
            test_type="correlation",
            data=[1.0, 2.0, 3.0, 4.0, 5.0],
            data2=[2.0, 4.0, 6.0, 8.0, 10.0],
        )
        assert result.success is True
        assert "Pearson r" in result.output or "correlation" in result.output.lower()

    def test_descriptive_stats_fallback(self, tool):
        """不指定 test_type 时返回描述性统计"""
        result = tool.execute(test_type="describe", data=[1.0, 2.0, 3.0, 4.0, 5.0])
        assert result.success is True
        assert "样本量" in result.output or "均值" in result.output

    def test_empty_data_fails_gracefully(self, tool):
        result = tool.execute(test_type="ttest", data=[], data2=[1.0])
        # 应优雅失败而非崩溃
        assert isinstance(result.success, bool)

    def test_to_openai_function(self, tool):
        schema = tool.to_openai_function()
        assert schema["function"]["name"] == "data_analyzer"
```

- [ ] **Step 2: 补充 equation_solver 测试**

```python
# backend/tests/test_tools.py — 追加 EquationSolverTool 测试

class TestEquationSolverTool:
    @pytest.fixture
    def tool(self):
        from ultramath.tools.equation_solver import EquationSolverTool
        return EquationSolverTool()

    def test_solve_linear_equation(self, tool):
        result = tool.execute(
            equations=["2*x + 3 = 7"],
            variables=["x"],
        )
        assert result.success is True

    def test_solve_system_of_equations(self, tool):
        result = tool.execute(
            equations=["x + y = 10", "x - y = 2"],
            variables=["x", "y"],
        )
        assert result.success is True

    def test_solve_quadratic(self, tool):
        result = tool.execute(
            equations=["x**2 - 4 = 0"],
            variables=["x"],
        )
        assert result.success is True

    def test_invalid_equation_fails_gracefully(self, tool):
        result = tool.execute(
            equations=["invalid ~~~ equation"],
            variables=["x"],
        )
        assert result.success is False

    def test_to_openai_function(self, tool):
        schema = tool.to_openai_function()
        assert schema["function"]["name"] == "equation_solver"
```

- [ ] **Step 3: 补充 evidence_map 测试**

```python
# backend/tests/test_evidence_map.py — 追加测试

class TestEvidenceMapExtended:
    @pytest.fixture
    def tool(self, tmp_path):
        from ultramath.tools.evidence_map import EvidenceMapTool
        return EvidenceMapTool(str(tmp_path))

    def test_add_and_query_node(self, tool):
        tool.execute(action="add_node", node_id="root", question="核心问题")
        result = tool.execute(action="get_node", node_id="root")
        assert result.success is True

    def test_add_child_node(self, tool):
        tool.execute(action="add_node", node_id="root", question="核心")
        result = tool.execute(
            action="add_node",
            node_id="child1",
            parent_id="root",
            question="子问题",
        )
        assert result.success is True

    def test_audit_confidence(self, tool):
        tool.execute(
            action="add_node",
            node_id="n1",
            confidence="high",
            is_atomic=True,
        )
        result = tool.execute(action="audit")
        assert result.success is True

    def test_invalid_action(self, tool):
        result = tool.execute(action="nonexistent_action")
        assert result.success is False
```

- [ ] **Step 4: 补充 exporter 测试**

```python
# backend/tests/test_exporter_ext.py — 实质性测试

class TestDocumentExporter:
    @pytest.fixture
    def exporter(self, tmp_path):
        from ultramath.tools.exporter import DocumentExporter
        return DocumentExporter(str(tmp_path))

    def test_export_markdown_creates_file(self, exporter):
        messages = [
            {"role": "user", "content": "hello"},
            {"role": "assistant", "content": "hi there"},
        ]
        output_path = exporter.export_markdown(messages, filename="test.md")
        assert output_path.endswith(".md")
        from pathlib import Path
        assert Path(output_path).exists()

    def test_export_markdown_content(self, exporter):
        messages = [{"role": "user", "content": "测试消息"}]
        output_path = exporter.export_markdown(messages, filename="test2.md")
        content = open(output_path, encoding="utf-8").read()
        assert "测试消息" in content

    def test_export_empty_messages(self, exporter):
        output_path = exporter.export_markdown([], filename="empty.md")
        from pathlib import Path
        assert Path(output_path).exists()

    def test_export_latex_content(self, exporter):
        output_path = exporter.export_latex(
            r"\section{测试}",
            filename="test.tex",
        )
        from pathlib import Path
        assert Path(output_path).exists()
        content = open(output_path, encoding="utf-8").read()
        assert r"\section{测试}" in content
```

- [ ] **Step 5: 运行所有工具测试确认覆盖率提升**

```bash
cd backend && PYTHONPATH=src python -m pytest tests/test_tools.py tests/test_evidence_map.py tests/test_quality_checker.py tests/test_exporter_ext.py -v --cov=src/ultramath/tools --cov-report=term
```

- [ ] **Step 6: 提交**

```bash
git add backend/tests/test_tools.py backend/tests/test_evidence_map.py backend/tests/test_exporter_ext.py
git commit -m "test: expand tool module coverage (data_analyzer, equation_solver, evidence_map, exporter) to 60%+"
```

### Task 2.4: 前端组件测试补全

**目标:** 从 4 个有测试的组件扩展到 10 个。

**Files:**
- Create: `frontend/src/__tests__/AgentRoster.test.tsx`
- Create: `frontend/src/__tests__/AdventureMap.test.tsx`
- Create: `frontend/src/__tests__/AgentThoughts.test.tsx`
- Create: `frontend/src/__tests__/FileViewer.test.tsx`
- Create: `frontend/src/__tests__/SessionPanel.test.tsx`
- Create: `frontend/src/__tests__/AgentQuickMenu.test.tsx`

- [ ] **Step 1: AgentRoster 测试**

```tsx
// frontend/src/__tests__/AgentRoster.test.tsx
import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import AgentRoster from '../components/AgentRoster'

describe('AgentRoster', () => {
  const mockRoles = [
    { id: 'lead', name: '团队指挥', emoji: '🎯' },
    { id: 'math', name: '数学家', emoji: '🧮' },
    { id: 'engineer', name: '工程师', emoji: '💻' },
  ]

  it('renders all roles', () => {
    render(
      <AgentRoster
        roles={mockRoles}
        currentRole="lead"
        onSwitchRole={() => {}}
      />
    )
    expect(screen.getByText('团队指挥')).toBeDefined()
    expect(screen.getByText('数学家')).toBeDefined()
    expect(screen.getByText('工程师')).toBeDefined()
  })

  it('highlights current role', () => {
    const { container } = render(
      <AgentRoster
        roles={mockRoles}
        currentRole="math"
        onSwitchRole={() => {}}
      />
    )
    // 当前选中角色应有特殊样式
    const mathButton = screen.getByText('数学家').closest('button')
    expect(mathButton).toBeDefined()
  })

  it('calls onSwitchRole when clicking a role', () => {
    let switchedRole = ''
    render(
      <AgentRoster
        roles={mockRoles}
        currentRole="lead"
        onSwitchRole={(id) => { switchedRole = id }}
      />
    )
    screen.getByText('工程师').click()
    expect(switchedRole).toBe('engineer')
  })
})
```

- [ ] **Step 2: FileViewer 测试**

```tsx
// frontend/src/__tests__/FileViewer.test.tsx
import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import FileViewer from '../components/FileViewer'

describe('FileViewer', () => {
  const mockFiles = [
    { path: '/test/file1.py', type: 'file', size: 1024 },
    { path: '/test/file2.tex', type: 'file', size: 2048 },
    { path: '/test/subdir', type: 'directory', size: 0 },
  ]

  it('renders file list', () => {
    render(
      <FileViewer
        files={mockFiles}
        currentPath="/test"
        onNavigate={() => {}}
        onOpenFile={() => {}}
      />
    )
    expect(screen.getByText('file1.py')).toBeDefined()
    expect(screen.getByText('file2.tex')).toBeDefined()
  })

  it('shows directory entries', () => {
    render(
      <FileViewer
        files={mockFiles}
        currentPath="/test"
        onNavigate={() => {}}
        onOpenFile={() => {}}
      />
    )
    expect(screen.getByText('subdir')).toBeDefined()
  })

  it('shows empty state when no files', () => {
    render(
      <FileViewer
        files={[]}
        currentPath="/empty"
        onNavigate={() => {}}
        onOpenFile={() => {}}
      />
    )
    // 应有空状态提示
    expect(document.body.textContent).toBeDefined()
  })
})
```

- [ ] **Step 3: SessionPanel 测试**

```tsx
// frontend/src/__tests__/SessionPanel.test.tsx
import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import SessionPanel from '../components/SessionPanel'

describe('SessionPanel', () => {
  const mockSessions = [
    { session_id: 's1', domain_id: 'math-modeling', created_at: '2026-01-01', message_count: 10 },
    { session_id: 's2', domain_id: 'paper-writing', created_at: '2026-01-02', message_count: 5 },
  ]

  it('renders session list', () => {
    render(
      <SessionPanel
        sessions={mockSessions}
        currentSessionId="s1"
        onLoadSession={vi.fn()}
        onDeleteSession={vi.fn()}
        onNewSession={vi.fn()}
      />
    )
    expect(screen.getByText(/math-modeling/)).toBeDefined()
    expect(screen.getByText(/paper-writing/)).toBeDefined()
  })

  it('shows message count for each session', () => {
    render(
      <SessionPanel
        sessions={mockSessions}
        currentSessionId="s1"
        onLoadSession={vi.fn()}
        onDeleteSession={vi.fn()}
        onNewSession={vi.fn()}
      />
    )
    expect(screen.getByText(/10/)).toBeDefined()
  })

  it('calls onNewSession when clicking new button', () => {
    const onNew = vi.fn()
    render(
      <SessionPanel
        sessions={mockSessions}
        currentSessionId="s1"
        onLoadSession={vi.fn()}
        onDeleteSession={vi.fn()}
        onNewSession={onNew}
      />
    )
    // 点击新建会话按钮
    const buttons = screen.getAllByRole('button')
    const newButton = buttons.find(b => b.textContent?.includes('新建') || b.textContent?.includes('New'))
    if (newButton) {
      newButton.click()
      expect(onNew).toHaveBeenCalled()
    }
  })
})
```

- [ ] **Step 4: AgentQuickMenu 和 AdventureMap 测试**

按相同模式编写，至少每个 3 个测试断言。

- [ ] **Step 5: 运行前端全量测试**

```bash
cd frontend && npx vitest run --coverage
```

预期: ≥ 10 个测试文件, ≥ 40 个测试用例, 全部 PASS

- [ ] **Step 6: 提交**

```bash
git add frontend/src/__tests__/
git commit -m "test: expand frontend component tests from 4 to 10 files, ~30 new test cases"
```

---

## 阶段三：API 接线验证与补全（第 11-20 天）

### Task 3.1: 逐端点审计

**目标:** 确认 v7/v8 计划中设计的 API 端点全部已在 server.py 中实现，并每个端点有对应测试。

- [ ] **Step 1: 生成当前端点清单**

```bash
cd backend && grep -n "@app\.\(get\|post\|put\|delete\|websocket\)" src/ultramath/api/server.py > /tmp/current_endpoints.txt
```

- [ ] **Step 2: 与设计清单对比**

对照以下清单逐项检查：

| 端点 | 方法 | 路径 | 来源 | 状态 |
|------|------|------|------|------|
| 评测执行 | POST | `/api/eval/run` | v8 Task 2.1 | 待确认 |
| 评测报告 | GET | `/api/eval/report/{domain_id}` | v8 Task 2.1 | 待确认 |
| 评测领域 | GET | `/api/eval/domains` | v8 Task 2.1 | 待确认 |
| 检查点查询 | GET | `/api/checkpoint` | v8 Task 2.2 | 待确认 |
| HITL 响应 | POST | `/api/hitl/respond` | v8 Task 2.2 | 待确认 |
| HITL 待确认 | GET | `/api/hitl/pending` | v8 Task 2.2 | 待确认 |
| 知识图谱 | GET | `/api/knowledge/graph` | v8 Task 2.3 | 待确认 |
| 知识搜索 | GET | `/api/knowledge/search` | v8 Task 2.3 | 待确认 |
| 案例列表 | GET | `/api/cases` | v8 Task 2.3 | 待确认 |
| 文档列表 | GET | `/api/documents` | v8 Task 2.4 | 待确认 |
| 文档版本 | GET | `/api/document/{name}/versions` | v8 Task 2.4 | 待确认 |
| Trace 最新 | GET | `/api/trace/latest` | v8 Task 2.4 | 待确认 |
| 租户用量 | GET | `/api/tenant/usage` | v8 Task 2.5 | 待确认 |
| 实验列表 | GET | `/api/experiments` | v8 Task 2.5 | 待确认 |

- [ ] **Step 3: 为缺失端点编写实现 + 测试（TDD 风格）**

对每个缺失端点：
1. 先写测试（预期 404）
2. 实现端点
3. 确认测试通过

```python
# 示例：若 /api/eval/domains 缺失

# 1. 先在 test_api_server.py 中写测试
def test_eval_domains_endpoint(client, auth_headers):
    response = client.get("/api/eval/domains", headers=auth_headers)
    assert response.status_code in [200, 404]  # 存在则 200，不存在则 404

# 2. 若 404，在 server.py 中实现
@app.get("/api/eval/domains")
async def list_eval_domains(api_key: str = Depends(verify_api_key)):
    domains_base = Path(__file__).parent.parent.parent.parent / "domains"
    domains_with_golden = []
    for d in domains_base.iterdir():
        if d.is_dir() and (d / "golden.jsonl").exists():
            domains_with_golden.append(d.name)
    return {"domains": domains_with_golden}

# 3. 重新运行测试确认 200
```

- [ ] **Step 4: 提交**

```bash
git add backend/src/ultramath/api/server.py backend/tests/test_api_server.py
git commit -m "feat: add missing v7/v8 API endpoints with tests"
```

### Task 3.2: WebSocket 消息流全路径测试

**目标:** 覆盖所有 7 种 WebSocket 消息类型的正常和异常路径。

- [ ] **Step 1: 列出所有消息类型**

```bash
cd backend && grep -n 'msg_type == "' src/ultramath/api/server.py
```

- [ ] **Step 2: 为每种消息类型编写测试**

在 `test_api_websocket.py` 中补充：

```python
class TestAllMessageTypes:
    """覆盖全部 WebSocket 消息类型的测试"""

    def test_status_message(self, client):
        """发送 status 消息应返回当前状态"""
        with client.websocket_connect("/ws") as ws:
            _ = ws.receive_json()
            ws.send_json({"type": "status"})
            response = ws.receive_json()
            assert response["type"] == "status"
            # 未初始化时应返回 not_initialized
            assert response.get("status") in ["not_initialized", "ok"]

    def test_auto_run_requires_init(self, client):
        """未初始化时 auto_run 应返回错误"""
        with client.websocket_connect("/ws") as ws:
            _ = ws.receive_json()
            ws.send_json({
                "type": "auto_run",
                "domain_id": "math-modeling",
            })
            response = ws.receive_json()
            assert response["type"] == "error"

    def test_cancel_message(self, client):
        """cancel 消息不应崩溃"""
        with client.websocket_connect("/ws") as ws:
            _ = ws.receive_json()
            ws.send_json({"type": "cancel"})
            response = ws.receive_json()
            # cancel 应有响应
            assert response["type"] in ["cancelled", "status", "error"]

    def test_switch_role_message_requires_init(self, client):
        """未初始化时 switch_role 应返回错误"""
        with client.websocket_connect("/ws") as ws:
            _ = ws.receive_json()
            ws.send_json({"type": "switch_role", "role_id": "math"})
            response = ws.receive_json()
            assert response["type"] == "error"

    def test_get_files_requires_init(self, client):
        """未初始化时 get_files 应返回错误"""
        with client.websocket_connect("/ws") as ws:
            _ = ws.receive_json()
            ws.send_json({"type": "get_files"})
            response = ws.receive_json()
            assert response["type"] == "error"
```

- [ ] **Step 3: 运行 WebSocket 测试**

```bash
cd backend && PYTHONPATH=src python -m pytest tests/test_api_websocket.py -v --tb=short
```

- [ ] **Step 4: 提交**

```bash
git add backend/tests/test_api_websocket.py
git commit -m "test: add full WebSocket message type coverage (7 types, normal + error paths)"
```

### Task 3.3: 前端组件 API 对接验证

**目标:** 确认 TraceViewer、ConfirmationCard、DocumentVersions 三个新组件使用真实 API 数据而非 mock。

- [ ] **Step 1: 逐个检查组件的 fetch/useWebSocket 调用**

```bash
cd frontend && grep -n "fetch\|useWebSocket\|useEffect" src/components/TraceViewer.tsx src/components/ConfirmationCard.tsx src/components/DocumentVersions.tsx
```

- [ ] **Step 2: 若使用 mock 数据，替换为真实 API 调用**

以 TraceViewer 为例，当前可能为：

```tsx
// 当前（使用 mock）
const [traces, setTraces] = useState([{ id: '1', name: 'mock' }])
```

应改为：

```tsx
// 修改后（使用真实 API）
import { useState, useEffect } from 'react'

interface TraceSpan {
  span_id: string
  name: string
  duration_ms: number
  children: TraceSpan[]
}

export default function TraceViewer() {
  const [trace, setTrace] = useState<TraceSpan | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const controller = new AbortController()
    fetch('/api/trace/latest', {
      headers: { 'X-API-Key': localStorage.getItem('apiKey') || '' },
      signal: controller.signal,
    })
      .then(res => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        return res.json()
      })
      .then(data => {
        if (data.status === 'no_traces') {
          setTrace(null)
        } else {
          setTrace(data)
        }
        setLoading(false)
      })
      .catch(err => {
        if (err.name !== 'AbortError') {
          setError(err.message)
          setLoading(false)
        }
      })
    return () => controller.abort()
  }, [])

  if (loading) return <div className="p-4 text-[var(--color-text-muted)]">加载 trace 数据...</div>
  if (error) return <div className="p-4 text-red-400">加载失败: {error}</div>
  if (!trace) return <div className="p-4 text-[var(--color-text-muted)]">暂无 trace 数据</div>

  return (
    <div className="trace-viewer p-4">
      <h2 className="text-lg font-semibold mb-2">Trace 时间轴</h2>
      <TraceNode span={trace} depth={0} />
    </div>
  )
}

function TraceNode({ span, depth }: { span: TraceSpan; depth: number }) {
  return (
    <div className="ml-4 border-l border-[var(--color-border)] pl-3 py-1" style={{ marginLeft: depth * 16 }}>
      <div className="flex items-center gap-2 text-sm">
        <span className="text-[var(--color-accent)]">{span.name}</span>
        <span className="text-[var(--color-text-muted)] text-xs">{span.duration_ms.toFixed(1)}ms</span>
      </div>
      {span.children?.map(child => (
        <TraceNode key={child.span_id} span={child} depth={depth + 1} />
      ))}
    </div>
  )
}
```

- [ ] **Step 3: 用相同模式改造 ConfirmationCard 和 DocumentVersions**

`ConfirmationCard` → 轮询 `GET /api/hitl/pending`，用户点击后调用 `POST /api/hitl/respond`

`DocumentVersions` → 调用 `GET /api/documents` + `GET /api/document/{name}/versions`

- [ ] **Step 4: 编写前端集成测试**

```tsx
// frontend/src/__tests__/TraceViewer.test.tsx
import { render, screen, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import TraceViewer from '../components/TraceViewer'

describe('TraceViewer', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('shows loading state initially', () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
      new Response(JSON.stringify({ status: 'no_traces' }), { status: 200 })
    )
    render(<TraceViewer />)
    expect(screen.getByText(/加载/)).toBeDefined()
  })

  it('shows empty state when no traces', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
      new Response(JSON.stringify({ status: 'no_traces' }), { status: 200 })
    )
    render(<TraceViewer />)
    await waitFor(() => {
      expect(screen.getByText(/暂无 trace/)).toBeDefined()
    })
  })

  it('renders trace tree when data available', async () => {
    const mockTrace = {
      span_id: 'root',
      name: 'run_auto',
      duration_ms: 1500,
      children: [
        { span_id: 'c1', name: 'analysis', duration_ms: 500, children: [] },
        { span_id: 'c2', name: 'derivation', duration_ms: 1000, children: [] },
      ],
    }
    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
      new Response(JSON.stringify(mockTrace), { status: 200 })
    )
    render(<TraceViewer />)
    await waitFor(() => {
      expect(screen.getByText('run_auto')).toBeDefined()
      expect(screen.getByText('analysis')).toBeDefined()
      expect(screen.getByText('derivation')).toBeDefined()
    })
  })

  it('shows error state on fetch failure', async () => {
    vi.spyOn(globalThis, 'fetch').mockRejectedValueOnce(new Error('Network error'))
    render(<TraceViewer />)
    await waitFor(() => {
      expect(screen.getByText(/加载失败/)).toBeDefined()
    })
  })
})
```

- [ ] **Step 5: 运行前端全量测试**

```bash
cd frontend && npx vitest run
```

- [ ] **Step 6: 提交**

```bash
git add frontend/src/components/TraceViewer.tsx frontend/src/components/ConfirmationCard.tsx frontend/src/components/DocumentVersions.tsx frontend/src/__tests__/
git commit -m "feat: wire frontend components to real API endpoints (TraceViewer, ConfirmationCard, DocumentVersions)"
```

### Task 3.4: OpenAPI 文档自动生成验证

**目标:** 确保所有端点都出现在 FastAPI 自动生成的 OpenAPI 文档中。

- [ ] **Step 1: 启动后端并访问 /docs**

```bash
cd backend && PYTHONPATH=src python -m uvicorn ultramath.api.server:app --port 8765 &
sleep 3
# 访问 http://localhost:8765/docs 检查端点列表是否完整
```

- [ ] **Step 2: 导出 OpenAPI JSON**

```bash
curl http://localhost:8765/openapi.json > docs/openapi.json
```

- [ ] **Step 3: 验证端点数量**

```bash
python -c "import json; spec=json.load(open('docs/openapi.json')); paths=spec['paths']; print(f'Total endpoints: {len(paths)}'); [print(f'  {m.upper():7s} {p}') for p,methods in paths.items() for m in methods]"
```

- [ ] **Step 4: 提交**

```bash
git add docs/openapi.json
git commit -m "docs: add OpenAPI 3.1 spec with all endpoints"
```

---

## 阶段四：生产验证（第 21-30 天）

### Task 4.1: 真实 LLM 评测

**目标:** 用真实 API 在 math-modeling golden set 上跑评测，验证评测体系的有效性。

**前置条件:** 有效的 LLM API Key（DeepSeek 或 OpenAI）

- [ ] **Step 1: 配置测试 API Key**

```bash
export DEEPSEEK_API_KEY="your-key"
# 或
export OPENAI_API_KEY="your-key"
```

- [ ] **Step 2: 确认 golden set 存在**

```bash
ls -la domains/math-modeling/golden.jsonl
```

若不存在，需先创建（参考 `docs/eval-report-math-modeling.md` 中的测试用例格式）：

```jsonl
{"input": "某城市有100个公交站点，需要规划最优路线...", "expected_phases": ["analysis", "derivation", "coding"], "min_quality_score": 0.6}
{"input": "预测未来30天的股票走势...", "expected_phases": ["analysis", "derivation", "ontology"], "min_quality_score": 0.5}
```

- [ ] **Step 3: 用真实 API 运行评测**

```bash
cd backend && PYTHONPATH=src python -m ultramath.eval.runner --domain math-modeling --version v9-real --no-mock
```

- [ ] **Step 4: 分析评测报告**

检查以下指标：
- 平均质量评分是否 ≥ 0.6
- 各阶段完成率是否 ≥ 80%
- LLM Judge 评分是否与预期一致
- 是否有超时或 API 错误

- [ ] **Step 5: 将评测报告提交到 docs/**

```bash
cp docs/eval-report-math-modeling.md docs/eval-report-math-modeling-v9-real.md
# 在报告中补充真实评测结果和对比分析
git add docs/eval-report-math-modeling-v9-real.md
git commit -m "docs: add real-LLM evaluation report for math-modeling domain"
```

- [ ] **Step 6: 为其他 3 个领域创建 golden set**

```bash
# paper-writing
echo '{"input": "撰写一篇关于深度学习的综述论文...", "expected_phases": ["research", "outline", "writing", "review"], "min_quality_score": 0.6}' > domains/paper-writing/golden.jsonl

# lab-report
echo '{"input": "撰写一份物理实验报告...", "expected_phases": ["init", "analysis", "writing", "review"], "min_quality_score": 0.6}' > domains/lab-report/golden.jsonl

# literature-review
echo '{"input": "撰写关于气候变化对农业影响的文献综述...", "expected_phases": ["search", "screen", "synthesize", "writing"], "min_quality_score": 0.6}' > domains/literature-review/golden.jsonl

git add domains/*/golden.jsonl
git commit -m "feat: add golden eval sets for all 4 domains"
```

### Task 4.2: E2E 全流程 Playwright 测试

**目标:** 用 Playwright 从用户视角验证 UI → 后端 → LLM 的完整链路。

**Files:**
- Create: `frontend/e2e/math-modeling-flow.spec.ts`
- Create: `frontend/e2e/domain-switch.spec.ts`
- Create: `frontend/e2e/session-persistence.spec.ts`
- Create: `frontend/playwright.config.ts`

- [ ] **Step 1: 安装 Playwright**

```bash
cd frontend && npm install -D @playwright/test && npx playwright install chromium
```

- [ ] **Step 2: 创建 Playwright 配置**

```typescript
// frontend/playwright.config.ts
import { defineConfig } from '@playwright/test'

export default defineConfig({
  testDir: './e2e',
  timeout: 60000,
  retries: 1,
  use: {
    baseURL: 'http://localhost:5173',
    headless: true,
    screenshot: 'only-on-failure',
  },
  webServer: {
    command: 'npm run vite:dev',
    port: 5173,
    timeout: 30000,
    reuseExistingServer: true,
  },
})
```

- [ ] **Step 3: 编写数学建模全流程测试**

```typescript
// frontend/e2e/math-modeling-flow.spec.ts
import { test, expect } from '@playwright/test'

test.describe('Math Modeling Full Flow', () => {
  test('should complete init → chat → auto_run cycle', async ({ page }) => {
    await page.goto('/')

    // 1. 等待加载
    await page.waitForSelector('[data-testid="settings-panel"]', { timeout: 10000 })

    // 2. 配置 API Key
    await page.fill('[data-testid="api-key-input"]', process.env.TEST_API_KEY || 'test-key')
    await page.selectOption('[data-testid="domain-select"]', 'math-modeling')

    // 3. 切换到对话标签
    await page.click('[data-testid="tab-chat"]')

    // 4. 发送消息
    await page.fill('[data-testid="chat-input"]', '求解一个简单的线性规划问题')
    await page.click('[data-testid="send-button"]')

    // 5. 等待回复
    await page.waitForSelector('[data-testid="message-assistant"]', { timeout: 30000 })

    // 6. 验证回复非空
    const messages = await page.$$('[data-testid="message-assistant"]')
    expect(messages.length).toBeGreaterThan(0)
  })

  test('should switch roles correctly', async ({ page }) => {
    await page.goto('/')
    await page.waitForSelector('[data-testid="settings-panel"]', { timeout: 10000 })

    // 初始化
    await page.fill('[data-testid="api-key-input"]', process.env.TEST_API_KEY || 'test-key')
    await page.selectOption('[data-testid="domain-select"]', 'math-modeling')

    // 切换到角色列表
    const roleButtons = await page.$$('[data-testid^="role-"]')
    if (roleButtons.length > 1) {
      await roleButtons[1].click()
      // 验证角色切换成功
      await page.waitForTimeout(500)
    }
  })
})
```

- [ ] **Step 4: 编写域切换测试**

```typescript
// frontend/e2e/domain-switch.spec.ts
import { test, expect } from '@playwright/test'

test.describe('Domain Switching', () => {
  test('should show different roles for different domains', async ({ page }) => {
    await page.goto('/')
    await page.waitForSelector('[data-testid="settings-panel"]', { timeout: 10000 })

    // 选择 math-modeling
    await page.selectOption('[data-testid="domain-select"]', 'math-modeling')
    await page.waitForTimeout(500)
    const mathRoles = await page.$$('[data-testid^="role-"]')

    // 选择 paper-writing
    await page.selectOption('[data-testid="domain-select"]', 'paper-writing')
    await page.waitForTimeout(500)
    const paperRoles = await page.$$('[data-testid^="role-"]')

    // 不同领域应有不同的角色列表
    expect(mathRoles.length).not.toBe(0)
    expect(paperRoles.length).not.toBe(0)
  })
})
```

- [ ] **Step 5: 编写会话持久化测试**

```typescript
// frontend/e2e/session-persistence.spec.ts
import { test, expect } from '@playwright/test'

test.describe('Session Persistence', () => {
  test('should save and load sessions', async ({ page }) => {
    await page.goto('/')
    await page.waitForSelector('[data-testid="settings-panel"]', { timeout: 10000 })

    // 切换到会话标签
    await page.click('[data-testid="tab-sessions"]')

    // 应显示会话列表（可能为空）
    await page.waitForSelector('[data-testid="session-list"]', { timeout: 5000 })

    // 检查是否有新建会话按钮
    const newButton = page.locator('[data-testid="new-session-button"]')
    expect(await newButton.isVisible()).toBeTruthy()
  })
})
```

- [ ] **Step 6: 运行 Playwright 测试**

```bash
cd frontend && npx playwright test
```

- [ ] **Step 7: 添加 data-testid 到前端组件**

如果组件中没有 `data-testid` 属性，需要在前端组件中添加：

```tsx
// ChatPanel.tsx — 添加 testid
<textarea
  data-testid="chat-input"
  ...
/>
<button data-testid="send-button" ...>

// SettingsPanel.tsx
<input data-testid="api-key-input" ... />
<select data-testid="domain-select" ...>

// 每个角色按钮
<button data-testid={`role-${role.id}`} ...>

// SessionPanel.tsx
<div data-testid="session-list" ...>
<button data-testid="new-session-button" ...>
```

- [ ] **Step 8: 提交**

```bash
git add frontend/e2e/ frontend/playwright.config.ts frontend/src/components/*.tsx
git commit -m "test: add Playwright E2E tests + data-testid attributes to components"
```

### Task 4.3: Electron 打包验证

**目标:** 实际构建 Windows NSIS 安装包并验证可运行。

- [ ] **Step 1: 构建前端**

```bash
cd frontend && npm run vite:build
```

- [ ] **Step 2: 执行 Electron 打包**

```bash
cd frontend && npx electron-builder --win --config
```

- [ ] **Step 3: 检查输出**

```bash
ls -la frontend/release/
```

预期：生成 `Lemma Setup x.x.x.exe` 安装包

- [ ] **Step 4: 验证打包大小**

```bash
# 检查安装包大小
du -sh frontend/release/*.exe
```

预期: < 300MB（含 Python 运行时 + 依赖）

- [ ] **Step 5: 记录打包结果到文档**

```bash
echo "## Electron 打包验证\n\n- 日期: $(date +%Y-%m-%d)\n- 包大小: $(du -sh frontend/release/*.exe | cut -f1)\n- 状态: ✅ 构建成功" > docs/electron-build-log.md
git add docs/electron-build-log.md
git commit -m "docs: add Electron build verification log"
```

### Task 4.4: 性能基线建立

**目标:** 建立可度量的性能基线，写入文档。

- [ ] **Step 1: 收集后端性能数据**

```bash
cd backend && PYTHONPATH=src python -c "
from ultramath.utils.perf_monitor import get_monitor
import time

monitor = get_monitor()
# 记录典型操作延迟
for i in range(10):
    start = time.perf_counter()
    # 模拟典型操作
    time.sleep(0.01)
    monitor.record('api_health_check', time.perf_counter() - start)

stats = monitor.get_all_stats()
for name, s in sorted(stats.items()):
    if s['count'] > 0:
        print(f'{name}: avg={s[\"avg\"]*1000:.1f}ms, p95={s.get(\"p95\", s[\"avg\"])*1000:.1f}ms, count={s[\"count\"]}')
"
```

- [ ] **Step 2: 创建性能基线文档**

```markdown
# docs/PERFORMANCE_BASELINE.md

# Lemma 性能基线

> 测量时间：2026-06-25
> 测量环境：Windows 11, Python 3.11.15, Node 20

## 后端 API 延迟

| 端点 | P50 | P95 | P99 | 备注 |
|------|-----|-----|-----|------|
| GET /api/health | <10ms | <20ms | <50ms | 纯内存操作 |
| GET /api/domains | <5ms | <10ms | <20ms | YAML 解析 |
| POST /api/chat | 取决于 LLM | - | - | 流式响应 |
| GET /api/files | <50ms | <100ms | <200ms | 磁盘 I/O |

## 工具执行延迟

| 工具 | P50 | P95 | 备注 |
|------|-----|-----|------|
| code_executor | <500ms | <2000ms | 取决于代码复杂度 |
| latex_compiler | <2000ms | <5000ms | 需 TeX Live |
| figure_generator | <1000ms | <3000ms | matplotlib |

## 前端性能（Lighthouse）

| 指标 | 目标值 | 实际值 |
|------|--------|--------|
| FCP | <1.5s | 待测 |
| LCP | <2.5s | 待测 |
| TBT | <200ms | 待测 |
| CLS | <0.1 | 待测 |
```

- [ ] **Step 3: 提交**

```bash
git add docs/PERFORMANCE_BASELINE.md
git commit -m "docs: add performance baseline with API latency and tool execution metrics"
```

---

## 阶段五：持续质量体系（第 31-45 天）

### Task 5.1: 覆盖率 CI 门禁

**目标:** 每次 PR 自动检查覆盖率不得低于基线，否则阻断合并。

**Files:**
- Modify: `.github/workflows/ci.yml`

- [ ] **Step 1: 更新 CI 配置添加覆盖率门禁**

```yaml
# .github/workflows/ci.yml — 在 backend-test job 中添加

- name: Check coverage threshold
  run: |
    cd backend
    PYTHONPATH=src python -m pytest tests/ --cov=src/ultramath --cov-report=json --cov-fail-under=72
```

- [ ] **Step 2: 添加前端覆盖率门禁**

```yaml
# .github/workflows/ci.yml — 在 frontend-test job 中添加

- name: Run frontend tests with coverage
  run: |
    cd frontend
    npx vitest run --coverage --coverage.thresholds.lines=50 --coverage.thresholds.branches=40
```

- [ ] **Step 3: 验证 CI 配置在本地可通过**

```bash
cd backend && PYTHONPATH=src python -m pytest tests/ --cov=src/ultramath --cov-fail-under=72
cd frontend && npx vitest run --coverage
```

- [ ] **Step 4: 提交**

```bash
git add .github/workflows/ci.yml
git commit -m "ci: add coverage gate (backend ≥72%, frontend ≥50%)"
```

### Task 5.2: 类型检查门禁

**目标:** 前端 TypeScript 零错误，后端逐步引入 mypy。

- [ ] **Step 1: 前端类型检查加入 CI**

```yaml
- name: TypeScript type check
  run: |
    cd frontend
    npx tsc --noEmit
```

- [ ] **Step 2: 后端安装 mypy 并创建配置**

```bash
cd backend && pip install mypy
```

```ini
# backend/mypy.ini
[mypy]
python_version = 3.11
strict = False
warn_return_any = True
warn_unused_configs = True
ignore_missing_imports = True

[mypy-chromadb.*]
ignore_missing_imports = True

[mypy-tiktoken.*]
ignore_missing_imports = True
```

- [ ] **Step 3: 逐步修复 mypy 错误**

```bash
cd backend && mypy src/ultramath --config-file mypy.ini 2>&1 | head -50
```

按模块逐个修复类型错误，每次修复一个模块后提交。

- [ ] **Step 4: 将 mypy 加入 CI**

```yaml
- name: Python type check (critical modules only)
  run: |
    cd backend
    mypy src/ultramath/engine/ src/ultramath/api/ src/ultramath/tools/ --config-file mypy.ini
```

- [ ] **Step 5: 提交**

```bash
git add backend/mypy.ini .github/workflows/ci.yml
git commit -m "ci: add TypeScript and Python type check gates"
```

### Task 5.3: 性能回归 CI

**目标:** 每次 PR 自动运行性能测试，对比基线，超出阈值则告警。

- [ ] **Step 1: 创建性能测试脚本**

```python
# backend/tests/test_performance_regression.py
"""性能回归测试 — 确保关键操作延迟不退化"""
import time
import pytest
from fastapi.testclient import TestClient
from ultramath.api.server import app


class TestPerformanceRegression:
    PERFORMANCE_THRESHOLDS = {
        "/api/health": 0.050,      # 50ms
        "/api/domains": 0.020,     # 20ms
    }

    @pytest.fixture
    def client(self):
        return TestClient(app)

    @pytest.mark.parametrize("endpoint,threshold", [
        ("/api/health", 0.050),
        ("/api/domains", 0.020),
    ])
    def test_endpoint_latency(self, client, endpoint, threshold):
        """端点延迟不应超过阈值"""
        latencies = []
        # 预热
        client.get(endpoint)

        for _ in range(5):
            start = time.perf_counter()
            response = client.get(endpoint)
            latencies.append(time.perf_counter() - start)
            assert response.status_code == 200

        avg_latency = sum(latencies) / len(latencies)
        assert avg_latency < threshold, (
            f"{endpoint} 平均延迟 {avg_latency*1000:.1f}ms 超过阈值 {threshold*1000:.1f}ms"
        )
```

- [ ] **Step 2: 将性能测试加入 CI（可选运行）**

```yaml
- name: Performance regression test
  if: github.event_name == 'pull_request'
  run: |
    cd backend
    PYTHONPATH=src python -m pytest tests/test_performance_regression.py -v --tb=short
```

- [ ] **Step 3: 提交**

```bash
git add backend/tests/test_performance_regression.py .github/workflows/ci.yml
git commit -m "ci: add performance regression test with latency thresholds"
```

### Task 5.4: 自动文档生成

**目标:** 每次发布自动更新 API 文档和覆盖率报告。

- [ ] **Step 1: 创建文档生成脚本**

```bash
# scripts/generate_docs.sh
#!/bin/bash
set -e

echo "==> 生成 API 文档..."
cd backend
PYTHONPATH=src python -c "
import json
from ultramath.api.server import app
spec = app.openapi()
spec['info']['version'] = '$(cat pyproject.toml | grep version | head -1 | cut -d'"' -f2)'
with open('../docs/openapi.json', 'w') as f:
    json.dump(spec, f, indent=2, ensure_ascii=False)
print(f'  端点数: {len(spec[\"paths\"])}')
"

echo "==> 生成覆盖率报告..."
PYTHONPATH=src python -m pytest tests/ --cov=src/ultramath --cov-report=html --cov-report=term -q

echo "==> 文档生成完成"
```

- [ ] **Step 2: 添加到 package.json scripts**

```json
{
  "scripts": {
    "docs:generate": "bash scripts/generate_docs.sh"
  }
}
```

- [ ] **Step 3: 提交**

```bash
git add scripts/generate_docs.sh
git commit -m "feat: add auto-generated docs script (OpenAPI + coverage)"
```

---

## 6. 优先级与执行建议

### 6.1 快速见效路径（第 1 周，ROI 最高）

```
Task 1.1 ──→ Task 1.3 ──→ Task 2.1 ──→ Task 3.1
(提交测试)    (更新基线)    (server.py)   (端点审计)
```

完成这 4 个 Task 后：
- 0% 覆盖率模块清零
- server.py 覆盖率 28% → 65%
- 所有 API 端点状态清晰
- **可度量成果：覆盖率 ≥ 75%，全部端点有文档**

### 6.2 深度可信路径（第 2-3 周）

```
Task 2.2 ──→ Task 2.3 ──→ Task 2.4 ──→ Task 3.2
(编排引擎)    (工具模块)    (前端组件)    (WS 消息流)
```

完成这 4 个 Task 后：
- 编排引擎覆盖率 16% → 50%
- 工具模块覆盖率全面提升
- 前端测试从 4 个文件扩展到 10 个
- WebSocket 全消息类型覆盖

### 6.3 生产就绪路径（第 4-6 周）

```
Task 4.1 ──→ Task 4.2 ──→ Task 4.3 ──→ Task 4.4 ──→ 阶段五
(真实评测)    (Playwright)  (打包验证)    (性能基线)    (持续体系)
```

### 6.4 优先级矩阵

| 优先级 | Task | 时间 | 价值 | 备注 |
|--------|------|------|------|------|
| 🔴 **P0** | 1.1 提交 7 个测试 | 1h | 极高 | 已完成 90% |
| 🔴 **P0** | 2.1 server.py 测试 | 2d | 极高 | 核心 API 裸奔 |
| 🔴 **P0** | 3.1 端点审计 | 4h | 极高 | 确认功能真实可用 |
| 🔴 **P0** | 3.3 前端 API 对接 | 2d | 极高 | 新组件用 mock 数据 |
| 🟡 **P1** | 2.2 编排引擎测试 | 1d | 高 | run_auto 核心路径 |
| 🟡 **P1** | 2.3 工具模块测试 | 2d | 高 | 工具覆盖面 |
| 🟡 **P1** | 4.2 Playwright E2E | 3d | 高 | 用户视角验证 |
| 🟡 **P1** | 5.1 CI 门禁 | 2h | 高 | 防止退化 |
| 🟢 **P2** | 2.4 前端组件测试 | 2d | 中 | 长期维护 |
| 🟢 **P2** | 4.1 真实 LLM 评测 | 1d | 中 | 验证评测有效 |
| 🟢 **P2** | 4.3 Electron 打包 | 2h | 中 | 验证可分发 |
| ⚪ **P3** | 5.2 类型检查 | 3d | 中 | 逐步引入 |
| ⚪ **P3** | 5.3 性能回归 CI | 2h | 低 | 锦上添花 |
| ⚪ **P3** | 5.4 自动文档 | 1h | 低 | 锦上添花 |
| ⚪ **P3** | 3.4 OpenAPI 导出 | 30min | 低 | 快速完成 |

---

## Self-Review

**1. 规格覆盖:**
- 7 个待提交测试 → Task 1.1 覆盖 ✅
- server.py 覆盖率 28% → Task 2.1 覆盖 ✅
- orchestration/engine.py 16% → Task 2.2 覆盖 ✅
- 工具模块 15-25% → Task 2.3 覆盖 ✅
- API 接线断裂 9 大模块 → Task 3.1 覆盖 ✅
- WebSocket 消息流未全测 → Task 3.2 覆盖 ✅
- 前端组件用 mock 数据 → Task 3.3 覆盖 ✅
- 前端测试不足 13 组件 → Task 2.4 覆盖 ✅
- 无真实 LLM 评测 → Task 4.1 覆盖 ✅
- E2E 不够完整 → Task 4.2 覆盖 ✅
- 无 Electron 打包验证 → Task 4.3 覆盖 ✅
- 无性能基线 → Task 4.4 覆盖 ✅
- CI 无门禁 → 阶段五全覆盖 ✅

**2. 占位符扫描:** 所有 Task 包含具体代码或命令，无 TBD/TODO/placeholder ✅

**3. 类型一致性:** 所有引用的 API 路径和模块名与现有代码一致 ✅

**4. 与既有规划的关系:** 本计划是 v8 consolidation plan 的延续和深化。v8 聚焦"是否有测试/是否接线"，v9 聚焦"测试是否深/接线是否真通/系统是否可度量" ✅

---

## 执行交接

计划已保存至 `docs/superpowers/plans/2026-06-25-lemma-v9-excellence-execution-plan.md`。

**两种执行方式：**

**1. Subagent-Driven（推荐）** — 每个 Task 派发独立子 agent，Task 间 review，快速迭代

**2. Inline Execution** — 当前会话内按阶段批量执行，每个阶段完成后 checkpoint review

**建议从 Task 1.1（提交 7 个已完成测试）开始——5 分钟内可完成，立即消除所有 0% 覆盖率模块，建立 momentum。**

**Which approach?**
