# Lemma v4.0 — 从原型到产品：集成化、可扩展、真实验证

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 v3.0 中"已写好但从未集成"的模块真正串联起来，把 4 个空骨架领域充实为可运行的完整体验，让系统能端到端解决一个真实的非数学建模任务，并建立可持续迭代的工程基础。

**Architecture:** 分 5 个阶段。阶段一"缝合"（把散落的模块接入引擎和 API）→ 阶段二"充实"（为 3 个新领域写 phase_handlers 和 prompts）→ 阶段三"对齐"（前端彻底去硬编码，成为领域驱动的动态 UI）→ 阶段四"验证"（端到端跑通一个真实任务，补齐集成测试）→ 阶段五"打磨"（文档、性能、Electron 打包、发布）。

**Tech Stack:** Python 3.11+, FastAPI, OpenAI SDK, React 18, TypeScript, Tailwind CSS, Electron, pytest, Vitest, Docker

---

## 全量审计结论

在动手写计划之前，我读了全部 60+ 源文件。以下是精确的 gap 列表：

### 已验证通过的（105 个测试覆盖的）
- DomainProfile 加载和查询 ✅
- StateMachine 短语转换 ✅
- AcademicAgent 基本创建 ✅
- 交接协议解析 ✅
- 信赖阈值计算 ✅
- 固化模式目录创建 ✅
- 文件隔离过滤 ✅
- 短长期记忆 ✅
- 工具系统（沙箱/文件管理器/代码执行） ✅
- LLM 后端重试 ✅

### 集成 gap（0 个测试覆盖，都是"写了但没用"）
| 文件 | 问题 |
|------|------|
| `engine/agent.py:AcademicAgent` | 从未被 API server 调用，server.py 仍用 LemmaAgent |
| `engine/handoff.py` | 解析函数已完成，但 AcademicAgent 的 chat 方法从未调用它 |
| `engine/trust.py:TrustManager` | 完整实现，但无任何地方实例化或记录反馈 |
| `engine/solidify.py:solidify_session` | 能创建目录结构，但无 API 端点触发 |
| `engine/isolation.py:FileVisibility` | ACL 逻辑完整，但 ToolRegistry 从不检查文件可见性 |
| `api/server.py:create_agent` | 硬编码 `LemmaAgent(work_dir, router, role_mgr, tool_registry)` |
| `orchestration/engine.py:LemmaAgent` | 仍依赖旧的 `Phase` 枚举和 `PHASE_NAMES`，不走 DomainProfile |
| 4 个 `domains/*/domain.yaml` | 没有任何一个定义 `phase_handlers` |
| 4 个 `domains/*/prompts/` | 全部为空目录，零个 prompt 文件 |
| `api/server.py` 的 `create_agent` | 不接受 `domain_id` 参数 |

### 前端硬编码
| 位置 | 硬编码内容 |
|------|-----------|
| `App.tsx:PHASES` | 8 个数学建模阶段名 |
| `ChatPanel.tsx:ROLES` | 6 个角色（emoji + 名称） |
| `PipelinePanel.tsx:PHASE_DESCRIPTIONS` | 8 个数学建模阶段描述 |
| `PipelinePanel.tsx:PHASE_ICONS` | 8 个角色图标 |
| `Sidebar.tsx:NAV_ITEMS` | 4 个导航项（这是正常的） |

---

## 阶段一：缝合 — 让写好的模块真正工作（预计 3-4 天）

### 目标
把 engine/ 下 4 个"写了但没用的"模块接入 AcademicAgent 和 API server，让后端真正支持多领域切换。

---

### Task 1.1: 将 AcademicAgent 接入 API server

**Files:**
- Modify: `backend/src/ultramath/api/server.py:115-151`

**当前状态:** `create_agent()` 调用 `LemmaAgent(work_dir, router, role_mgr, tool_registry)`。
**目标:** `create_agent()` 接受可选 `domain_id`，加载对应的 DomainProfile，创建 `AcademicAgent`。

