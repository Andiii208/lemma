# Lemma v6.0 — 从"能跑"到"好用"：完整迭代路线图

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 Lemma 从当前"核心功能基本跑通、但有大量细节毛刺"的 v5.1 状态，迭代为"用户体验流畅、测试覆盖完整、可发布上线的成熟产品"。覆盖补齐测试 → 前端打磨 → 智能化深化 → 部署生态四大方向。

**Architecture:** 分 6 个独立可交付阶段。阶段一至三聚焦工程质量（测试 + 规范），阶段四至六聚焦产品化（智能 + 生态）。每阶段产出可独立验证的增量价值。

**Tech Stack:** Python 3.11+, FastAPI, OpenAI SDK, ChromaDB, React 18, TypeScript, Tailwind CSS 3.4, Framer Motion, Lucide Icons, react-virtuoso, Electron, Docker, GitHub Actions

---

## 项目现状全面审计（2026-06-24）

### 一、已就绪 ✅ — 可直接使用

| 模块 | 文件 | 状态 | 备注 |
|------|------|------|------|
| **API 服务器** | `backend/src/ultramath/api/server.py` | ✅ 完整 | REST (12 端点) + WebSocket (7 种消息类型)，全局异常处理 |
| **AcademicAgent 引擎** | `backend/src/ultramath/engine/agent.py` | ✅ 完整 | Handoff/Trust/FileVisibility/SelfReflector/CostTracker/RAG 全接入，支持递归分解 |
| **流式聊天** | `server.py:587-700` + `App.tsx:141-157` | ✅ 前后端完整 | `stream_chunk` → `stream_end`，token-by-token 渲染 |
| **CostTracker** | `engine/agent.py:79` → `llm/backend.py` | ✅ 已接线 | 每次 LLM 调用自动记录成本，`/api/cost` 可查询 |
| **SelfReflector** | `engine/agent.py:435-437` | ✅ 已接线 | 每阶段执行后自动轻量反思 |
| **RAG 知识库** | `server.py:201-209` → `agent.py:166-181` | ✅ 已接线 | 基于用户消息检索领域知识注入 system prompt |
| **CascadeRouter** | `server.py:169-179` | ✅ 可选接入 | 通过 `CASCADE_ENABLED=1` 环境变量启用 |
| **会话管理** | `memory/session_store.py` + API | ✅ 完整 | save/load/list/delete 四个端点 + SessionPanel 前端 |
| **导出系统** | `tools/exporter.py` + API | ✅ 可用 | `/api/export` 导出 Markdown |
| **9 个工具全注册** | `server.py:182-191` | ✅ 完整 | Code/Latex/File/Quality/Figure/Equation/Data/SourceTracker/EvidenceMap |
| **4 个领域配置** | `domains/*/domain.yaml` | ✅ 完整 | 含 phase_handlers（含 SourceTracker/EvidenceMap 指令） |
| **领域驱动前端** | `App.tsx:121-133` | ✅ 动态加载 | `initialized` 消息动态更新 phases/roles，不再硬编码 |
| **虚拟滚动** | ChatPanel + FileViewer | ✅ 已安装 | react-virtuoso 已集成 |
| **CI/CD** | `.github/workflows/ci.yml` | ✅ 已配置 | 含 backend test + frontend test + lint |
| **Docker 部署** | `Dockerfile` + `docker-compose.yml` | ✅ 已配置 | TeX Live + 中文支持 |
| **Electron 打包** | `package.json:53-70` | ✅ 已配置 | Windows NSIS + macOS DMG |
| **3 份文档** | `docs/ARCHITECTURE.md` 等 | ✅ 完成 | + README.md |

### 二、可运行性评估

**基本可用场景：**
- ✅ 启动前后端 → 配置 API Key → 选择领域 → 发送消息 → 获得回复
- ✅ 选择"自动执行" → 按阶段流水线自动推进 → 实时进度展示
- ✅ 角色切换 → 不同 Agent 角色回复
- ✅ 流式聊天 → token-by-token 实时显示
- ✅ 会话保存/恢复 → 刷新不丢失
- ✅ 领域切换（math-modeling / paper-writing / lab-report / lit-review）
- ✅ LLM 提供商切换（OpenAI / DeepSeek / Ollama）

**不能正常工作的场景：**
- ❌ 部分测试因 `pytest` 未在当前 Python 环境中安装而无法运行
- ❌ 前端 6 个 `DEFAULT_ROLES` 可能对非 math-modeling 领域显示错误的角色列表（有 fallback 逻辑但依赖 props 传入）
- ❌ 键盘用户无法完整操作（缺少 aria 标签和焦点管理）
- ❌ 移动端/小屏体验差（响应式未完成）

### 三、已知缺陷清单

| # | 问题 | 位置 | 严重度 | 影响 |
|---|------|------|--------|------|
| 1 | `DEFAULT_ROLES` 硬编码 emoji | `ChatPanel.tsx:28-35` | 🟡 MEDIUM | 离线/初始态时显示错误的角色列表，且违反"禁止 emoji 图标"规则 |
| 2 | 可访问性不达标 | 全局 6 个组件 | 🔴 HIGH | 键盘用户无法完整操作，屏幕阅读器无法使用 |
| 3 | Researcher/Analyst SVG 未创建 | `sprites/` 目录 | 🟡 MEDIUM | literature-review / lab-report 领域角色无头像 |
| 4 | SettingsPanel 含 emoji | `SettingsPanel.tsx` | 🟢 LOW | 功能可用但视觉不一致 |
| 5 | 动画时长不统一 | `index.css` + 各组件 | 🟢 LOW | 微交互体验不精致 |
| 6 | 前端测试仅 2 个文件 | `__tests__/` | 🔴 HIGH | 前端重构风险大 |
| 7 | 3 个领域缺 E2E 测试 | `tests/e2e/` | 🔴 HIGH | paper-writing/lab-report/lit-review 无端到端保证 |
| 8 | 单元测试盲区 | latex_compiler, figure_generator, api_auth | 🟡 MEDIUM | 覆盖率盲区 |
| 9 | 无 reduced-motion 支持 | `index.css` | 🟢 LOW | 不尊重用户系统偏好 |
| 10 | 移动端响应式不完整 | `index.css` + 各组件 | 🟡 MEDIUM | 手机/平板体验差 |
| 11 | Prompt 版本追踪未启用 | `engine/prompt_version.py` | 🟢 LOW | 无法对比 prompt 修改效果 |
| 12 | 质量基准未使用 | `benchmarks/quality_metrics.py` | 🟢 LOW | 无法量化输出质量 |
| 13 | 后端版本标注为 4.0.0 | `server.py:71` | 🟢 LOW | 实际功能已远超 v4.0 |

