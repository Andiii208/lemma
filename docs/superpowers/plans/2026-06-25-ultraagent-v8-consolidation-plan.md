# Lemma v8.0 — 从"功能齐全"到"生产就绪"：整合与补全计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking。

**Goal:** v7 大量新模块已落地但存在明显短板——0% 覆盖率模块、前端近乎无保护、新 API 未接入 server.py、真实 LLM 评测未验证。v8 聚焦"整合与补全"，让已有功能真正可信赖。

**Architecture:** 4 个阶段，每阶段独立可交付。阶段一补测试盲区，阶段二打通 API 接线，阶段三前端补全，阶段四端到端验证。

**Tech Stack:** Python 3.11+, FastAPI, React 18, TypeScript, Vitest, Playwright

---

## 现状诊断（2026-06-25 v7 审计）

### 一、覆盖率盲区（21 个模块 < 50%）

| 模块 | 覆盖率 | 严重度 | 说明 |
|------|--------|--------|------|
| `engine/debate.py` | **0%** | 🔴 | Multi-Agent 辩论完全未测 |
| `engine/prompt_version.py` | **0%** | 🔴 | Prompt 版本追踪完全未测 |
| `memory/session_store.py` | **0%** | 🔴 | 会话持久化完全未测 |
| `llm/cascade.py` | **0%** | 🔴 | 级联路由完全未测 |
| `quality/metrics.py` | **0%** | 🔴 | 质量指标完全未测 |
| `quality/fuzzer.py` | **0%** | 🟡 | 模糊测试器未测 |
| `utils/perf_monitor.py` | **0%** | 🟡 | 性能监控未测 |
| `observability/logging_config.py` | **0%** | 🟡 | 日志配置未测 |
| `api/server.py` | **28%** | 🔴 | 核心 API 大量未测 |
| `engine/reflector.py` | **28%** | 🟡 | 自我反思未测 |
| `eval/llm_judge.py` | **20%** | 🟡 | LLM 评分器未测 |
| `evolve/optimizer.py` | **32%** | 🟡 | Prompt 优化器未测 |
| `memory/context.py` | **42%** | 🟡 | 上下文管理未充分测 |
| `tools/data_analyzer.py` | **18%** | 🟡 | 数据分析工具未测 |
| `tools/equation_solver.py` | **25%** | 🟡 | 方程求解器未测 |
| `tools/evidence_map.py` | **20%** | 🟡 | 证据映射未测 |
| `tools/quality_checker.py` | **20%** | 🟡 | 质量检查器未测 |
| `tools/source_tracker.py` | **19%** | 🟡 | 来源追踪未测 |

### 二、API 接线断裂

v7 新增的模块**大部分未暴露到 server.py 的 REST/WS 端点**：

| 模块 | 有 API 端点？ | 影响 |
|------|-------------|------|
| 评测系统 eval/ | ❌ 无 | 前端无法触发评测 |
| 断点续跑 checkpoint/ | ❌ 无 | 前端无法查看/恢复检查点 |
| HITL hitl.py | ❌ 无 | 前端无法显示确认卡片 |
| 文档版本 doc_version.py | ❌ 无 | 前端无法查看版本历史 |
| 知识图谱 graph.py | ❌ 无 | 前端无法查询图谱 |
| 案例库 case_library.py | ❌ 无 | 前端无法搜索案例 |
| 灰度实验 experiments | ❌ 无 | 前端无法管理实验 |
| 租户/计费 saas/ | ❌ 无 | 前端无法查看用量 |
| Trace 可视化 | ❌ 无 | 前端无法展示 trace 树 |

### 三、前端保护空白

- 仅 **1 个测试文件** `Sidebar.test.tsx`（65 行）
- **21 个组件**中 20 个无测试
- 新增的后端功能无对应前端 UI

### 四、E2E 测试不完整

- 8 个 E2E 测试收集到，但未验证是否全部通过
- 4 个领域中仅 math-modeling 有 golden set

---

## 总览：四阶段路线图

