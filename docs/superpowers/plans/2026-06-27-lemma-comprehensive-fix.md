# Lemma v5.2.0 全面修复实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修复审计报告中发现的 38 个问题，使 Lemma 桌面应用可启动、可运行、可用，统一品牌和设计系统。

**Architecture:** 按优先级 6 个阶段修复：P0 让应用跑起来 → P1 修复核心功能 → P2 清理架构 → P3 补全缺失 UI → P4 测试与打磨 → P5 构建与部署。每个阶段独立可验证，阶段内任务可并行。

**Tech Stack:** Python 3.11+ (FastAPI), TypeScript 5.5 (React 18 + Vite 5), Electron 31, Tailwind CSS 3.4

**审计基准:** 详见审计报告 38 个问题，6 大分类。

---

## Phase 0: 让应用跑起来（致命问题 — 3 个任务，预估 15 分钟）

### Task 0.1: 修复 start.py 包名引用

**Files:**
- Modify: `backend/start.py:27`

- [ ] **Step 1: 替换旧的包名引用**

```python
# backend/start.py:27 — 将
uvicorn.run(
    "ultramath.api.server:app",
    host=host,
    port=port,
    reload=True,
    log_level="info",
)

# 改为
uvicorn.run(
    "lemma.api.server:app",
    host=host,
    port=port,
    reload=True,
    log_level="info",
)
```

- [ ] **Step 2: 同时更新版本号字符串（第19行 `v1.0.0` → `v5.2.0`）**

```python
# backend/start.py:19 — 将
║  UltraMath Agent Backend v1.0.0              ║

# 改为
║  Lemma Backend v5.2.0                        ║
```

- [ ] **Step 3: 验证后端可启动**

```bash
cd E:\数学建模agent\backend
python start.py
# 预期：uvicorn 成功启动，访问 http://127.0.0.1:8765/api/health 返回 {"status":"ok","version":"5.1.0"}
```

- [ ] **Step 4: Commit**

```bash
git add backend/start.py
git commit -m "fix: update start.py to use lemma package name and v5.2.0"
```

---

### Task 0.2: 修复 start.bat 启动脚本

**Files:**
- Modify: `start.bat:1-52`

- [ ] **Step 1: 修改第7行 PYTHONPATH 和标题**

```batch
# start.bat:1-7 — 将
echo   UltraMath Agent - 启动
set PYTHONPATH=%~dp0backend\src

# 改为
echo   Lemma - 启动
set PYTHONPATH=%~dp0backend\src;%~dp0backend\src\lemma
```

- [ ] **Step 2: 修改第24行的 uvicorn 启动命令**

```batch
# start.bat:24 — 将
start "UltraMath Backend" cmd /c "set PYTHONPATH=%~dp0backend\src && python -c "import sys; sys.path.insert(0,'src'); import uvicorn; uvicorn.run('ultramath.api.server:app',host='127.0.0.1',port=8765)""

# 改为
start "Lemma Backend" cmd /c "set PYTHONPATH=%~dp0backend\src && python -c "import sys; sys.path.insert(0,'src'); import uvicorn; uvicorn.run('lemma.api.server:app',host='127.0.0.1',port=8765)""
```

- [ ] **Step 3: 验证 start.bat 可以启动后端**

```bash
# 在项目根目录运行
start.bat
# 预期：后端窗口出现，无 ModuleNotFoundError
```

- [ ] **Step 4: Commit**

```bash
git add start.bat
git commit -m "fix: update start.bat to use lemma package name"
```

---

### Task 0.3: 修复 install.bat 错误抑制

**Files:**
- Modify: `install.bat:32-38`

- [ ] **Step 1: 移除错误输出抑制，添加 pip install 的正确方式**

```batch
# install.bat:32-38 — 将
echo [3/4] 安装后端依赖...
cd /d "%~dp0backend"
pip install -e . >nul 2>&1
if errorlevel 1 (
    echo [警告] pip install 失败，尝试直接安装依赖...
    pip install fastapi uvicorn openai pydantic chromadb matplotlib numpy scipy tiktoken jinja2 pyyaml aiofiles httpx
)
echo   后端依赖安装完成

# 改为
echo [3/4] 安装后端依赖...
cd /d "%~dp0backend"
echo   正在安装 lemma 包及其依赖...
pip install -e .
if errorlevel 1 (
    echo [错误] pip install 失败！请检查错误信息。
    echo 尝试手动安装: pip install -e . 
    pause
    exit /b 1
)
echo   后端依赖安装完成
```

- [ ] **Step 2: 同时修复标题（第3行 `UltraAgent` → `Lemma`）**

```batch
# install.bat:3 — 将
echo   UltraAgent 一键安装

# 改为
echo   Lemma 一键安装
```

- [ ] **Step 3: Commit**

```bash
git add install.bat
git commit -m "fix: unhide install errors and rename to Lemma in install.bat"
```

---

## Phase 1: 修复设计系统与品牌统一（严重问题 — 7 个任务，预估 60 分钟）

### Task 1.1: 清理 index.css 重复定义

**Files:**
- Modify: `frontend/src/index.css`

**变更概要:** 删除 3 处重复定义（focus-visible、sr-only、reduced-motion），保留第一次出现位置的版本。

- [ ] **Step 1: 删除第 348-358 行的重复 `.sr-only` 定义**

删除 `frontend/src/index.css:348-358`：
```css
/* 可访问性：跳过链接 */
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}
```

- [ ] **Step 2: 删除第 362-369 行的重复 `@media (prefers-reduced-motion)` 块**

删除 `frontend/src/index.css:362-369`：
```css
/* 可访问性：减少动画 */
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```

- [ ] **Step 3: 删除第 422-426 行的重复 `*:focus-visible` 规则**

删除 `frontend/src/index.css:422-426`：
```css
*:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
  border-radius: 4px;
}
```

- [ ] **Step 4: 验证 CSS 无语法错误**

```bash
cd frontend
npx tailwindcss -i src/index.css -o /dev/null --dry-run 2>&1
# 预期：无错误输出
```

- [ ] **Step 5: Commit**

```bash
git add frontend/src/index.css
git commit -m "fix: remove duplicate CSS rules (sr-only, reduced-motion, focus-visible)"
```

---

### Task 1.2: 统一 `[data-theme="light"]` 与 `@media (prefers-color-scheme: light)` 的 CSS 变量

**Files:**
- Modify: `frontend/src/index.css:144-189`

- [ ] **Step 1: 将 `[data-theme="light"]` 块替换为与 `@media (prefers-color-scheme: light)` 完全一致的变量**