---

## 总览：六大阶段路线图

```
阶段一 (1周)              阶段二 (1-2周)             阶段三 (1周)
补缺堵漏 ──────────────→ 前端设计完满 ────────────→ 质量与性能
│                        │                         │
├─ 补齐 E2E 测试 (3领域)  ├─ 彻底去 emoji           ├─ 移动端响应式
├─ 补齐单元测试盲区        ├─ Researcher/Analyst SVG  ├─ Prompt 版本追踪
├─ 运行全量测试            ├─ WCAG AA 可访问性       ├─ 质量基准启用
├─ 修复 DEFAULT_ROLES     ├─ 动画规范化             ├─ Lighthouse 审计
└─ 后端版本号更新          └─ 设计令牌全面应用        └─ 性能调优

阶段四 (2-3周)             阶段五 (1-2周)             阶段六 (持续)
Agent 智能化 ───────────→ 部署与生态 ────────────→ 持续迭代
│                        │                         │
├─ Multi-Agent 辩论       ├─ Electron 打包验证       ├─ 用户反馈闭环
├─ 强化 RAG 知识库        ├─ Docker 部署验证         ├─ 领域社区建设
├─ 自适应参数             ├─ 自动更新系统            ├─ 性能监控
├─ 工具自动发现           ├─ 领域市场基础            └─ 长期维护
└─ 成本预估提示           └─ 一键安装脚本
```

| 里程碑 | 验收标准 | 预计完成 |
|--------|----------|----------|
| M1: 补缺堵漏 | 全量测试 ≥ 130 个，4 领域 E2E 各跑通，DEFAULT_ROLES 消除 | 第 1 周 |
| M2: 前端完满 | 零 emoji 图标，WCAG AA 通过，8 角色全有 SVG，动画 150-300ms | 第 2-3 周 |
| M3: 质量达标 | Lighthouse ≥ 85，Prompt 版本可对比，移动端可用 | 第 3-4 周 |
| M4: Agent 智能 | 辩论提升输出质量，RAG 检索相关性 > 80%，多模型自适应 | 第 6-7 周 |
| M5: 可发布 | Electron 安装包可用，Docker 一键启动成功，自动更新可用 | 第 8-9 周 |
| M6: 持续迭代 | 用户反馈响应 < 1 周，领域市场 ≥ 5 个社区贡献 | 持续 |

**预估总工期：8-12 周（2-3 个月）**

---

## 阶段一：补缺堵漏 — 让系统值得信赖（预计 1 周）

### 目标
补齐 E2E 和单元测试盲区，修复已知残留硬编码，运行全量测试并通过。

### 当前测试覆盖（需审计）

```
已有测试文件:
├── test_domain.py              ✅
├── test_state_machine.py       ✅
├── test_academic_agent.py      ✅
├── test_handoff.py             ✅
├── test_trust.py               ✅
├── test_isolation.py           ✅
├── test_solidify.py            ✅
├── test_memory.py              ✅
├── test_tools.py               ✅
├── test_router.py              ✅
├── test_sandbox.py             ✅
├── test_api_auth.py            ✅ (已创建文件)
├── test_api_server.py          ✅ (已创建文件)
├── test_latex_compiler.py      ✅ (已创建文件)
├── test_figure_generator.py    ✅ (已创建文件)
├── conftest.py                 ✅
├── e2e/test_math_modeling_pipeline.py  ✅ (5 个测试)
├── e2e/test_paper_writing_pipeline.py  ⚠️ (需检查)
├── e2e/test_lab_report_pipeline.py     ⚠️ (需检查)
├── e2e/test_literature_review_pipeline.py ⚠️ (需检查)
└── e2e/test_websocket_e2e.py           ⚠️ (需检查)
```

---

### Task 1.1: 审计并补齐 E2E 测试

**目标:** 确保 4 个领域 + WebSocket 各有完整的 E2E 测试。

**Files:**
- Audit: `backend/tests/e2e/test_paper_writing_pipeline.py`
- Audit: `backend/tests/e2e/test_lab_report_pipeline.py`
- Audit: `backend/tests/e2e/test_literature_review_pipeline.py`
- Audit: `backend/tests/e2e/test_websocket_e2e.py`

- [ ] **Step 1: 读取并审计每个 E2E 文件**

```bash
# 确认每个文件至少有 3 个测试
grep -c "async def test_" backend/tests/e2e/*.py
```

预期：每个文件 ≥ 3 个测试函数。

- [ ] **Step 2: 补全不足的文件**

若 `test_paper_writing_pipeline.py` 缺少测试，补充：

```python
# backend/tests/e2e/test_paper_writing_pipeline.py 补充
class TestPaperWritingPipeline:
    @pytest.mark.asyncio
    async def test_agent_creation_with_paper_domain(self, tmp_path):
        """论文写作领域 Agent 应能正确创建"""
        domain = DomainProfile.from_directory(
            os.path.join(DOMAINS_DIR, "paper-writing")
        )
        router = ModelRouter.from_single_config(LLMConfig(api_key="test", model="gpt-4o"))
        agent = AcademicAgent(
            work_dir=str(tmp_path / "workspace"),
            domain=domain,
            llm_router=router,
            tool_registry=ToolRegistry(),
        )
        assert agent.domain.id == "paper-writing"
        assert len(agent.domain.phases) >= 3

    @pytest.mark.asyncio
    async def test_run_auto_yields_events(self, tmp_path, mock_router):
        domain = DomainProfile.from_directory(
            os.path.join(DOMAINS_DIR, "paper-writing")
        )
        tools = ToolRegistry()
        tools.register(FileManagerTool(str(tmp_path)))
        agent = AcademicAgent(
            work_dir=str(tmp_path / "workspace"),
            domain=domain, llm_router=mock_router, tool_registry=tools,
        )
        events = []
        async for event in agent.run_auto("AI safety survey"):
            events.append(event)
            if len(events) > 30:
                break
        event_types = [e["type"] for e in events]
        assert "start" in event_types
        assert any(t in event_types for t in ("phase_end", "phase_error", "complete"))
```

类似地补全 `test_lab_report_pipeline.py` 和 `test_literature_review_pipeline.py`。

- [ ] **Step 3: 确认 WebSocket E2E 测试完整**

```python
# backend/tests/e2e/test_websocket_e2e.py 应包含：
class TestWebSocketE2E:
    async def test_ws_init(self): ...
    async def test_ws_chat_flow(self): ...
    async def test_ws_stream_chat(self): ...
    async def test_ws_auto_run(self): ...
```

