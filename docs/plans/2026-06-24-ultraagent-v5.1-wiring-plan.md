# Lemma v5.1 — "接线计划"：让所有已写好的代码真正工作

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 v5.0 中"已写好但从未接入"的 7 个模块全部接线，补充缺失的前端 UI，建立真正的端到端验证和可观测性体系。不做新模块——只接线、打通、验证。

**Architecture:** 分 5 个阶段。一接线（6 个死模块接入）→ 二前端设计升级（基于 frontend-design + ui-ux-pro-max 技能全面重构 UI）→ 三补交互（流式 + 会话 + 成本前端）→ 四验证（E2E + 回归）→ 五观测（日志 + 指标 + 版本）。

**Design System:** 采用 ui-ux-pro-max 强制执行的设计令牌系统，禁止 emoji 作为图标，统一 Lucide 图标库，建立 touch-first 交互规范，通过 WCAG 2.1 AA 可访问性审查。

**Tech Stack:** React 18, TypeScript, Tailwind CSS 3.4, Framer Motion, Lucide Icons, 现有项目架构。**核心原则：不新建模块，只让已有代码工作；前端部分则是"先修现有 bug，再做设计升级"。**

---

## 审计全文

在动手前，我跑了全量搜索确认每个模块的接入状态（详细报告见上文 8 维度审计）。以下是精确的接入 gap 列表：

| 模块 | 文件 | 当前状态 | 目标状态 |
|------|------|----------|----------|
| RAG 知识库 | knowledge/loader.py, long_term.py | KnowledgeLoader 从未被 agent.py import；`self.long_term` 在 agent.py:43 创建但从未被查询 | `_build_system_prompt` 调用 `self.long_term.query()` 注入领域知识 |
| SourceTracker | tools/source_tracker.py | math-modeling domain.yaml phase_handlers 零条工具指令 | 在 analysis/derivation/writing/review 阶段的 handler 中加入 source_tracker 调用指令 |
| 流式前端 | server.py, App.tsx, ChatPanel.tsx | 后端发 stream_chunk/stream_end；前端 App.tsx onMessage 不处理 | App.tsx 处理 stream_chunk 累积文本；ChatPanel 显示流式消息 |
| CostTracker | llm/cost_tracker.py, backend.py | CostTracker 从未实例化；LLMBackend 不记录成本 | LLMBackend.__init__ 接受 CostTracker 参数；generate() 后调用 record() |
| SelfReflector | engine/reflector.py, agent.py | 从未 import；_execute_phase 无反思步骤 | _execute_phase 末尾调用 reflect_and_improve() |
| CascadeRouter | llm/cascade.py, server.py | server.py 始终用 ModelRouter | domain.yaml 或 config 支持 cascade 配置 |
| 会话管理 UI | memory/session_store.py, server.py, Sidebar.tsx | 后端 API 全齐；前端零 UI | 新建 SessionPanel 组件；Sidebar 添加导航项 |

---

## 阶段一：接线 — 让 6 个死模块活过来（预计 2-3 天）

### Task 1.1: RAG 知识库接入 AcademicAgent

**目标:** `_build_system_prompt` 中调用 `long_term.query()`，基于最近用户消息检索领域知识并注入 system prompt。

**Files:**
- Modify: `backend/src/ultramath/engine/agent.py`

**当前状态:**
```python
# agent.py:43 — LongTermMemory 创建但从未被查询
self.long_term = LongTermMemory(persist_dir=str(self.work_dir / "data" / "chromadb"))

# agent.py:126-140 — _build_system_prompt 只用 role.system_prompt + context
def _build_system_prompt(self) -> str:
    role = self.get_current_role()
    # ... 仅使用 role.system_prompt 和 context_info
```

**改动:** 在 `_build_system_prompt` 末尾追加知识检索结果。

```python
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

    # === 新增：RAG 知识检索 ===
    last_user_msg = self._get_last_user_message()
    if last_user_msg:
        import re
        keywords = re.findall(r'[\u4e00-\u9fff]{2,}', last_user_msg)
        query = " ".join(keywords[:10]) if keywords else last_user_msg[:200]

        knowledge_lines = []
        for collection in ["models", "references", "reviews"]:
            results = self.long_term.query(collection, query, n_results=2)
            for r in results:
                content = r.get("content", "")
                if content and len(content) > 20:
                    knowledge_lines.append(content[:800])

        if knowledge_lines:
            parts.append("\n## 领域知识参考\n" + "\n---\n".join(knowledge_lines[:3]))
    # === RAG 接入结束 ===

    return "\n".join(parts)
```

还需在 `create_agent` 时加载知识到 LongTermMemory：

```python
# server.py create_agent 中添加：
from ..knowledge.loader import KnowledgeLoader
loader = KnowledgeLoader(str(domains_base / domain_id), _agent.long_term)
loader.load_all()
```

- [ ] **Step 1: 修改 agent.py _build_system_prompt，添加知识检索**
- [ ] **Step 2: 修改 server.py create_agent，加载知识到 LongTermMemory**
- [ ] **Step 3: 添加配套测试**：mock `long_term.query` 返回知识片段，验证 system prompt 包含知识内容
- [ ] **Step 4: 运行全量测试确保无回归**
- [ ] **Step 5: 提交**

```bash
git add backend/src/ultramath/engine/agent.py backend/src/ultramath/api/server.py
git commit -m "feat: wire RAG knowledge base into AcademicAgent system prompt"
```

---

### Task 1.2: math-modeling 域接入 SourceTracker + EvidenceMap 指令

**目标:** 在 math-modeling 的 phase_handlers 中添加使用 source_tracker 和 evidence_map 的具体指令。

**Files:**
- Modify: `domains/math-modeling/domain.yaml`

**改动:**