- [ ] **Step 1: 编写 server 模块的集成测试**

创建 `backend/tests/test_server_agent.py`：

```python
"""API server create_agent 集成测试"""
import pytest
from pathlib import Path
from unittest.mock import patch
from ultramath.api.server import create_agent, _agent
from ultramath.llm.backend import LLMConfig


class TestCreateAgent:
    def test_create_with_default_domain(self, tmp_path):
        """不指定 domain_id 时应使用 math-modeling"""
        # 确保 domains 目录存在
        with patch('ultramath.api.server._agent', None):
            agent = create_agent(
                work_dir=str(tmp_path),
                config=LLMConfig(api_key="test", model="gpt-4o"),
                domain_id="math-modeling",
            )
            assert agent.domain.id == "math-modeling"
            assert agent.domain.name == "数学建模竞赛"

    def test_create_with_paper_domain(self, tmp_path):
        """指定 domain_id 应加载对应领域"""
        with patch('ultramath.api.server._agent', None):
            agent = create_agent(
                work_dir=str(tmp_path),
                config=LLMConfig(api_key="test", model="gpt-4o"),
                domain_id="paper-writing",
            )
            assert agent.domain.id == "paper-writing"

    def test_create_with_invalid_domain_falls_back(self, tmp_path):
        """无效 domain_id 应 fallback 到 math-modeling"""
        with patch('ultramath.api.server._agent', None):
            agent = create_agent(
                work_dir=str(tmp_path),
                config=LLMConfig(api_key="test", model="gpt-4o"),
                domain_id="nonexistent",
            )
            assert agent.domain is not None  # 至少能创建
```

- [ ] **Step 2: 运行测试确认失败**

```bash
python -m pytest backend/tests/test_server_agent.py -v --tb=short
```

Expected: FAIL — `create_agent` 不接受 `domain_id` 参数。

- [ ] **Step 3: 修改 create_agent 函数**

```python
def create_agent(
    work_dir: str,
    config: ConfigRequest | None = None,
    domain_id: str = "math-modeling",
) -> AcademicAgent:
    """创建 Agent 实例，支持多领域"""
    global _agent

    # 加载 DomainProfile
    domains_base = Path(__file__).parent.parent.parent.parent / "domains"
    try:
        domain = DomainProfile.from_directory(str(domains_base / domain_id))
    except (FileNotFoundError, Exception):
        logger.warning(f"Domain '{domain_id}' not found, falling back to math-modeling")
        domain = DomainProfile.from_directory(str(domains_base / "math-modeling"))

    # 创建 LLM 路由器
    if config:
        llm_config = LLMConfig(
            provider=config.provider, model=config.model,
            api_key=config.api_key, base_url=config.base_url,
            max_tokens=config.max_tokens, temperature=config.temperature,
        )
    else:
        llm_config = LLMConfig(
            provider=os.environ.get("LLM_PROVIDER", "openai"),
            model=os.environ.get("LLM_MODEL", "gpt-4o"),
            api_key=os.environ.get("LLM_API_KEY", os.environ.get("OPENAI_API_KEY", "")),
            base_url=os.environ.get("LLM_BASE_URL", "https://api.openai.com/v1"),
        )
    router = ModelRouter.from_single_config(llm_config)

    # 创建工具注册表（根据 domain 的 roles 选择工具）
    tool_registry = ToolRegistry()
    tool_registry.register(CodeExecutorTool(work_dir))
    tool_registry.register(LatexCompilerTool(work_dir))
    tool_registry.register(FileManagerTool(work_dir))
    tool_registry.register(QualityCheckerTool(work_dir))
    tool_registry.register(FigureGeneratorTool(work_dir))

    # 创建 AcademicAgent（替代 LemmaAgent）
    _agent = AcademicAgent(work_dir, domain, router, tool_registry)

    # 设置 WebSocket 广播回调
    async def broadcast(event_type: str, data: dict):
        msg = json.dumps({"type": event_type, **data}, ensure_ascii=False)
        async with _ws_lock:
            dead = []
            for ws in _ws_connections:
                try:
                    await ws.send_text(msg)
                except Exception:
                    dead.append(ws)
            for ws in dead:
                if ws in _ws_connections:
                    _ws_connections.remove(ws)

    def schedule_broadcast(event_type: str):
        def callback(data: dict):
            asyncio.create_task(broadcast(event_type, data))
        return callback

    _agent.set_callbacks(
        on_message=schedule_broadcast("message"),
        on_phase_change=schedule_broadcast("phase_change"),
        on_tool_call=schedule_broadcast("tool_call"),
    )

    return _agent
```