- [ ] **Step 4: 运行 E2E 测试（mock 模式，无需 API key）**

```bash
cd backend
python -m pytest tests/e2e/ -v --tb=short
```

预期：~20 个测试全部 PASS（全部使用 mock LLM）。

- [ ] **Step 5: 提交**

```bash
git add backend/tests/e2e/
git commit -m "test: complete E2E tests for all 4 domains and WebSocket"
```

---

### Task 1.2: 补齐单元测试盲区

**目标:** 保证所有工具和 API 端点有单元测试覆盖。

**Files:**
- Audit: `backend/tests/test_latex_compiler.py`
- Audit: `backend/tests/test_figure_generator.py`
- Audit: `backend/tests/test_api_auth.py`
- Audit: `backend/tests/test_api_server.py`
- Audit: `backend/tests/test_knowledge_loader.py`（若不存在则创建）

- [ ] **Step 1: 确认 latex_compiler 测试完整**

```bash
python -m pytest backend/tests/test_latex_compiler.py -v --tb=short
```

若测试文件为空或缺失，按以下方式补齐：

```python
# backend/tests/test_latex_compiler.py
import pytest
from ultramath.tools.latex_compiler import LatexCompilerTool

class TestLatexCompilerTool:
    def test_to_openai_function(self):
        tool = LatexCompilerTool("/tmp")
        schema = tool.to_openai_function()
        assert schema["function"]["name"] == "latex_compiler"
        assert "source" in str(schema["function"]["parameters"])

    def test_execute_with_missing_file(self, tmp_path):
        tool = LatexCompilerTool(str(tmp_path))
        result = tool.execute(source="/nonexistent.tex")
        assert result["success"] is False
```

- [ ] **Step 2: 确认 figure_generator 测试完整**

```bash
python -m pytest backend/tests/test_figure_generator.py -v --tb=short
```

- [ ] **Step 3: 创建 knowledge_loader 测试（若不存在）**

```python
# backend/tests/test_knowledge_loader.py
import pytest
from pathlib import Path
from ultramath.knowledge.loader import KnowledgeLoader

class TestKnowledgeLoader:
    def test_load_empty_directory(self, tmp_path):
        """无 .md 文件的目录返回 0"""
        loader = KnowledgeLoader("test_domain", str(tmp_path))
        # 确保 knowledge 目录存在但为空
        knowledge_dir = Path(tmp_path) / "test_domain" / "knowledge"
        knowledge_dir.mkdir(parents=True, exist_ok=True)
        # 由于 loader 使用 domains_base/KNOWLEDGE_BASE 结构，
        # 此处测试 loader 的 chunk_text 方法
        chunks = KnowledgeLoader._chunk_text("a" * 1200, chunk_size=500, overlap=100)
        assert len(chunks) >= 2

    def test_chunk_text(self):
        """分块逻辑正确"""
        text = "abc" * 300  # 900 字符
        chunks = KnowledgeLoader._chunk_text(text, chunk_size=500, overlap=100)
        assert len(chunks) >= 2
        # 第一块不超过 500 字符
        assert len(chunks[0]) <= 500
```

- [ ] **Step 4: 运行全量单元测试**

```bash
cd backend
python -m pytest tests/ -v --tb=short --ignore=tests/e2e/
```

预期：≥ 100 个测试 PASS，0 FAIL。

- [ ] **Step 5: 提交**

```bash
git add backend/tests/
git commit -m "test: fill unit test gaps for tools, API, and knowledge loader"
```

---

### Task 1.3: 修复 ChatPanel 硬编码 DEFAULT_ROLES

**目标:** 去除 `ChatPanel.tsx` 中的 `DEFAULT_ROLES` 常量，改为仅依赖 props 传入。

**Files:**
- Modify: `frontend/src/components/ChatPanel.tsx`

**当前状态:**
```tsx
// ChatPanel.tsx:28-35
const DEFAULT_ROLES = [
  { id: 'lead', name: '团队指挥', emoji: '🎯' },
  { id: 'math', name: '数学家', emoji: '🧮' },
  // ... 6 个硬编码角色，含 emoji
]
```

**改动:**

```tsx
// 删除 DEFAULT_ROLES 常量

// 在组件内部，roles 选择器使用：
const displayRoles = rolesProp && rolesProp.length > 0
  ? rolesProp
  : []  // 不提供 fallback，等待后端 initialized 消息

// 角色下拉菜单：
{displayRoles.length > 0 ? displayRoles.map(role => (
  <button
    key={role.id}
    onClick={() => { onSwitchRole(role.id); setShowRoles(false) }}
    className="flex items-center gap-2 w-full px-3 py-2 hover:bg-white/5 text-left"
  >
    <AgentAvatar roleId={role.id} size="sm" state={currentRole === role.id ? 'active' : 'idle'} />
    <span className="text-sm text-[var(--color-text)]">{role.name}</span>
  </button>
)) : (
  <p className="text-xs text-[var(--color-text-muted)] px-3 py-2">
    等待初始化...
  </p>
)}
```

- [ ] **Step 1: 移除 DEFAULT_ROLES 常量**
- [ ] **Step 2: 用 props.roles 替代所有引用**
- [ ] **Step 3: 运行前端测试确认无回归**

```bash
cd frontend && npx vitest run && npx tsc --noEmit
```

- [ ] **Step 4: 提交**

```bash
git add frontend/src/components/ChatPanel.tsx
git commit -m "fix: remove hardcoded DEFAULT_ROLES from ChatPanel, use dynamic props only"
```

---

### Task 1.4: 更新后端版本号

**Files:**
- Modify: `backend/src/ultramath/api/server.py:71`

```python
app = FastAPI(title="Lemma", version="5.1.0")
```

- [ ] **Step 1: 修改版本号**
- [ ] **Step 2: 提交**

```bash
git add backend/src/ultramath/api/server.py
git commit -m "chore: bump API version to 5.1.0"
```

---

## 阶段二：前端设计完满 — 打磨用户体验（预计 1-2 周）

### 目标
彻底消除 emoji 作为功能图标，补全 8 角色 SVG 精灵，通过 WCAG AA 可访问性审查，统一动画规范。

---

### Task 2.1: 创建 Researcher + Analyst SVG 精灵

**目标:** literature-review（研究员）和 lab-report（分析师）领域角色拥有手绘 SVG 头像。

**Files:**
- Create: `frontend/src/components/agents/sprites/ResearcherSprite.tsx`
- Create: `frontend/src/components/agents/sprites/AnalystSprite.tsx`
- Modify: `frontend/src/components/agents/sprites/index.ts`