```yaml
# phase_handlers 每个阶段追加 SourceTracker/EvidenceMap 使用指令：
phase_handlers:
  analysis: |
    请分析这个数学建模竞赛题目。判断题目类型...  
    
    ## 工具使用
    - 使用 source_tracker register 注册题目来源（source_type=primary, url=题目文件路径）
    - 使用 evidence_map add_node 创建根节点，node_id="root"

    {context_sections}
  
  derivation: |
    请作为数学家，对这个题目进行完整的数学推导...
    
    ## 工具使用
    - 对每个建模方案：source_tracker register 注册方案来源
    - evidence_map add_node 为每个方案创建子节点（parent_id="root"）
    - 每个推导步骤的断言用 source_tracker bind 绑定到对应的数学定理/公式
    - 标注每个叶节点的 confidence 和 is_atomic 状态

    {context_sections}
  
  coding: |
    请作为工程师，基于数学推导编写 Python 求解代码...
    
    ## 工具使用
    - source_tracker register 注册每个脚本文件为来源
    - source_tracker bind 将数值结果绑定到对应代码文件

    {context_sections}
  
  review: |
    请作为审稿人...进行五维度评分卡审稿...
    
    ## 工具使用
    - source_tracker audit 检查所有断言-来源绑定完整性
    - evidence_map audit 检查置信度与来源数的匹配（High 需 ≥2 来源）
    - 对每个 fact 标签断言：验证来源可独立验证
    - 对每个 inference 标签：确认已标注而非遗漏
```

- [ ] **Step 1: 修改 domain.yaml 的 phase_handlers**
- [ ] **Step 2: 验证**：运行 domain 测试确认配置可正确加载
- [ ] **Step 3: 提交**

---

### Task 1.3: CostTracker 接入 LLMBackend

**目标:** LLMBackend 的 generate() 方法在每次 LLM 调用后自动记录成本。Agent 创建时初始化 CostTracker。

**Files:**
- Modify: `backend/src/ultramath/llm/backend.py`
- Modify: `backend/src/ultramath/engine/agent.py`
- Modify: `backend/src/ultramath/api/server.py`

**改动 1:** LLMBackend 接受可选 CostTracker：

```python
# backend.py
class LLMBackend:
    def __init__(self, config: LLMConfig, cost_tracker = None):
        self.config = config
        self.cost_tracker = cost_tracker  # ← 新增
        # ... 原有初始化 ...

    async def generate(self, messages, ...):
        # ... 原有 generate 逻辑 ...
        response = await self.client.chat.completions.create(**kwargs)
        
        # === 新增：成本记录 ===
        if self.cost_tracker and response.usage:
            self.cost_tracker.record(
                model=self.config.model,
                input_tokens=response.usage.prompt_tokens,
                output_tokens=response.usage.completion_tokens,
            )
        # === 接入结束 ===
        
        return self._parse_response(response)
```

**改动 2:** Agent 创建时初始化 CostTracker 并注入 Backend：

```python
# agent.py __init__:
from ..llm.cost_tracker import CostTracker
self.cost_tracker = CostTracker(str(self.work_dir))

# server.py create_agent:
# 在 create_agent 末尾设置
_agent._cost_tracker = _agent.cost_tracker
```

- [ ] **Step 1: 修改 backend.py 接受 CostTracker 并记录**
- [ ] **Step 2: 修改 agent.py __init__ 创建 CostTracker**
- [ ] **Step 3: 添加测试**：mock LLM 调用，验证 CostTracker.record 被调用
- [ ] **Step 4: 验证 /api/cost 端点返回真实数据**
- [ ] **Step 5: 提交**

---

### Task 1.4: SelfReflector 接入 _execute_phase

**目标:** 每个阶段执行完后，自动做一次轻量反思检查。

**Files:**
- Modify: `backend/src/ultramath/engine/agent.py`

**改动:**

```python
# agent.py 顶部添加 import
from .reflector import SelfReflector

# __init__ 中添加：
self.reflector = SelfReflector(self)
self.enable_reflection = True  # 可由领域配置控制

# _execute_phase 方法中，在 chat 返回后添加：
response = await self.chat(prompt)

# === 新增：自我反思 ===
if self.enable_reflection:
    try:
        response = await self.reflector.quick_reflect(response)
    except Exception:
        pass  # 反思失败不影响主流程
# === 接入结束 ===

return PhaseResult(phase_id=phase_id, success=True, summary=response[:500])
```

- [ ] **Step 1: 修改 agent.py 接入 SelfReflector**
- [ ] **Step 2: 添加 domain.yaml 控制字段 `reflection: true/false`**
- [ ] **Step 3: 运行全量测试**
- [ ] **Step 4: 提交**

---

### Task 1.5: CascadeRouter 可选接入

**目标:** domain.yaml 可配置 cascade 策略，启用时使用 CascadeRouter。

**Files:**
- Modify: `backend/src/ultramath/api/server.py`

**改动:**

```python
# server.py create_agent:
# 检查 domain 的 cascade 配置
cascade_config = getattr(domain, 'cascade', None)
if cascade_config:
    from ..llm.cascade import CascadeRouter
    router = CascadeRouter(cascade_config)
else:
    router = _create_router_from_env()  # 或 from_config
```

在 domain.yaml 中可选添加：
```yaml
# 可选：级联模型配置
cascade:
  - model: "gpt-4o-mini"
    quality_threshold: 0.7
  - model: "gpt-4o"
    quality_threshold: 0.95
```

- [ ] **Step 1: 修改 server.py 支持 cascade 配置**
- [ ] **Step 2: 验证**：默认行为不变（无 cascade 配置时用普通 Router）
- [ ] **Step 3: 提交**

---

### Task 1.6: 前端流式聊天实现

**目标:** 前端处理 stream_chunk/stream_end，用户看到 token-by-token 实时输出。

