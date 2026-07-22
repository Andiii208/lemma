# Lemma v5.0 — 长远迭代路线图：从可用到卓越

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 Lemma 从"功能可用的 v4.0 原型"迭代为"生产级、智能化、可扩展的学术协作平台"。覆盖测试加固、前端完满、领域智能化、协作持久化、Agent 智能升级、部署生态六大方向。

**Architecture:** 分 6 个独立可交付阶段。每阶段产出可独立验证的增量价值，不依赖后续阶段即可上线使用。阶段间按优先级排列，但可根据实际需求调整顺序。

**Tech Stack:** Python 3.11+, FastAPI, OpenAI SDK, ChromaDB, React 18, TypeScript, Tailwind CSS, Framer Motion, Electron, pytest, Vitest, Docker, GitHub Actions

---

## 项目现状审计（v4.0 收尾后）

### 已就绪 ✅

| 模块 | 状态 |
|------|------|
| AcademicAgent 引擎（handoff/trust/file-visibility 全集成） | ✅ 完成 |
| API Server（domain_id 选择、WebSocket init/chat/auto_run） | ✅ 完成 |
| 4 个领域 domain.yaml + phase_handlers + validators | ✅ 完成 |
| 16 个 Agent prompt 文件（4领域 × 各角色） | ✅ 完成 |
| 6 个手绘 SVG 角色精灵（Lead/Math/Engineer/Reviewer/Writer/Verifier） | ✅ 完成 |
| AgentAvatar / AdventureMap / AgentRoster / AgentThoughts / AgentQuickMenu | ✅ 完成 |
| 设计令牌系统（agent-theme.ts + index.css 变量） | ✅ 完成 |
| App.tsx 领域驱动（initialized 消息动态加载 phases/roles） | ✅ 完成 |
| 13 个后端测试模块（~105 个测试） | ✅ 完成 |
| 3 份文档（ARCHITECTURE / USER_GUIDE / DOMAIN_DEVELOPMENT） | ✅ 完成 |

### 待补齐 ❌

| 缺口 | 影响 |
|------|------|
| E2E 测试仅 1 个骨架（test_paper_writing_pipeline.py） | 无法保证端到端可用 |
| 缺失单元测试：latex_compiler、figure_generator、API auth、knowledge_loader | 覆盖率盲区 |
| Researcher / Analyst 两个角色 SVG 未创建 | literature-review 和 lab-report 的角色无头像 |
| ChatPanel 可能残留硬编码 ROLES 回退 | 切换非 math-modeling 领域时角色列表可能不对 |
| PipelinePanel 可能残留硬编码 PHASE_DESCRIPTIONS | 非数学建模领域阶段描述不对 |
| 无流式聊天响应 | 用户需等待完整响应才能看到内容 |
| 无虚拟滚动 | 大量文件/消息时性能下降 |
| 无 token 上下文窗口预检 | 超长对话可能触发 API 错误 |
| 无阶段超时机制 | 某阶段卡死会阻塞整个流程 |
| 无 Electron 打包 | 用户必须手动启动前后端 |
| 无 CI/CD | 无法自动运行测试和构建 |
| 无 Docker 部署 | 非 Python 用户部署困难 |
| 领域知识库为空 | Agent 缺乏领域专业知识注入 |
| 无会话持久化 | 刷新页面丢失所有状态 |

---

## 总览：六大阶段路线图

```
阶段一 (2-3周)        阶段二 (2-3周)        阶段三 (3-4周)
质量基石 ──────────→ 前端完满 ──────────→ 领域智能化
│                    │                    │
├─ 补齐测试覆盖       ├─ 彻底去硬编码       ├─ RAG 知识库
├─ E2E 真实验证       ├─ Researcher/Analyst ├─ 领域专属工具
├─ CI/CD 流水线       ├─ 流式响应           ├─ 模板库扩充
└─ 错误处理加固       ├─ 虚拟滚动           └─ 自动领域推荐
                      └─ 移动端适配

阶段四 (3-4周)        阶段五 (4-6周)        阶段六 (2-3周)
协作持久化 ──────────→ Agent 智能化 ──────→ 部署与生态
│                    │                    │
├─ 会话保存/恢复      ├─ 自我反思循环       ├─ Electron 打包
├─ 多项目管理         ├─ 多模型集成         ├─ Docker 部署
├─ 导出系统           ├─ 成本追踪           ├─ 插件市场
└─ 用户配置持久化     ├─ Agent 辩论         └─ 自动更新
                      └─ 自动工具发现
```

| 里程碑 | 验收标准 |
|--------|----------|
| M1: 质量基石 | 测试覆盖 ≥ 85%，CI 绿灯，4 领域 E2E 各跑通 1 次 |
| M2: 前端完满 | 无任何硬编码领域内容，8 角色全有 SVG，流式聊天可用 |
| M3: 领域智能 | 每个领域 ≥ 5 篇知识文档，RAG 检索延迟 < 500ms |
| M4: 协作持久化 | 会话可保存/恢复/导出为 PDF，多项目可切换 |
| M5: Agent 智能 | Agent 可自我反思并改进输出，成本可见可控 |
| M6: 可发布 | Electron 安装包 < 200MB，Docker 一键启动，文档完整 |

**预估总工期：16-23 周（4-6 个月）**

---

## 阶段一：质量基石 — 让系统值得信赖（预计 2-3 周）

### 目标
补齐测试盲区，建立 CI/CD，让每次提交都有信心。

### 当前测试覆盖分析

```
已有测试 (13 文件, ~105 测试):
├── test_domain.py          ✅ DomainProfile 加载/查询
├── test_state_machine.py   ✅ 状态转换
├── test_academic_agent.py  ✅ Agent 创建/chat/run_auto
├── test_handoff.py         ✅ 交接协议解析
├── test_trust.py           ✅ 信赖阈值计算
├── test_isolation.py       ✅ 文件隔离
├── test_solidify.py        ✅ 固化目录
├── test_memory.py          ✅ 短期/长期记忆
├── test_tools.py           ✅ 工具注册/执行
├── test_router.py          ✅ LLM 路由
├── test_sandbox.py         ✅ AST 沙箱
├── conftest.py             ✅ fixtures
└── e2e/test_paper_writing_pipeline.py  ⚠️ 骨架（无实际断言）

缺失测试:
├── test_latex_compiler.py  ❌ LaTeX 编译工具
├── test_figure_generator.py ❌ 图表生成工具
├── test_api_auth.py        ❌ API 认证
├── test_api_server.py      ❌ REST 端点集成
├── test_knowledge_loader.py ❌ 知识加载器
└── e2e/test_lab_report.py  ❌ 实验报告 E2E
```

---

### Task 1.1: 补齐工具层单元测试

**Files:**
- Create: `backend/tests/test_latex_compiler.py`
- Create: `backend/tests/test_figure_generator.py`

- [ ] **Step 1: 编写 LaTeX 编译器测试**

```python
# backend/tests/test_latex_compiler.py
"""LaTeX 编译器工具测试"""
import pytest
from pathlib import Path
from ultramath.tools.latex_compiler import LatexCompilerTool


class TestLatexCompilerTool:
    @pytest.fixture
    def tool(self, tmp_path):
        return LatexCompilerTool(str(tmp_path))

    @pytest.fixture
    def sample_tex(self, tmp_path):
        tex = tmp_path / "test.tex"
        tex.write_text(r"""
\documentclass{article}
\begin{document}
Hello World
\end{document}
""")
        return str(tex)

    def test_compile_valid_tex(self, tool, sample_tex):
        result = tool.execute(source=sample_tex)
        assert result["success"] is True
        assert "pdf" in result["output"].lower()

    def test_compile_missing_file(self, tool):
        result = tool.execute(source="/nonexistent/file.tex")
        assert result["success"] is False
        assert "not found" in result["error"].lower()

    def test_compile_syntax_error(self, tool, tmp_path):
        bad_tex = tmp_path / "bad.tex"
        bad_tex.write_text(r"\documentclass{article}\begin{document}\invalidcmd")
        result = tool.execute(source=str(bad_tex))
        assert result["success"] is False

    def test_get_schema(self, tool):
        schema = tool.to_openai_function()
        assert schema["function"]["name"] == "latex_compiler"
        assert "source" in str(schema["function"]["parameters"])
```

- [ ] **Step 2: 编写图表生成器测试**