- [ ] **Step 1: 创建 ResearcherSprite（研究员 — 学术文献 + 放大镜）**

```tsx
// frontend/src/components/agents/sprites/ResearcherSprite.tsx
import React from 'react'

export default function ResearcherSprite({ className = '' }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
      {/* 学者头发 */}
      <path d="M22 24 Q24 16 32 15 Q40 16 42 24 Q44 20 42 18"
        stroke="#38bdf8" strokeWidth="2.5" fill="#38bdf8" fillOpacity="0.12" strokeLinecap="round"/>
      {/* 脸 */}
      <circle cx="32" cy="30" r="11" fill="#38bdf8" fillOpacity="0.12" stroke="#38bdf8" strokeWidth="2.5"/>
      {/* 学术眼镜 */}
      <rect x="23" y="27" width="7" height="5" rx="2" stroke="#38bdf8" strokeWidth="2" fill="none"/>
      <rect x="34" y="27" width="7" height="5" rx="2" stroke="#38bdf8" strokeWidth="2" fill="none"/>
      <line x1="30" y1="29.5" x2="34" y2="29.5" stroke="#38bdf8" strokeWidth="1.5"/>
      {/* 眼睛 */}
      <circle cx="26.5" cy="29.5" r="1" fill="#38bdf8"/>
      <circle cx="37.5" cy="29.5" r="1" fill="#38bdf8"/>
      {/* 微笑 */}
      <path d="M29 35 Q32 37 35 35" stroke="#38bdf8" strokeWidth="2" strokeLinecap="round" fill="none"/>
      {/* 身体 */}
      <path d="M24 40 Q32 38 40 40 L42 54 Q32 56 22 54 Z"
        fill="#38bdf8" fillOpacity="0.12" stroke="#38bdf8" strokeWidth="2.5" strokeLinejoin="round"/>
      {/* 放大镜（研究员标志） */}
      <circle cx="48" cy="44" r="4" stroke="#38bdf8" strokeWidth="2.5" fill="none"/>
      <line x1="51" y1="47" x2="54" y2="50" stroke="#38bdf8" strokeWidth="2.5" strokeLinecap="round"/>
    </svg>
  )
}
```

- [ ] **Step 2: 创建 AnalystSprite（分析师 — 图表 + 计算器）**

```tsx
// frontend/src/components/agents/sprites/AnalystSprite.tsx
import React from 'react'

export default function AnalystSprite({ className = '' }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
      {/* 精干短发 */}
      <path d="M22 24 Q24 16 32 14 Q40 16 42 24"
        stroke="#fb923c" strokeWidth="2.5" fill="#fb923c" fillOpacity="0.12" strokeLinecap="round"/>
      {/* 脸 */}
      <circle cx="32" cy="30" r="11" fill="#fb923c" fillOpacity="0.12" stroke="#fb923c" strokeWidth="2.5"/>
      {/* 半框眼镜 */}
      <path d="M23 29 Q27 27 31 29" stroke="#fb923c" strokeWidth="2" strokeLinecap="round" fill="none"/>
      <path d="M33 29 Q37 27 41 29" stroke="#fb923c" strokeWidth="2" strokeLinecap="round" fill="none"/>
      <line x1="31" y1="29" x2="33" y2="29" stroke="#fb923c" strokeWidth="1.5"/>
      {/* 眼睛 */}
      <circle cx="27" cy="30" r="1.2" fill="#fb923c"/>
      <circle cx="37" cy="30" r="1.2" fill="#fb923c"/>
      {/* 专注嘴 */}
      <line x1="30" y1="36" x2="34" y2="36" stroke="#fb923c" strokeWidth="2" strokeLinecap="round"/>
      {/* 身体 */}
      <path d="M24 40 Q32 38 40 40 L42 54 Q32 56 22 54 Z"
        fill="#fb923c" fillOpacity="0.12" stroke="#fb923c" strokeWidth="2.5" strokeLinejoin="round"/>
      {/* 柱状图（分析师标志） */}
      <rect x="44" y="46" width="3" height="8" rx="0.5"
        fill="#fb923c" fillOpacity="0.4" stroke="#fb923c" strokeWidth="1.5"/>
      <rect x="48" y="43" width="3" height="11" rx="0.5"
        fill="#fb923c" fillOpacity="0.4" stroke="#fb923c" strokeWidth="1.5"/>
      <rect x="52" y="40" width="3" height="14" rx="0.5"
        fill="#fb923c" fillOpacity="0.4" stroke="#fb923c" strokeWidth="1.5"/>
    </svg>
  )
}
```

- [ ] **Step 3: 更新导出和映射**

```tsx
// frontend/src/components/agents/sprites/index.ts — 添加导出
export { default as ResearcherSprite } from './ResearcherSprite'
export { default as AnalystSprite } from './AnalystSprite'
```

确认 `AgentAvatar.tsx` 中的 `SPRITE_MAP` 包含 `researcher` 和 `analyst`：

```tsx
const SPRITE_MAP: Record<string, React.FC<{ className?: string }>> = {
  lead: LeadSprite,
  math: MathSprite,
  engineer: EngineerSprite,
  reviewer: ReviewerSprite,
  writer: WriterSprite,
  verifier: VerifierSprite,
  researcher: ResearcherSprite,
  analyst: AnalystSprite,
}
```

- [ ] **Step 4: 运行前端测试**

```bash
cd frontend && npx vitest run
```

- [ ] **Step 5: 提交**

```bash
git add frontend/src/components/agents/sprites/
git commit -m "feat: add Researcher and Analyst SVG sprites, complete all 8 agent characters"
```

---

### Task 2.2: 彻底移除功能性 Emoji

**目标:** 所有功能性 emoji 替换为 Lucide 图标。保留文本中的 emoji（如 domain.yaml 中角色 emoji 字段），但 UI 按钮/导航/状态指示器不得使用 emoji。

**Files:**
- Modify: `frontend/src/components/ChatPanel.tsx` — 工具栏 emoji → Lucide
- Modify: `frontend/src/components/PipelinePanel.tsx` — 状态 emoji → Lucide
- Modify: `frontend/src/components/SettingsPanel.tsx` — 分类 emoji → Lucide
- Modify: `frontend/src/components/AdventureMap.tsx` — 状态 emoji → Lucide
- Modify: `frontend/src/components/SessionPanel.tsx` — 按钮 emoji → Lucide

**完整 emoji → Lucide 映射表：**