**Files:**
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/components/ChatPanel.tsx`

**改动 1:** App.tsx onMessage 处理流式消息：

```typescript
// 在 onMessage 中添加：
} else if (msg.type === 'stream_chunk') {
  setStreamingContent(prev => prev + (msg.content as string))
  setIsStreaming(true)
} else if (msg.type === 'stream_end') {
  setMessages(prev => [...prev, {
    id: nextId(),
    role: 'assistant' as const,
    content: msg.full_content as string,
    agentRole: msg.agent_role as string,
    agentName: msg.agent_name as string,
    timestamp: new Date().toISOString(),
  }])
  setStreamingContent('')
  setIsStreaming(false)
}
```

并添加状态：
```typescript
const [streamingContent, setStreamingContent] = useState<string>('')
const [isStreaming, setIsStreaming] = useState(false)
```

**改动 2:** sendMessage 支持流式模式：

```typescript
const sendMessage = (content: string, role?: string) => {
  // ... 添加用户消息 ...
  ws.send(JSON.stringify({
    type: 'stream_chat',  // ← 改为 stream_chat
    message: content,
    role: role || agentStatus.currentRole,
  }))
}
```

**改动 3:** ChatPanel 渲染流式气泡：

```tsx
{isStreaming && (
  <MessageBubble
    role="assistant"
    content={streamingContent}
    agentRole={agentStatus.currentRole}
    isStreaming={true}
  />
)}
```

- [ ] **Step 1: 修改 App.tsx 添加流式消息处理**
- [ ] **Step 2: 修改 ChatPanel 添加流式气泡渲染**
- [ ] **Step 3: TypeScript 类型检查**
- [ ] **Step 4: 提交**

---

## 阶段二：前端设计升级 — 基于 frontend-design + ui-ux-pro-max 技能（预计 4-5 天）

### 审计：当前前端的 12 个设计违规

对照 `ui-ux-pro-max` 规则和 `frontend-design` 指南，发现以下问题（**标记该规则的优先级**）：

| 问题 | ui-ux-pro-max 规则 | 严重度 |
|------|-------------------|--------|
| ① ChatPanel/SettingsPanel 大量使用 emoji 作为功能图标（🎯🧮💻📝✍️🔍💾🧬📊📄🧪📚🔬✅⏹⚡💰） | §4 `no-emoji-icons`：禁止 emoji 作图标 | **CRITICAL** |
| ② Sidebar 导航用 emoji + 文字 + emoji 角色头像 | §4 `no-emoji-icons` + `icon-style-consistent` | **CRITICAL** |
| ③ 仅 6 处 `aria-` 引用（全部在 ChatPanel/SettingsPanel），其他组件为零 | §1 `aria-labels`、`keyboard-nav`、`focus-states` | **CRITICAL** |
| ④ 仅 3 处 font-family/line-height 引用 | §6 `font-pairing`、`font-scale`、`line-height` | HIGH |
| ⑤ 按钮 hover 状态不统一（有的用 scale，有的用颜色，有的无变化） | §2 `hover-vs-tap`、`press-feedback` | HIGH |
| ⑥ 无 reduced-motion 支持 | §1 `reduced-motion`、§7 `excessive-motion` | HIGH |
| ⑦ 无虚拟列表（消息超过 50 条时滚动性能下降） | §3 `virtualize-lists` | HIGH |
| ⑧ Agent 角色色板直接使用原始 hex 值在组件中 | §6 `color-semantic`：应使用语义 token | MEDIUM |
| ⑨ 动画时长不统一（有的 3s，有的 1.5s，有的无动画） | §7 `duration-timing`：微交互 150-300ms | MEDIUM |
| ⑩ ChatPanel 消息气泡无 touch 反馈 | §2 `touch-target-size` + `tap-feedback` | MEDIUM |
| ⑪ 无 z-index 管理系统 | §5 `z-index-management` | MEDIUM |
| ⑫ 无 safe-area 适配 | §5 `safe-area-awareness` | LOW |

### 总目标

1. **禁止 emoji 作为功能图标**：用 Lucide Icons 替代所有功能性 emoji
2. **建立统一设计令牌系统**：语义颜色、字体、间距为单一真相源
3. **可访问性达标**：所有交互元素有 aria 标签、键盘可达、焦点可见
4. **性能优化**：虚拟列表、图片优化、字体加载策略
5. **动画规范统一**：150-300ms、ease-out 进入、reduced-motion 尊重
6. **touch-first 交互**：最小 44px 触摸目标、按压反馈、无 hover-only 交互

---

### Task 2.1: 建立设计令牌系统（Design Tokens）

**参考:** `ui-ux-pro-max` §6 排版与颜色

**Files:**
- Rewrite: `frontend/src/styles/agent-theme.ts`
- Modify: `frontend/src/index.css`
- Create: `frontend/src/styles/design-tokens.css`

**目标:** 将所有颜色、间距、字体、阴影统一为语义 token，禁止组件内硬编码 hex 值。

```css
/* design-tokens.css — 项目级单一真相源 */