同时更新全局类型标注：
```python
_agent: AcademicAgent | None = None
```

- [ ] **Step 4: 更新所有 API 端点中的 Agent 类型引用**

`chat` 端点中 `_agent.chat()` 的签名变了 — AcademicAgent.chat 不再接受 `role` 参数（因为角色由 domain 定义，role_id 是 string 而非 Role enum）。需要更新：

```python
@app.post("/api/chat")
async def chat(req: ChatRequest, api_key: str = Depends(verify_api_key)):
    if not _agent:
        raise HTTPException(status_code=400, detail="Agent 未初始化")
    async with _agent_lock:
        response = await _agent.chat(req.message)
    return {"response": response}
```

`get_status` 端点中：
```python
@app.get("/api/status")
async def get_status():
    if not _agent:
        return {"status": "not_initialized"}
    return _agent.get_status()
```
（AcademicAgent.get_status 返回的键名略有不同 — `current_role` 是 `current_role_id`，`current_role_name` 是新字段）

`switch_role` WebSocket 处理器改为：
```python
elif msg_type == "switch_role":
    if _agent and msg.get("role"):
        _agent.switch_role(msg["role"])
        role = _agent.get_current_role()
        await websocket.send_text(json.dumps({
            "type": "role_switched",
            "role": msg["role"],
            "name": role.name if role else msg["role"],
        }, ensure_ascii=False))
```

- [ ] **Step 5: 更新 `/api/init` WebSocket 处理器接受 domain_id**

```python
elif msg_type == "init":
    work_dir = msg.get("work_dir", "")
    domain_id = msg.get("domain_id", "math-modeling")
    ...
    async with _agent_lock:
        create_agent(validated_dir, config, domain_id)
```

- [ ] **Step 6: 运行全部测试**

```bash
python -m pytest backend/tests/ -v --tb=short
```

- [ ] **Step 7: 提交**

```bash
git add .
git commit -m "feat: wire AcademicAgent into API server with domain selection"
```

---

### Task 1.2: 将 Handoff 协议接入 AcademicAgent

**Files:**
- Modify: `backend/src/ultramath/engine/agent.py`

**当前状态:** AcademicAgent.chat 只是做了 LLM 调用，响应后不解析交接表。
**目标:** 每次 `chat` 返回后尝试解析交接表，将摘要注入 context。

- [ ] **Step 1: 在 AcademicAgent 中集成 handoff 解析**

在 `_generate_with_tools` 返回后添加：

```python
async def chat(self, user_message: str) -> str:
    """与 Agent 对话（非流式），自动解析交接表"""
    self._ensure_system_message()
    self.memory.add("user", user_message)
    # ... emit ...
    response_text = await self._generate_with_tools()
    self.memory.add("assistant", response_text)

    # 尝试解析交接表
    from .handoff import parse_handoff_from_text
    handoff = parse_handoff_from_text(response_text)
    if handoff:
        self.context.update_phase(
            self.state.current_phase,
            phase_name=self.state.phase_name,
            summary=handoff.conclusion,
        )

    # ... emit response ...
    return response_text
```

- [ ] **Step 2: 编写交接集成测试**

创建 `backend/tests/test_handoff_integration.py`：