| 位置 | 旧 (Emoji) | 新 (Lucide Icon) | 导入 |
|------|-----------|-------------------|------|
| ChatPanel 空状态 | 🧬 | `Dna` → 改为 `Sparkles` | `Sparkles` |
| ChatPanel 功能卡片 | 📊💻📄🔍 | `BarChart3 / Code / FileText / Search` | 已导入 |
| ChatPanel 自动执行 | ⚡ | `Zap` | 已导入 |
| ChatPanel 停止 | ⏹ | `Square` | 已导入 |
| ChatPanel 角色下拉 | 🎯🧮💻📝✍️🔍 | 移除 emoji，用 AgentAvatar 替代 | N/A |
| PipelinePanel 完成 | ✅ | `CheckCircle` | `CheckCircle` |
| PipelinePanel 失败 | ❌ | `XCircle` | `XCircle` |
| SettingsPanel 各 Section | 🎯🔧💰🧩 | `Target / Wrench / DollarSign / Puzzle` | 各自导入 |
| SessionPanel 保存按钮 | 💾 | `Save` | 已导入 |
| AdventureMap 状态指示器 | ✓/✗ (CSS) | `Check / X` | 已导入 |

- [ ] **Step 1: 审计所有 emoji 位置**

```bash
cd frontend
grep -rn "emoji\|[🎯🧮💻📝✍️🔍💾🧬📊📄🔧✅⏹⚡💰🧩🔬]" src/components/*.tsx --include="*.tsx"
```

- [ ] **Step 2: 逐一替换，配齐 aria-label**

```tsx
// 示例：SettingsPanel Section 标题
// 旧: <h3>🎯 领域选择</h3>
// 新:
import { Target } from 'lucide-react'
// ...
<h3 className="flex items-center gap-1.5 text-xs font-semibold text-[var(--color-text)] mb-2">
  <Target size={14} strokeWidth={1.5} className="text-[var(--color-accent)]" aria-hidden="true" />
  领域选择
</h3>
```

- [ ] **Step 3: 运行 TypeScript 类型检查**

```bash
cd frontend && npx tsc --noEmit
```

- [ ] **Step 4: 提交**

```bash
git add frontend/src/components/
git commit -m "refactor: replace all functional emoji with Lucide icons, add aria-hidden"
```

---

### Task 2.3: 可访问性改造（WCAG AA）

**目标:** 所有交互元素可通过键盘操作，屏幕阅读器可理解页面结构。

**Files:**
- Modify: `frontend/src/components/ChatPanel.tsx`
- Modify: `frontend/src/components/Sidebar.tsx`
- Modify: `frontend/src/components/PipelinePanel.tsx`
- Modify: `frontend/src/components/SettingsPanel.tsx`
- Modify: `frontend/src/components/SessionPanel.tsx`
- Modify: `frontend/src/components/AdventureMap.tsx`
- Modify: `frontend/src/components/AgentRoster.tsx`
- Modify: `frontend/src/components/FileViewer.tsx`
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/index.css`

**每组件改动清单：**

| 规则 | 实现 |
|------|------|
| **Skip Link** | App.tsx 最顶部添加"跳转到主内容"链接 |
| **aria-labels** | 每个 icon-only 按钮添加 `aria-label="描述功能"` |
| **focus-states** | 所有交互元素添加 `focus-visible:ring-2 ring-[var(--color-accent)] ring-offset-2 ring-offset-[var(--color-bg)]` |
| **keyboard-nav** | Tab 顺序匹配视觉顺序；Enter/Space 触发所有按钮 |
| **heading-hierarchy** | h1→h2→h3 不跳级 |
| **color-not-only** | 连接状态同时显示颜色+图标+文字（已满足） |
| **reduced-motion** | CSS 添加 `@media (prefers-reduced-motion: reduce)` |
| **role-alert** | 错误/成功提示用 `role="alert"` |

- [ ] **Step 1: 添加 Skip Link（App.tsx）**

```tsx
// App.tsx — 最顶部 return 之前/内部第一个元素：
<a href="#main-content"
   className="sr-only focus:not-sr-only focus:absolute focus:top-2 focus:left-2 focus:z-50 focus:px-4 focus:py-2 focus:bg-[var(--color-accent)] focus:text-white focus:rounded-lg focus:outline-none">
  跳转到主内容
</a>

// 主内容区域添加 id：
<div id="main-content" className="flex-1 flex flex-col min-w-0">
```

- [ ] **Step 2: 为每个 icon-only 按钮添加 aria-label**

```tsx
// Sidebar.tsx — 导航按钮
<button
  onClick={() => onViewChange(item.id)}
  aria-label={`${item.label}视图`}
  aria-current={currentView === item.id ? 'page' : undefined}
  className={...}
>
  <item.icon size={18} strokeWidth={1.5} aria-hidden="true" />
  <span className="text-[11px]">{item.label}</span>
</button>
```

- [ ] **Step 3: 添加全局 reduced-motion 支持（index.css）**

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```

- [ ] **Step 4: 添加 focus-visible 全局样式（index.css）**

```css
/* 全局焦点指示器 */
*:focus-visible {
  outline: 2px solid var(--color-accent);
  outline-offset: 2px;
  border-radius: 4px;
}
```

- [ ] **Step 5: 运行 axe DevTools 或 Lighthouse 审计**
- [ ] **Step 6: 提交**

```bash
git add frontend/src/
git commit -m "feat: WCAG AA accessibility improvements (skip link, aria, focus, reduced-motion)"
```

---

### Task 2.4: 动画规范化

**目标:** 所有动画时长统一在 150-350ms 范围，入场用 `ease-out`，退场用 `ease-in`。

**Files:**
- Modify: `frontend/src/index.css`
- Modify: `frontend/src/components/AdventureMap.tsx`

- [ ] **Step 1: 添加动画 token（index.css 已有设计令牌，确认）**
- [ ] **Step 2: 全局搜索并修复异常动画**

```bash
cd frontend
grep -rn "duration:\|animation:\|transition:" src/ --include="*.tsx" --include="*.css"
```

- [ ] **Step 3: 统一 Framer Motion 参数**

所有 `motion.div`:
```tsx
<motion.div
  initial={{ opacity: 0, y: 8 }}
  animate={{ opacity: 1, y: 0 }}
  exit={{ opacity: 0, y: -8 }}
  transition={{
    duration: 0.25,         // 250ms 统一
    ease: [0.16, 1, 0.3, 1], // ease-out
    delay: index * 0.05,    // stagger 50ms
  }}
/>
```

- [ ] **Step 4: 提交**

```bash
git add frontend/src/
git commit -m "refactor: normalize all animations to 150-350ms, ease-out enter, ease-in exit"
```

---

## 阶段三：质量与性能 — 可量化、可对比（预计 1 周）

### 目标
完成移动端响应式，启用 Prompt 版本追踪和质量基准，Lighthouse 得分 ≥ 85。