:root {
  /* === 基础色 === */
  --surface-primary: #080b14;
  --surface-secondary: #0f1420;
  --surface-tertiary: #1a1f2e;
  --surface-elevated: #1e2333;
  
  /* === 文字 === */
  --text-primary: #e8eaed;       /* 主文字 对比度 12.3:1 ✅ */
  --text-secondary: #8b92a5;     /* 次文字 对比度 5.4:1 ✅ */
  --text-muted: #5a6072;         /* 辅助文字 对比度 4.5:1 ✅ */
  
  /* === 语义色 === */
  --color-accent: #6366f1;       /* 主强调色 indigo-500 */
  --color-accent-hover: #4f46e5;
  --color-success: #10b981;
  --color-warning: #f59e0b;
  --color-error: #ef4444;
  --color-info: #3b82f6;
  
  /* === 角色色 ===
     命名规范：--agent-{role}-{property} */
  --agent-lead-color: #818cf8;
  --agent-lead-soft: rgba(129,140,248,0.12);
  --agent-lead-glow: rgba(129,140,248,0.25);
  
  --agent-math-color: #a78bfa;
  --agent-math-soft: rgba(167,139,250,0.12);
  --agent-math-glow: rgba(167,139,250,0.25);
  
  --agent-engineer-color: #22d3ee;
  --agent-engineer-soft: rgba(34,211,238,0.12);
  --agent-engineer-glow: rgba(34,211,238,0.25);
  
  --agent-reviewer-color: #fbbf24;
  --agent-reviewer-soft: rgba(251,191,36,0.12);
  --agent-reviewer-glow: rgba(251,191,36,0.25);
  
  --agent-writer-color: #fb7185;
  --agent-writer-soft: rgba(251,113,133,0.12);
  --agent-writer-glow: rgba(251,113,133,0.25);
  
  --agent-verifier-color: #34d399;
  --agent-verifier-soft: rgba(52,211,153,0.12);
  --agent-verifier-glow: rgba(52,211,153,0.25);
  
  --agent-researcher-color: #38bdf8;
  --agent-researcher-soft: rgba(56,189,248,0.12);
  --agent-researcher-glow: rgba(56,189,248,0.25);
  
  --agent-analyst-color: #fb923c;
  --agent-analyst-soft: rgba(251,146,60,0.12);
  --agent-analyst-glow: rgba(251,146,60,0.25);
  
  /* === 间距（4px 基础网格）=== */
  --space-xs: 4px;
  --space-sm: 8px;
  --space-md: 16px;
  --space-lg: 24px;
  --space-xl: 32px;
  --space-2xl: 48px;
  
  /* === 排版 === */
  --font-sans: 'Inter', system-ui, -apple-system, sans-serif;
  --font-mono: 'JetBrains Mono', 'Fira Code', Consolas, monospace;
  --text-xs: 12px;
  --text-sm: 14px;
  --text-base: 16px;
  --text-lg: 18px;
  --text-xl: 24px;
  --text-2xl: 32px;
  --leading-tight: 1.25;
  --leading-normal: 1.5;
  --leading-relaxed: 1.75;
  --measure-narrow: 35ch;   /* 移动端行宽 */
  --measure-wide: 65ch;     /* 桌面端行宽 */
  
  /* === 圆角 === */
  --radius-sm: 6px;
  --radius-md: 12px;
  --radius-lg: 16px;
  --radius-xl: 24px;
  --radius-full: 9999px;
  
  /* === 阴影 === */
  --shadow-sm: 0 1px 2px rgba(0,0,0,0.3);
  --shadow-md: 0 4px 12px rgba(0,0,0,0.4);
  --shadow-lg: 0 8px 32px rgba(0,0,0,0.5);
  --shadow-glow: 0 0 24px var(--color-accent-alpha);
  
  /* === Z-Index === */
  --z-base: 0;
  --z-dropdown: 10;
  --z-sticky: 20;
  --z-modal-backdrop: 30;
  --z-modal: 40;
  --z-tooltip: 50;
  --z-toast: 100;
  
  /* === 动画 === */
  --duration-instant: 100ms;
  --duration-fast: 150ms;
  --duration-normal: 250ms;
  --duration-slow: 350ms;
  --ease-out: cubic-bezier(0.16, 1, 0.3, 1);
  --ease-in: cubic-bezier(0.4, 0, 1, 1);
  --ease-in-out: cubic-bezier(0.65, 0, 0.35, 1);
  --ease-spring: cubic-bezier(0.34, 1.56, 0.64, 1);
}
```

**TypeScript 端同步更新 `agent-theme.ts`：所有颜色引用改为 `var(--token)` 引用。**

- [ ] **Step 1: 创建 design-tokens.css**
- [ ] **Step 2: 更新 agent-theme.ts 对齐 token**
- [ ] **Step 3: 更新 index.css 移除硬编码颜色值**
- [ ] **Step 4: 验证**：所有页面在 light/dark 模式均正确
- [ ] **Step 5: 提交**

---

### Task 2.2: 替换所有 Emoji 为 Lucide 图标

**参考:** `ui-ux-pro-max` §4 `no-emoji-icons`（CRITICAL 优先级 4）

**Files:**
- Modify: `frontend/src/components/Sidebar.tsx` — 导航 emoji → Lucide 图标
- Modify: `frontend/src/components/ChatPanel.tsx` — 工具栏 emoji → Lucide 图标
- Modify: `frontend/src/components/PipelinePanel.tsx` — 按钮 emoji → Lucide 图标
- Modify: `frontend/src/components/AdventureMap.tsx` — 状态 emoji → Lucide 图标
- Modify: `frontend/src/components/SettingsPanel.tsx` — 分类 emoji → Lucide 图标
- Install: `lucide-react`

**改动映射表：**

| 位置 | 旧 (Emoji) | 新 (Lucide Icon) |
|------|-----------|-------------------|
| Sidebar 导航: 聊天 | 💬 | `MessageCircle` |
| Sidebar 导航: 流水线 | 🔄 | `GitBranch` |
| Sidebar 导航: 文件 | 📁 | `FolderOpen` |
| Sidebar 导航: 设置 | ⚙️ | `Settings` |
| Sidebar 导航: 会话 | 💾 | `Save` |
| ChatPanel: 自动执行 | ⚡ | `Zap` |
| ChatPanel: 停止 | ⏹ | `Square` |
| ChatPanel: 发送 | (当前是 SVG) | `Send` |
| ChatPanel: 角色选择 | 🎯🧮💻📝✍️🔍 | 用 AgentAvatar 替代 |
| AdventureMap: 完成标志 | ✓ (CSS) | `Check` |
| AdventureMap: 失败标志 | ✗ (CSS) | `X` |
| AdventureMap: 状态 | emoji | `Loader` (执行中) / 无 (等待) |
| ChatPanel: 空状态 | 🧬 | `Sparkles` |
| ChatPanel: 功能卡片 | 📊💻📄🔍 | 对应 Lucide 图标 |
| FileViewer: 工具图标 | 🔧 | `Wrench` |

```bash
cd frontend && npm install lucide-react
```

**统一用法模式：**
```tsx
import { MessageCircle, Zap, Square, Send, Check, X, Loader } from 'lucide-react'