```python
class TestHandoffIntegration:
    def test_chat_response_with_handoff_table(self, tmp_path, sample_domain):
        """当 LLM 输出包含交接表时，应自动解析并存入 context"""
        # 创建 mock LLM backend 返回包含交接表的响应
        ...
        response = await agent.chat("请完成分析")
        # context 应包含交接结论
        status = agent.get_status()
        assert "context" in status
```

- [ ] **Step 3: 运行测试并提交**

```bash
python -m pytest backend/tests/ -v --tb=short
git add .
git commit -m "feat: integrate handoff protocol parsing into AcademicAgent.chat"
```

---

### Task 1.3: 将 TrustManager 接入 AcademicAgent

**Files:**
- Modify: `backend/src/ultramath/engine/agent.py`

- [ ] **Step 1: 在 AcademicAgent.__init__ 中创建 TrustManager 实例**

```python
from .trust import TrustManager

class AcademicAgent:
    def __init__(self, ...):
        ...
        self.trust = TrustManager(str(self.work_dir / "trust.json"))
```

- [ ] **Step 2: 在 run_auto 中询问确认（当需要时）**

在 `run_auto` 的每个阶段开始前：

```python
if self.trust.should_confirm(phase_id):
    yield {
        "type": "confirm_required",
        "phase": phase_id,
        "name": phase_cfg.name,
        "message": f"即将执行阶段 '{phase_cfg.name}'，是否继续？",
    }
    # 等待用户确认（通过 WebSocket）
    await self._wait_confirmation()
```

- [ ] **Step 3: 添加确认等待机制和 API 端点**

```python
class AcademicAgent:
    def __init__(self, ...):
        ...
        self._confirm_event = asyncio.Event()
    
    async def _wait_confirmation(self) -> None:
        self._confirm_event.clear()
        await self._confirm_event.wait()
    
    def confirm(self, accepted: bool = True, phase_id: str | None = None) -> None:
        self.trust.record(phase_id or self.state.current_phase, accepted=accepted)
        self._confirm_event.set()
```

添加 API 端点：
```python
@app.post("/api/confirm")
async def confirm_step(api_key: str = Depends(verify_api_key)):
    if _agent:
        _agent.confirm(accepted=True)
        return {"status": "confirmed"}
    return {"status": "no_agent"}
```

- [ ] **Step 4: 编写测试**

```python
class TestTrustIntegration:
    def test_should_confirm_default(self):
        """默认应确认"""
        ...
    def test_confirm_records_feedback(self):
        """确认后应记录反馈"""
        ...
    def test_reject_tightens_trust(self):
        """连续拒绝后信赖收紧"""
        ...
```

- [ ] **Step 5: 运行测试并提交**

```bash
python -m pytest backend/tests/ -v --tb=short
git add .
git commit -m "feat: integrate TrustManager into AcademicAgent with confirmation flow"
```

---

### Task 1.4: 将 FileVisibility 接入 ToolRegistry（只给 Agent 看它能看的文件）

**Files:**
- Modify: `backend/src/ultramath/engine/agent.py`
- Modify: `backend/src/ultramath/tools/file_manager.py`

**设计:** `AcademicAgent` 维护一个 `FileVisibility` 实例。FileManagerTool 在列出/读取文件时先检查可见性。

- [ ] **Step 1: 在 AcademicAgent 中创建 FileVisibility**

```python
# 域定义中可增加 isolation_rules 字段：
# domain.yaml:
# isolation:
#   generator: ["*.md"]
#   critic: ["generator_output.md"]
```

在 AcademicAgent 初始化时：
```python
from .isolation import FileVisibility
from .domain import DomainProfile

# 从 domain 获取 isolation rules（如果有）
isolation_rules = getattr(domain, 'isolation', {})
self.file_visibility = FileVisibility(self.work_dir, self.current_role_id, isolation_rules)
```

- [ ] **Step 2: 更新 _ensure_system_prompt 注入可见文件列表**

```python
def _ensure_system_message(self) -> None:
    system_prompt = self._build_system_prompt()
    # 注入文件可见性
    if self.file_visibility:
        system_prompt = self.file_visibility.filter_system_prompt(system_prompt)
    ...
```