```css
/* frontend/src/index.css:170-189 — 替换为 */
[data-theme="light"] {
  --color-bg: #f8fafc;
  --color-bg-secondary: #ffffff;
  --color-bg-tertiary: #f1f5f9;
  --color-bg-elevated: #ffffff;
  --color-surface: #ffffff;
  --color-surface-hover: #f1f5f9;
  --color-text: #0f172a;
  --color-text-secondary: #475569;
  --color-text-muted: #94a3b8;
  --color-border: #e2e8f0;
  --color-border-strong: #cbd5e1;
  --color-primary: #2563eb;
  --color-primary-hover: #1d4ed8;
  --color-accent: #7c3aed;
  --color-error: #dc2626;
  --color-success: #16a34a;
  --color-warning: #d97706;
  --color-danger-bg: #fef2f2;
  --color-danger-border: #fca5a5;
  --color-danger-text: #dc2626;
  --color-ring: #2563eb;
  --color-scrollbar-thumb: #cbd5e1;
  --color-scrollbar-track: #f1f5f9;

  /* Agent 色保持不变（暗色模式下更醒目） */
  --agent-lead-color: #6366f1;
  --agent-lead-soft: rgba(99,102,241,0.08);
  --agent-lead-glow: rgba(99,102,241,0.15);
  --agent-math-color: #7c3aed;
  --agent-math-soft: rgba(124,58,237,0.08);
  --agent-math-glow: rgba(124,58,237,0.15);
  --agent-engineer-color: #0d9488;
  --agent-engineer-soft: rgba(13,148,136,0.08);
  --agent-engineer-glow: rgba(13,148,136,0.15);
  --agent-reviewer-color: #d97706;
  --agent-reviewer-soft: rgba(217,119,6,0.08);
  --agent-reviewer-glow: rgba(217,119,6,0.15);
  --agent-writer-color: #e11d48;
  --agent-writer-soft: rgba(225,29,72,0.08);
  --agent-writer-glow: rgba(225,29,72,0.15);
  --agent-verifier-color: #059669;
  --agent-verifier-soft: rgba(5,150,105,0.08);
  --agent-verifier-glow: rgba(5,150,105,0.15);
  --agent-researcher-color: #0284c7;
  --agent-researcher-soft: rgba(2,132,199,0.08);
  --agent-researcher-glow: rgba(2,132,199,0.15);
  --agent-analyst-color: #ea580c;
  --agent-analyst-soft: rgba(234,88,12,0.08);
  --agent-analyst-glow: rgba(234,88,12,0.15);
}
```

- [ ] **Step 2: 同步更新 `@media (prefers-color-scheme: light)` 块，添加缺失变量**

在 `frontend/src/index.css:144-168` 的 `@media (prefers-color-scheme: light)` 末尾（`}` 之前）追加：
```css
    --color-bg-elevated: #ffffff;
    --color-border-strong: #cbd5e1;
    --color-danger-bg: #fef2f2;
    --color-danger-border: #fca5a5;
    --color-danger-text: #dc2626;
    --color-ring: #2563eb;
    --color-scrollbar-thumb: #cbd5e1;
    --color-scrollbar-track: #f1f5f9;

    --agent-lead-color: #6366f1;
    --agent-lead-soft: rgba(99,102,241,0.08);
    --agent-lead-glow: rgba(99,102,241,0.15);
    --agent-math-color: #7c3aed;
    --agent-math-soft: rgba(124,58,237,0.08);
    --agent-math-glow: rgba(124,58,237,0.15);
    --agent-engineer-color: #0d9488;
    --agent-engineer-soft: rgba(13,148,136,0.08);
    --agent-engineer-glow: rgba(13,148,136,0.15);
    --agent-reviewer-color: #d97706;
    --agent-reviewer-soft: rgba(217,119,6,0.08);
    --agent-reviewer-glow: rgba(217,119,6,0.15);
    --agent-writer-color: #e11d48;
    --agent-writer-soft: rgba(225,29,72,0.08);
    --agent-writer-glow: rgba(225,29,72,0.15);
    --agent-verifier-color: #059669;
    --agent-verifier-soft: rgba(5,150,105,0.08);
    --agent-verifier-glow: rgba(5,150,105,0.15);
    --agent-researcher-color: #0284c7;
    --agent-researcher-soft: rgba(2,132,199,0.08);
    --agent-researcher-glow: rgba(2,132,199,0.15);
    --agent-analyst-color: #ea580c;
    --agent-analyst-soft: rgba(234,88,12,0.08);
    --agent-analyst-glow: rgba(234,88,12,0.15);
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/index.css
git commit -m "fix: unify light theme CSS variables across media query and data-theme"
```

---

### Task 1.3: 修复 Markdown 渲染支持亮色模式

**Files:**
- Modify: `frontend/src/index.css:191-261`

- [ ] **Step 1: 将 `.markdown-body` 及其子规则的硬编码暗色值替换为 CSS 变量引用**

```css
/* frontend/src/index.css:191-261 — 完整替换为 */
.markdown-body {
  line-height: 1.7;
  font-size: 13px;
  max-width: 65ch;
}

.markdown-body h1 { font-size: 1.35rem; font-weight: 600; margin: 0.8rem 0 0.4rem; color: var(--color-text); }
.markdown-body h2 { font-size: 1.15rem; font-weight: 600; margin: 0.7rem 0 0.35rem; color: var(--color-text); }
.markdown-body h3 { font-size: 1rem; font-weight: 600; margin: 0.5rem 0 0.25rem; color: var(--color-text-secondary); }
.markdown-body p { margin: 0.35rem 0; }
.markdown-body ul, .markdown-body ol { padding-left: 1.25rem; margin: 0.35rem 0; }
.markdown-body li { margin: 0.15rem 0; }
.markdown-body code {
  background: var(--color-bg-tertiary);
  padding: 0.1rem 0.35rem;
  border-radius: 4px;
  font-size: 0.8rem;
  font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
  color: var(--color-primary);
}
.markdown-body pre {
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  padding: 0;
  margin: 0.5rem 0;
  overflow-x: auto;
}
.markdown-body pre code {
  background: transparent;
  padding: 0;
  color: var(--color-text);
}
.markdown-body blockquote {
  border-left: 2px solid var(--color-primary);
  padding-left: 0.75rem;
  margin: 0.4rem 0;
  color: var(--color-text-secondary);
}
.markdown-body table {
  border-collapse: collapse;
  margin: 0.4rem 0;
  width: 100%;
}
.markdown-body th, .markdown-body td {
  border: 1px solid var(--color-border);
  padding: 0.4rem 0.6rem;
  text-align: left;
  font-size: 12px;
}
.markdown-body th {
  background: var(--color-bg-tertiary);
  font-weight: 600;
}
.markdown-body a {
  color: var(--color-primary);
  text-decoration: none;
}
.markdown-body a:hover {
  text-decoration: underline;
}
.markdown-body strong {
  color: var(--color-text);
  font-weight: 600;
}
.markdown-body hr {
  border: none;
  border-top: 1px solid var(--color-border);
  margin: 0.75rem 0;
}
```

- [ ] **Step 2: 验证亮色模式下 markdown 可读**