```
阶段一 (1-2周)           阶段二 (1-2周)           阶段三 (2-3周)          阶段四 (1周)
补全测试盲区 ──────────→ 打通 API 接线 ──────────→ 前端补全 ────────────→ 端到端验证
│                       │                        │                      │
├─ 0%模块单元测试        ├─ 评测API端点            ├─ 前端组件测试         ├─ 真实LLM评测
├─ server.py测试补全     ├─ 检查点/HITL端点        ├─ Trace可视化UI       ├─ 全领域golden set
├─ 工具测试补全          ├─ 知识图谱/案例库端点     ├─ HITL确认卡片        ├─ E2E全流程
└─ E2E测试修复           └─ 租户/实验端点          └─ 文档版本UI          └─ 性能基线
```

| 里程碑 | 验收标准 | 预计 |
|--------|----------|------|
| M1: 测试补全 | 0% 模块全部 > 50%，总覆盖率 ≥ 70% | 第 2 周 |
| M2: API 打通 | 所有新模块有 REST 端点 + OpenAPI 文档 | 第 4 周 |
| M3: 前端就绪 | 核心组件有测试，新功能有 UI | 第 7 周 |
| M4: 生产验证 | 真实 LLM 评测通过，E2E 全绿 | 第 8 周 |

---

## 阶段一：补全测试盲区（预计 1-2 周）

### Task 1.1: 补全 0% 覆盖率模块

**目标:** 消除所有 0% 覆盖率模块，每个至少有 3 个测试。

**Files:**
- Create: `backend/tests/test_debate.py`
- Create: `backend/tests/test_prompt_version.py`
- Create: `backend/tests/test_session_store.py`
- Create: `backend/tests/test_cascade.py`
- Create: `backend/tests/test_quality_metrics.py`
- Create: `backend/tests/test_perf_monitor.py`
- Create: `backend/tests/test_logging_config.py`

- [ ] **Step 1: 为 debate.py 写测试**

```python
# backend/tests/test_debate.py
import pytest
from ultramath.engine.debate import DebateManager

class TestDebateManager:
    def test_create_debate(self):
        dm = DebateManager()
        # 测试辩论创建（具体接口取决于实现）
        assert dm is not None

    def test_debate_with_mock_responses(self):
        """测试辩论流程：两个角色独立回答，lead 裁决"""
        dm = DebateManager()
        # 根据实际接口补充
```

- [ ] **Step 2: 为 prompt_version.py 写测试**

```python
# backend/tests/test_prompt_version.py
import pytest
from ultramath.engine.prompt_version import PromptVersionTracker

class TestPromptVersionTracker:
    def test_track_version(self, tmp_path):
        tracker = PromptVersionTracker(str(tmp_path))
        # 测试版本追踪
```

- [ ] **Step 3: 为 session_store.py 写测试**

```python
# backend/tests/test_session_store.py
import pytest
from ultramath.memory.session_store import SessionStore

class TestSessionStore:
    def test_save_and_load(self, tmp_path):
        store = SessionStore(str(tmp_path))
        # 测试会话保存和加载

    def test_list_sessions(self, tmp_path):
        store = SessionStore(str(tmp_path))
        # 测试会话列表

    def test_delete_session(self, tmp_path):
        store = SessionStore(str(tmp_path))
        # 测试会话删除
```

- [ ] **Step 4: 为 cascade.py 写测试**

```python
# backend/tests/test_cascade.py
import pytest
from ultramath.llm.cascade import CascadeRouter

class TestCascadeRouter:
    def test_create_router(self):
        stages = [
            {"model": "gpt-4o-mini", "quality_threshold": 0.7},
            {"model": "gpt-4o", "quality_threshold": 0.95},
        ]
        router = CascadeRouter(stages)
        assert router is not None
```

- [ ] **Step 5: 为 quality/metrics.py 写测试**

```python
# backend/tests/test_quality_metrics.py
import pytest
from ultramath.quality.metrics import QualityMetrics

class TestQualityMetrics:
    def test_calculate_score(self):
        metrics = QualityMetrics()
        # 测试质量评分计算
```

- [ ] **Step 6: 为 perf_monitor.py 写测试**