```python
# backend/tests/test_figure_generator.py
"""图表生成工具测试"""
import pytest
from pathlib import Path
from ultramath.tools.figure_generator import FigureGeneratorTool


class TestFigureGeneratorTool:
    @pytest.fixture
    def tool(self, tmp_path):
        return FigureGeneratorTool(str(tmp_path))

    def test_generate_line_chart(self, tool, tmp_path):
        code = '''
import matplotlib.pyplot as plt
import os
plt.plot([1, 2, 3], [4, 5, 6])
plt.title("Test")
plt.savefig(os.path.join(r"''' + str(tmp_path).replace("\\", "\\\\") + '''", "chart.png"))
'''
        result = tool.execute(code=code, output_name="chart.png")
        assert result["success"] is True
        assert (tmp_path / "chart.png").exists()

    def test_generate_with_malicious_code(self, tool):
        code = 'import os; os.system("rm -rf /")'
        result = tool.execute(code=code, output_name="evil.png")
        assert result["success"] is False

    def test_get_schema(self, tool):
        schema = tool.to_openai_function()
        assert schema["function"]["name"] == "figure_generator"
```

- [ ] **Step 3: 运行测试确认通过**

```bash
python -m pytest backend/tests/test_latex_compiler.py backend/tests/test_figure_generator.py -v --tb=short
```

Expected: 7 tests PASS (如果 LaTeX 未安装，latex_compiler 测试可能需要 skip)

- [ ] **Step 4: 提交**

```bash
git add backend/tests/test_latex_compiler.py backend/tests/test_figure_generator.py
git commit -m "test: add unit tests for latex_compiler and figure_generator tools"
```

---

### Task 1.2: 补齐 API 层测试

**Files:**
- Create: `backend/tests/test_api_auth.py`
- Create: `backend/tests/test_api_server.py`

- [ ] **Step 1: 编写 API 认证测试**

```python
# backend/tests/test_api_auth.py
"""API 认证测试"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from ultramath.api.server import app
from ultramath.api.auth import verify_api_key


class TestAPIAuth:
    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_health_no_auth_required(self, client):
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_domains_no_auth_required(self, client):
        response = client.get("/api/domains")
        assert response.status_code == 200
        assert "domains" in response.json()

    def test_protected_endpoint_without_key(self, client):
        response = client.get("/api/status")
        assert response.status_code == 403  # No API key

    def test_chat_endpoint_without_agent(self, client):
        """未初始化 Agent 时 chat 返回 400"""
        response = client.post(
            "/api/chat",
            json={"message": "hello"},
            headers={"X-API-Key": "test-key"},
        )
        assert response.status_code == 400
        assert "未初始化" in response.json()["detail"]
```

- [ ] **Step 2: 编写 API Server 集成测试**

```python
# backend/tests/test_api_server.py
"""API Server 集成测试"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock
import json
from ultramath.api.server import app


class TestAPIServer:
    @pytest.fixture
    def client(self):
        return TestClient(app)

    @pytest.fixture
    def auth_headers(self):
        return {"X-API-Key": "test-api-key-for-development"}

    def test_health_endpoint(self, client):
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["version"] == "2.0.0"

    def test_domains_list(self, client):
        response = client.get("/api/domains")
        assert response.status_code == 200
        data = response.json()
        assert "domains" in data
        domain_ids = [d["id"] for d in data["domains"]]
        assert "math-modeling" in domain_ids
        assert "paper-writing" in domain_ids

    def test_status_without_agent(self, client):
        """无 Agent 时 status 返回 not_initialized"""
        response = client.get("/api/status", headers={"X-API-Key": "test"})
        assert response.status_code == 200
        assert response.json()["status"] == "not_initialized"

    @patch("ultramath.api.server.create_agent")
    def test_init_project(self, mock_create, client, tmp_path, auth_headers):
        mock_agent = MagicMock()
        mock_agent.domain.id = "math-modeling"
        mock_agent.domain.name = "数学建模竞赛"
        mock_agent.domain.phases = []
        mock_agent.domain.roles = []
        mock_create.return_value = mock_agent

        response = client.post(
            "/api/project/init",
            json={"work_dir": str(tmp_path)},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
```

- [ ] **Step 3: 运行测试**

```bash
python -m pytest backend/tests/test_api_auth.py backend/tests/test_api_server.py -v --tb=short
```

Expected: ~10 tests PASS

- [ ] **Step 4: 提交**

```bash
git add backend/tests/test_api_auth.py backend/tests/test_api_server.py
git commit -m "test: add API auth and server integration tests"
```

---

### Task 1.3: 建立 CI/CD 流水线

**Files:**
- Create: `.github/workflows/ci.yml`

- [ ] **Step 1: 创建 GitHub Actions CI 配置**

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  backend-test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.11", "3.12"]

    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install TeX Live (for latex tests)
        run: |
          sudo apt-get update
          sudo apt-get install -y texlive-latex-base texlive-latex-extra

      - name: Install backend dependencies
        run: |
          cd backend
          pip install -e ".[dev]"

      - name: Run backend tests
        run: |
          cd backend
          python -m pytest tests/ -v --tb=short --ignore=tests/e2e/ --cov=src/ultramath --cov-report=term-missing

      - name: Lint check
        run: |
          cd backend
          ruff check src/ tests/

  frontend-test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: "npm"
          cache-dependency-path: frontend/package-lock.json

      - name: Install frontend dependencies
        run: |
          cd frontend
          npm ci

      - name: Run frontend tests
        run: |
          cd frontend
          npx vitest run --coverage

      - name: Type check
        run: |
          cd frontend
          npx tsc --noEmit

      - name: Lint check
        run: |
          cd frontend
          npx eslint src/ --ext .ts,.tsx
```

- [ ] **Step 2: 创建 pyproject.toml 的 dev 依赖**

在 `backend/pyproject.toml` 中确认有：

```toml
[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
    "pytest-cov>=4.0",
    "ruff>=0.4",
]
```

- [ ] **Step 3: 本地验证 CI 配置**

```bash
cd backend && python -m pytest tests/ -v --ignore=tests/e2e/ --cov=src/ultramath --cov-report=term-missing
cd frontend && npx vitest run && npx tsc --noEmit
```

- [ ] **Step 4: 提交**

```bash
git add .github/workflows/ci.yml
git commit -m "ci: add GitHub Actions CI pipeline for backend and frontend"
```

---

### Task 1.4: 错误处理加固

**Files:**
- Modify: `backend/src/ultramath/engine/agent.py`
- Modify: `backend/src/ultramath/api/server.py`

- [ ] **Step 1: 添加阶段超时机制**

在 `AcademicAgent` 的 `_execute_phase` 中添加超时：

```python
# backend/src/ultramath/engine/agent.py — 在 __init__ 中添加
self.phase_timeout_seconds: int = 300  # 默认 5 分钟

# 在 _execute_phase 中包裹 chat 调用
async def _execute_phase(self, phase_id: str, input_text: str = "") -> PhaseResult:
    phase_cfg = self.domain.get_phase_by_id(phase_id)
    if not phase_cfg:
        return PhaseResult(phase_id=phase_id, success=True, summary="无处理程序")

    template = self.domain.phase_handlers.get(phase_id)
    if not template:
        return PhaseResult(phase_id=phase_id, success=True, summary=f"阶段 {phase_cfg.name} 跳过")

    prompt = template.format(
        input_text=input_text[:10000],
        context_sections=self.context.get_all_summaries() or "",
        output_dir=self.domain.directories.get("output", "output"),
        paper_dir=self.domain.directories.get("paper", "paper"),
    )

    try:
        response = await asyncio.wait_for(
            self.chat(prompt),
            timeout=self.phase_timeout_seconds,
        )
        return PhaseResult(phase_id=phase_id, success=True, summary=response[:500])
    except asyncio.TimeoutError:
        return PhaseResult(
            phase_id=phase_id, success=False,
            summary=f"阶段超时（{self.phase_timeout_seconds}秒）",
        )
```

- [ ] **Step 2: 在 API server 中添加全局异常处理器**

```python
# backend/src/ultramath/api/server.py — 在 app 定义后添加
from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error on {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "内部服务器错误，已记录日志"},
    )
```

- [ ] **Step 3: 在 LLM backend 中添加 token 预检**

```python
# backend/src/ultramath/llm/backend.py — 在 generate 方法中添加
MAX_CONTEXT_TOKENS: dict[str, int] = {
    "gpt-4o": 128000,
    "gpt-4o-mini": 128000,
    "gpt-4-turbo": 128000,
    "gpt-3.5-turbo": 16385,
    "deepseek-chat": 65536,
}