```bash
cd frontend && npx vite build --mode development 2>&1 | tail -5
# 预期：build 成功
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/index.css
git commit -m "fix: use CSS variables for markdown rendering to support light theme"
```

---

### Task 1.4: 修复 tailwind.config.js 语法错误

**Files:**
- Modify: `frontend/tailwind.config.js`

- [ ] **Step 1: 删除 colors 对象后多余的 `},`**

```js
// frontend/tailwind.config.js:35 — 将
        },
        },
        fontFamily: {

// 改为
        },
        fontFamily: {
```

正确的完整结构是：
```js
theme: {
  extend: {
    colors: { ... },
    fontFamily: { ... },
    animation: { ... },
  },
},
```

- [ ] **Step 2: 验证 Tailwind 编译无错误**

```bash
cd frontend
npx tailwindcss -i src/index.css -o /tmp/test.css 2>&1
# 预期：无错误，正常输出
```

- [ ] **Step 3: Commit**

```bash
git add frontend/tailwind.config.js
git commit -m "fix: remove extraneous closing brace in tailwind.config.js"
```

---

### Task 1.5: 移除全局按钮 min-height/min-width 破坏性规则

**Files:**
- Modify: `frontend/src/index.css:137-140`

- [ ] **Step 1: 删除全局按钮尺寸强制规则**

删除 `frontend/src/index.css:137-140`：
```css
/* 按钮最小触控目标 */
button, [role="button"] {
  min-height: 44px;
  min-width: 44px;
}
```

- [ ] **Step 2: 改为在需要的具体按钮上单独设置**

不需要额外的 CSS 规则，交互按钮已经通过 Tailwind 的 `px-*` `py-*` 类获得了足够的触控区域。

- [ ] **Step 3: Commit**

```bash
git add frontend/src/index.css
git commit -m "fix: remove global button min-size rule that breaks Tailwind utilities"
```

---

### Task 1.6: 统一品牌名称和版本号

**Files:**
- Modify: `frontend/src/components/ChatPanel.tsx:225`
- Modify: `frontend/src/config.ts:2`
- Modify: `backend/start.py:19`
- Modify: `frontend/src/components/Sidebar.tsx:38`

- [ ] **Step 1: ChatPanel 欢迎语 — "UltraMath Agent" → "Lemma"**

```tsx
// frontend/src/components/ChatPanel.tsx:225 — 将
<h2 className="text-lg font-semibold text-[var(--color-text)] mb-1.5 tracking-tight">UltraMath Agent</h2>

// 改为
<h2 className="text-lg font-semibold text-[var(--color-text)] mb-1.5 tracking-tight">Lemma</h2>
```

- [ ] **Step 2: config.ts 注释 — "UltraMath Agent" → "Lemma"**

```typescript
// frontend/src/config.ts:2 — 将
 * UltraMath Agent 前端配置

// 改为
 * Lemma 前端配置
```

- [ ] **Step 3: Sidebar 版本号 — v5.1.0 → v5.2.0**

```tsx
// frontend/src/components/Sidebar.tsx:38 — 将
<p className="text-[10px] text-[var(--color-text-secondary)] font-mono">v5.1.0</p>

// 改为
<p className="text-[10px] text-[var(--color-text-secondary)] font-mono">v5.2.0</p>
```

- [ ] **Step 4: server.py 版本号**

```python
# backend/src/lemma/api/server.py:91 — 将
app = FastAPI(title="Lemma", version="5.1.0")

# 改为
app = FastAPI(title="Lemma", version="5.2.0")
```

- [ ] **Step 5: 同步更新 package.json 和 pyproject.toml 版本号**

```bash
# 检查所有版本号引用
grep -r "5\.1\.0" --include="*.json" --include="*.toml" --include="*.py" --include="*.tsx" --include="*.ts" E:\数学建模agent
```

然后逐个更新为 `5.2.0`（除 lock 文件外）。需要更新的文件：
- `frontend/package.json:3`
- `backend/pyproject.toml:7`
- `backend/src/lemma/api/server.py:276`（`/api/health` 返回值）

- [ ] **Step 6: Commit**

```bash
git add frontend/src/components/ChatPanel.tsx frontend/src/config.ts frontend/src/components/Sidebar.tsx backend/src/lemma/api/server.py frontend/package.json backend/pyproject.toml
git commit -m "fix: unify branding to Lemma v5.2.0 across all files"
```

---

### Task 1.7: 统一 localStorage 键名前缀

**Files:**
- Modify: `frontend/src/components/SettingsPanel.tsx:19-24`
- Modify: `frontend/src/App.tsx:62-63`

- [ ] **Step 1: SettingsPanel — 将所有 `um_` 前缀改为 `lemma_`**

```typescript
// frontend/src/components/SettingsPanel.tsx:19-24 — 将
const [provider, setProvider] = useState(() => localStorage.getItem('um_provider') || 'openai')
const [model, setModel] = useState(() => localStorage.getItem('um_model') || 'gpt-4o')
const [apiKey, setApiKey] = useState(() => localStorage.getItem('um_api_key') || '')
const [baseUrl, setBaseUrl] = useState(() => localStorage.getItem('um_base_url') || 'https://api.openai.com/v1')
const [maxTokens, setMaxTokens] = useState(() => Number(localStorage.getItem('um_max_tokens')) || 8192)
const [temperature, setTemperature] = useState(() => Number(localStorage.getItem('um_temperature')) || 0.7)

// 改为
const [provider, setProvider] = useState(() => localStorage.getItem('lemma_provider') || 'openai')
const [model, setModel] = useState(() => localStorage.getItem('lemma_model') || 'gpt-4o')
const [apiKey, setApiKey] = useState(() => localStorage.getItem('lemma_api_key') || '')
const [baseUrl, setBaseUrl] = useState(() => localStorage.getItem('lemma_base_url') || 'https://api.openai.com/v1')
const [maxTokens, setMaxTokens] = useState(() => Number(localStorage.getItem('lemma_max_tokens')) || 8192)
const [temperature, setTemperature] = useState(() => Number(localStorage.getItem('lemma_temperature')) || 0.7)
```

- [ ] **Step 2: SettingsPanel — 同步更新所有 localStorage.setItem 调用**

```typescript
// frontend/src/components/SettingsPanel.tsx:57-63 — persistConfig 函数
const persistConfig = () => {
  localStorage.setItem('lemma_provider', provider)
  localStorage.setItem('lemma_model', model)
  localStorage.setItem('lemma_api_key', apiKey)
  localStorage.setItem('lemma_base_url', baseUrl)
  localStorage.setItem('lemma_max_tokens', String(maxTokens))
  localStorage.setItem('lemma_temperature', String(temperature))
}
```

- [ ] **Step 3: SettingsPanel — 同步更新所有读取旧 key 的地方**