- [ ] **Step 3: 角色切换时更新 FileVisibility**

```python
def switch_role(self, role_id: str) -> None:
    if self.domain.get_role_by_id(role_id):
        self.current_role_id = role_id
        # 更新文件可见性
        isolation_rules = getattr(self.domain, 'isolation', {})
        self.file_visibility = FileVisibility(self.work_dir, role_id, isolation_rules)
```

- [ ] **Step 4: 运行测试并提交**

```bash
python -m pytest backend/tests/ -v --tb=short
git add .
git commit -m "feat: integrate FileVisibility into AcademicAgent and system prompt"
```

---

## 阶段二：充实 — 为新领域写提示词和处理器（预计 3-4 天）

### 目标
让 paper-writing/lab-report/literature-review 三个领域从空骨架变为可真正运行的完整体验。

---

### Task 2.1: 为 paper-writing 编写 phase_handlers 和 prompts

**Files:**
- Create: `domains/paper-writing/prompts/agent_lead.md`
- Create: `domains/paper-writing/prompts/agent_writer.md`
- Create: `domains/paper-writing/prompts/agent_reviewer.md`
- Create: `domains/paper-writing/prompts/agent_formatter.md`
- Create: `domains/paper-writing/prompts/phase_outline.md`
- Create: `domains/paper-writing/prompts/phase_drafting.md`
- Create: `domains/paper-writing/prompts/phase_formatting.md`
- Create: `domains/paper-writing/prompts/phase_review.md`
- Create: `domains/paper-writing/templates/paper-template.tex`
- Modify: `domains/paper-writing/domain.yaml`（添加 phase_handlers 引用）

- [ ] **Step 1: 编写 `agent_lead.md` — 论文主编**

```markdown
# 论文主编 — Paper Writing Lead

你是学术论文写作的协调者。你负责：
1. 理解研究大纲和核心贡献
2. 拆解为可执行的章节计划
3. 调度章节作者完成各章节

## 工作流程
1. 分析输入的研究大纲
2. 确定论文结构（Introduction → Related Work → Method → Experiments → Conclusion）
3. 为每个章节指定核心内容和关键引用

## 输出格式
每次完成阶段后，必须输出以下交接表：

| 字段 | 内容 |
|------|------|
| 结论 | [一句话总结当前进度] |
| 置信度 | green/yellow/red |
| 未解决分歧 | [如有，列出] |
| 下游警告 | [如有，列出] |
```

- [ ] **Step 2: 编写每个 phase 的 handler prompt**

`phase_outline.md`:

```markdown
请根据以下研究主题构建论文大纲：

{input_text}

要求：
1. 确定论文标题
2. 列出所有章节（Introduction, Related Work, Method, Experiments, Discussion, Conclusion）
3. 每个章节标注核心内容和预计篇幅
4. 确定关键引用列表

{context_sections}
```

`phase_drafting.md`:

```markdown
请逐章撰写正文。当前已完成大纲：{context_sections}

要求：
1. 每章独立成文，逻辑连贯
2. Introduction：研究背景、问题、贡献
3. Related Work：分类综述，指出不足
4. Method：详细描述方法，可复现
5. Experiments：实验设置、结果、分析
6. Conclusion：总结、局限性、未来工作

| 字段 | 内容 |
|------|------|
| 结论 | [...] |
| 置信度 | green/yellow/red |
| 下游警告 | [...] |
```

`phase_review.md`:

```markdown
请作为学术审稿人，从以下维度评审：

1. **论证逻辑**: 每章的论点是否支持结论？
2. **文献覆盖**: 是否遗漏关键相关工作？
3. **方法描述**: 是否足够详细可复现？
4. **语言表达**: 是否清晰、无 jargon？

{context_sections}

| 字段 | 内容 |
|------|------|
| 结论 | [总体评价] |
| 置信度 | green/yellow/red |
| 未解决分歧 | [如有] |
| 下游警告 | [需要修改的部分] |
```