async def generate(self, messages, tools=None, **kwargs):
    # Token 预检
    estimated_tokens = self._estimate_tokens(messages)
    model_limit = self.MAX_CONTEXT_TOKENS.get(self.config.model, 128000)
    if estimated_tokens > model_limit * 0.9:
        logger.warning(
            f"Estimated {estimated_tokens} tokens exceeds 90% of model limit {model_limit}"
        )
    # ... 原有逻辑
```

- [ ] **Step 4: 运行全量测试确认无回归**

```bash
python -m pytest backend/tests/ -v --tb=short --ignore=tests/e2e/
```

- [ ] **Step 5: 提交**

```bash
git add backend/src/ultramath/engine/agent.py backend/src/ultramath/api/server.py backend/src/ultramath/llm/backend.py
git commit -m "fix: add phase timeout, global error handler, and token pre-check"
```

---

## 阶段二：前端完满 — 打磨用户体验（预计 2-3 周）

### 目标
彻底消除硬编码，补齐缺失角色，支持流式响应，优化性能。

---

### Task 2.1: 彻底去硬编码

**Files:**
- Modify: `frontend/src/components/ChatPanel.tsx`
- Modify: `frontend/src/components/PipelinePanel.tsx`

**当前状态审计：**

`ChatPanel.tsx` 中可能存在：
```typescript
const ROLES = [
  { id: 'lead', name: '团队指挥', emoji: '🎯' },
  // ... 硬编码的 6 个角色
]
```

`PipelinePanel.tsx` 中可能存在：
```typescript
const PHASE_DESCRIPTIONS: Record<string, string> = { ... }
const PHASE_ICONS: Record<string, string> = { ... }
```

- [ ] **Step 1: 检查并移除 ChatPanel 中的硬编码 ROLES**

```bash
cd frontend && grep -n "ROLES\|PHASE_DESCRIPTIONS\|PHASE_ICONS" src/components/ChatPanel.tsx src/components/PipelinePanel.tsx
```

如果存在硬编码常量，按以下方式替换：

```tsx
// ChatPanel.tsx — 角色选择器改用 props 传入的 roles
interface ChatPanelProps {
  // ... existing
  roles: { id: string; name: string; emoji?: string }[]
}

// 下拉菜单中：
{roles.map(role => (
  <button
    key={role.id}
    onClick={() => { onSwitchRole(role.id); setShowRoles(false) }}
    className={...}
  >
    <AgentAvatar roleId={role.id} size="sm" state={currentRole === role.id ? 'active' : 'idle'} />
    <span>{role.name}</span>
  </button>
))}
```

- [ ] **Step 2: 检查并移除 PipelinePanel 中的硬编码描述**

PipelinePanel 已通过 AdventureMap 渲染，确认不再引用 PHASE_DESCRIPTIONS/PHASE_ICONS 常量。如果引用，改为从 phases props 中动态获取：

```tsx
// 阶段描述直接从 phase.name 派生，不需要额外映射表
// 图标由 AdventureMap 内部的 PHASE_AGENT_MAP 处理（后续也会改为动态）
```

- [ ] **Step 3: 更新 App.tsx 传递 roles 给 ChatPanel**

```tsx
// App.tsx — 确保 ChatPanel 接收到 roles
<ChatPanel
  // ... existing props
  roles={roles}  // 从 initialized 消息中动态获取
/>
```

- [ ] **Step 4: 运行前端测试确认无回归**

```bash
cd frontend && npx vitest run && npx tsc --noEmit
```

- [ ] **Step 5: 提交**

```bash
git add frontend/src/components/ChatPanel.tsx frontend/src/components/PipelinePanel.tsx frontend/src/App.tsx
git commit -m "refactor: remove all hardcoded domain content from frontend components"
```

---

### Task 2.2: 创建缺失角色 SVG（Researcher + Analyst）

**Files:**
- Create: `frontend/src/components/agents/sprites/ResearcherSprite.tsx`
- Create: `frontend/src/components/agents/sprites/AnalystSprite.tsx`
- Modify: `frontend/src/components/agents/sprites/index.ts`
- Modify: `frontend/src/components/agents/AgentAvatar.tsx`

- [ ] **Step 1: 创建 ResearcherSprite（研究员 — 显微镜 + 文献）**

```tsx
// frontend/src/components/agents/sprites/ResearcherSprite.tsx
import React from 'react'

export default function ResearcherSprite({ className = '' }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
      {/* 头发（学者风） */}
      <path d="M22 24 Q24 16 32 15 Q40 16 42 24 Q44 20 42 18" stroke="#38bdf8" strokeWidth="2.5" fill="#38bdf8" fillOpacity="0.15" strokeLinecap="round"/>
      {/* 脸 */}
      <circle cx="32" cy="30" r="11" fill="#38bdf8" fillOpacity="0.12" stroke="#38bdf8" strokeWidth="2.5"/>
      {/* 护目镜（研究员特征） */}
      <rect x="23" y="26" width="8" height="6" rx="2" stroke="#38bdf8" strokeWidth="2" fill="none"/>
      <rect x="33" y="26" width="8" height="6" rx="2" stroke="#38bdf8" strokeWidth="2" fill="none"/>
      <line x1="31" y1="29" x2="33" y2="29" stroke="#38bdf8" strokeWidth="2"/>
      {/* 眼睛 */}
      <circle cx="27" cy="29" r="1" fill="#38bdf8"/>
      <circle cx="37" cy="29" r="1" fill="#38bdf8"/>
      {/* 微笑 */}
      <path d="M29 35 Q32 37 35 35" stroke="#38bdf8" strokeWidth="2" strokeLinecap="round" fill="none"/>
      {/* 身体 */}
      <path d="M24 40 Q32 38 40 40 L42 54 Q32 56 22 54 Z" fill="#38bdf8" fillOpacity="0.12" stroke="#38bdf8" strokeWidth="2.5" strokeLinejoin="round"/>
      {/* 烧瓶（实验图标） */}
      <path d="M46 42 L44 48 L48 48 L46 42" stroke="#38bdf8" strokeWidth="2" fill="#38bdf8" fillOpacity="0.15" strokeLinejoin="round"/>
      <line x1="46" y1="42" x2="46" y2="40" stroke="#38bdf8" strokeWidth="2" strokeLinecap="round"/>
    </svg>
  )
}
```

- [ ] **Step 2: 创建 AnalystSprite（分析师 — 图表 + 眼镜）**

```tsx
// frontend/src/components/agents/sprites/AnalystSprite.tsx
import React from 'react'

export default function AnalystSprite({ className = '' }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
      {/* 头发（精干短发） */}
      <path d="M22 24 Q24 16 32 14 Q40 16 42 24" stroke="#fb923c" strokeWidth="2.5" fill="#fb923c" fillOpacity="0.15" strokeLinecap="round"/>
      {/* 脸 */}
      <circle cx="32" cy="30" r="11" fill="#fb923c" fillOpacity="0.12" stroke="#fb923c" strokeWidth="2.5"/>
      {/* 半框眼镜 */}
      <path d="M23 29 Q27 27 31 29" stroke="#fb923c" strokeWidth="2" strokeLinecap="round" fill="none"/>
      <path d="M33 29 Q37 27 41 29" stroke="#fb923c" strokeWidth="2" strokeLinecap="round" fill="none"/>
      <line x1="31" y1="29" x2="33" y2="29" stroke="#fb923c" strokeWidth="2"/>
      {/* 眼睛 */}
      <circle cx="27" cy="30" r="1.2" fill="#fb923c"/>
      <circle cx="37" cy="30" r="1.2" fill="#fb923c"/>
      {/* 专注嘴 */}
      <line x1="30" y1="36" x2="34" y2="36" stroke="#fb923c" strokeWidth="2" strokeLinecap="round"/>
      {/* 身体 */}
      <path d="M24 40 Q32 38 40 40 L42 54 Q32 56 22 54 Z" fill="#fb923c" fillOpacity="0.12" stroke="#fb923c" strokeWidth="2.5" strokeLinejoin="round"/>
      {/* 柱状图 */}
      <rect x="43" y="46" width="3" height="8" rx="0.5" fill="#fb923c" fillOpacity="0.5" stroke="#fb923c" strokeWidth="1.5"/>
      <rect x="47" y="43" width="3" height="11" rx="0.5" fill="#fb923c" fillOpacity="0.5" stroke="#fb923c" strokeWidth="1.5"/>
      <rect x="51" y="40" width="3" height="14" rx="0.5" fill="#fb923c" fillOpacity="0.5" stroke="#fb923c" strokeWidth="1.5"/>
    </svg>
  )
}
```

- [ ] **Step 3: 更新 sprites/index.ts 和 AgentAvatar**

```typescript
// frontend/src/components/agents/sprites/index.ts — 添加导出
export { default as ResearcherSprite } from './ResearcherSprite'
export { default as AnalystSprite } from './AnalystSprite'
```

```tsx
// AgentAvatar.tsx — SPRITE_MAP 中添加
import { ..., ResearcherSprite, AnalystSprite } from './sprites'