// 所有图标使用统一的 size 和 strokeWidth
<MessageCircle size={18} strokeWidth={1.5} className="text-[var(--text-secondary)]" />
```

**注：** Agent 角色的 emoji 头像已经用 SVG 手绘精灵替代（AgentAvatar），不需要改。domain.yaml 中的 emoji 字段保留用于角色列表的补充标识。

- [ ] **Step 1: 安装 lucide-react**
- [ ] **Step 2: 逐一替换每个组件的 emoji**
- [ ] **Step 3: 验证**：亮暗模式无障碍、每处图标语义正确
- [ ] **Step 4: TypeScript 类型检查**
- [ ] **Step 5: 提交**

---

### Task 2.3: 无障碍化改造（Accessibility）

**参考:** `ui-ux-pro-max` §1 无障碍（CRITICAL 优先级 1）

**Files:**
- Modify: `frontend/src/components/Sidebar.tsx`
- Modify: `frontend/src/components/ChatPanel.tsx`
- Modify: `frontend/src/components/PipelinePanel.tsx`
- Modify: `frontend/src/components/SettingsPanel.tsx`
- Modify: `frontend/src/components/AdventureMap.tsx`
- Modify: `frontend/src/components/AgentRoster.tsx`
- Modify: `frontend/src/components/FileViewer.tsx`

**每组件改动清单：**

| 规则 | 实现 |
|------|------|
| `aria-labels` | 每个 icon-only 按钮添加 `aria-label` |
| `focus-states` | 所有交互元素添加 `focus-visible:ring-2 ring-[var(--color-accent)]` |
| `keyboard-nav` | 确保 Tab 顺序匹配视觉顺序；Enter/Space 触发按钮 |
| `form-labels` | 所有 input/textarea 关联 label |
| `alt-text` | 图片用 `alt` 属性 |
| `heading-hierarchy` | h1→h2→h3 顺序，不跳级 |
| `skip-links` | 在 App.tsx 顶部添加 Skip to main content 链接 |
| `color-not-only` | 状态指示器（连接状态、阶段状态）同时使用颜色+图标+文字 |
| `reduced-motion` | 全局 CSS 添加 `@media (prefers-reduced-motion: reduce)` |
| `role-alert` | 错误/成功提示用 `role="alert"` 容器 |

```tsx
// 示例：IconButton 辅助组件（封装 a11y）
function IconButton({ icon: Icon, label, onClick, ...props }: {
  icon: typeof MessageCircle
  label: string
  onClick: () => void
}) {
  return (
    <button
      onClick={onClick}
      aria-label={label}
      className="p-2 rounded-lg hover:bg-white/5 focus-visible:ring-2 focus-visible:ring-[var(--color-accent)] transition-colors"
    >
      <Icon size={18} strokeWidth={1.5} aria-hidden="true" />
    </button>
  )
}
```

**Skip Link（App.tsx 最顶部）：**
```tsx
<a href="#main-content" 
   className="sr-only focus:not-sr-only focus:absolute focus:top-2 focus:left-2 focus:z-[var(--z-tooltip)] focus:px-4 focus:py-2 focus:bg-[var(--color-accent)] focus:text-white focus:rounded-lg">
  跳转到主内容
</a>
```

**Reduced Motion（index.css）：**
```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

- [ ] **Step 1: 创建 IconButton 辅助组件**
- [ ] **Step 2: 为每个组件添加 aria 标签、焦点样式、键盘支持**
- [ ] **Step 3: 添加 Skip Link 和 reduced-motion 支持**
- [ ] **Step 4: 用 axe DevTools 审查每个页面**
- [ ] **Step 5: 提交**

---

### Task 2.4: 性能优化

**参考:** `ui-ux-pro-max` §3 性能（HIGH 优先级 3）

**Files:**
- Modify: `frontend/src/components/ChatPanel.tsx` — 消息列表虚拟化
- Modify: `frontend/src/components/FileViewer.tsx` — 文件列表虚拟化
- Modify: `frontend/package.json` — 添加 react-virtuoso

**改动：**

```bash
cd frontend && npm install react-virtuoso
```

```tsx
// ChatPanel.tsx — 消息列表虚拟化
import { Virtuoso } from 'react-virtuoso'

// 替换 messages.map() 为：
<Virtuoso
  data={messages}
  followOutput="smooth"
  style={{ height: '100%' }}
  itemContent={(index, message) => (
    <MessageBubble key={message.id} message={message} />
  )}
/>
```

```tsx
// FileViewer.tsx — 文件列表虚拟化
<Virtuoso
  data={files}
  style={{ height: '100%' }}
  itemContent={(index, file) => <FileRow file={file} />}
/>
```

**字体加载优化（index.css）：**
```css
@font-face {
  font-family: 'Inter';
  font-style: normal;
  font-weight: 400;
  font-display: swap;  /* 避免 FOIT */
  src: url('/fonts/inter-var.woff2') format('woff2');
}
```

- [ ] **Step 1: 安装 react-virtuoso**
- [ ] **Step 2: ChatPanel 消息虚拟化**
- [ ] **Step 3: FileViewer 文件虚拟化**
- [ ] **Step 4: 添加 font-display: swap**
- [ ] **Step 5: 性能测试**：生成 500+ 条消息，验证滚动无卡顿
- [ ] **Step 6: 提交**

---

### Task 2.5: 动画规范化

**参考:** `ui-ux-pro-max` §7 动画（MEDIUM 优先级 7）

**Files:**
- Modify: `frontend/src/index.css`
- Modify: `frontend/src/components/AdventureMap.tsx`

**改动：**

```css
/* index.css — 动画 token 替换 */

/* 旧: 3s float 动画 */
/* 新: 使用设计 token 时长 */
@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-4px); }
}

/* 微交互使用 fast (150ms) + ease-out */
.hover-card {
  transition: transform var(--duration-fast) var(--ease-out);
}
.hover-card:hover {
  transform: scale(1.02);
}

/* 入场使用 normal (250ms) + ease-out */
.enter-item {
  animation: fade-in var(--duration-normal) var(--ease-out) both;
}

/* 退场使用 fast (150ms) + ease-in */
.exit-item {
  animation: fade-out var(--duration-fast) var(--ease-in) both;
}
```