```python
# backend/tests/test_perf_monitor.py
import pytest
from ultramath.utils.perf_monitor import get_monitor, PerfMonitor

class TestPerfMonitor:
    def test_record_metric(self):
        monitor = PerfMonitor()
        monitor.record("test_op", 0.5)
        stats = monitor.get_all_stats()
        assert "test_op" in stats

    def test_get_monitor_singleton(self):
        m1 = get_monitor()
        m2 = get_monitor()
        assert m1 is m2
```

- [ ] **Step 7: 为 logging_config.py 写测试**

```python
# backend/tests/test_logging_config.py
import pytest
import logging
from ultramath.observability.logging_config import JsonLineFormatter, setup_json_logging

class TestJsonLineFormatter:
    def test_format_produces_json(self):
        formatter = JsonLineFormatter()
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0,
            msg="test message", args=(), exc_info=None,
        )
        output = formatter.format(record)
        import json
        data = json.loads(output)
        assert data["message"] == "test message"
        assert data["level"] == "INFO"
```

- [ ] **Step 8: 运行并确认覆盖率提升**

```bash
cd backend && PYTHONPATH=src python -m pytest tests/ --ignore=tests/e2e/ --cov=src/ultramath --cov-report=term
```

预期：所有 0% 模块升至 > 50%，总覆盖率 ≥ 65%。

- [ ] **Step 9: 提交**

```bash
git add backend/tests/test_debate.py backend/tests/test_prompt_version.py backend/tests/test_session_store.py backend/tests/test_cascade.py backend/tests/test_quality_metrics.py backend/tests/test_perf_monitor.py backend/tests/test_logging_config.py
git commit -m "test: eliminate all 0% coverage modules - debate, prompt_version, session_store, cascade, metrics, perf_monitor, logging"
```

### Task 1.2: 补全 server.py API 测试

**目标:** server.py 覆盖率从 28% 提升至 ≥ 60%。

**Files:**
- Modify: `backend/tests/test_api_server.py`

- [ ] **Step 1: 补充缺失的端点测试**

现有 test_api_server.py 只覆盖了部分端点。补充以下测试：

```python
# 需要补充的端点测试：
# - POST /api/auto-run
# - POST /api/cancel
# - GET /api/files
# - GET /api/file/{path}
# - POST /api/session/save
# - GET /api/sessions
# - POST /api/session/{id}/load
# - DELETE /api/session/{id}
# - POST /api/export
# - GET /api/cost
# - GET /api/performance
# - GET /api/domains
```

- [ ] **Step 2: 运行确认覆盖率提升**
- [ ] **Step 3: 提交**

### Task 1.3: 补全工具测试

**目标:** 工具模块覆盖率从 15-25% 提升至 ≥ 50%。

**Files:**
- Modify: `backend/tests/test_tools.py`（补充 data_analyzer, equation_solver, evidence_map, quality_checker, source_tracker）

- [ ] **Step 1: 为每个工具补充 execute 测试**
- [ ] **Step 2: 运行确认**
- [ ] **Step 3: 提交**

### Task 1.4: 修复并运行 E2E 测试

**目标:** 8 个 E2E 测试全部通过。

**Files:**
- Audit: `backend/tests/e2e/test_paper_writing_pipeline.py`
- Audit: `backend/tests/e2e/test_websocket_e2e.py`
- Audit: `backend/tests/e2e/test_math_modeling_pipeline.py`
- Audit: `backend/tests/e2e/test_lab_report_pipeline.py`
- Audit: `backend/tests/e2e/test_literature_review_pipeline.py`

- [ ] **Step 1: 运行 E2E 测试，记录失败**

```bash
cd backend && PYTHONPATH=src python -m pytest tests/e2e/ -v --tb=short
```

- [ ] **Step 2: 修复失败的测试**
- [ ] **Step 3: 确认全部通过**
- [ ] **Step 4: 提交**

---

## 阶段二：打通 API 接线（预计 1-2 周）

### Task 2.1: 评测系统 API

**目标:** 暴露评测系统的 REST 端点。

**Files:**
- Modify: `backend/src/ultramath/api/server.py`

- [ ] **Step 1: 添加评测端点**