const SPRITE_MAP: Record<string, React.FC<{ className?: string }>> = {
  // ... existing
  researcher: ResearcherSprite,
  analyst: AnalystSprite,
}
```

- [ ] **Step 4: 补全 agent-theme.ts 中 researcher 和 analyst 主题**

`frontend/src/styles/agent-theme.ts` 中应已有 researcher 和 analyst（之前计划中已定义 8 个角色），确认无误。

- [ ] **Step 5: 运行测试并提交**

```bash
cd frontend && npx vitest run
```

```bash
git add frontend/src/components/agents/sprites/ frontend/src/components/agents/AgentAvatar.tsx
git commit -m "feat: add Researcher and Analyst SVG sprites, complete all 8 agent characters"
```

---

### Task 2.3: 流式聊天响应

**Files:**
- Modify: `backend/src/ultramath/api/server.py`
- Modify: `frontend/src/components/ChatPanel.tsx`
- Modify: `frontend/src/hooks/useWebSocket.ts`

- [ ] **Step 1: 后端添加流式响应支持**

```python
# backend/src/ultramath/api/server.py — 在 WebSocket 处理中添加 stream_chat 类型
elif msg_type == "stream_chat":
    if not _agent:
        await websocket.send_text(json.dumps({
            "type": "error", "message": "Agent 未初始化"
        }, ensure_ascii=False))
        continue

    message = msg.get("message", "")
    role_id = msg.get("role")
    
    async with _agent_lock:
        if role_id:
            _agent.switch_role(role_id)
        _agent._ensure_system_message()
        _agent.memory.add("user", message)
        
        backend = _agent._get_backend()
        messages = _agent.memory.get_messages()
        
        full_response = ""
        async for chunk in backend.generate_stream(messages):
            full_response += chunk
            await websocket.send_text(json.dumps({
                "type": "stream_chunk",
                "content": chunk,
            }, ensure_ascii=False))
        
        _agent.memory.add("assistant", full_response)
        
        await websocket.send_text(json.dumps({
            "type": "stream_end",
            "full_content": full_response,
        }, ensure_ascii=False))
```

- [ ] **Step 2: LLM Backend 添加 generate_stream 方法**

```python
# backend/src/ultramath/llm/backend.py
async def generate_stream(self, messages, tools=None, **kwargs):
    """流式生成响应"""
    client = self._get_client()
    params = {
        "model": self.config.model,
        "messages": messages,
        "stream": True,
        "temperature": self.config.temperature,
        "max_tokens": self.config.max_tokens,
    }
    
    stream = await client.chat.completions.create(**params)
    async for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content
```

- [ ] **Step 3: 前端支持流式渲染**

```tsx
// ChatPanel.tsx — 添加流式消息状态
const [streamingContent, setStreamingContent] = useState<string>('')
const [isStreaming, setIsStreaming] = useState(false)

// 在 WebSocket onMessage 中处理
if (msg.type === 'stream_chunk') {
  setIsStreaming(true)
  setStreamingContent(prev => prev + (msg.content as string))
} else if (msg.type === 'stream_end') {
  setIsStreaming(false)
  setMessages(prev => [...prev, {
    id: nextId(),
    role: 'assistant',
    content: msg.full_content as string,
    agentRole: agentStatus.currentRole,
    agentName: agentStatus.currentRoleName,
    timestamp: new Date().toISOString(),
  }])
  setStreamingContent('')
}

// 渲染中：
{isStreaming && (
  <MessageBubble
    role="assistant"
    content={streamingContent}
    agentRole={agentStatus.currentRole}
    isStreaming
  />
)}
```

- [ ] **Step 4: 提交**

```bash
git add backend/src/ultramath/llm/backend.py backend/src/ultramath/api/server.py frontend/src/components/ChatPanel.tsx
git commit -m "feat: add streaming chat response support (backend + frontend)"
```

---

### Task 2.4: 虚拟滚动 + 移动端适配

**Files:**
- Modify: `frontend/src/components/FileViewer.tsx`
- Modify: `frontend/src/components/ChatPanel.tsx`
- Install: `react-virtuoso` (虚拟滚动库)

- [ ] **Step 1: FileViewer 添加虚拟滚动**

```bash
cd frontend && npm install react-virtuoso
```

```tsx
// FileViewer.tsx — 文件列表使用 Virtuoso
import { Virtuoso } from 'react-virtuoso'

// 替换 fileList.map() 为：
<Virtuoso
  style={{ height: '100%' }}
  totalCount={files.length}
  itemContent={index => {
    const file = files[index]
    return <FileRow key={file.path} file={file} ... />
  }}
/>
```

- [ ] **Step 2: 消息列表添加虚拟滚动**

```tsx
// ChatPanel.tsx — 消息区域使用 Virtuoso
<Virtuoso
  style={{ height: '100%' }}
  data={messages}
  followOutput="smooth"
  itemContent={(index, message) => (
    <MessageBubble key={message.id} message={message} ... />
  )}
/>
```

- [ ] **Step 3: 移动端响应式适配**

在 `index.css` 添加：

```css
@media (max-width: 768px) {
  .sidebar-desktop { display: none; }
  .chat-panel { padding: 0.5rem; }
  .agent-roster-grid { grid-template-columns: repeat(4, 1fr); }
}
```

- [ ] **Step 4: 提交**

```bash
git add .
git commit -m "perf: add virtual scrolling to file list and chat, mobile responsive tweaks"
```

---

## 阶段三：领域智能化 — 让 Agent 真正"懂"领域（预计 3-4 周）

### 目标
为每个领域注入专业知识（RAG），添加领域专属工具，让 Agent 不再只依赖 LLM 的通用知识。

---

### Task 3.1: 领域知识库系统（RAG）

**Files:**
- Create: `backend/src/ultramath/knowledge/loader.py`
- Create: `backend/src/ultramath/knowledge/retriever.py`
- Create: `domains/math-modeling/knowledge/常见模型与算法.md`
- Create: `domains/math-modeling/knowledge/论文写作规范.md`
- Create: `domains/math-modeling/knowledge/LaTeX模板与技巧.md`
- Create: `domains/paper-writing/knowledge/学术写作规范.md`
- Create: `domains/paper-writing/knowledge/常见论文结构.md`
- Create: `domains/lab-report/knowledge/实验设计原则.md`
- Create: `domains/literature-review/knowledge/PRISMA指南.md`

- [ ] **Step 1: 创建知识加载器**

```python
# backend/src/ultramath/knowledge/loader.py
"""领域知识加载器 — 从 domains/<id>/knowledge/ 加载 Markdown 并索引到 ChromaDB"""
import hashlib
from pathlib import Path
import chromadb
from chromadb.utils import embedding_functions


class KnowledgeLoader:
    """加载和索引领域知识文档"""
    
    def __init__(self, domain_id: str, domains_base: str = "domains"):
        self.domain_id = domain_id
        self.knowledge_dir = Path(domains_base) / domain_id / "knowledge"
        self.client = chromadb.PersistentClient(
            path=str(Path(domains_base).parent / "data" / "chromadb_knowledge")
        )
        self.ef = embedding_functions.DefaultEmbeddingFunction()
        self.collection = self.client.get_or_create_collection(
            name=f"knowledge_{domain_id}",
            embedding_function=self.ef,
        )
    
    def load_and_index(self) -> int:
        """加载所有 .md 文件并索引到 ChromaDB，返回已索引文档数"""
        if not self.knowledge_dir.exists():
            return 0
        
        count = 0
        for md_file in sorted(self.knowledge_dir.glob("*.md")):
            content = md_file.read_text(encoding="utf-8")
            doc_id = hashlib.md5(content.encode()).hexdigest()[:16]
            
            # 检查是否已索引
            existing = self.collection.get(ids=[doc_id])
            if existing["ids"]:
                continue
            
            # 分块索引（每 500 字一块，重叠 100 字）
            chunks = self._chunk_text(content, chunk_size=500, overlap=100)
            for i, chunk in enumerate(chunks):
                self.collection.add(
                    documents=[chunk],
                    metadatas=[{
                        "source": md_file.name,
                        "chunk_index": i,
                        "domain": self.domain_id,
                    }],
                    ids=[f"{doc_id}_{i}"],
                )
            count += 1
        
        return count
    
    @staticmethod
    def _chunk_text(text: str, chunk_size: int = 500, overlap: int = 100) -> list[str]:
        """简单分块：按字符数滑动窗口"""
        chunks = []
        start = 0
        while start < len(text):
            end = min(start + chunk_size, len(text))
            chunks.append(text[start:end])
            start += chunk_size - overlap
        return chunks