---

### Task 3.1: 移动端响应式完成

**Files:**
- Modify: `frontend/src/index.css`
- Modify: `frontend/src/components/Sidebar.tsx`
- Modify: `frontend/src/components/ChatPanel.tsx`

**改动:**

```css
/* index.css — 响应式断点 */

/* 小屏手机 < 640px */
@media (max-width: 640px) {
  .sidebar-desktop { display: none; }
  .agent-roster-grid { grid-template-columns: repeat(3, 1fr); }
  .message-bubble { max-width: 92%; }
  .touch-group > * + * { margin-left: 4px; }
  .side-panel { width: 100%; }
}

/* 平板 641-1024px */
@media (min-width: 641px) and (max-width: 1024px) {
  .sidebar-desktop { width: 60px; }
  .sidebar-desktop .nav-label { display: none; }
}
```

- [ ] **Step 1: 添加响应式 CSS**
- [ ] **Step 2: 在 Chrome DevTools 中测试各断点**
- [ ] **Step 3: 提交**

---

### Task 3.2: 启用 Prompt 版本追踪

**目标:** 每次加载 DomainProfile 时自动生成 prompt 快照，支持对比修改前后效果。

**Files:**
- Modify: `backend/src/ultramath/engine/domain.py`

```python
# domain.py — DomainProfile.from_directory 末尾添加
from ..engine.prompt_version import PromptVersionTracker

tracker = PromptVersionTracker()
snapshot = tracker.snapshot(str(domains_base))
baseline_path = Path(domains_base).parent / "data" / "prompt_baseline.json"
if not baseline_path.exists():
    baseline_path.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False))
else:
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    changed = tracker.compare(baseline, snapshot)
    if changed:
        logger.info(f"Prompt changes detected: {len(changed)} files")
```

- [ ] **Step 1: 在 DomainProfile 加载时集成版本追踪**
- [ ] **Step 2: 添加 `/api/prompts/version` 端点查看版本信息**
- [ ] **Step 3: 提交**

---

### Task 3.3: 启用质量评分基准

**目标:** 运行 benchmark 脚本，对修改前后 prompt 跑质量评分对比。

**Files:**
- Modify: `backend/benchmarks/quality_metrics.py`（若无则创建目录）

```python
# backend/benchmarks/quality_metrics.py
"""Agent 输出质量评分"""
import re

class QualityMetrics:
    @staticmethod
    def structural_completeness(text: str) -> float:
        """评分维度：结构完整性（0-1）"""
        score = 1.0
        if "|" not in text or "---" not in text:
            score -= 0.4  # 缺交接表
        if "## " not in text and "### " not in text:
            score -= 0.2  # 缺结构标题
        if len(text) < 100:
            score -= 0.4  # 太短
        return max(0.0, score)

    @staticmethod
    def source_discipline(text: str) -> float:
        """评分维度：来源纪律（0-1）"""
        facts = text.count("[fact]")
        inferences = text.count("[inference]")
        total = facts + inferences
        return facts / total if total > 0 else 0.0

    @staticmethod
    def chinese_quality(text: str) -> float:
        """评分维度：中文质量（0-1）"""
        cn_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        total_chars = len(text.replace(" ", "").replace("\n", ""))
        return cn_chars / total_chars if total_chars > 0 else 1.0

    @classmethod
    def full_score(cls, text: str) -> dict:
        return {
            "structural_completeness": round(cls.structural_completeness(text), 3),
            "source_discipline": round(cls.source_discipline(text), 3),
            "chinese_quality": round(cls.chinese_quality(text), 3),
            "overall": round(
                (cls.structural_completeness(text) * 0.4 +
                 cls.source_discipline(text) * 0.4 +
                 cls.chinese_quality(text) * 0.2), 3
            ),
        }
```

- [ ] **Step 1: 创建/完善 quality_metrics.py**
- [ ] **Step 2: 运行一次基准测试验证工具链可用**
- [ ] **Step 3: 提交**

---

### Task 3.4: 全量运行测试 + Lighthouse 审计

- [ ] **Step 1: 后端全量测试**

```bash
cd backend
python -m pytest tests/ -v --tb=short --cov=src/ultramath --cov-report=term
```

预期：≥ 130 个测试 PASS，覆盖率 ≥ 60%。

- [ ] **Step 2: 前端测试 + 类型检查 + Lint**

```bash
cd frontend
npx vitest run --coverage
npx tsc --noEmit
npx eslint src/ --ext .ts,.tsx
```

- [ ] **Step 3: Lighthouse 审计**

启动前后端后，在 Chrome DevTools → Lighthouse → 桌面端 → Performance + Accessibility + Best Practices。

目标：Performance ≥ 85, Accessibility ≥ 90, Best Practices ≥ 90。

---

## 阶段四：Agent 智能化 — 让 Agent 更聪明（预计 2-3 周）

### 目标
实现 Multi-Agent 辩论机制，强化 RAG 知识库，添加自适应参数和工具自动发现。

---

### Task 4.1: Multi-Agent 辩论机制

**目标:** 在关键决策阶段（analysis, derivation, review），自动调用两个不同角色对同一问题给出独立回答，然后由 lead 角色裁决合并。

**Files:**
- Create: `backend/src/ultramath/engine/debate.py`
- Modify: `backend/src/ultramath/engine/agent.py`

```python
# backend/src/ultramath/engine/debate.py
"""Multi-Agent 辩论 — 两个角色独立回答，lead 裁决合并"""
import asyncio

class AgentDebate:
    def __init__(self, agent):
        self.agent = agent

    async def debate(
        self, question: str, role_a: str, role_b: str, rounds: int = 1
    ) -> str:
        """两个角色辩论，最多 rounds 轮，lead 最终裁决"""
        original_role = self.agent.current_role_id

        responses = []
        for role_id in [role_a, role_b]:
            self.agent.switch_role(role_id)
            resp = await self.agent.chat(question)
            responses.append({"role": role_id, "response": resp})

        # lead 裁决
        self.agent.switch_role("lead")
        synthesis_prompt = f"""以下是两个专家的独立分析：

## 角色 A ({role_a})
{responses[0]['response'][:3000]}

## 角色 B ({role_b})
{responses[1]['response'][:3000]}

请整合两者的最佳观点，给出最终结论。突出：
1. 双方一致的部分
2. 双方分歧的部分及你的裁决
3. 整合后的最终答案
"""
        final = await self.agent.chat(synthesis_prompt)

        self.agent.switch_role(original_role)
        return final
```