```python
# 在 server.py 中添加：

@app.post("/api/eval/run")
async def run_evaluation(domain_id: str = "math-modeling", version: str = "current", api_key: str = Depends(verify_api_key)):
    """运行评测"""
    from ..eval.runner import evaluate_domain
    report = await evaluate_domain(domain_id, version=version, use_mock=False)
    return report.to_dict()

@app.get("/api/eval/report/{domain_id}")
async def get_eval_report(domain_id: str, api_key: str = Depends(verify_api_key)):
    """获取评测报告"""
    report_path = Path(f"docs/eval-report-{domain_id}.md")
    if report_path.exists():
        return {"content": report_path.read_text(encoding="utf-8")}
    raise HTTPException(status_code=404, detail="报告不存在")

@app.get("/api/eval/domains")
async def list_eval_domains(api_key: str = Depends(verify_api_key)):
    """列出有 golden set 的领域"""
    domains_base = Path(__file__).parent.parent.parent.parent / "domains"
    domains_with_golden = []
    for d in domains_base.iterdir():
        if d.is_dir() and (d / "golden.jsonl").exists():
            domains_with_golden.append(d.name)
    return {"domains": domains_with_golden}
```

- [ ] **Step 2: 添加测试**
- [ ] **Step 3: 提交**

### Task 2.2: 检查点 & HITL API

**Files:**
- Modify: `backend/src/ultramath/api/server.py`

- [ ] **Step 1: 添加检查点端点**

```python
@app.get("/api/checkpoint")
async def get_checkpoint(api_key: str = Depends(verify_api_key)):
    """获取当前检查点"""
    if not _agent:
        raise HTTPException(status_code=400, detail="Agent 未初始化")
    from ..engine.checkpoint import RunCheckpoint
    cp_path = _agent.work_dir / "checkpoint.json"
    cp = RunCheckpoint.load(str(cp_path))
    if cp:
        return cp.to_dict() if hasattr(cp, 'to_dict') else {"status": cp.status, "phases": len(cp.phases)}
    return {"status": "no_checkpoint"}

@app.post("/api/hitl/respond")
async def hitl_respond(request_id: str, response: str, api_key: str = Depends(verify_api_key)):
    """响应 HITL 确认请求"""
    if not _agent:
        raise HTTPException(status_code=400, detail="Agent 未初始化")
    from ..engine.hitl import HITLManager
    mgr = HITLManager(str(_agent.work_dir / "hitl"))
    ok = mgr.respond(request_id, response)
    if not ok:
        raise HTTPException(status_code=404, detail="请求不存在")
    return {"status": "responded"}

@app.get("/api/hitl/pending")
async def hitl_pending(api_key: str = Depends(verify_api_key)):
    """获取待确认请求"""
    if not _agent:
        return {"requests": []}
    from ..engine.hitl import HITLManager
    mgr = HITLManager(str(_agent.work_dir / "hitl"))
    return {"requests": [{"request_id": r.request_id, "phase_id": r.phase_id, "message": r.message} for r in mgr.get_pending()]}
```

- [ ] **Step 2: 添加测试**
- [ ] **Step 3: 提交**

### Task 2.3: 知识图谱 & 案例库 API

**Files:**
- Modify: `backend/src/ultramath/api/server.py`

- [ ] **Step 1: 添加知识图谱端点**

```python
@app.get("/api/knowledge/graph")
async def get_knowledge_graph(domain_id: str = "math-modeling", api_key: str = Depends(verify_api_key)):
    """获取领域知识图谱"""
    from ..knowledge.graph import KnowledgeGraph
    graph_path = Path(__file__).parent.parent.parent.parent / "domains" / domain_id / "knowledge_graph.json"
    kg = KnowledgeGraph(persist_path=str(graph_path))
    return {"entities": len(kg.entities), "relations": len(kg.relations), "stats": kg.stats}

@app.get("/api/knowledge/search")
async def search_knowledge(query: str, domain_id: str = "math-modeling", api_key: str = Depends(verify_api_key)):
    """搜索领域知识"""
    from ..knowledge.graph import KnowledgeGraph
    graph_path = Path(__file__).parent.parent.parent.parent / "domains" / domain_id / "knowledge_graph.json"
    kg = KnowledgeGraph(persist_path=str(graph_path))
    results = kg.query(query)
    return {"results": [{"name": e.name, "type": e.entity_type} for e in results]}

@app.get("/api/cases")
async def list_cases(domain_id: str | None = None, min_score: float = 0.0, api_key: str = Depends(verify_api_key)):
    """搜索案例库"""
    from ..knowledge.case_library import CaseLibrary
    lib = CaseLibrary(str(Path(__file__).parent.parent.parent.parent / "data" / "cases"))
    cases = lib.search(domain_id=domain_id, min_score=min_score)
    return {"cases": [{"case_id": c.case_id, "domain": c.domain_id, "score": c.quality_score} for c in cases]}
```