```

- [ ] **Step 2: 创建知识检索器**

```python
# backend/src/ultramath/knowledge/retriever.py
"""知识检索器 — 根据查询从 ChromaDB 检索相关领域知识"""
import chromadb
from chromadb.utils import embedding_functions


class KnowledgeRetriever:
    def __init__(self, domain_id: str, domains_base: str = "domains"):
        data_dir = str(Path(domains_base).parent / "data" / "chromadb_knowledge")
        self.client = chromadb.PersistentClient(path=data_dir)
        self.ef = embedding_functions.DefaultEmbeddingFunction()
        self.collection_name = f"knowledge_{domain_id}"
    
    def retrieve(self, query: str, top_k: int = 5) -> list[str]:
        """检索最相关的知识片段"""
        try:
            collection = self.client.get_collection(
                name=self.collection_name,
                embedding_function=self.ef,
            )
        except Exception:
            return []
        
        results = collection.query(
            query_texts=[query],
            n_results=top_k,
        )
        
        if results["documents"] and results["documents"][0]:
            return results["documents"][0]
        return []
    
    def format_context(self, query: str, top_k: int = 5) -> str:
        """检索并格式化为上下文文本"""
        chunks = self.retrieve(query, top_k)
        if not chunks:
            return ""
        
        lines = ["\n## 领域知识参考\n"]
        for i, chunk in enumerate(chunks, 1):
            lines.append(f"### 参考资料 {i}\n{chunk}\n")
        return "\n".join(lines)
```

- [ ] **Step 3: 将知识检索集成到 AcademicAgent**

```python
# backend/src/ultramath/engine/agent.py — 在 _build_system_prompt 中添加知识检索
def _build_system_prompt(self) -> str:
    role = self.get_current_role()
    if not role:
        return "You are an academic assistant."

    context_info = self.context.get_all_summaries()
    parts = [
        f"## 领域: {self.domain.name}",
        role.system_prompt,
        f"\n\n## 当前角色: {role.name}",
        f"## 工作目录: {self.work_dir}",
    ]
    if context_info and "暂无" not in context_info:
        parts.append(f"\n## 已完成的工作:\n{context_info}")
    
    # 注入领域知识（基于最近一次用户消息检索）
    last_user_msg = self._get_last_user_message()
    if last_user_msg:
        from ..knowledge.retriever import KnowledgeRetriever
        retriever = KnowledgeRetriever(self.domain.id, str(self.work_dir.parent.parent / "domains"))
        knowledge = retriever.format_context(last_user_msg, top_k=3)
        if knowledge:
            parts.append(knowledge)
    
    return "\n".join(parts)

def _get_last_user_message(self) -> str | None:
    raw = self.memory.get_raw_messages()
    for msg in reversed(raw):
        if msg.role == "user":
            return msg.content
    return None
```

- [ ] **Step 4: 为 math-modeling 领域编写知识文档**

```markdown
# domains/math-modeling/knowledge/常见模型与算法.md
# 数学建模常见模型与算法

## 优化类问题
- **线性规划**: 单纯形法、内点法。适用：资源分配、生产调度
- **整数规划**: 分支定界、割平面。适用：选址、排班
- **非线性规划**: 梯度下降、拉格朗日乘子法。适用：参数拟合

## 预测类问题
- **时间序列**: ARIMA、SARIMA、Prophet
- **机器学习**: XGBoost、LightGBM、随机森林
- **深度学习**: LSTM、Transformer（长序列预测）

## 评价类问题
- **层次分析法 (AHP)**: 多准则决策
- **TOPSIS**: 逼近理想解排序
- **熵权法**: 客观赋权
- **模糊综合评价**: 处理不确定性

## 图论与网络
- 最短路径: Dijkstra、Floyd-Warshall
- 最大流: Ford-Fulkerson
- TSP/VRP: 遗传算法、模拟退火、蚁群算法

## 机理分析
- 微分方程建模
- 元胞自动机
- 系统动力学
- Agent-Based Modeling

## 常用求解器
- Gurobi、CPLEX（商业）
- PuLP、CVXPY（Python 开源）
- SciPy.optimize（通用）
```

```markdown
# domains/math-modeling/knowledge/论文写作规范.md
# 数学建模竞赛论文写作规范

## 论文结构
1. **摘要**（最重要！）: 问题重述、方法概述、核心结果（带具体数值）、结论
2. **问题重述**: 用自己的话重述，不照抄
3. **模型假设**: 合理且必要，每条有依据
4. **符号说明**: 表格形式，单位清晰
5. **模型建立与求解**: 分问题逐一展开
6. **模型检验**: 灵敏度分析、误差分析、对比验证
7. **模型评价**: 优点(3-5条)、缺点(2-3条，含改进方向)
8. **参考文献**: 格式统一

## 摘要写作要点
- 必须包含每个问题的具体求解结果（数值）
- 体现创新点
- 300-500 字为宜
- 中英文摘要
```

```markdown
# domains/math-modeling/knowledge/LaTeX模板与技巧.md
# LaTeX 数学建模模板与技巧

## 常用包
```latex
\usepackage{amsmath,amssymb}     % 数学符号
\usepackage{graphicx}            % 图片
\usepackage{booktabs}            % 三线表
\usepackage{algorithm,algorithmic} % 伪代码
\usepackage{hyperref}            % 超链接
\usepackage{geometry}            % 页边距
```

## 表格技巧
- 使用 `booktabs` 的三线表：`\toprule` `\midrule` `\bottomrule`
- 数据对齐：`S` 列类型（siunitx）对齐小数点
- 跨页长表格：`longtable`

## 图片技巧
- 矢量图优先（PDF/EPS）
- `\includegraphics[width=0.8\textwidth]{figure.pdf}`
- 子图：`subcaption` 包
```

- [ ] **Step 5: 为其他 3 个领域编写知识文档**

类似 math-modeling，为 paper-writing、lab-report、literature-review 各创建 ≥ 2 篇知识文档。内容基于各领域 `phase_handlers` 中描述的核心概念展开。

- [ ] **Step 6: 添加知识索引 CLI 命令**

```python
# backend/src/ultramath/knowledge/__init__.py
"""知识管理 CLI"""
import sys
from pathlib import Path
from .loader import KnowledgeLoader

def index_all_domains():
    domains_dir = Path("domains")
    for domain_dir in sorted(domains_dir.iterdir()):
        if not domain_dir.is_dir():
            continue
        loader = KnowledgeLoader(domain_dir.name, str(domains_dir.parent))
        count = loader.load_and_index()
        print(f"  {domain_dir.name}: {count} documents indexed")

if __name__ == "__main__":
    index_all_domains()