全局搜索替换 `frontend/src/components/SettingsPanel.tsx` 中的：
- `'um_domain'` → `'lemma_domain'`
- `localStorage.getItem('um_api_key')` → `localStorage.getItem('lemma_api_key')`

- [ ] **Step 4: 其他文件中的 `um_api_key` 引用**

搜索并替换：
- `frontend/src/components/SessionPanel.tsx` 中的 `'um_api_key'` → `'lemma_api_key'`
- `frontend/src/components/TraceViewer.tsx` 中的 `'um_api_key'` → `'lemma_api_key'`
- `frontend/src/components/DocumentVersions.tsx` 中的 `'um_api_key'` → `'lemma_api_key'`

- [ ] **Step 5: 添加旧 key 迁移逻辑**

在 `frontend/src/App.tsx` 的 useEffect 中添加一次性迁移：

```tsx
// 在 App 组件的 useEffect 开头添加
useEffect(() => {
  // 一次性迁移旧 localStorage key
  const keyMap: Record<string, string> = {
    'um_provider': 'lemma_provider',
    'um_model': 'lemma_model',
    'um_api_key': 'lemma_api_key',
    'um_base_url': 'lemma_base_url',
    'um_max_tokens': 'lemma_max_tokens',
    'um_temperature': 'lemma_temperature',
    'um_domain': 'lemma_domain',
  }
  for (const [oldKey, newKey] of Object.entries(keyMap)) {
    const value = localStorage.getItem(oldKey)
    if (value !== null && localStorage.getItem(newKey) === null) {
      localStorage.setItem(newKey, value)
      localStorage.removeItem(oldKey)
    }
  }
}, [])
```

- [ ] **Step 6: Commit**

```bash
git add frontend/src/components/SettingsPanel.tsx frontend/src/components/SessionPanel.tsx frontend/src/components/TraceViewer.tsx frontend/src/components/DocumentVersions.tsx frontend/src/App.tsx
git commit -m "fix: unify localStorage keys to lemma_ prefix with migration"
```

---

## Phase 2: 修复核心功能（严重问题 — 5 个任务，预估 45 分钟）

### Task 2.1: 修复流式聊天竞态条件

**Files:**
- Modify: `backend/src/lemma/api/server.py:970-1008`

- [ ] **Step 1: 重写 `_stream_chat_ws` 使用 agent.chat 方法而非手动拼接**

```python
# backend/src/lemma/api/server.py:970-1008 — 替换为
async def _stream_chat_ws(websocket: WebSocket, message: str, role_id: str | None = None):
    """流式聊天 — 通过 WebSocket 实时推送 token"""
    agent = _agent
    if not agent:
        return
    try:
        async with _agent_lock:
            if role_id:
                agent.switch_role(role_id)
            agent._ensure_system_message()
            agent.memory.add("user", message)

            backend = agent._get_backend()
            # 每次都获取最新的消息列表
            messages = agent.memory.get_messages()

            full_response = ""
            async for chunk in backend.generate_stream(messages):
                if isinstance(chunk, dict):
                    continue
                full_response += chunk
                await websocket.send_text(json.dumps({
                    "type": "stream_chunk",
                    "content": chunk,
                }, ensure_ascii=False))

            # 流式完成后统一添加到 memory
            agent.memory.add("assistant", full_response)

            role = agent.get_current_role()
            await websocket.send_text(json.dumps({
                "type": "stream_end",
                "full_content": full_response,
                "agent_role": agent.current_role_id,
                "agent_name": role.name if role else "",
            }, ensure_ascii=False))
    except Exception as e:
        logger.error(f"Stream chat error: {e}")
        try:
            await websocket.send_text(json.dumps({
                "type": "error", "message": str(e)
            }, ensure_ascii=False))
        except Exception:
            pass
```

关键修改：移除了 `type('', (), {'name': ''})()` 这一行 hack，改为使用已有的 `role.name if role else ""`。

- [ ] **Step 2: Commit**

```bash
git add backend/src/lemma/api/server.py
git commit -m "fix: resolve stream chat race condition and remove dynamic type hack"
```

---

### Task 2.2: 修复 Auto Run REST 端点使其真正启动执行

**Files:**
- Modify: `backend/src/lemma/api/server.py:368-376`

- [ ] **Step 1: 修改 `/api/auto-run` 端点启动后台任务**

```python
# backend/src/lemma/api/server.py:368-376 — 替换为
@app.post("/api/auto-run")
async def auto_run(req: AutoRunRequest, api_key: str = Depends(verify_api_key)):
    """启动自动执行"""
    global _agent
    async with _agent_lock:
        if not _agent:
            work_dir = str(_validate_work_dir(req.work_dir))
            _agent = create_agent(work_dir)

    if _agent:
        asyncio.create_task(_run_auto_broadcast(req.problem_text))
        return {"status": "started", "message": "自动执行已启动"}
    return {"status": "error", "message": "Agent 未初始化"}
```

- [ ] **Step 2: 添加 `_run_auto_broadcast` 辅助函数**

在 `_run_auto_ws` 函数后面添加：

```python
async def _run_auto_broadcast(problem_text: str):
    """通过 WebSocket 广播 auto run 进度给所有连接的客户端"""
    if not _agent:
        return
    try:
        async for event in _agent.run_auto(problem_text):
            msg = json.dumps(event, ensure_ascii=False)
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
    except Exception as e:
        logger.error(f"Auto run broadcast error: {e}")
```

- [ ] **Step 3: Commit**

```bash
git add backend/src/lemma/api/server.py
git commit -m "fix: make /api/auto-run REST endpoint actually execute pipeline"
```

---

### Task 2.3: 移除硬编码的假 API Key

**Files:**
- Modify: `frontend/src/components/ChatPanel.tsx:83-84`
- Modify: `frontend/src/components/SessionPanel.tsx:29-30,46-47,63-64,78-79`

- [ ] **Step 1: 创建统一的 API 辅助函数**

新建 `frontend/src/api-helpers.ts`：

```typescript
// frontend/src/api-helpers.ts
import { API_BASE_URL } from './config'

function getApiKey(): string {
  return localStorage.getItem('lemma_api_key') || ''
}

export async function apiGet(path: string): Promise<Response> {
  return fetch(`${API_BASE_URL}${path}`, {
    headers: { 'X-API-Key': getApiKey() },
  })
}

export async function apiPost(path: string, body?: unknown): Promise<Response> {
  return fetch(`${API_BASE_URL}${path}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-API-Key': getApiKey(),
    },
    body: body ? JSON.stringify(body) : undefined,
  })
}

export async function apiDelete(path: string): Promise<Response> {
  return fetch(`${API_BASE_URL}${path}`, {
    method: 'DELETE',
    headers: { 'X-API-Key': getApiKey() },
  })
}
```

- [ ] **Step 2: ChatPanel — 替换 cost fetch**

```tsx
// frontend/src/components/ChatPanel.tsx:82-85 — 将
fetch(`${API_BASE_URL}/api/cost`, {
  headers: { 'X-API-Key': 'dev-key-change-in-production' }
}).then(r => r.json()).then(d => setCost(d.session_cost_usd || 0)).catch(() => {})