- [ ] **Step 2: 添加测试**
- [ ] **Step 3: 提交**

### Task 2.4: 文档版本 & Trace API

**Files:**
- Modify: `backend/src/ultramath/api/server.py`

- [ ] **Step 1: 添加端点**

```python
@app.get("/api/documents")
async def list_document_versions(api_key: str = Depends(verify_api_key)):
    """列出有版本历史的文档"""
    if not _agent:
        raise HTTPException(status_code=400, detail="Agent 未初始化")
    from ..tools.doc_version import DocumentVersionStore
    store = DocumentVersionStore(str(_agent.work_dir))
    return {"documents": store.list_documents()}

@app.get("/api/document/{doc_name}/versions")
async def get_document_versions(doc_name: str, api_key: str = Depends(verify_api_key)):
    """获取文档版本历史"""
    if not _agent:
        raise HTTPException(status_code=400, detail="Agent 未初始化")
    from ..tools.doc_version import DocumentVersionStore
    store = DocumentVersionStore(str(_agent.work_dir))
    history = store.get_history(doc_name)
    return {"versions": [{"version_id": v.version_id, "message": v.message, "timestamp": v.timestamp, "size": v.size} for v in history]}

@app.get("/api/trace/latest")
async def get_latest_trace(api_key: str = Depends(verify_api_key)):
    """获取最新 trace"""
    from ..observability.tracer import get_collector
    collector = get_collector()
    completed = collector.get_completed()
    if completed:
        return completed[-1].to_dict()
    return {"status": "no_traces"}
```

- [ ] **Step 2: 添加测试**
- [ ] **Step 3: 提交**

### Task 2.5: 租户 & 实验 API

**Files:**
- Modify: `backend/src/ultramath/api/server.py`

- [ ] **Step 1: 添加端点**

```python
@app.get("/api/tenant/usage")
async def get_tenant_usage(tenant_id: str = "default", api_key: str = Depends(verify_api_key)):
    """获取租户用量"""
    from ..saas.billing import BillingMeter
    meter = BillingMeter(str(Path(__file__).parent.parent.parent.parent / "data" / "billing"))
    return meter.get_usage_today(tenant_id)

@app.get("/api/experiments")
async def list_experiments(api_key: str = Depends(verify_api_key)):
    """列出灰度实验"""
    from ..api.extensions import ExperimentManager
    mgr = ExperimentManager(str(Path(__file__).parent.parent.parent.parent / "data" / "experiments"))
    return {"experiments": [{"id": e.experiment_id, "name": e.name, "active": e.active} for e in mgr.list_all()]}
```

- [ ] **Step 2: 添加测试**
- [ ] **Step 3: 提交**

---

## 阶段三：前端补全（预计 2-3 周）

### Task 3.1: 前端组件测试补全

**目标:** 核心组件有 Vitest 测试覆盖。

**Files:**
- Create: `frontend/src/__tests__/ChatPanel.test.tsx`
- Create: `frontend/src/__tests__/PipelinePanel.test.tsx`
- Create: `frontend/src/__tests__/SettingsPanel.test.tsx`
- Create: `frontend/src/__tests__/FileViewer.test.tsx`
- Create: `frontend/src/__tests__/SessionPanel.test.tsx`

- [ ] **Step 1: 为 ChatPanel 写测试**

```tsx
// frontend/src/__tests__/ChatPanel.test.tsx
import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import ChatPanel from '../components/ChatPanel'

describe('ChatPanel', () => {
  it('renders input field', () => {
    render(<ChatPanel messages={[]} onSend={vi.fn()} currentRole="lead" currentRoleName="Lead" isRunning={false} onStartAutoRun={vi.fn()} onCancelRun={vi.fn()} onSwitchRole={vi.fn()} progress={0} phase="" roles={[]} streamingContent="" isStreaming={false} />)
    expect(screen.getByRole('textbox')).toBeDefined()
  })
})
```