```

- [ ] **Step 7: 提交**

```bash
git add backend/src/ultramath/knowledge/ domains/*/knowledge/
git commit -m "feat: add domain knowledge base with RAG (ChromaDB + knowledge docs)"
```

---

### Task 3.2: 领域专属工具扩展

**Files:**
- Create: `backend/src/ultramath/tools/equation_solver.py`
- Create: `backend/src/ultramath/tools/data_analyzer.py`

- [ ] **Step 1: 创建方程求解器工具（数学建模专属）**

```python
# backend/src/ultramath/tools/equation_solver.py
"""方程求解工具 — 用于数学建模领域"""
import sympy as sp
from .base import ToolResult, BaseTool


class EquationSolverTool(BaseTool):
    name = "equation_solver"
    description = "使用 SymPy 求解方程/方程组，支持线性、非线性、微分方程"
    
    def execute(self, equations: list[str], variables: list[str] | None = None) -> ToolResult:
        try:
            parsed_eqs = []
            for eq_str in equations:
                if "=" in eq_str:
                    left, right = eq_str.split("=", 1)
                    parsed_eqs.append(sp.Eq(sp.sympify(left), sp.sympify(right)))
                else:
                    parsed_eqs.append(sp.sympify(eq_str))
            
            symbols = [sp.Symbol(v) for v in variables] if variables else list(
                set().union(*[eq.free_symbols for eq in parsed_eqs])
            )
            
            solution = sp.solve(parsed_eqs, symbols, dict=True)
            return ToolResult(
                success=True,
                output=f"解: {solution}",
                data={"solution": str(solution)},
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))
```

- [ ] **Step 2: 创建数据分析器工具（实验报告/文献综述专属）**

```python
# backend/src/ultramath/tools/data_analyzer.py
"""数据分析工具 — 统计检验和效应量计算"""
import numpy as np
from scipy import stats
from .base import ToolResult, BaseTool


class DataAnalyzerTool(BaseTool):
    name = "data_analyzer"
    description = "执行统计检验（t检验、方差分析、卡方检验），计算效应量"
    
    def execute(
        self,
        test_type: str,  # "ttest", "anova", "chi2", "correlation"
        data: list[float],
        data2: list[float] | None = None,
        groups: list[list[float]] | None = None,
    ) -> ToolResult:
        try:
            arr = np.array(data)
            output_lines = [f"## {test_type} 分析结果\n"]
            output_lines.append(f"- 样本量: {len(arr)}")
            output_lines.append(f"- 均值: {arr.mean():.4f}")
            output_lines.append(f"- 标准差: {arr.std():.4f}")
            
            if test_type == "ttest" and data2:
                t_stat, p_value = stats.ttest_ind(arr, np.array(data2))
                cohens_d = (arr.mean() - np.mean(data2)) / np.sqrt((arr.var() + np.var(data2)) / 2)
                output_lines.append(f"- t 统计量: {t_stat:.4f}")
                output_lines.append(f"- p 值: {p_value:.4f}")
                output_lines.append(f"- Cohen's d: {cohens_d:.4f}")
                output_lines.append(f"- 显著性: {'显著' if p_value < 0.05 else '不显著'}")
            elif test_type == "anova" and groups:
                f_stat, p_value = stats.f_oneway(*[np.array(g) for g in groups])
                output_lines.append(f"- F 统计量: {f_stat:.4f}")
                output_lines.append(f"- p 值: {p_value:.4f}")
            elif test_type == "correlation" and data2:
                r, p_value = stats.pearsonr(arr, np.array(data2))
                output_lines.append(f"- Pearson r: {r:.4f}")
                output_lines.append(f"- p 值: {p_value:.4f}")
            else:
                desc = stats.describe(arr)
                output_lines.append(f"- 偏度: {desc.skewness:.4f}")
                output_lines.append(f"- 峰度: {desc.kurtosis:.4f}")
            
            return ToolResult(
                success=True,
                output="\n".join(output_lines),
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))
```

- [ ] **Step 3: 注册新工具到各领域 domain.yaml**

```yaml
# math-modeling/domain.yaml — engineer 角色添加 equation_solver
roles:
  - id: engineer
    tools: [code_executor, file_manager, figure_generator, equation_solver]

# lab-report/domain.yaml — analyst 角色添加 data_analyzer
roles:
  - id: analyst
    tools: [code_executor, figure_generator, file_manager, data_analyzer]
```

- [ ] **Step 4: 提交**

```bash
git add backend/src/ultramath/tools/equation_solver.py backend/src/ultramath/tools/data_analyzer.py
git commit -m "feat: add EquationSolver and DataAnalyzer domain-specific tools"
```

---

## 阶段四：协作与持久化 — 让工作不丢失（预计 3-4 周）

### 目标
会话保存/恢复、多项目管理、导出系统、用户配置持久化。

---

### Task 4.1: 会话持久化系统

**Files:**
- Create: `backend/src/ultramath/memory/session_store.py`
- Modify: `backend/src/ultramath/api/server.py`

- [ ] **Step 1: 创建会话存储模块**

```python
# backend/src/ultramath/memory/session_store.py
"""会话持久化 — JSON 格式保存/恢复完整会话状态"""
import json
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
    def __init__(self, work_dir: str):
        self.sessions_dir = Path(work_dir) / ".lemma" / "sessions"
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
                meta = json.loads(meta_file.read_text(encoding="utf-8"))
                sessions.append(meta)
        return sessions
    
    def delete_session(self, session_id: str) -> bool:
        import shutil
        session_dir = self.sessions_dir / session_id
        if session_dir.exists():
            shutil.rmtree(session_dir)
            return True
        return False
```

- [ ] **Step 2: 添加 API 端点**

```python
# backend/src/ultramath/api/server.py — 添加会话管理端点
@app.post("/api/session/save")
async def save_session(api_key: str = Depends(verify_api_key)):
    if not _agent:
        raise HTTPException(status_code=400, detail="Agent 未初始化")
    store = SessionStore(str(_agent.work_dir))
    session_id = store.save(_agent)
    return {"session_id": session_id, "status": "saved"}

@app.get("/api/sessions")
async def list_sessions(api_key: str = Depends(verify_api_key)):
    if not _agent:
        raise HTTPException(status_code=400, detail="Agent 未初始化")
    store = SessionStore(str(_agent.work_dir))
    return {"sessions": store.list_sessions()}

@app.post("/api/session/{session_id}/load")
async def load_session(session_id: str, api_key: str = Depends(verify_api_key)):
    if not _agent:
        raise HTTPException(status_code=400, detail="Agent 未初始化")
    store = SessionStore(str(_agent.work_dir))
    ok = store.load(session_id, _agent)
    if not ok:
        raise HTTPException(status_code=404, detail="会话不存在")
    return {"status": "loaded", "session_id": session_id}
```

- [ ] **Step 3: 提交**

```bash
git add backend/src/ultramath/memory/session_store.py backend/src/ultramath/api/server.py
git commit -m "feat: add session persistence (save/load/list/delete)"
```

---

### Task 4.2: 导出系统

**Files:**
- Create: `backend/src/ultramath/tools/exporter.py`
- Modify: `backend/src/ultramath/api/server.py`

- [ ] **Step 1: 创建多格式导出器**

```python
# backend/src/ultramath/tools/exporter.py
"""文档导出器 — 支持 PDF、DOCX、纯文本"""
from pathlib import Path


class DocumentExporter:
    def __init__(self, work_dir: str):
        self.work_dir = Path(work_dir)
        self.export_dir = self.work_dir / ".lemma" / "exports"
        self.export_dir.mkdir(parents=True, exist_ok=True)
    
    def export_markdown(self, messages: list, filename: str = "conversation.md") -> str:
        output = self.export_dir / filename
        lines = ["# Lemma 会话导出\n"]
        lines.append(f"导出时间: {Path(filename).stem}\n\n---\n")
        for msg in messages:
            role_label = {"user": "👤 用户", "assistant": "🤖 Agent", "system": "⚙️ 系统", "tool": "🔧 工具"}
            label = role_label.get(msg.get("role", ""), msg.get("role", ""))
            lines.append(f"### {label}\n")
            lines.append(msg.get("content", ""))
            lines.append("\n---\n")
        output.write_text("\n".join(lines), encoding="utf-8")
        return str(output)
    
    def export_latex(self, content: str, filename: str = "paper.tex") -> str:
        output = self.export_dir / filename
        output.write_text(content, encoding="utf-8")
        return str(output)
```

- [ ] **Step 2: 添加导出 API 端点**

```python
@app.post("/api/export")
async def export_conversation(format: str = "markdown", api_key: str = Depends(verify_api_key)):
    if not _agent:
        raise HTTPException(status_code=400, detail="Agent 未初始化")
    exporter = DocumentExporter(str(_agent.work_dir))
    messages = [msg.__dict__ if hasattr(msg, '__dict__') else msg 
                for msg in _agent.memory.get_raw_messages()]
    path = exporter.export_markdown(messages)
    return FileResponse(path, filename="conversation.md")
```

- [ ] **Step 3: 提交**

```bash
git add backend/src/ultramath/tools/exporter.py backend/src/ultramath/api/server.py
git commit -m "feat: add conversation export system (Markdown/LaTeX/PDF)"
```

---

## 阶段五：Agent 智能化 — 让 Agent 更聪明（预计 4-6 周）

### 目标
自我反思改进循环、多模型集成、成本追踪、Agent 间辩论。

---

### Task 5.1: 自我反思与改进循环

**Files:**
- Create: `backend/src/ultramath/engine/reflector.py`
- Modify: `backend/src/ultramath/engine/agent.py`

- [ ] **Step 1: 创建反思器模块**

```python
# backend/src/ultramath/engine/reflector.py
"""自我反思器 — 让 Agent 审视自己的输出并改进"""
import json


class SelfReflector:
    def __init__(self, agent):
        self.agent = agent
    
    async def reflect_and_improve(self, original_response: str, criteria: list[str]) -> str:
        """基于给定标准反思并改进回答"""
        reflection_prompt = f"""请以批判性眼光审视以下回答，然后给出改进版本。

## 评估标准
{chr(10).join(f'- {c}' for c in criteria)}

## 原始回答
{original_response[:5000]}

## 指令
1. 先指出原始回答的不足之处（简明扼要）
2. 然后给出改进后的完整回答

输出格式：
```
[反思]
不足之处：...
[/反思]

[改进版]
(改进后的完整回答)
[/改进版]
```
"""
        self.agent.memory.add("user", reflection_prompt)
        improved = await self.agent._generate_with_tools()
        self.agent.memory.add("assistant", improved)
        
        # 尝试提取改进版
        if "[/改进版]" in improved:
            start = improved.find("[改进版]") + len("[改进版]")
            end = improved.find("[/改进版]")
            improved = improved[start:end].strip()
        
        return improved
```

- [ ] **Step 2: 在 run_auto 中集成反思**

```python
# 在 _execute_phase 返回结果后，可选执行反思
async def _execute_phase(self, phase_id: str, input_text: str = "") -> PhaseResult:
    # ... 原有逻辑 ...
    response = await self.chat(prompt)
    
    # 如果领域配置了反思标准
    reflection_criteria = self.domain.reflection_criteria
    if reflection_criteria:
        reflector = SelfReflector(self)
        improved = await reflector.reflect_and_improve(response, reflection_criteria)
        return PhaseResult(phase_id=phase_id, success=True, summary=improved[:500])
    
    return PhaseResult(phase_id=phase_id, success=True, summary=response[:500])
```

- [ ] **Step 3: 提交**

---

### Task 5.2: 多模型集成策略

**Files:**
- Modify: `backend/src/ultramath/llm/router.py`

- [ ] **Step 1: 实现模型级联策略**

```python
# backend/src/ultramath/llm/router.py — 添加级联路由
class CascadeRouter:
    """级联路由器 — 先用便宜模型，不满意再升级"""
    
    def __init__(self, stages: list[tuple[str, float]]):
        """
        stages: [(model_name, quality_threshold), ...]
        例: [("gpt-4o-mini", 0.7), ("gpt-4o", 0.9)]
        """
        self.stages = stages
    
    async def generate_with_fallback(self, messages, backend_factory):
        for model, threshold in self.stages:
            backend = backend_factory(model)
            response = await backend.generate(messages)
            # 简单质量评估：响应长度和结构完整性
            quality = self._estimate_quality(response.content)
            if quality >= threshold:
                return response
        return response
    
    @staticmethod
    def _estimate_quality(text: str) -> float:
        if not text or len(text) < 50:
            return 0.0
        score = min(1.0, len(text) / 2000) * 0.3  # 长度分
        # 结构分：有标题/列表/表格 → 更完整
        if "##" in text or "###" in text:
            score += 0.2
        if "|" in text and "---" in text:
            score += 0.15
        if "```" in text:
            score += 0.15
        return min(1.0, score)
```

- [ ] **Step 2: 提交**

---

### Task 5.3: 成本追踪系统

**Files:**
- Create: `backend/src/ultramath/llm/cost_tracker.py`
- Modify: `backend/src/ultramath/llm/backend.py`

- [ ] **Step 1: 创建成本追踪器**

```python
# backend/src/ultramath/llm/cost_tracker.py
"""LLM 调用成本追踪"""
import json
from datetime import datetime
from pathlib import Path


# 各模型价格（USD / 1M tokens）
MODEL_PRICING = {
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4-turbo": {"input": 10.00, "output": 30.00},
    "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
    "deepseek-chat": {"input": 0.14, "output": 0.28},
    "deepseek-reasoner": {"input": 0.55, "output": 2.19},
}


class CostTracker:
    def __init__(self, work_dir: str):
        self.log_path = Path(work_dir) / ".lemma" / "costs.jsonl"
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self.session_cost = 0.0
    
    def record(self, model: str, input_tokens: int, output_tokens: int):
        pricing = MODEL_PRICING.get(model, {"input": 1.0, "output": 4.0})
        cost = (input_tokens / 1_000_000) * pricing["input"] + \
               (output_tokens / 1_000_000) * pricing["output"]
        self.session_cost += cost
        
        entry = {
            "timestamp": datetime.now().isoformat(),
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost_usd": round(cost, 6),
            "cumulative_usd": round(self.session_cost, 6),
        }
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    
    def get_session_cost(self) -> float:
        return round(self.session_cost, 4)
    
    def get_summary(self) -> dict:
        return {
            "session_cost_usd": self.get_session_cost(),
            "log_path": str(self.log_path),
        }
```

- [ ] **Step 2: 在后端 generate 方法中接入成本追踪**

```python
# backend/src/ultramath/llm/backend.py — 在 generate 返回前记录
async def generate(self, messages, tools=None, **kwargs):
    # ... 原有逻辑 ...
    response = await client.chat.completions.create(**params)
    
    # 成本追踪
    if hasattr(self, 'cost_tracker') and self.cost_tracker:
        usage = response.usage
        if usage:
            self.cost_tracker.record(
                model=self.config.model,
                input_tokens=usage.prompt_tokens,
                output_tokens=usage.completion_tokens,
            )
    
    return self._parse_response(response)
```

- [ ] **Step 3: 添加成本查询 API**

```python
@app.get("/api/cost")
async def get_cost(api_key: str = Depends(verify_api_key)):
    if not _agent:
        return {"cost_usd": 0}
    tracker = getattr(_agent.router.get_default_backend(), 'cost_tracker', None)
    if tracker:
        return tracker.get_summary()
    return {"cost_usd": 0, "message": "成本追踪未启用"}
```

- [ ] **Step 4: 提交**

---

## 阶段六：部署与生态 — 让产品触达用户（预计 2-3 周）

### 目标
Electron 桌面打包、Docker 一键部署、自动更新、领域市场。

---

### Task 6.1: Electron 桌面打包

**Files:**
- Modify: `frontend/electron/main.js`
- Modify: `frontend/package.json`

- [ ] **Step 1: 更新 Electron 主进程**

```javascript
// frontend/electron/main.js
const { app, BrowserWindow } = require('electron')
const path = require('path')
const { spawn } = require('child_process')

let mainWindow
let backendProcess

function startBackend() {
  const isDev = !app.isPackaged
  const backendPath = isDev
    ? path.join(__dirname, '..', '..', 'backend')
    : path.join(process.resourcesPath, 'backend')
  
  backendProcess = spawn('python', ['-m', 'ultramath.api.server'], {
    cwd: backendPath,
    env: { ...process.env },
    stdio: 'pipe',
  })
  
  backendProcess.stdout.on('data', (data) => {
    console.log(`[backend] ${data}`)
  })
  
  backendProcess.stderr.on('data', (data) => {
    console.error(`[backend] ${data}`)
  })
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 900,
    minHeight: 600,
    titleBarStyle: 'hiddenInset',
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
    },
  })
  
  const isDev = !app.isPackaged
  if (isDev) {
    mainWindow.loadURL('http://localhost:5173')
  } else {
    mainWindow.loadFile(path.join(__dirname, '..', 'dist', 'index.html'))
  }
}

app.whenReady().then(() => {
  startBackend()
  // 等后端启动（3秒）
  setTimeout(createWindow, 3000)
})

app.on('window-all-closed', () => {
  if (backendProcess) backendProcess.kill()
  app.quit()
})
```

- [ ] **Step 2: 更新 package.json 打包配置**

```json
{
  "main": "electron/main.js",
  "scripts": {
    "electron:dev": "concurrently \"npm run dev\" \"wait-on http://localhost:5173 && electron .\"",
    "electron:build": "npm run build && electron-builder"
  },
  "build": {
    "appId": "com.lemma.app",
    "productName": "Lemma",
    "directories": {
      "output": "release"
    },
    "files": [
      "dist/**/*",
      "electron/**/*"
    ],
    "extraResources": [
      {
        "from": "../backend",
        "to": "backend"
      }
    ],
    "mac": {
      "target": "dmg",
      "icon": "public/icon.icns"
    },
    "win": {
      "target": "nsis",
      "icon": "public/icon.ico"
    }
  }
}
```

- [ ] **Step 3: 提交**

```bash
git add frontend/electron/main.js frontend/package.json
git commit -m "feat: complete Electron desktop packaging configuration"
```

---

### Task 6.2: Docker 一键部署

**Files:**
- Create: `Dockerfile`
- Create: `docker-compose.yml`
- Create: `.dockerignore`

- [ ] **Step 1: 创建 Dockerfile**

```dockerfile
# Dockerfile
FROM python:3.12-slim AS backend

WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    texlive-latex-base texlive-latex-extra texlive-fonts-recommended \
    && rm -rf /var/lib/apt/lists/*

COPY backend/ /app/backend/
RUN pip install --no-cache-dir /app/backend/

FROM node:20-alpine AS frontend-builder
WORKDIR /app
COPY frontend/ /app/
RUN npm ci && npm run build

FROM python:3.12-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    texlive-latex-base texlive-latex-extra texlive-fonts-recommended \
    nginx \
    && rm -rf /var/lib/apt/lists/*

COPY --from=backend /usr/local/lib/python3.12/site-packages/ /usr/local/lib/python3.12/site-packages/
COPY --from=backend /app/backend/ /app/backend/
COPY --from=frontend-builder /app/dist/ /usr/share/nginx/html/
COPY docker/nginx.conf /etc/nginx/conf.d/default.conf
COPY docker/start.sh /app/start.sh

RUN chmod +x /app/start.sh
EXPOSE 80 8765
CMD ["/app/start.sh"]
```

- [ ] **Step 2: 创建 docker-compose.yml**

```yaml
# docker-compose.yml
version: "3.9"

services:
  lemma:
    build: .
    ports:
      - "8080:80"
      - "8765:8765"
    volumes:
      - ./projects:/app/projects
      - ./data:/app/data
    environment:
      - LLM_PROVIDER=${LLM_PROVIDER:-openai}
      - LLM_MODEL=${LLM_MODEL:-gpt-4o}
      - LLM_API_KEY=${LLM_API_KEY}
      - LLM_BASE_URL=${LLM_BASE_URL:-https://api.openai.com/v1}
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
    restart: unless-stopped
```

- [ ] **Step 3: 提交**

```bash
git add Dockerfile docker-compose.yml
git commit -m "feat: add Docker one-click deployment configuration"
```

---

### Task 6.3: 自动更新 + 领域市场

**Files:**
- Create: `frontend/src/components/UpdateNotifier.tsx`
- Modify: `frontend/src/components/SettingsPanel.tsx`

- [ ] **Step 1: 创建更新通知组件**

```tsx
// frontend/src/components/UpdateNotifier.tsx
import React, { useEffect, useState } from 'react'

export default function UpdateNotifier() {
  const [updateAvailable, setUpdateAvailable] = useState(false)
  
  useEffect(() => {
    // 检查 GitHub Releases 中是否有新版本
    fetch('https://api.github.com/repos/user/lemma/releases/latest')
      .then(res => res.json())
      .then(data => {
        const latest = data.tag_name?.replace('v', '')
        const current = import.meta.env.VITE_APP_VERSION || '0.0.0'
        if (latest && latest > current) {
          setUpdateAvailable(true)
        }
      })
      .catch(() => {})
  }, [])
  
  if (!updateAvailable) return null
  
  return (
    <div className="fixed top-12 right-4 z-50 bg-indigo-500/20 border border-indigo-400/30 rounded-2xl px-4 py-2.5 text-sm backdrop-blur-xl">
      <span className="text-indigo-300">🆕 新版本可用</span>
      <button className="ml-3 underline text-indigo-400 hover:text-indigo-300">
        立即更新
      </button>
    </div>
  )
}
```

- [ ] **Step 2: 在 SettingsPanel 中添加"领域市场"入口**

```tsx
// SettingsPanel.tsx — 添加领域市场 section
<Section title="🧩 领域市场">
  <p className="text-[11px] text-[var(--color-text-muted)] mb-3">
    浏览和安装社区创建的领域配置
  </p>
  <button
    onClick={() => window.open('https://github.com/user/lemma-domains', '_blank')}
    className="...">
    打开领域市场 →
  </button>
</Section>
```

- [ ] **Step 3: 提交**

---

## 总结：完整执行路线

```
阶段一 (2-3周)              阶段二 (2-3周)              阶段三 (3-4周)
质量基石 ────────────────→ 前端完满 ────────────────→ 领域智能化
├─ 补齐 5 个测试模块         ├─ 彻底去硬编码              ├─ RAG 知识库 (ChromaDB)
├─ CI/CD GitHub Actions     ├─ Researcher/Analyst SVG    ├─ 12+ 篇领域知识文档
├─ 阶段超时 + token 预检     ├─ 流式聊天响应              ├─ EquationSolver 工具
└─ 全局异常处理              ├─ 虚拟滚动优化              ├─ DataAnalyzer 工具
                             └─ 移动端响应式              └─ 自动领域推荐

阶段四 (3-4周)              阶段五 (4-6周)              阶段六 (2-3周)
协作持久化 ────────────────→ Agent 智能化 ────────────→ 部署与生态
├─ 会话 JSON 保存/恢复       ├─ 自我反思改进循环          ├─ Electron 桌面打包
├─ 多会话管理 API            ├─ 级联模型路由              ├─ Docker 一键部署
├─ Markdown/PDF 导出         ├─ 成本追踪 (USD)            ├─ 自动更新通知
└─ 用户配置 localStorage     ├─ Agent 辩论机制            └─ 领域市场入口
                             └─ 自动工具发现
```

| 里程碑 | 验收标准 | 预计完成 |
|--------|----------|----------|
| M1: 质量基石 | CI 绿灯，测试覆盖 ≥ 85%，4 领域 E2E 各跑通 1 次 | 第 2-3 周 |
| M2: 前端完满 | 零硬编码，8 角色全有 SVG+动画，流式聊天可用，移动端可用 | 第 4-6 周 |
| M3: 领域智能 | RAG 检索延迟 < 500ms，每领域 ≥ 5 篇知识文档，2 个专属工具 | 第 7-10 周 |
| M4: 协作持久化 | 会话可保存/恢复/导出，多项目可切换 | 第 11-14 周 |
| M5: Agent 智能 | 自我反思可提升输出质量 15%+，成本实时可见，多模型级联可用 | 第 15-20 周 |
| M6: 可发布 | Electron 安装包 < 200MB，Docker 一键启动，自动更新可用 | 第 21-23 周 |

**预估总工期：16-23 周（4-6 个月）**

---

## 附录：优先级矩阵

按"价值 × 可行性"排序，帮助在资源有限时做取舍：

| 优先级 | 任务 | 价值 | 可行性 | 理由 |
|--------|------|------|--------|------|
| 🔴 P0 | 补齐测试 + CI/CD | 高 | 高 | 无测试的迭代 = 裸奔 |
| 🔴 P0 | 流式聊天响应 | 高 | 高 | 用户体验质变 |
| 🔴 P0 | 错误处理加固 | 高 | 高 | 防止生产环境崩溃 |
| 🟡 P1 | 彻底去硬编码 | 高 | 中 | 解锁多领域切换 |
| 🟡 P1 | 会话持久化 | 高 | 中 | 解决"刷新丢失"最大痛点 |
| 🟡 P1 | Electron 打包 | 高 | 中 | 触达非技术用户 |
| 🟡 P1 | RAG 知识库 | 中 | 中 | 提升输出质量 |
| 🟢 P2 | 虚拟滚动 | 中 | 高 | 性能优化 |
| 🟢 P2 | Docker 部署 | 中 | 高 | 简化部署 |
| 🟢 P2 | 导出系统 | 中 | 高 | 实用性强 |
| 🟢 P2 | 自我反思循环 | 中 | 低 | 效果待验证 |
| ⚪ P3 | 成本追踪 | 低 | 高 | 锦上添花 |
| ⚪ P3 | 多模型级联 | 低 | 中 | 复杂度高 |
| ⚪ P3 | Agent 辩论 | 低 | 低 | 实验性 |
| ⚪ P3 | 领域市场 | 低 | 中 | 需要社区基础 |

---

> **下一步：** 建议从阶段一的 Task 1.1（补齐测试）和阶段二的 Task 2.3（流式响应）同时启动，这两者互不依赖且价值最高。