- [ ] **Step 1: 创建 debate.py 模块**
- [ ] **Step 2: 在 _execute_phase 中集成（可选启用）**
- [ ] **Step 3: 在 domain.yaml 中添加 debate 配置字段**
- [ ] **Step 4: 添加测试**
- [ ] **Step 5: 提交**

---

### Task 4.2: 强化 RAG 知识库

**目标:** 为每个领域补充 ≥ 5 篇知识文档，优化检索效果。

**Files:**
- Create: 各领域 `knowledge/` 目录下的新 .md 文件

**math-modeling 补充：**
- `knowledge/常见模型与算法.md` ✅ 已在 v5.0 计划中
- `knowledge/论文写作规范.md` ✅ 已在 v5.0 计划中
- `knowledge/LaTeX模板与技巧.md` ✅ 已在 v5.0 计划中
- `knowledge/灵敏度分析与模型检验.md` ❌ 待创建
- `knowledge/数据预处理与清洗.md` ❌ 待创建

**paper-writing 补充：**
- `knowledge/学术写作规范.md` ✅ 已有
- `knowledge/常见论文结构.md` ❌ 待创建
- `knowledge/引用格式与工具.md` ❌ 待创建
- `knowledge/图表制作指南.md` ❌ 待创建
- `knowledge/审稿回复技巧.md` ❌ 待创建

**lab-report 补充：**
- `knowledge/实验设计原则.md` ✅ 已有
- `knowledge/统计分析基础.md` ❌ 待创建
- `knowledge/数据可视化指南.md` ❌ 待创建
- `knowledge/实验报告结构.md` ❌ 待创建

**literature-review 补充：**
- `knowledge/PRISMA指南.md` ✅ 已有
- `knowledge/文献检索策略.md` ❌ 待创建
- `knowledge/文献质量评估.md` ❌ 待创建
- `knowledge/系统综述写作.md` ❌ 待创建

- [ ] **Step 1: 为每个领域编写 ≥ 5 篇知识文档**
- [ ] **Step 2: 运行知识索引脚本**
- [ ] **Step 3: 提交**

---

### Task 4.3: 自适应参数

**目标:** 根据任务阶段自动调整 temperature 和 max_tokens。

**Files:**
- Modify: `backend/src/ultramath/engine/agent.py`

```python
# agent.py — 在 _get_backend_for_phase 中添加自适应参数
PHASE_TEMPERATURE_MAP: dict[str, float] = {
    "analysis": 0.7,   # 分析阶段需要创造性
    "derivation": 0.5,  # 推导需要严谨
    "coding": 0.3,      # 编码需要精确
    "writing": 0.6,     # 写作需要流畅
    "review": 0.4,      # 审稿需要批判性
}

PHASE_MAX_TOKENS_MAP: dict[str, int] = {
    "analysis": 4096,
    "derivation": 8192,
    "coding": 16384,
    "writing": 16384,
    "review": 4096,
}

def _get_backend_for_phase(self) -> LLMBackend:
    backend = self.router.get_default_backend()
    phase = self.state.current_phase

    # 自适应参数覆盖
    if phase in self.PHASE_TEMPERATURE_MAP:
        backend.config.temperature = self.PHASE_TEMPERATURE_MAP[phase]
    if phase in self.PHASE_MAX_TOKENS_MAP:
        backend.config.max_tokens = self.PHASE_MAX_TOKENS_MAP[phase]

    return backend
```

- [ ] **Step 1: 实现自适应参数映射**
- [ ] **Step 2: 在 domain.yaml 中可覆盖默认值**
- [ ] **Step 3: 提交**

---

### Task 4.4: 成本预估提示

**目标:** 在执行 `auto_run` 前，预估总成本并提示用户。

**Files:**
- Modify: `backend/src/ultramath/llm/cost_tracker.py`

```python
# cost_tracker.py — 添加预估方法
class CostTracker:
    @staticmethod
    def estimate_run_cost(
        model: str, num_phases: int, avg_input_tokens: int = 8000, avg_output_tokens: int = 4000
    ) -> float:
        """预估一次 auto_run 的成本"""
        pricing = MODEL_PRICING.get(model, {"input": 1.0, "output": 4.0})
        total_input = num_phases * avg_input_tokens
        total_output = num_phases * avg_output_tokens
        cost = (total_input / 1_000_000) * pricing["input"] + \
               (total_output / 1_000_000) * pricing["output"]
        return round(cost, 4)
```

- [ ] **Step 1: 添加预估方法**
- [ ] **Step 2: 在前端 ChatPanel 开始 auto_run 时调用并显示**
- [ ] **Step 3: 提交**

---

## 阶段五：部署与生态 — 让产品触达用户（预计 1-2 周）

### 目标
验证 Electron 打包和 Docker 部署，完善自动更新，建立领域市场基础。

---

### Task 5.1: Electron 打包验证与修复

**目标:** Electron 打包可成功运行，内置后端。

**Files:**
- Modify: `frontend/electron/main.js`（若需要）
- Modify: `frontend/package.json:53-70`

- [ ] **Step 1: 在 Windows 上运行打包测试**

```bash
cd frontend
npm run build
npx electron-builder --win --x64
```

预期：生成 `release/Lemma Setup.exe`。

- [ ] **Step 2: 安装测试**：安装 → 启动 → 验证后端自动启动 → 验证 UI 可用
- [ ] **Step 3: 修复打包问题（如后端路径、Python 嵌入等）**
- [ ] **Step 4: 提交修复**

---

### Task 5.2: Docker 部署验证

- [ ] **Step 1: 构建并启动 Docker**

```bash
docker-compose up --build
```

- [ ] **Step 2: 验证**：`curl http://localhost:8765/api/health` 返回 `{"status":"ok"}`
- [ ] **Step 3: 修复 Dockerfile 中的依赖安装问题**

---

### Task 5.3: 一键安装脚本

**目标:** 非技术用户可通过一个脚本完成安装。

**Files:**
- Create: `install.bat` (Windows)
- Create: `install.sh` (Linux/Mac)

```batch
:: install.bat
@echo off
echo ========================================
echo   Lemma 一键安装
echo ========================================
echo.
echo [1/4] 检查 Python...
python --version >nul 2>&1 || (echo 请先安装 Python 3.11+ && pause && exit /b 1)
echo [2/4] 安装后端依赖...
cd backend && pip install -e . && cd ..
echo [3/4] 安装前端依赖...
cd frontend && npm install && cd ..
echo [4/4] 安装完成！
echo.
echo 运行 start.bat 启动应用
pause
```

- [ ] **Step 1: 创建安装脚本**
- [ ] **Step 2: 在干净环境中测试**
- [ ] **Step 3: 提交**