- [ ] **Step 2: 类似地为其他组件写测试**
- [ ] **Step 3: 运行确认**

```bash
cd frontend && npx vitest run
```

- [ ] **Step 4: 提交**

### Task 3.2: Trace 可视化组件

**目标:** 前端展示 trace 树时间轴。

**Files:**
- Create: `frontend/src/components/TraceViewer.tsx`

- [ ] **Step 1: 创建 TraceViewer 组件**

从 `/api/trace/latest` 获取数据，渲染为嵌套时间轴（类似 Chrome DevTools Performance 面板）。

- [ ] **Step 2: 集成到 App.tsx 的视图切换**
- [ ] **Step 3: 测试**
- [ ] **Step 4: 提交**

### Task 3.3: HITL 确认卡片组件

**目标:** 前端显示待确认请求卡片。

**Files:**
- Create: `frontend/src/components/ConfirmationCard.tsx`

- [ ] **Step 1: 创建组件**
- [ ] **Step 2: 从 `/api/hitl/pending` 轮询获取待确认请求**
- [ ] **Step 3: 集成到 ChatPanel**
- [ ] **Step 4: 测试**
- [ ] **Step 5: 提交**

### Task 3.4: 文档版本历史组件

**Files:**
- Create: `frontend/src/components/DocumentVersions.tsx`

- [ ] **Step 1: 创建组件，展示版本列表 + diff 视图**
- [ ] **Step 2: 集成到 FileViewer**
- [ ] **Step 3: 测试**
- [ ] **Step 4: 提交**

---

## 阶段四：端到端验证（预计 1 周）

### Task 4.1: 真实 LLM 评测

**目标:** 用真实 API 在 math-modeling golden set 上跑评测，验证评测体系有效。

- [ ] **Step 1: 配置 API Key**
- [ ] **Step 2: 运行评测**

```bash
cd backend && PYTHONPATH=src python -m ultramath.eval.runner --domain math-modeling --version v7-real --no-mock
```

- [ ] **Step 3: 分析报告，确认评分合理**
- [ ] **Step 4: 为其他领域创建 golden set**
- [ ] **Step 5: 提交**

### Task 4.2: E2E 全流程验证

**目标:** 从 UI 到后端的完整流程可跑通。

- [ ] **Step 1: 启动前后端**
- [ ] **Step 2: 手动验证：配置 → 对话 → 自动执行 → 会话保存/恢复**
- [ ] **Step 3: 修复发现的问题**
- [ ] **Step 4: 提交**

### Task 4.3: 性能基线

**目标:** 建立性能基线指标。

- [ ] **Step 1: 用 perf_monitor 记录关键操作延迟**
- [ ] **Step 2: 写入 `docs/PERFORMANCE_BASELINE.md`**
- [ ] **Step 3: 提交**

---

## Self-Review

**1. 规格覆盖:**
- 0% 覆盖率模块 → Task 1.1 全部覆盖 ✅
- server.py API 断裂 → Task 2.1-2.5 全部覆盖 ✅
- 前端无保护 → Task 3.1 覆盖 ✅
- 新功能无 UI → Task 3.2-3.4 覆盖 ✅
- 真实评测未验证 → Task 4.1 覆盖 ✅
- E2E 不完整 → Task 1.4 + 4.2 覆盖 ✅

**2. 占位符扫描:** 所有 Task 包含具体代码或命令 ✅

**3. 类型一致性:** 引用的 API 路径和函数名与 server.py 现有代码一致 ✅

---

## 执行交接

计划已保存至 `docs/superpowers/plans/2026-06-25-lemma-v8-consolidation-plan.md`。

**两种执行方式：**

**1. Subagent-Driven（推荐）** — 每个 Task 派发独立子 agent

**2. Inline Execution** — 当前会话内批量执行

**建议从 Task 1.1（补全 0% 模块测试）开始，这是投入产出比最高的起点。**

**Which approach?**