- [ ] **Step 3: 创建 LaTeX 模板**

```latex
\documentclass[11pt,a4paper]{article}
\usepackage[utf8]{inputenc}
\usepackage{amsmath,amssymb,graphicx,hyperref,booktabs,natbib}

\title{Your Paper Title}
\author{Author Name}
\date{\today}

\begin{document}
\maketitle
\begin{abstract} % ABSTRACT_PLACEHOLDER \end{abstract}
\section{Introduction} % INTRODUCTION_PLACEHOLDER \end{document}
```

- [ ] **Step 4: 更新 domain.yaml 添加 phase_handlers**

在 `paper-writing/domain.yaml` 的 `validators` 后面添加：

```yaml
phase_handlers:
  outline: |
    请根据以下研究主题构建论文大纲：
    {input_text}
    确定标题、章节结构（Intro/Related Work/Method/Experiments/Conclusion）、关键引用。
    {context_sections}
  drafting: |
    请逐章撰写正文。
    {context_sections}
  formatting: |
    请将撰写的章节整合到 LaTeX 模板中并编译检查。
    {context_sections}
  review: |
    请作为学术审稿人从论证逻辑、文献覆盖、方法可复现性、语言表达四个维度评审。
    {context_sections}
```

- [ ] **Step 5: 验证领域可加载**

```bash
python -c "
from ultramath.engine.domain import DomainProfile
p = DomainProfile.from_directory('domains/paper-writing')
assert 'outline' in p.phase_handlers, 'outline handler missing'
assert 'drafting' in p.phase_handlers, 'drafting handler missing'
print('✅ paper-writing domain fully loaded with handlers')
"
```

- [ ] **Step 6: 提交**

```bash
git add domains/paper-writing/
git commit -m "feat: complete paper-writing domain with prompts, handlers, and LaTeX template"
```

---

### Task 2.2: 为 lab-report 编写 phase_handlers 和 prompts

**Files:**
- Create: `domains/lab-report/prompts/agent_lead.md`
- Create: `domains/lab-report/prompts/agent_analyst.md`
- Create: `domains/lab-report/prompts/agent_writer.md`
- Create: `domains/lab-report/prompts/phase_design.md`
- Create: `domains/lab-report/prompts/phase_methods.md`
- Create: `domains/lab-report/prompts/phase_results.md`
- Create: `domains/lab-report/prompts/phase_discussion.md`
- Create: `domains/lab-report/templates/lab-report.tex`
- Modify: `domains/lab-report/domain.yaml`

按照 plan 中 Task 3.2 的 domain.yaml 和 prompts 设计填充（略原文，因已在计划中）。

---

### Task 2.3: 为 literature-review 编写 phase_handlers 和 prompts

**Files:**
- Create: `domains/literature-review/prompts/agent_lead.md`
- Create: `domains/literature-review/prompts/agent_researcher.md`
- Create: `domains/literature-review/prompts/agent_synthesizer.md`
- Create: `domains/literature-review/prompts/phase_search.md`
- Create: `domains/literature-review/prompts/phase_screen.md`
- Create: `domains/literature-review/prompts/phase_synthesize.md`
- Create: `domains/literature-review/prompts/phase_draft.md`
- Create: `domains/literature-review/prompts/phase_review.md`
- Create: `domains/literature-review/templates/review-template.tex`
- Modify: `domains/literature-review/domain.yaml`

按照 plan 中 Task 3.3 的设计填充。

---

## 阶段三：对齐 — 前端彻底去硬编码（预计 3-4 天）

### 目标
让前端的 phases、roles、descriptions 全部从后端动态加载，不再硬编码任何领域相关内容。

---

### Task 3.1: 前端从后端动态获取 phases 和 roles