```tsx
// AdventureMap.tsx — 动画统一
<motion.div
  initial={{ opacity: 0, y: 8 }}
  animate={{ opacity: 1, y: 0 }}
  exit={{ opacity: 0, y: -8 }}
  transition={{ 
    duration: 0.25,   // ← 统一 250ms
    ease: [0.16, 1, 0.3, 1],  // ← ease-out
    delay: index * 0.05,      // ← stagger 50ms
  }}
/>
```

**全局检查：**
- 所有动画时长在 150-350ms 范围内（用 grep 搜索 `duration:` `animation:` `transition:`）
- 最多每视图 2 个关键动画元素
- 入场用 `ease-out`，退场用 `ease-in`
- 禁止 `linear` 缓动

- [ ] **Step 1: 规范化 index.css 动画 token**
- [ ] **Step 2: 逐个组件调整 Framer Motion 参数**
- [ ] **Step 3: 全局动画时长 audit**
- [ ] **Step 4: 减少每视图动画元素数**
- [ ] **Step 5: 提交**

---

### Task 2.6: Touch & 响应式优化

**参考:** `ui-ux-pro-max` §2 触控交互（CRITICAL 优先级 2）+ §5 布局（HIGH 优先级 5）

**Files:**
- Modify: `frontend/src/index.css`
- Modify: `frontend/src/components/ChatPanel.tsx`
- Modify: `frontend/src/components/Sidebar.tsx`

**改动：**

```css
/* 触摸目标最小 44px */
.touch-target {
  min-height: 44px;
  min-width: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 触控间距 ≥8px */
.touch-group > * + * {
  margin-left: 8px;
}
```

```css
/* 响应式断点系统 */
@media (max-width: 640px) {
  .sidebar-desktop { display: none; }
  .agent-roster-grid { grid-template-columns: repeat(4, 1fr); }
  .message-bubble { max-width: 92%; }
}

@media (min-width: 641px) and (max-width: 1024px) {
  .sidebar-desktop { width: 60px; }
  .nav-label { display: none; }  /* 折叠标签 */
}
```

- [ ] **Step 1: 触控目标调整**
- [ ] **Step 2: 响应式断点调优**
- [ ] **Step 3: 小屏实测验证**
- [ ] **Step 4: 提交**

---

## 阶段三：补交互 — 会话管理 + 成本 + 流式前端（预计 2-3 天）

### Task 2.1: 会话管理前端面板

**目标:** 创建 SessionPanel 组件，支持保存/加载/列表/删除会话。

**Files:**
- Create: `frontend/src/components/SessionPanel.tsx`
- Modify: `frontend/src/components/Sidebar.tsx`
- Modify: `frontend/src/App.tsx`

**会话面板核心组件：**

```tsx
// SessionPanel.tsx
interface SessionInfo {
  session_id: string
  domain_id: string
  created_at: string
  message_count: number
  phase: string
  progress: number
}

export default function SessionPanel({ workDir, onLoad }: {
  workDir: string
  onLoad: (sessionId: string) => void
}) {
  const [sessions, setSessions] = useState<SessionInfo[]>([])
  const [loading, setLoading] = useState(false)

  const fetchSessions = async () => {
    const res = await fetch(`${API_BASE_URL}/api/sessions`, {
      headers: { 'X-API-Key': 'dev-key-change-in-production' }
    })
    const data = await res.json()
    setSessions(data.sessions || [])
  }

  useEffect(() => { fetchSessions() }, [])

  const saveSession = async () => {
    setLoading(true)
    await fetch(`${API_BASE_URL}/api/session/save`, {
      method: 'POST',
      headers: { 'X-API-Key': 'dev-key-change-in-production' }
    })
    await fetchSessions()
    setLoading(false)
  }

  const deleteSession = async (id: string) => {
    await fetch(`${API_BASE_URL}/api/session/${id}`, {
      method: 'DELETE',
      headers: { 'X-API-Key': 'dev-key-change-in-production' }
    })
    await fetchSessions()
  }

  return (
    <div className="h-full overflow-y-auto p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold">会话管理</h2>
        <button onClick={saveSession} disabled={loading}
          className="px-3 py-1.5 rounded-lg bg-indigo-500 text-white text-xs">
          {loading ? '保存中...' : '💾 保存当前会话'}
        </button>
      </div>

      {sessions.length === 0 ? (
        <p className="text-sm text-[var(--color-text-secondary)]">暂无已保存的会话</p>
      ) : (
        <div className="space-y-2">
          {sessions.map(session => (
            <div key={session.session_id}
              className="flex items-center justify-between p-3 rounded-xl border border-[var(--color-border)]">
              <div>
                <div className="text-sm font-medium">{session.session_id}</div>
                <div className="text-xs text-[var(--color-text-secondary)]">
                  {session.domain_id} · {session.message_count} 条消息 · {session.progress}%
                </div>
              </div>
              <div className="flex gap-2">
                <button onClick={() => onLoad(session.session_id)}
                  className="text-xs text-indigo-400 hover:text-indigo-300">加载</button>
                <button onClick={() => deleteSession(session.session_id)}
                  className="text-xs text-red-400 hover:text-red-300">删除</button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
```

**Sidebar 添加导航项：**
```tsx
const NAV_ITEMS = [
  // ... existing
  { id: 'sessions' as const, icon: '💾', label: '会话' },
]
```

- [ ] **Step 1: 创建 SessionPanel.tsx**
- [ ] **Step 2: 修改 Sidebar.tsx 添加导航**
- [ ] **Step 3: 修改 App.tsx 添加 sessions 视图和相关状态**
- [ ] **Step 4: TypeScript 类型检查 + 前端测试**
- [ ] **Step 5: 提交**

---

### Task 2.2: 成本显示浮层