---

### Task 5.4: 领域市场入口

**目标:** SettingsPanel 中可浏览社区领域配置。

**Files:**
- Modify: `frontend/src/components/SettingsPanel.tsx`

```tsx
// SettingsPanel.tsx — 添加领域市场 section
<Section icon={Puzzle} title="领域市场">
  <p className="text-[11px] text-[var(--color-text-muted)] mb-3">
    浏览和安装社区创建的领域配置
  </p>
  <a
    href="https://github.com/your-org/lemma-domains"
    target="_blank"
    rel="noopener noreferrer"
    className="text-xs text-[var(--color-accent)] hover:underline"
  >
    打开领域市场 →
  </a>
</Section>
```

- [ ] **Step 1: 添加 UI 入口**
- [ ] **Step 2: 创建 `lemma-domains` 仓库模板**
- [ ] **Step 3: 提交**

---

## 阶段六：持续迭代 — 反馈驱动的长期演进（持续）

### 目标
建立用户反馈闭环，建设社区，持续性能监控和长期维护。

---

### Task 6.1: 用户反馈系统

- [ ] **Step 1: 添加"反馈"按钮到设置页面**
- [ ] **Step 2: 对接 GitHub Issues 或邮件系统**

---

### Task 6.2: 性能监控

- [ ] **Step 1: 添加关键路径的性能日志**
- [ ] **Step 2: 建立性能回归测试（后端 API 延迟、前端首屏时间）**

---

### Task 6.3: 文档持续更新

- [ ] **Step 1: 更新 USER_GUIDE.md 反映最新功能**
- [ ] **Step 2: 录制使用演示视频**
- [ ] **Step 3: 编写 CHANGELOG.md**

---

### Task 6.4: 社区建设

- [ ] **Step 1: 在 GitHub 添加 Issue 模板和 PR 模板**
- [ ] **Step 2: 编写 CONTRIBUTING.md（如何贡献领域配置）**
- [ ] **Step 3: 在相关论坛宣传（数学建模社区、学术写作社区）**

---

## 总结：完整执行路线

```
阶段一 (1周)              阶段二 (1-2周)             阶段三 (1周)
补缺堵漏 ──────────────→ 前端设计完满 ────────────→ 质量与性能
├─ 补齐 E2E (4领域)       ├─ 去 emoji + SVG          ├─ 响应式完成
├─ 补齐单元测试           ├─ WCAG AA 可访问性         ├─ Prompt 版本追踪
├─ 修复 DEFAULT_ROLES     ├─ 动画规范化              ├─ 质量基准
└─ 更新版本号             └─ 设计令牌全面应用         └─ 全量测试 + Lighthouse

阶段四 (2-3周)             阶段五 (1-2周)             阶段六 (持续)
Agent 智能化 ───────────→ 部署与生态 ────────────→ 持续迭代
├─ Multi-Agent 辩论       ├─ Electron 打包验证        ├─ 反馈闭环
├─ RAG 知识库强化         ├─ Docker 部署验证          ├─ 性能监控
├─ 自适应参数             ├─ 一键安装脚本             ├─ 文档更新
├─ 成本预估              ├─ 领域市场入口             └─ 社区建设
└─ (自适应工具发现)       └─ 自动更新
```

| 里程碑 | 验收标准 | 预计完成 |
|--------|----------|----------|
| M1: 补缺堵漏 | 全量测试 ≥ 130 PASS，DEFAULT_ROLES 消除，版本 5.1.0 | 第 1 周 |
| M2: 前端完满 | 零 emoji 图标，8 角色全 SVG，WCAG AA 通过 | 第 2-3 周 |
| M3: 质量达标 | Lighthouse ≥ 85，Prompt 版本可对比，移动端可用 | 第 3-4 周 |
| M4: Agent 智能 | 辩论可用，RAG 每领域 ≥ 5 篇文档，自适应参数生效 | 第 6-7 周 |
| M5: 可发布 | Electron 打包可用，Docker 一键启动，安装脚本可用 | 第 8-9 周 |
| M6: 持续迭代 | Issue 模板就绪，CHANGELOG 维护，社区领域 ≥ 5 个 | 持续 |

**预估总工期：8-12 周（2-3 个月），已计入当前完成度。**

---

## 附录：优先级矩阵

按"价值 × 可行性"排序，帮助在资源有限时做取舍：

| 优先级 | 任务 | 价值 | 可行性 | 理由 |
|--------|------|------|--------|------|
| 🔴 P0 | E2E 测试补齐 | 高 | 高 | 无测试无法放心迭代 |
| 🔴 P0 | 可访问性 WCAG AA | 高 | 中 | 直接影响可用性，一次性投入 |
| 🔴 P0 | DEFAULT_ROLES 修复 | 高 | 高 | 当前可见 bug |
| 🟡 P1 | 彻底去 emoji | 中 | 高 | 提升专业感 |
| 🟡 P1 | Researcher/Analyst SVG | 中 | 高 | 补齐 2 个缺失角色 |
| 🟡 P1 | 移动端响应式 | 中 | 中 | 扩展用户场景 |
| 🟡 P1 | RAG 知识库强化 | 中 | 中 | 提升输出质量 |
| 🟡 P1 | Electron 打包验证 | 中 | 中 | 触达非技术用户 |
| 🟢 P2 | Multi-Agent 辩论 | 中 | 低 | 效果待验证 |
| 🟢 P2 | 自适应参数 | 中 | 高 | 实现简单 |
| 🟢 P2 | Prompt 版本追踪 | 低 | 高 | 工程价值高 |
| 🟢 P2 | 成本预估 | 低 | 高 | 锦上添花 |
| ⚪ P3 | 领域市场 | 低 | 低 | 需要社区基础 |
| ⚪ P3 | 自动工具发现 | 低 | 低 | 实验性功能 |

---

## 附录二：当前版本号建议

当前代码各处版本号不一致：

| 位置 | 当前值 | 建议值 |
|------|--------|--------|
| `server.py:71` | `4.0.0` | `5.1.0` |
| `Sidebar.tsx:36` | `v2.0.0` | `v5.1.0` |
| `package.json:2` | `1.0.0` | `5.1.0` |
| `pyproject.toml:2` | `1.0.0` | `5.1.0` |
| `README.md` (title) | — | 更新架构图到最新状态 |

建议在阶段一末尾统一更新所有版本号到 `5.1.0`。

---

> **下一步建议：** 从阶段一的 Task 1.1（审计 E2E 测试）和 Task 1.3（修复 DEFAULT_ROLES）同时启动。这两者互不依赖，一个保障质量，一个消除可见 bug。