**Files:**
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/components/ChatPanel.tsx`
- Modify: `frontend/src/components/PipelinePanel.tsx`
- Create: `frontend/src/components/DomainSelector.tsx`

- [ ] **Step 1: 在 App.tsx 中移除 PHASES 常量，改为从后端获取**

```typescript
// 替换静态 PHASES 为动态从 status 响应构建
// status 响应中 state 字段已包含 phase 名称（来自 DomainProfile）
// 初始化时发送 init 消息并传递 domain_id

// 在 initProject 函数中添加 domain_id：
const initProject = (dir: string, domainId: string = 'math-modeling', config?: Record<string, unknown>) => {
  setWorkDir(dir)
  ws.send(JSON.stringify({
    type: 'init',
    work_dir: dir,
    domain_id: domainId,
    config,
  }))
}
```

- [ ] **Step 2: 从后端返回 phases 信息**

在 `create_agent` 的成功响应中，添加 phases 信息：

```python
await websocket.send_text(json.dumps({
    "type": "initialized",
    "work_dir": validated_dir,
    "domain": {
        "id": domain.id,
        "name": domain.name,
        "phases": [{"id": p.id, "name": p.name, "order": p.order} for p in domain.phases if p.id not in ("idle", "done")],
        "roles": [{"id": r.id, "name": r.name, "emoji": r.emoji} for r in domain.roles],
    },
}, ensure_ascii=False))
```

- [ ] **Step 3: 前端消费 domain 数据**

在 `onMessage` 中解析 `initialized` 消息的 domain 字段：

```typescript
} else if (msg.type === 'initialized') {
  setAgentStatus(prev => ({ ...prev, initialized: true }))
  setWorkDir(msg.work_dir as string)
  if (msg.domain) {
    const domain = msg.domain as { id: string; name: string; phases: PhaseInfo[]; roles: RoleDef[] }
    setPhases(domain.phases.map((p, i) => ({
      id: i,
      name: p.name,
      status: 'pending' as const,
    })))
    setRoles(domain.roles)
  }
}
```

- [ ] **Step 4: 更新 ChatPanel 和 PipelinePanel 接受动态数据**

ChatPanel 的角色选择器改为从 props 接收 roles：

```tsx
interface ChatPanelProps {
  // ... existing
  roles: { id: string; name: string; emoji: string }[]
}
```

PipelinePanel 改为纯展示组件，不再内置 PHASE_ICONS 和 PHASE_DESCRIPTIONS。

- [ ] **Step 5: 运行前端测试**

```bash
cd frontend && npx vitest run
```

- [ ] **Step 6: 提交**

```bash
git add .
git commit -m "feat: make frontend domain-driven - phases and roles from backend"
```

---

### Task 3.2: 创建设置页中的领域选择器

**Files:**
- Modify: `frontend/src/components/SettingsPanel.tsx`

在 SettingsPanel 中添加领域选择下拉：

```tsx
// 在项目设置 section 后添加
<Section title="🎯 领域选择">
  <select
    value={selectedDomain}
    onChange={e => setSelectedDomain(e.target.value)}
    className="w-full bg-white/[0.03] border border-white/[0.06] rounded-lg px-3 py-2 text-xs text-[var(--color-text)]"
  >
    {domains.map((d: { id: string; name: string }) => (
      <option key={d.id} value={d.id}>{d.name}</option>
    ))}
  </select>
</Section>
```

`initProject` 的调用中传入 `selectedDomain`。

- [ ] **Step 2: 运行测试并提交**

---

## 阶段四：验证 — 端到端真实验证（预计 2-3 天）

### 目标
用一个真实任务跑通完整流程，补充缺失的集成测试。

---

### Task 4.1: 端到端集成测试 — paper-writing 领域

**Files:**
- Create: `backend/tests/e2e/test_paper_writing_pipeline.py`

```python
"""端到端测试 — paper-writing 领域"""
import pytest
import os