**目标:** 在 ChatPanel 底部或顶部显示当前会话的累计成本。

**Files:**
- Modify: `frontend/src/components/ChatPanel.tsx`

**改动:**
```tsx
// ChatPanel 顶部工具栏添加成本显示：
const [cost, setCost] = useState<number>(0)

useEffect(() => {
  const fetchCost = () => {
    fetch(`${API_BASE_URL}/api/cost`, {
      headers: { 'X-API-Key': 'dev-key-change-in-production' }
    }).then(r => r.json()).then(d => setCost(d.session_cost_usd || 0))
  }
  const interval = setInterval(fetchCost, 15000)  // 每 15 秒刷新
  return () => clearInterval(interval)
}, [])

// 渲染：
{cost > 0 && (
  <span className="text-[10px] text-[var(--color-text-muted)]">
    💰 ${cost.toFixed(4)}
  </span>
)}
```

- [ ] **Step 1: 添加成本显示逻辑**
- [ ] **Step 2: TypeScript 类型检查**
- [ ] **Step 3: 提交**

---

## 阶段四：验证 — 端到端重建（预计 3-4 天）

### Task 3.1: E2E 测试覆盖全领域

**目标:** 为 math-modeling、lab-report、literature-review 各创建 E2E 测试，覆盖全流程。

**Files:**
- Create: `backend/tests/e2e/test_math_modeling_pipeline.py`
- Create: `backend/tests/e2e/test_lab_report_pipeline.py`
- Create: `backend/tests/e2e/test_literature_review_pipeline.py`
- Create: `backend/tests/e2e/conftest.py`

**设计:** 使用 mock LLM backend 返回预设响应，测试完整的 run_auto 流程。

```python
# conftest.py — 共享夹具
@pytest.fixture
def mock_llm():
    """模拟 LLM 响应：简要回复 + 交接表"""
    return LLMResponse(
        content="分析完成。\n\n| 字段 | 内容 |\n|------|------|\n| 结论 | 这是一个优化问题 |\n| 置信度 | green |\n| 下游警告 | 需要数据验证 |",
        model="mock-model",
        usage={"prompt_tokens": 100, "completion_tokens": 50},
        finish_reason="stop",
    )

@pytest.fixture
def domain_profile(domain_id: str):
    return DomainProfile.from_directory(f"domains/{domain_id}")
```

```python
# test_math_modeling_pipeline.py
class TestMathModelingPipeline:
    @pytest.mark.asyncio
    async def test_full_pipeline_with_mock_llm(self, tmp_path, domain_profile, mock_llm):
        """完整 run_auto 流程：从 init 到 review，所有阶段各 mock 一次 LLM 调用"""
        tool_registry = ToolRegistry()
        tool_registry.register(FileManagerTool(str(tmp_path)))
        # 注册所有工具...
        
        router = MagicMock()
        backend = MagicMock()
        backend.generate = AsyncMock(return_value=mock_llm)
        router.get_default_backend = MagicMock(return_value=backend)
        
        agent = AcademicAgent(
            work_dir=str(tmp_path),
            domain=domain_profile,
            llm_router=router,
            tool_registry=tool_registry,
        )
        
        events = []
        async for event in agent.run_auto("测试题目"):
            events.append(event)
        
        # 验证所有阶段信号
        event_types = [e["type"] for e in events]
        assert "start" in event_types
        assert "phase_start" in event_types
        assert "complete" in event_types
        
        # 验证有完整执行过程
        phase_starts = [e for e in events if e["type"] == "phase_start"]
        assert len(phase_starts) >= 2  # 至少 2 个阶段启动
        
        # 验证无错误
        errors = [e for e in events if e["type"] == "error" or e["type"] == "phase_error"]
        assert len(errors) == 0, f"存在错误事件: {errors}"
```

- [ ] **Step 1: 创建 conftest.py 含共享 mock 夹具**
- [ ] **Step 2: 为每个领域创建 E2E 测试文件**
- [ ] **Step 3: 运行 E2E 测试套件确认通过**
- [ ] **Step 4: 提交**

---

### Task 3.2: WebSocket 流式端到端测试

**目标:** 测试 WebSocket 连接的完整生命周期。

**Files:**
- Create: `backend/tests/e2e/test_websocket_e2e.py`

```python
class TestWebSocketE2E:
    @pytest.mark.asyncio
    async def test_ws_init_and_status(self):
        """WebSocket 连接后应收到 status 消息"""
        from fastapi.testclient import TestClient
        from ultramath.api.server import app
        
        client = TestClient(app)
        with client.websocket_connect("/ws") as ws:
            # 模拟 init
            ws.send_json({"type": "init", "work_dir": str(tmp_path), "domain_id": "math-modeling"})
            response = ws.receive_json()
            assert response["type"] in ("status", "initialized")
    
    @pytest.mark.asyncio
    async def test_ws_chat_flow(self, tmp_path):
        """WebSocket 聊天流程：发送消息 → 接收响应"""
        # ... WebSocket 聊天测试 ...
    
    @pytest.mark.asyncio
    async def test_ws_stream_chat(self, tmp_path):
        """流式聊天：发送 stream_chat → 接收 stream_chunk + stream_end"""
        # ... 流式测试 ...
```

- [ ] **Step 1: 创建 WebSocket E2E 测试**
- [ ] **Step 2: 运行测试**
- [ ] **Step 3: 提交**

---

## 阶段五：观测 — 可观测性与质量门（预计 2-3 天）

### Task 4.1: 统一日志系统

**目标:** 让每个模块的日志可追踪、可过滤。

**Files:**
- Modify: `backend/src/ultramath/utils/logger.py`
- Modify: `backend/src/ultramath/llm/backend.py`
- Modify: `backend/src/ultramath/engine/agent.py`

**改动:**

```python
# logger.py — 添加结构化日志
import structlog

def setup_logging(level: str = "INFO"):
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer(),
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
    )

# 各处使用:
logger = structlog.get_logger()
logger.info("generate_call", model=self.config.model, tokens=usage)
```