// 改为
import { apiGet } from '../api-helpers'
// ...
apiGet('/api/cost').then(r => r.json()).then(d => setCost(d.session_cost_usd || 0)).catch(() => {})
```

- [ ] **Step 3: SessionPanel — 替换所有 fetch 调用**

```tsx
// frontend/src/components/SessionPanel.tsx — 将所有
fetch(`${API_BASE_URL}/api/...`, {
  headers: { 'X-API-Key': 'dev-key-change-in-production' }
})

// 替换为使用 apiGet / apiPost / apiDelete
import { apiGet, apiPost, apiDelete } from '../api-helpers'
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/api-helpers.ts frontend/src/components/ChatPanel.tsx frontend/src/components/SessionPanel.tsx
git commit -m "fix: replace hardcoded dev API key with dynamic key from localStorage"
```

---

### Task 2.4: 修复设置保存流程

**Files:**
- Modify: `frontend/src/components/SettingsPanel.tsx:66-108`

- [ ] **Step 1: 修改 `handleSave` — 只走 WebSocket init 一条路径**

```typescript
// frontend/src/components/SettingsPanel.tsx:66-108 — 替换 handleSave 函数
const handleSave = async () => {
  if (!apiKey.trim()) {
    setError('请输入 API Key')
    return
  }
  if (!projectDir.trim()) {
    setError('请设置工作目录')
    return
  }

  setSaving(true)
  setError(null)
  persistConfig()

  const config = { provider, model, api_key: apiKey, base_url: baseUrl, max_tokens: maxTokens, temperature }

  // 通过 WebSocket 统一初始化（包含 config）
  localStorage.setItem('lemma_domain', selectedDomain)
  onInitProject(projectDir, selectedDomain, config as unknown as Record<string, unknown>)

  setSaved(true)
  setSaving(false)
  setTimeout(() => setSaved(false), 2000)
}
```

去掉 `fetch('/api/config')` 调用——配置和初始化通过 WebSocket init 消息一起发送。

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/SettingsPanel.tsx
git commit -m "fix: simplify settings save flow to use single WebSocket init path"
```

---

### Task 2.5: 修复 `_generate_with_tools` 消息列表操作

**Files:**
- Modify: `backend/src/lemma/engine/agent.py:267-317`

- [ ] **Step 1: 确保工具调用结果被持久化并用于后续 LLM 调用**

```python
# backend/src/lemma/engine/agent.py:267-317 — _generate_with_tools 方法
async def _generate_with_tools(self) -> str:
    """带工具调用的生成（最多 10 轮工具调用）"""
    backend = self._get_backend()
    self._apply_phase_params(backend)
    tools = self.tools.to_openai_tools()
    max_rounds = 10
    full_response = ""

    for _ in range(max_rounds):
        messages = self.memory.get_messages()  # 每轮重新获取最新消息
        response = await backend.generate(
            messages=messages, tools=tools if tools else None,
        )
        if response.content:
            full_response += response.content
        if not response.tool_calls:
            break

        # 将 assistant 消息写入 memory
        assistant_msg = Message(
            role="assistant", content=response.content or "",
            tool_calls=response.tool_calls,
        )
        self.memory.add_message(assistant_msg)  # 使用 add_message 持久化

        for tc in response.tool_calls:
            tool_name = tc["name"]
            try:
                args = json.loads(tc["arguments"]) if tc["arguments"] else {}
            except json.JSONDecodeError:
                args = {}

            await self._emit("tool_call", {
                "name": tool_name, "arguments": args,
                "timestamp": datetime.now().isoformat(),
            })

            result = await self.tools.execute(tool_name, **args)

            await self._emit("tool_call", {
                "name": tool_name,
                "result": result.to_display(),
                "success": result.success,
                "timestamp": datetime.now().isoformat(),
            })

            # 将工具结果写入 memory
            self.memory.add("tool", result.to_display())

    return full_response or "(无响应)"
```

注意：这里假设 `ShortTermMemory` 有 `add_message` 方法或将 `Message` 对象转为 dict。需要确认实际的 `memory.add()` 签名。如果 `add` 接受 `Message` 对象则直接用。

- [ ] **Step 2: 检查 `ShortTermMemory.add()` 的实际签名**

```bash
grep -n "def add" backend/src/lemma/memory/short_term.py
```

如果 `add` 只接受 `(role: str, content: str)`：
```python
self.memory.add("assistant", response.content or "")
self.memory.add("tool", result.to_display())
```

- [ ] **Step 3: Commit**

```bash
git add backend/src/lemma/engine/agent.py
git commit -m "fix: persist tool call results to memory for proper LLM context"
```

---

## Phase 3: 架构清理（中等问题 — 4 个任务，预估 50 分钟）

### Task 3.1: 提取 WebSocket 消息处理到独立模块

**Files:**
- Create: `frontend/src/hooks/useMessageHandler.ts`
- Modify: `frontend/src/App.tsx:94-187`

- [ ] **Step 1: 创建消息处理 hook**