@pytest.mark.integration
@pytest.mark.slow
class TestPaperWritingPipeline:
    async def test_full_outline_to_draft(self, tmp_path):
        """给定一个研究主题，应完成大纲构建和第一章撰写"""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            pytest.skip("需要 OPENAI_API_KEY")

        from ultramath.engine.agent import AcademicAgent
        from ultramath.engine.domain import DomainProfile
        from ultramath.llm.router import ModelRouter
        from ultramath.llm.backend import LLMConfig
        from ultramath.tools.registry import ToolRegistry
        from ultramath.tools.file_manager import FileManagerTool
        from ultramath.tools.latex_compiler import LatexCompilerTool

        domain = DomainProfile.from_directory("domains/paper-writing")
        config = LLMConfig(api_key=api_key, model="gpt-4o")
        router = ModelRouter.from_single_config(config)
        tools = ToolRegistry()
        tools.register(FileManagerTool(str(tmp_path)))
        tools.register(LatexCompilerTool(str(tmp_path)))

        agent = AcademicAgent(
            work_dir=str(tmp_path),
            domain=domain,
            llm_router=router,
            tool_registry=tools,
        )

        research_topic = "A survey of transformer-based models for time series forecasting"

        events = []
        async for event in agent.run_auto(research_topic):
            events.append(event)
            if event.get("type") == "error":
                pytest.fail(f"Pipeline error: {event['content']}")

        # 验证产出物
        assert any(e["type"] == "phase_end" and e["success"] for e in events)
```

- [ ] **Step 2: 运行（需要 API key）**

```bash
OPENAI_API_KEY=sk-xxx python -m pytest backend/tests/e2e/ -v --tb=short
```

- [ ] **Step 3: 提交**

---

### Task 4.2: 补充缺失的模块测试

**Files:**
- Create: `backend/tests/test_knowledge_loader.py` — 测试 KnowledgeLoader
- Create: `backend/tests/test_latex_compiler.py` — 测试 LatexCompilerTool
- Create: `backend/tests/test_figure_generator.py` — 测试 FigureGeneratorTool
- Create: `backend/tests/test_api_auth.py` — 测试 API 认证端点

（每项 10+ 测试，略具体代码）

---

## 阶段五：打磨 — 文档、性能、发布（预计 2-3 天）

### Task 5.1: 项目文档

**Files:**
- Create: `docs/ARCHITECTURE.md`（已计划但未创建）
- Create: `docs/USER_GUIDE.md` — 用户使用指南
- Create: `docs/DOMAIN_DEVELOPMENT.md` — 如何创建新领域
- Modify: `README.md` — 更新为 v4.0 状态

### Task 5.2: 性能和健壮性

**Files:**
- Modify: `frontend/src/components/FileViewer.tsx` — 添加虚拟滚动（文件超过 100 个时）
- Modify: `backend/src/ultramath/llm/backend.py` — 添加 token 上下文窗口预检查
- Modify: `backend/src/ultramath/engine/agent.py` — 添加阶段超时配置

### Task 5.3: Electron 打包

**Files:**
- Modify: `frontend/package.json` — 确保 build 配置正确
- Modify: `frontend/electron/main.js` — 适配新路径

---

## 总结：执行路线

```
阶段一 (3-4天)        阶段二 (3-4天)        阶段三 (3-4天)
缝合集成 ──────────→ 充实领域 ──────────→ 前端对齐
                                                     │
阶段四 (2-3天)        阶段五 (2-3天)                 │
真实验证 ──────────→ 打磨发布 ←──────────────────┘
```

| 里程碑 | 验收标准 |
|--------|----------|
| M1: 缝合完成 | `curl /api/chat` 走 AcademicAgent；handoff 解析存入 context；TrustManager 记录反馈；文件隔离生效 |
| M2: 领域就绪 | paper-writing/lab-report/lit-review 各含 4+ prompts + phase handlers + LaTeX template |
| M3: 前端对齐 | phases/roles 从后端动态加载，不硬编码任何领域内容 |
| M4: 验证通过 | paper-writing 领域端到端跑通一个真实研究主题 |
| M5: 可发布 | docs 完整，Electron 可打包，Docker 可部署 |

**预估总工期：13-18 个工作日**