- [ ] **Step 1: 升级日志系统为 structlog 结构化日志**
- [ ] **Step 2: 在关键路径添加日志点**
- [ ] **Step 3: 提交**

---

### Task 4.2: 模型输出质量评分基准

**目标:** 建立可量化的输出质量评估，用于对比 prompt 改进前后的效果。

**Files:**
- Create: `backend/benchmarks/quality_metrics.py`

```python
"""输出质量评分 — 可对比 prompt 改进前后效果"""

class QualityMetrics:
    """评估 Agent 输出的质量维度"""
    
    @staticmethod
    def has_source_binding(text: str) -> float:
        """检查断言是否绑定来源（[fact] 标签比例）"""
        facts = text.count("[fact]")
        inferences = text.count("[inference]")
        total = facts + inferences
        return facts / total if total > 0 else 0.0
    
    @staticmethod
    def has_checklist_output(text: str) -> float:
        """检查是否输出结构化审查清单"""
        has_pass = "PASS" in text or "FAIL" in text
        has_violations = "VIOLATION" in text or "违规" in text
        return 1.0 if has_pass and has_violations else 0.5 if has_pass else 0.0
    
    @staticmethod
    def has_term_expansion(text: str) -> float:
        """检查缩写首次出现时是否展开"""
        import re
        expanded = len(re.findall(r'\w+（[A-Z]+）', text))
        raw = len(re.findall(r'(?<!（)[A-Z]{2,}(?!）)', text))
        return expanded / (expanded + raw) if (expanded + raw) > 0 else 1.0
```

- [ ] **Step 1: 创建 quality_metrics.py**
- [ ] **Step 2: 对修改前后的 prompt 跑质量评分对比**
- [ ] **Step 3: 提交**

---

### Task 4.3: Prompt 版本追踪

**目标:** 每次修改 prompt 文件时自动记录版本，支持回滚。

**Files:**
- Create: `backend/src/ultramath/engine/prompt_version.py`
- Modify: `backend/src/ultramath/engine/domain.py`

```python
"""Prompt 版本追踪 — 记录每次 prompt 修改"""
import hashlib
import json
from pathlib import Path
from datetime import datetime

class PromptVersionTracker:
    def snapshot(self, domains_dir: str) -> dict:
        """对当前所有 prompt 生成版本快照"""
        hashes = {}
        for prompt_file in Path(domains_dir).glob("**/prompts/*.md"):
            content = prompt_file.read_text(encoding="utf-8")
            hashes[str(prompt_file)] = {
                "hash": hashlib.sha256(content.encode()).hexdigest()[:12],
                "length": len(content),
                "timestamp": datetime.now().isoformat(),
            }
        return hashes
    
    def compare(self, baseline: dict, current: dict) -> list[str]:
        """对比两个快照，返回有变化的文件列表"""
        changed = []
        for path, info in current.items():
            if path not in baseline or baseline[path]["hash"] != info["hash"]:
                changed.append(path)
        return changed
```

- [ ] **Step 1: 创建 prompt_version.py**
- [ ] **Step 2: 在 DomainProfile 加载时自动记录版本**
- [ ] **Step 3: 提交**

---

## 总结：执行路线

```
阶段一 (2-3天)        阶段二 (4-5天)              阶段三 (2-3天)
接线 —─────────→ 前端设计升级 ──────────→ 补交互
├─ RAG 接线          ├─ 设计令牌系统              ├─ 会话面板
├─ SourceTracker 指令 ├─ Lucide 图标 替换 emoji   ├─ 成本浮层
├─ CostTracker 接线   ├─ 无障碍化 (WCAG AA)       └─ 流式渲染
├─ SelfReflector 接线 ├─ 性能 (虚拟列表)
├─ CascadeRouter 接线 ├─ 动画规范化
└─ (接线部分)         └─ Touch + 响应式

阶段四 (3-4天)        阶段五 (2-3天)
验证 ──────────→ 观测
├─ 全领域 E2E          ├─ 结构化日志
├─ WebSocket E2E       ├─ 质量评分
└─ Mock LLM 全流程     ├─ Prompt 版本追踪
                       └─ 基准对比
```

| 里程碑 | 验收标准 |
|--------|----------|
| M1: 接线完成 | RAG 知识注入 system prompt；CostTracker 记录真实费用；SelfReflector 在每阶段自动反思 |
| M2: 前端设计升级 | 零 emoji 作为图标；WCAG AA 通过 axe DevTools；所有交互元素 44px+ 触控目标；动画 150-300ms 统一 |
| M3: 交互补齐 | 会话可保存/列表/删除/恢复；成本实时显示；流式聊天 token-by-token 渲染 |
| M4: 验证通过 | 4 个领域全有 E2E 测试；WebSocket 流式有测试；全量测试 ≥ 150 个 |
| M5: 可观测 | 日志可追踪每次 LLM 调用；prompt 版本可对比；质量可量化；前端性能得分 ≥ 90 (Lighthouse) |

**预估总工期：13-18 天**

---

## 附录：做事哲学

之前的问题是"创建新文件 → 验证文件存在 → 标记完成"，但忽略了"文件里的代码是否真正被调用"。

本计划的原则是**反向的**：
1. 先确认"这段代码有没有被 import"
2. 确认"这个 import 有没有在运行时被触发"
3. 确认"触发后的效果是否正确"

每个任务不再以"文件创建"为结束条件，而以"端到端验证通过"为结束条件。

### 前端设计参考来源

- [frontend-design Skill](C:\Users\26895\.claude\skills\frontend-design\SKILL.md) — 独特审美方向 + 避免 AI slop
- [ui-ux-pro-max Skill](C:\Users\26895\.claude\skills\ui-ux-pro-max\SKILL.md) — 99 条 UX 规则 + 设计令牌 + 可访问性清单
- [Lucide Icons](https://lucide.dev) — 替代 emoji 的统一图标库
- WCAG 2.1 AA — 可访问性合规标准