```typescript
// frontend/src/hooks/useMessageHandler.ts
import { useCallback } from 'react'
import { Message, PhaseInfo, AgentStatus } from '../App'

let msgCounter = 0
const nextId = () => `${Date.now()}-${++msgCounter}`

interface MessageHandlerDeps {
  setMessages: React.Dispatch<React.SetStateAction<Message[]>>
  setPhases: React.Dispatch<React.SetStateAction<PhaseInfo[]>>
  setAgentStatus: React.Dispatch<React.SetStateAction<AgentStatus>>
  setStreamingContent: React.Dispatch<React.SetStateAction<string>>
  setIsStreaming: React.Dispatch<React.SetStateAction<boolean>>
  setIsRunning: React.Dispatch<React.SetStateAction<boolean>>
  setWorkDir: React.Dispatch<React.SetStateAction<string>>
  setRoles: React.Dispatch<React.SetStateAction<{ id: string; name: string }[]>>
  streamingContent: string
}

export function useMessageHandler(deps: MessageHandlerDeps) {
  const {
    setMessages, setPhases, setAgentStatus,
    setStreamingContent, setIsStreaming, setIsRunning,
    setWorkDir, setRoles, streamingContent,
  } = deps

  return useCallback((data: unknown) => {
    const msg = data as Record<string, unknown>

    switch (msg.type) {
      case 'message':
        setMessages(prev => [...prev, {
          id: nextId(),
          role: ((msg.role as string) || 'assistant') as Message['role'],
          content: (msg.content as string) || '',
          agentRole: msg.agent_role as string,
          agentName: msg.agent_name as string,
          timestamp: (msg.timestamp as string) || new Date().toISOString(),
        }])
        break

      case 'tool_call':
        if (msg.result) {
          setMessages(prev => [...prev, {
            id: nextId(),
            role: 'tool',
            content: msg.result as string,
            toolName: msg.name as string,
            toolSuccess: msg.success as boolean,
            timestamp: (msg.timestamp as string) || new Date().toISOString(),
          }])
        }
        break

      case 'phase_start':
        setPhases(prev => prev.map(p =>
          p.id === msg.phase ? { ...p, status: 'running' as const } : p
        ))
        break

      case 'phase_end':
        setPhases(prev => prev.map(p =>
          p.id === msg.phase ? { ...p, status: (msg.success ? 'completed' : 'failed') as const, summary: msg.summary as string } : p
        ))
        setAgentStatus(prev => ({ ...prev, progress: (msg.progress as number) || prev.progress }))
        break

      case 'status':
        if (msg.data) {
          const statusData = msg.data as Record<string, unknown>
          const stateData = statusData.state as Record<string, unknown> | undefined
          setAgentStatus({
            initialized: true,
            currentRole: (statusData.current_role as string) || 'lead',
            currentRoleName: (statusData.current_role_name as string) || '团队指挥',
            progress: (stateData?.progress as number) || 0,
            phase: (stateData?.current_phase_name as string) || '空闲',
            memoryTokens: (statusData.memory_tokens as number) || 0,
            memoryMessages: (statusData.memory_messages as number) || 0,
            domainName: (stateData?.domain_name as string) || (statusData.domain_name as string) || '',
          })
        }
        break

      case 'initialized':
        setAgentStatus(prev => ({ ...prev, initialized: true }))
        setWorkDir(msg.work_dir as string)
        if (msg.domain) {
          const domain = msg.domain as { id: string; name: string; phases: { id: string; name: string }[]; roles: { id: string; name: string }[] }
          if (domain.phases) {
            setPhases(domain.phases.map(p => ({
              id: p.id, name: p.name, status: 'pending' as const,
            })))
          }
          if (domain.roles) {
            setRoles(domain.roles)
          }
          setAgentStatus(prev => ({ ...prev, domainName: domain.name || domain.id }))
        }
        break

      case 'role_switched':
        setAgentStatus(prev => ({
          ...prev,
          currentRole: msg.role as string,
          currentRoleName: msg.name as string,
        }))
        break

      case 'stream_chunk':
        setStreamingContent(prev => prev + (msg.content as string || ''))
        setIsStreaming(true)
        break

      case 'stream_end': {
        const fullContent = msg.full_content as string || streamingContent
        if (fullContent) {
          setMessages(prev => [...prev, {
            id: nextId(),
            role: 'assistant' as const,
            content: fullContent,
            agentRole: msg.agent_role as string,
            agentName: msg.agent_name as string,
            timestamp: new Date().toISOString(),
          }])
        }
        setStreamingContent('')
        setIsStreaming(false)
        break
      }

      case 'complete':
        setIsRunning(false)
        setStreamingContent('')
        setIsStreaming(false)
        setAgentStatus(prev => ({ ...prev, progress: 100, phase: '完成' }))
        break

      case 'cancelled':
        setIsRunning(false)
        break

      case 'error':
        setIsRunning(false)
        break
    }
  }, [setMessages, setPhases, setAgentStatus, setStreamingContent, setIsStreaming, setIsRunning, setWorkDir, setRoles, streamingContent])
}
```

- [ ] **Step 2: 在 App.tsx 中使用新 hook**

```tsx
// frontend/src/App.tsx:94 — 将内联 onMessage 替换为
import { useMessageHandler } from './hooks/useMessageHandler'

// 在 App 组件内
const handleMessage = useMessageHandler({
  setMessages, setPhases, setAgentStatus,
  setStreamingContent, setIsStreaming, setIsRunning,
  setWorkDir, setRoles, streamingContent,
})

const ws = useWebSocket(WS_URL, {
  onMessage: handleMessage,
  onOpen: () => { /* ... 保持不变 ... */ },
  onClose: () => setIsConnected(false),
})
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/hooks/useMessageHandler.ts frontend/src/App.tsx
git commit -m "refactor: extract WebSocket message handler to dedicated hook"
```

---

### Task 3.2: 修复模块级可变状态 `msgCounter`

**Files:**
- Delete: `frontend/src/App.tsx:56-57`（在 Task 3.1 中已移走）
- Already fixed in: `frontend/src/hooks/useMessageHandler.ts`

在 Task 3.1 中已经将 `msgCounter` 和 `nextId` 移到了 hook 模块中。对于仍留在 App.tsx 中的 `sendMessage` 使用的 `nextId`，改用 `Date.now()` + `Math.random()` 的内联方案。

- [ ] **Step 1: 修改 App.tsx 中 `sendMessage` 的 ID 生成**

```tsx
// frontend/src/App.tsx:200-206 — 将
setMessages(prev => [...prev, {
  id: nextId(),
  role: 'user',
  content,
  timestamp: new Date().toISOString(),
}])

// 改为
setMessages(prev => [...prev, {
  id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
  role: 'user',
  content,
  timestamp: new Date().toISOString(),
}])
```

- [ ] **Step 2: 删除 App.tsx 中剩余的 `msgCounter` 和 `nextId` 引用**

```bash
grep -n "msgCounter\|nextId" frontend/src/App.tsx
# 确保无引用后删除第56-57行
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/App.tsx
git commit -m "fix: replace module-level counter with pure random ID generation"
```

---

### Task 3.3: 修复 Electron titleBarOverlay 支持亮色模式

**Files:**
- Modify: `frontend/electron/main.js:148-153`

- [ ] **Step 1: 根据系统主题动态设置 titleBarOverlay 颜色**

```js
// frontend/electron/main.js:148-153 — 将
titleBarStyle: 'hidden',
titleBarOverlay: {
  color: '#0f172a',
  symbolColor: '#e2e8f0',
  height: 36,
},

// 改为
titleBarStyle: 'hidden',
titleBarOverlay: {
  color: '#0f172a',
  symbolColor: '#e2e8f0',
  height: 36,
},
```

然后添加主题监听（在 `createWindow` 函数末尾）：

```js
// 监听系统主题变化
const { nativeTheme } = require('electron')
nativeTheme.on('updated', () => {
  const isDark = nativeTheme.shouldUseDarkColors
  mainWindow?.setTitleBarOverlay({
    color: isDark ? '#0f172a' : '#f8fafc',
    symbolColor: isDark ? '#e2e8f0' : '#0f172a',
    height: 36,
  })
})

// 初始设置
mainWindow.once('ready-to-show', () => {
  const isDark = nativeTheme.shouldUseDarkColors
  mainWindow.setTitleBarOverlay({
    color: isDark ? '#0f172a' : '#f8fafc',
    symbolColor: isDark ? '#e2e8f0' : '#0f172a',
    height: 36,
  })
  mainWindow.show()
})
```

- [ ] **Step 2: Commit**

```bash
git add frontend/electron/main.js
git commit -m "fix: dynamic Electron titleBarOverlay color for light/dark theme"
```

---

### Task 3.4: 添加 `@types/node` 依赖

**Files:**
- Modify: `frontend/package.json`

- [ ] **Step 1: 安装缺失的类型包**

```bash
cd frontend
npm install --save-dev @types/node
```

- [ ] **Step 2: 验证 TypeScript 编译**

```bash
cd frontend
npx tsc --noEmit 2>&1 | head -20
# 预期：之前因 path import 导致的类型错误消失
```

- [ ] **Step 3: Commit**

```bash
git add frontend/package.json frontend/package-lock.json
git commit -m "fix: add @types/node dev dependency for path module types"
```

---

## Phase 4: 补全缺失 UI（中等问题 — 4 个任务，预估 60 分钟）

### Task 4.1: 添加导出按钮

**Files:**
- Modify: `frontend/src/components/ChatPanel.tsx`

- [ ] **Step 1: 在 ChatPanel 顶部工具栏添加导出按钮**

在 `frontend/src/components/ChatPanel.tsx` 顶部工具栏（第135行区域）的 cost 显示旁边添加：

```tsx
{/* 在 cost 显示的 div 后面添加 */}
<button
  onClick={async () => {
    try {
      const apiKey = localStorage.getItem('lemma_api_key') || ''
      const res = await fetch(`${API_BASE_URL}/api/export`, {
        method: 'POST',
        headers: { 'X-API-Key': apiKey },
      })
      if (res.ok) {
        const blob = await res.blob()
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = 'conversation.md'
        a.click()
        URL.revokeObjectURL(url)
      }
    } catch { /* ignore */ }
  }}
  className="flex items-center gap-1 text-[10px] text-[var(--color-text-muted)] hover:text-[var(--color-text)] transition-colors"
  aria-label="导出对话"
  title="导出为 Markdown"
>
  <Download size={12} strokeWidth={1.5} aria-hidden="true" />
  <span>导出</span>
</button>
```

需要添加 `Download` 到 lucide-react import：
```tsx
import { Square, Zap, ChevronDown, Send, Copy, Check, Loader, Wrench, BarChart3, Code, FileText, Search, DollarSign, Download } from 'lucide-react'
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/ChatPanel.tsx
git commit -m "feat: add conversation export button to ChatPanel"
```

---

### Task 4.2: 添加 HITL 确认集成

**Files:**
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/components/ChatPanel.tsx`

- [ ] **Step 1: 在 App.tsx 中添加 HITL 待确认消息的处理**

在 `useMessageHandler` hook 的 switch 中添加：

```typescript
case 'hitl_request':
  // 存储待确认请求，在 ChatPanel 中展示
  setHITLRequest({
    requestId: msg.request_id as string,
    phaseId: msg.phase_id as string,
    message: msg.message as string,
  })
  break
```

添加状态：
```typescript
const [hitlRequest, setHITLRequest] = useState<{
  requestId: string; phaseId: string; message: string
} | null>(null)
```

- [ ] **Step 2: 在 ChatPanel 中添加确认卡片**

在 `frontend/src/components/ChatPanel.tsx` 的消息列表上方添加：

```tsx
{hitlRequest && (
  <ConfirmationCard
    phaseId={hitlRequest.phaseId}
    message={hitlRequest.message}
    onApprove={() => {
      ws.send(JSON.stringify({
        type: 'hitl_respond',
        request_id: hitlRequest.requestId,
        response: 'approve',
      }))
      setHITLRequest(null)
    }}
    onReject={() => {
      ws.send(JSON.stringify({
        type: 'hitl_respond',
        request_id: hitlRequest.requestId,
        response: 'reject',
      }))
      setHITLRequest(null)
    }}
  />
)}
```

需要传递 `hitlRequest` 和 `setHITLRequest` 作为 props，并导入 `ConfirmationCard`。

- [ ] **Step 3: Commit**

```bash
git add frontend/src/App.tsx frontend/src/components/ChatPanel.tsx
git commit -m "feat: integrate HITL confirmation into chat flow"
```

---

### Task 4.3: 在 ChatPanel 工具调用中渲染格式化内容

**Files:**
- Modify: `frontend/src/components/ChatPanel.tsx:328-348`

- [ ] **Step 1: 工具消息改为渲染 Markdown**

```tsx
// frontend/src/components/ChatPanel.tsx:342-344 — 将
<div className="bg-white/[0.02] rounded-lg px-3 py-2 border border-white/[0.04] text-[11px] font-mono text-[var(--color-text-secondary)] max-h-40 overflow-y-auto whitespace-pre-wrap break-all leading-relaxed">
  {message.content}
</div>

// 改为
<div className="bg-[var(--color-bg-tertiary)] rounded-lg px-3 py-2 border border-[var(--color-border)] text-[11px] max-h-60 overflow-y-auto leading-relaxed">
  <ReactMarkdown components={markdownComponents}>
    {message.content}
  </ReactMarkdown>
</div>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/ChatPanel.tsx
git commit -m "fix: render tool call results with markdown formatting"
```

---

### Task 4.4: 移除不存在的"领域市场"链接，改为占位说明

**Files:**
- Modify: `frontend/src/components/SettingsPanel.tsx:301-314`

- [ ] **Step 1: 替换领域市场区块**

```tsx
// frontend/src/components/SettingsPanel.tsx:301-314 — 替换为
<div className="bg-white/[0.02] rounded-xl p-4 border border-white/[0.04]">
  <h3 className="text-xs font-medium text-[var(--color-text)] mb-2">领域扩展</h3>
  <p className="text-[11px] text-[var(--color-text-secondary)]">
    当前已内置 5 个领域（数学建模、论文写作、实验报告、文献综述、数据挖掘）。
    自定义领域可通过在 <code className="text-[10px] bg-[var(--color-bg-tertiary)] px-1 rounded">domains/</code> 目录下添加 YAML 配置文件来扩展。
  </p>
</div>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/SettingsPanel.tsx
git commit -m "fix: replace dead domain marketplace link with documentation"
```

---

## Phase 5: 测试与打磨（轻微问题 — 3 个任务，预估 30 分钟）

### Task 5.1: 修复测试文件中的 `any` 类型

**Files:**
- Modify: `frontend/src/__tests__/ChatPanel.test.tsx:5`

- [ ] **Step 1: 替换 `any[]` 为正确的类型**

```typescript
// frontend/src/__tests__/ChatPanel.test.tsx:5 — 将
messages: [] as any[],

// 改为
import { Message } from '../App'
// ...
messages: [] as Message[],
```

- [ ] **Step 2: 运行前端测试验证**

```bash
cd frontend
npm test 2>&1
# 预期：所有测试通过
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/__tests__/ChatPanel.test.tsx
git commit -m "fix: replace any[] with Message[] type in ChatPanel test"
```

---

### Task 5.2: 添加 ChatPanel 发送消息的集成测试

**Files:**
- Modify: `frontend/src/__tests__/ChatPanel.test.tsx`

- [ ] **Step 1: 添加消息发送测试**

```typescript
it('calls onSend when send button is clicked with input', () => {
  const onSend = vi.fn()
  render(<ChatPanel {...defaultProps} onSend={onSend} />)
  
  const input = screen.getByPlaceholderText(/输入消息/)
  fireEvent.change(input, { target: { value: 'Hello' } })
  
  const sendButton = screen.getByLabelText('发送消息')
  fireEvent.click(sendButton)
  
  expect(onSend).toHaveBeenCalledWith('Hello')
})

it('calls onSend on Enter keypress', () => {
  const onSend = vi.fn()
  render(<ChatPanel {...defaultProps} onSend={onSend} />)
  
  const input = screen.getByPlaceholderText(/输入消息/)
  fireEvent.change(input, { target: { value: 'Test' } })
  fireEvent.keyDown(input, { key: 'Enter', shiftKey: false })
  
  expect(onSend).toHaveBeenCalledWith('Test')
})

it('does not call onSend for empty input', () => {
  const onSend = vi.fn()
  render(<ChatPanel {...defaultProps} onSend={onSend} />)
  
  const sendButton = screen.getByLabelText('发送消息')
  fireEvent.click(sendButton)
  
  expect(onSend).not.toHaveBeenCalled()
})
```

- [ ] **Step 2: 运行测试**

```bash
cd frontend && npm test -- --run 2>&1
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/__tests__/ChatPanel.test.tsx
git commit -m "test: add message send integration tests for ChatPanel"
```

---

### Task 5.3: 删除遗留的 `console.log` 调试语句

**Files:**
- Modify: `frontend/src/components/TraceViewer.tsx:37`
- Modify: `frontend/src/components/DocumentVersions.tsx:35,54`

- [ ] **Step 1: 搜索所有 console.log 并替换为静默错误处理**

```bash
grep -rn "console\." frontend/src/ --include="*.tsx" --include="*.ts"
```

将找到的 `console.error` 替换为 `// silently handle fetch error` 或使用 structured logging。

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/TraceViewer.tsx frontend/src/components/DocumentVersions.tsx
git commit -m "chore: remove console.log debug statements from components"
```

---

## Phase 6: 构建与部署修复（轻微问题 — 2 个任务，预估 20 分钟）

### Task 6.1: 修复 electron-builder domains 路径和 exe 依赖

**Files:**
- Modify: `frontend/package.json:66-75`

- [ ] **Step 1: 添加构建前检查脚本**

```json
// frontend/package.json:8-9 — 将 build:python 改为带检查的
"build:python": "if not exist \"electron\\backend\\lemma-server.exe\" (echo [ERROR] lemma-server.exe missing! Run build:python first. && exit /b 1) else (echo [OK] lemma-server.exe found)"
```

实际上，更好的做法是在 `build` 脚本中确保顺序：
```json
"build": "npm run build:python && npm run build:electron",
"build:electron:only": "vite build && electron-builder --win --config",
```

- [ ] **Step 2: 验证 `extraResources` 的 `from` 路径在 CI 中正确**

`"from": "../domains"` 相对于 `frontend/package.json` 的位置。在 monorepo 开发环境下正确，但需确认 CI 中也是从 `frontend/` 运行。

- [ ] **Step 3: Commit**

```bash
git add frontend/package.json
git commit -m "fix: add pre-build check for lemma-server.exe existence"
```

---

### Task 6.2: 修复 Electron 后端崩溃无重启机制

**Files:**
- Modify: `frontend/electron/main.js:118-121`

- [ ] **Step 1: 添加 Python 进程崩溃重启逻辑**

```js
// frontend/electron/main.js:118-121 — 替换 close 事件处理
pythonProcess.on('close', async (code) => {
  console.log(`Python process exited with code ${code}`)
  pythonProcess = null
  
  // 非正常退出时尝试重启（最多 3 次）
  if (code !== 0 && code !== null) {
    console.log('Backend crashed, attempting restart...')
    for (let attempt = 1; attempt <= 3; attempt++) {
      console.log(`Restart attempt ${attempt}/3...`)
      const ready = await startPythonBackend()
      if (ready) {
        console.log('Backend restarted successfully')
        return
      }
      await new Promise(r => setTimeout(r, 2000))
    }
    console.error('Backend restart failed after 3 attempts')
  }
})
```

- [ ] **Step 2: Commit**

```bash
git add frontend/electron/main.js
git commit -m "fix: add Python backend auto-restart on crash (max 3 attempts)"
```

---

## 验证清单

完成所有 Phase 后，按以下步骤验证：

- [ ] **启动验证**: 双击 `start.bat`，后端应正常启动（无 ModuleNotFoundError）
- [ ] **亮色模式验证**: 点击侧栏底部的 Sun 图标，所有文字可读，markdown 正常显示
- [ ] **聊天验证**: 在对话页输入消息，发送后收到流式回复
- [ ] **自动执行验证**: 点击"自动执行"，流水线页面显示进度
- [ ] **导出验证**: 点击导出按钮，下载的 .md 文件内容正确
- [ ] **会话保存/恢复验证**: 保存会话 → 切换目录 → 恢复会话，消息完整
- [ ] **Electron 验证**: `npm run build:electron` 成功打包，运行 exe 无白屏
- [ ] **测试验证**: `npm test` 全部通过（前端）；`pytest` 全部通过（后端）

---

## 预估总工时

| Phase | 任务数 | 预估时间 |
|-------|--------|---------|
| Phase 0: 致命修复 | 3 | 15 分钟 |
| Phase 1: 设计系统 | 7 | 60 分钟 |
| Phase 2: 核心功能 | 5 | 45 分钟 |
| Phase 3: 架构清理 | 4 | 50 分钟 |
| Phase 4: 缺失 UI | 4 | 60 分钟 |
| Phase 5: 测试打磨 | 3 | 30 分钟 |
| Phase 6: 构建部署 | 2 | 20 分钟 |
| **总计** | **28** | **约 4.5 小时** |

---

## 风险提示

1. **Phase 2.5** (修复 `_generate_with_tools`) 需要确认 `ShortTermMemory.add()` 的实际签名，可能需要小幅度调整
2. **Phase 1.2** (CSS 变量统一) 可能需要在多个组件中微调 `--color-*` 变量引用
3. **Phase 4.2** (HITL 集成) 依赖后端实际发出 `hitl_request` 类型的 WebSocket 消息——如果后端没实现，这个任务会变成后端的改动
4. 打包后的 exe 需要在实际 Windows 环境测试（CI 环境可能缺少某些系统依赖）
