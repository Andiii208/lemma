# Lemma v2.0 后续发展计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 Lemma 从功能原型升级为生产级可部署的数学建模自动化平台，补齐测试、安全、CI/CD 和真实场景验证的短板。

**Architecture:** 分 7 个阶段推进，每阶段独立可交付。阶段一（基础设施）→ 阶段二（关键 Bug 修复）→ 阶段三（安全加固）→ 阶段四（测试体系建设）→ 阶段五（功能补全）→ 阶段六（生产化）→ 阶段七（UX 优化）。每个阶段产出可独立验证的增量。

**Tech Stack:** Python 3.11+, FastAPI, OpenAI SDK, ChromaDB, React 18, TypeScript, Tailwind CSS, Electron, pytest, Vitest, Docker, GitHub Actions

---

## 项目现状摘要

### 已完成（功能原型）
- ✅ FastAPI 服务器 + WebSocket
- ✅ 12 角色 Agent 系统 + 精细 prompt
- ✅ 8 阶段状态机 + 重试逻辑
- ✅ LLM 抽象层（OpenAI/DeepSeek/Ollama）
- ✅ 短期/长期记忆系统
- ✅ 5 个工具（代码执行、LaTeX、文件、质量检查、图表）
- ✅ 知识库（模型库 + 参考文档）
- ✅ React 前端（聊天、管线、文件、设置）
- ✅ Electron 桌面端
- ✅ LaTeX 论文模板

### 关键短板
- ❌ 零单元测试
- ❌ 无 Git 版本控制
- ❌ 无 CI/CD
- ❌ 代码执行无沙箱
- ❌ 多模型路由是死代码
- ❌ 流式对话不支持工具调用
- ❌ LLM 调用无重试/退避
- ❌ 前端无语法高亮、无错误边界
- ❌ 未实际跑过竞赛题目

---

## 阶段一：基础设施建设（预计 2-3 天）

### 目标
建立版本控制、代码质量工具、项目规范化，为后续开发打好基础。

---

### Task 1.1: 初始化 Git 仓库

**Files:**
- Create: `.gitignore`
- Create: `.gitattributes`

- [ ] **Step 1: 创建 .gitignore**

```gitignore
# Python
__pycache__/
*.py[cod]
*.egg-info/
dist/
build/
*.egg
.venv/
venv/
env/

# Node
node_modules/
frontend/dist/
frontend/out/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Environment
.env
.env.local
.env.*.local

# Logs
*.log
stability.log
stability_output.log

# OS
.DS_Store
Thumbs.db

# Build artifacts
nul
*.tmp

# ChromaDB
chroma_db/

# Test workspace (user data)
test_workspace/
```

- [ ] **Step 2: 创建 .gitattributes**

```
* text=auto
*.py text eol=lf
*.ts text eol=lf
*.tsx text eol=lf
*.js text eol=lf
*.md text eol=lf
*.yaml text eol=lf
*.yml text eol=lf
*.bat text eol=crlf
*.sh text eol=lf
```

- [ ] **Step 3: 初始化仓库并首次提交**

```bash
cd E:\数学建模agent
git init
git add .
git commit -m "feat: initial commit - Lemma v1.0 prototype"
```

- [ ] **Step 4: 删除垃圾文件**

```bash
rm nul  # Windows 命令行误操作产物
```

---

### Task 1.2: 配置代码质量工具

**Files:**
- Create: `backend/pyproject.toml` (修改现有)
- Create: `frontend/.eslintrc.cjs`
- Create: `frontend/.prettierrc`
- Create: `Makefile` 或 `scripts/lint.bat`

- [ ] **Step 1: 配置 Python Ruff（修改 pyproject.toml）**

在 `backend/pyproject.toml` 末尾追加：

```toml
[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = [
    "E",    # pycodestyle errors
    "W",    # pycodestyle warnings
    "F",    # pyflakes
    "I",    # isort
    "N",    # pep8-naming
    "UP",   # pyupgrade
    "B",    # flake8-bugbear
    "SIM",  # flake8-simplify
    "TCH",  # flake8-type-checking
]
ignore = ["E501"]

[tool.ruff.lint.isort]
known-first-party = ["ultramath"]

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
markers = [
    "integration: requires running server",
    "slow: long-running tests",
]
```

- [ ] **Step 2: 配置前端 ESLint**

```bash
cd E:\数学建模agent\frontend
npm install -D eslint @typescript-eslint/parser @typescript-eslint/eslint-plugin eslint-plugin-react-hooks eslint-plugin-react-refresh prettier eslint-config-prettier
```

创建 `frontend/.eslintrc.cjs`：

```javascript
module.exports = {
  root: true,
  env: { browser: true, es2020: true },
  extends: [
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended',
    'plugin:react-hooks/recommended',
    'prettier',
  ],
  ignorePatterns: ['dist', '.eslintrc.cjs'],
  parser: '@typescript-eslint/parser',
  plugins: ['react-refresh'],
  rules: {
    'react-refresh/only-export-components': ['warn', { allowConstantExport: true }],
    '@typescript-eslint/no-explicit-any': 'error',
    '@typescript-eslint/no-unused-vars': ['error', { argsIgnorePattern: '^_' }],
  },
};
```

创建 `frontend/.prettierrc`：

```json
{
  "semi": true,
  "singleQuote": true,
  "trailingComma": "all",
  "printWidth": 100,
  "tabWidth": 2
}
```

- [ ] **Step 3: 添加 lint 脚本到 package.json**

在 `frontend/package.json` 的 `scripts` 中添加：

```json
{
  "lint": "eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0",
  "lint:fix": "eslint . --ext ts,tsx --fix",
  "format": "prettier --write \"src/**/*.{ts,tsx,css,json}\""
}
```

- [ ] **Step 4: 创建项目根目录的 lint 脚本**

创建 `scripts/lint.bat`：

```batch
@echo off
echo === Python Lint ===
cd backend
python -m ruff check src/
python -m ruff format --check src/
cd ..

echo === Frontend Lint ===
cd frontend
call npm run lint
cd ..

echo === All checks passed ===
```

- [ ] **Step 5: 运行 lint 修复现有问题**

```bash
cd E:\数学建模agent\backend
python -m ruff check --fix src/
python -m ruff format src/
```

- [ ] **Step 6: 提交**

```bash
git add .
git commit -m "chore: add ruff, eslint, prettier config and fix existing issues"
```

---

### Task 1.3: 创建开发文档

**Files:**
- Create: `CONTRIBUTING.md`
- Create: `docs/ARCHITECTURE.md`
- Create: `.env.example`

- [ ] **Step 1: 创建 .env.example**

```env
# LLM API Keys
OPENAI_API_KEY=sk-your-key-here
DEEPSEEK_API_KEY=sk-your-key-here

# Server
ULTRAMATH_HOST=127.0.0.1
ULTRAMATH_PORT=8765

# Logging
LOG_LEVEL=INFO
```

- [ ] **Step 2: 创建 ARCHITECTURE.md**

内容包含：系统架构图（ASCII）、模块职责说明、数据流图、技术栈说明。基于前面的分析结果撰写。

- [ ] **Step 3: 创建 CONTRIBUTING.md**

内容包含：开发环境搭建步骤、代码风格规范、提交规范（Conventional Commits）、PR 流程。

- [ ] **Step 4: 提交**

```bash
git add .env.example CONTRIBUTING.md docs/ARCHITECTURE.md
git commit -m "docs: add architecture docs, contributing guide, and env template"
```

---

## 阶段二：关键 Bug 修复（预计 2-3 天）

### 目标
修复影响核心功能的 Bug，确保基础流程可以跑通。

---

### Task 2.1: 修复 chat_stream 不支持工具调用

**Files:**
- Modify: `backend/src/ultramath/orchestration/engine.py:112-143`

**问题:** `chat_stream` 绕过了 `_generate_with_tools`，导致流式对话无法调用任何工具。同时 `chat_stream` 每次调用都会重复添加 system message。

- [ ] **Step 1: 编写复现测试**

创建 `backend/tests/test_engine_stream.py`：

```python
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from ultramath.orchestration.engine import LemmaAgent
from ultramath.memory.short_term import ShortTermMemory
from ultramath.memory.context import ContextManager
from ultramath.tools.registry import ToolRegistry
from ultramath.agent.role import RoleManager


@pytest.fixture
def mock_backend():
    backend = AsyncMock()
    backend.generate_stream = AsyncMock()
    return backend


@pytest.fixture
def agent(tmp_path, mock_backend):
    memory = ShortTermMemory()
    context = ContextManager(str(tmp_path / "context.json"))
    tools = ToolRegistry()
    roles = RoleManager()
    return LemmaAgent(
        backend=mock_backend,
        memory=memory,
        context=context,
        tools=tools,
        role_manager=roles,
        work_dir=str(tmp_path),
    )


def test_chat_stream_has_system_message(agent):
    """chat_stream should include exactly one system message."""
    # Collect messages passed to generate_stream
    collected_messages = []

    async def fake_stream(messages, tools=None):
        collected_messages.extend(messages)
        yield "test response"

    agent.backend.generate_stream = fake_stream
    agent.chat_stream("hello")
    agent.chat_stream("world")

    system_msgs = [m for m in collected_messages if m.get("role") == "system"]
    assert len(system_msgs) <= 2, f"Too many system messages: {len(system_msgs)}"
```

- [ ] **Step 2: 运行测试确认失败**

```bash
cd E:\数学建模agent\backend
python -m pytest tests/test_engine_stream.py -v
```

Expected: FAIL (test 文件还不存在或断言失败)

- [ ] **Step 3: 修复 chat_stream 方法**

修改 `engine.py` 的 `chat_stream` 方法，使其：
1. 检查是否已有 system message（与 `chat` 方法一致）
2. 支持工具调用（在流式响应中检测 tool_calls 并执行）

```python
async def chat_stream(self, user_message: str):
    """流式对话，支持工具调用"""
    self._ensure_system_message()

    self.memory.add("user", user_message)
    messages = self.memory.get_messages()

    current_messages = list(messages)
    tool_rounds = 0
    max_tool_rounds = 10

    while tool_rounds < max_tool_rounds:
        tool_calls_found = False
        full_content = ""
        tool_calls_buffer = []

        async for chunk in self.backend.generate_stream(
            current_messages, tools=self.tools.get_openai_tools()
        ):
            if isinstance(chunk, dict) and chunk.get("type") == "tool_calls":
                tool_calls_found = True
                tool_calls_buffer.extend(chunk.get("calls", []))
            elif isinstance(chunk, str):
                full_content += chunk
                yield chunk

        if not tool_calls_found:
            break

        # 执行工具调用
        tool_rounds += 1
        if full_content:
            current_messages.append({"role": "assistant", "content": full_content})

        for tc in tool_calls_buffer:
            result = await self.tools.execute(tc["name"], tc["arguments"])
            current_messages.append({
                "role": "tool",
                "tool_call_id": tc.get("id", ""),
                "content": result.to_text(),
            })
            yield f"\n\n🔧 调用工具 {tc['name']}...\n"

    self.memory.add("assistant", full_content)
```

- [ ] **Step 4: 运行测试确认通过**

```bash
python -m pytest tests/test_engine_stream.py -v
```

- [ ] **Step 5: 提交**

```bash
git add backend/src/ultramath/orchestration/engine.py backend/tests/test_engine_stream.py
git commit -m "fix: chat_stream now supports tool calls and avoids duplicate system messages"
```

---

### Task 2.2: 激活多模型路由

**Files:**
- Modify: `backend/src/ultramath/orchestration/engine.py:127,147`
- Modify: `backend/src/ultramath/llm/router.py`
- Modify: `backend/src/ultramath/api/server.py:135`

**问题:** `engine.py` 始终调用 `get_default_backend()`，从未使用 `get_backend(task_type)`。`models.yaml` 从未被加载。

- [ ] **Step 1: 编写路由测试**

创建 `backend/tests/test_router.py`：

```python
import pytest
from ultramath.llm.router import ModelRouter, TaskType


def test_get_backend_returns_mapped():
    config = {
        "backends": {
            "default": {"api_key": "test", "model": "gpt-4"},
            "creative": {"api_key": "test", "model": "deepseek-chat"},
        },
        "routing": {
            "math_derivation": "creative",
            "default": "default",
        },
    }
    router = ModelRouter.from_config(config)
    backend = router.get_backend(TaskType.MATH_DERIVATION)
    assert backend.model == "deepseek-chat"


def test_get_backend_falls_back_to_default():
    config = {
        "backends": {
            "default": {"api_key": "test", "model": "gpt-4"},
        },
        "routing": {"default": "default"},
    }
    router = ModelRouter.from_config(config)
    backend = router.get_backend(TaskType.CODE_GENERATION)
    assert backend.model == "gpt-4"


def test_from_single_config():
    router = ModelRouter.from_single_config(api_key="test", model="gpt-4")
    assert router.get_backend(TaskType.MATH_DERIVATION).model == "gpt-4"
```

- [ ] **Step 2: 运行测试确认当前行为**

```bash
python -m pytest tests/test_router.py -v
```

- [ ] **Step 3: 修改 engine.py 使用任务路由**

将 `engine.py` 中的 `self.router.get_default_backend()` 替换为根据当前阶段选择合适的 `TaskType`：

```python
def _get_task_type_for_phase(self) -> str:
    """根据当前阶段返回合适的任务类型"""
    phase_task_map = {
        "ANALYSIS": TaskType.REASONING,
        "DERIVATION": TaskType.MATH_DERIVATION,
        "ONTOLOGY": TaskType.REASONING,
        "CODING": TaskType.CODE_GENERATION,
        "TESTING": TaskType.CODE_GENERATION,
        "WRITING": TaskType.WRITING,
        "REVIEW": TaskType.REASONING,
    }
    return phase_task_map.get(self.state_machine.current_phase, TaskType.REASONING)
```

- [ ] **Step 4: 修改 server.py 加载 models.yaml**

```python
# 在 server.py 的 lifespan 或 startup 中
config_path = Path(__file__).parent.parent.parent / "config" / "models.yaml"
if config_path.exists():
    router = ModelRouter.from_config(str(config_path))
else:
    router = ModelRouter.from_single_config(
        api_key=os.getenv("OPENAI_API_KEY", ""),
        model="gpt-4o",
    )
```

- [ ] **Step 5: 更新 models.yaml 的路由配置**

```yaml
routing:
  reasoning: default
  math_derivation: deepseek
  code_generation: default
  writing: deepseek
  review: default
```

- [ ] **Step 6: 运行测试并提交**

```bash
python -m pytest tests/test_router.py -v
git add .
git commit -m "feat: activate multi-model routing by task type"
```

---

### Task 2.3: 添加 LLM 调用重试与退避

**Files:**
- Modify: `backend/src/ultramath/llm/backend.py`

**问题:** 单次 API 失败直接返回错误，无重试、无退避。对 transient 错误（429、500、502、503）无恢复能力。

- [ ] **Step 1: 编写重试测试**

创建 `backend/tests/test_llm_retry.py`：

```python
import pytest
from unittest.mock import AsyncMock, patch
import openai
from ultramath.llm.backend import LLMBackend


@pytest.fixture
def backend():
    return LLMBackend(api_key="test", model="gpt-4")


@pytest.mark.asyncio
async def test_retry_on_rate_limit(backend):
    call_count = 0

    async def mock_create(**kwargs):
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise openai.RateLimitError(
                message="rate limited",
                response=AsyncMock(status_code=429, headers={}),
                body=None,
            )
        return AsyncMock(
            choices=[AsyncMock(message=AsyncMock(content="success", tool_calls=None), finish_reason="stop")],
            usage=AsyncMock(prompt_tokens=10, completion_tokens=5, total_tokens=15),
        )

    with patch.object(backend.client.chat.completions, "create", mock_create):
        result = await backend.generate([{"role": "user", "content": "test"}])
        assert result["content"] == "success"
        assert call_count == 3


@pytest.mark.asyncio
async def test_retry_exhausted(backend):
    async def mock_create(**kwargs):
        raise openai.APIStatusError(
            message="server error",
            response=AsyncMock(status_code=500, headers={}),
            body=None,
        )

    with patch.object(backend.client.chat.completions, "create", mock_create):
        result = await backend.generate([{"role": "user", "content": "test"}])
        assert "error" in result["content"].lower() or "Error" in result["content"]
```

- [ ] **Step 2: 运行测试确认失败**

- [ ] **Step 3: 实现重试逻辑**

在 `backend.py` 的 `generate` 方法中添加重试装饰器：

```python
import asyncio
import random
from functools import wraps


def with_retry(max_retries: int = 3, base_delay: float = 1.0):
    """指数退避重试装饰器，针对 transient 错误"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except (
                    openai.RateLimitError,
                    openai.APIConnectionError,
                    openai.APITimeoutError,
                ) as e:
                    last_exception = e
                    if attempt < max_retries:
                        delay = base_delay * (2 ** attempt) + random.uniform(0, 0.5)
                        await asyncio.sleep(delay)
                except openai.APIStatusError as e:
                    if e.status_code in (500, 502, 503) and attempt < max_retries:
                        last_exception = e
                        delay = base_delay * (2 ** attempt) + random.uniform(0, 0.5)
                        await asyncio.sleep(delay)
                    else:
                        raise
            raise last_exception
        return wrapper
    return decorator
```

- [ ] **Step 4: 运行测试并提交**

```bash
python -m pytest tests/test_llm_retry.py -v
git add .
git commit -m "feat: add exponential backoff retry for LLM API calls"
```

---

### Task 2.4: 修复 PipelinePanel 阶段数错误

**Files:**
- Modify: `frontend/src/components/PipelinePanel.tsx:42`

**问题:** 副标题写 "6阶段自动求解流程" 但实际定义了 8 个阶段。

- [ ] **Step 1: 修改文案**

```tsx
// 将 "6阶段自动求解流程" 改为 "8阶段自动求解流程"
<p className="text-xs text-slate-400">8阶段自动求解流程</p>
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/components/PipelinePanel.tsx
git commit -m "fix: correct phase count from 6 to 8 in PipelinePanel"
```

---

### Task 2.5: 修复 figure_generator 竞态条件

**Files:**
- Modify: `backend/src/ultramath/tools/figure_generator.py`

**问题:** 使用固定临时文件名 `_fig_gen_tmp.py`，并发调用会冲突。

- [ ] **Step 1: 使用 UUID 替换固定文件名**

```python
import uuid

# 在 execute 方法中
temp_name = f"_fig_gen_{uuid.uuid4().hex[:8]}.py"
temp_path = os.path.join(self.work_dir, temp_name)
```

- [ ] **Step 2: 提交**

```bash
git add backend/src/ultramath/tools/figure_generator.py
git commit -m "fix: use UUID for temp filename to prevent race condition in figure_generator"
```

---

## 阶段三：安全加固（预计 3-4 天）

### 目标
消除关键安全风险，特别是代码执行沙箱和 API 认证。

---

### Task 3.1: 代码执行沙箱化

**Files:**
- Modify: `backend/src/ultramath/tools/code_executor.py`
- Create: `backend/src/ultramath/tools/sandbox.py`

**问题:** 当前代码执行无任何沙箱，任意 Python 代码可访问完整文件系统和网络。

- [ ] **Step 1: 实现基于 RestrictedPython 的受限执行**

创建 `backend/src/ultramath/tools/sandbox.py`：

```python
"""代码执行沙箱 - 限制危险操作"""
import ast
import sys
from typing import Optional

# 禁止的模块列表
BLOCKED_MODULES = {
    "subprocess", "os", "shutil", "pathlib",
    "socket", "http", "urllib", "requests",
    "ctypes", "importlib", "code", "codeop",
    "compile", "compileall", "py_compile",
    "signal", "multiprocessing", "threading",
    "webbrowser", "smtplib", "ftplib",
}

# 禁止的内置函数
BLOCKED_BUILTINS = {
    "exec", "eval", "compile", "__import__",
    "open",  # 将由安全版本替代
}

class SecurityError(Exception):
    """安全策略违规"""
    pass


class SecurityChecker(ast.NodeVisitor):
    """AST 级别的安全检查"""

    def __init__(self, allowed_modules: Optional[set] = None):
        self.allowed_modules = allowed_modules or set()
        self.errors: list[str] = []

    def check(self, code: str) -> list[str]:
        """检查代码安全性，返回错误列表"""
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return [f"Syntax error: {e}"]
        self.visit(tree)
        return self.errors

    def visit_Import(self, node):
        for alias in node.names:
            module_name = alias.name.split(".")[0]
            if module_name in BLOCKED_MODULES and module_name not in self.allowed_modules:
                self.errors.append(f"Blocked module: {alias.name}")
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module:
            module_name = node.module.split(".")[0]
            if module_name in BLOCKED_MODULES and module_name not in self.allowed_modules:
                self.errors.append(f"Blocked module: {node.module}")
        self.generic_visit(node)

    def visit_Call(self, node):
        # 检查危险函数调用
        if isinstance(node.func, ast.Name) and node.func.id in BLOCKED_BUILTINS:
            self.errors.append(f"Blocked builtin: {node.func.id}")
        self.generic_visit(node)
```

- [ ] **Step 2: 集成到 CodeExecutorTool**

修改 `code_executor.py`，在执行前调用 `SecurityChecker`：

```python
from .sandbox import SecurityChecker, SecurityError

async def execute(self, code: str, timeout: int = 60) -> ToolResult:
    # 安全检查
    checker = SecurityChecker(allowed_modules={"numpy", "scipy", "matplotlib", "pandas"})
    errors = checker.check(code)
    if errors:
        return ToolResult.fail(f"安全检查未通过: {'; '.join(errors)}")

    # 原有执行逻辑...
```

- [ ] **Step 3: 编写安全测试**

创建 `backend/tests/test_sandbox.py`：

```python
import pytest
from ultramath.tools.sandbox import SecurityChecker


def test_blocks_subprocess():
    checker = SecurityChecker()
    errors = checker.check("import subprocess; subprocess.call(['ls'])")
    assert any("subprocess" in e for e in errors)


def test_blocks_os():
    checker = SecurityChecker()
    errors = checker.check("import os; os.system('rm -rf /')")
    assert any("os" in e for e in errors)


def test_allows_numpy():
    checker = SecurityChecker(allowed_modules={"numpy"})
    errors = checker.check("import numpy as np; np.array([1,2,3])")
    assert len(errors) == 0


def test_blocks_exec():
    checker = SecurityChecker()
    errors = checker.check("exec('import os')")
    assert any("exec" in e for e in errors)
```

- [ ] **Step 4: 运行测试并提交**

```bash
python -m pytest tests/test_sandbox.py -v
git add .
git commit -m "feat: add AST-based code execution sandbox with module blocking"
```

---

### Task 3.2: 添加 API 认证

**Files:**
- Modify: `backend/src/ultramath/api/server.py`
- Create: `backend/src/ultramath/api/auth.py`

- [ ] **Step 1: 实现简单的 API Key 认证**

创建 `backend/src/ultramath/api/auth.py`：

```python
"""API 认证中间件"""
import os
from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

def get_api_key() -> str:
    return os.getenv("ULTRAMATH_API_KEY", "dev-key-change-in-production")

async def verify_api_key(api_key: str = Security(API_KEY_HEADER)):
    if api_key != get_api_key():
        raise HTTPException(status_code=401, detail="Invalid API Key")
    return api_key
```

- [ ] **Step 2: 在 server.py 中添加认证依赖**

```python
from .auth import verify_api_key

@app.get("/api/health")
async def health():
    # 健康检查不需要认证
    return {"status": "ok"}

@app.get("/api/roles")
async def get_roles(api_key: str = Depends(verify_api_key)):
    # 需要认证的端点
    ...
```

- [ ] **Step 3: 修改前端 SettingsPanel 支持 API Key**

在 SettingsPanel 中添加 API Key 输入字段，保存到 localStorage，并在每次请求中携带。

- [ ] **Step 4: 提交**

```bash
git add .
git commit -m "feat: add API key authentication for all endpoints"
```

---

### Task 3.3: 修复 preload.js 安全漏洞

**Files:**
- Modify: `frontend/electron/preload.js`

**问题:** `openExternal` 未验证 URL 协议，可能打开 `file://` 或恶意协议。

- [ ] **Step 1: 添加协议验证**

```javascript
contextBridge.exposeInMainWorld('electronAPI', {
  openDirectory: () => ipcRenderer.invoke('dialog:openDirectory'),
  openExternal: (url) => {
    // 只允许 http/https 协议
    try {
      const parsed = new URL(url);
      if (parsed.protocol === 'https:' || parsed.http === 'http:') {
        ipcRenderer.invoke('shell:openExternal', url);
      }
    } catch (e) {
      console.error('Invalid URL:', url);
    }
  },
  isElectron: true,
  platform: process.platform,
});
```

- [ ] **Step 2: 添加 TypeScript 类型声明**

创建 `frontend/src/types/electron.d.ts`：

```typescript
interface ElectronAPI {
  openDirectory: () => Promise<string | undefined>;
  openExternal: (url: string) => void;
  isElectron: boolean;
  platform: string;
}

declare global {
  interface Window {
    electronAPI?: ElectronAPI;
  }
}

export {};
```

- [ ] **Step 3: 移除 SettingsPanel 中的 @ts-ignore**

- [ ] **Step 4: 提交**

```bash
git add frontend/electron/preload.js frontend/src/types/ frontend/src/components/SettingsPanel.tsx
git commit -m "fix: validate URL protocol in preload.js and add TypeScript declarations"
```

---

## 阶段四：测试体系建设（预计 4-5 天）

### 目标
建立完整的单元测试和集成测试体系，覆盖核心模块。

---

### Task 4.1: 后端测试基础设施

**Files:**
- Create: `backend/tests/conftest.py`
- Create: `backend/tests/__init__.py`

- [ ] **Step 1: 安装测试依赖**

```bash
cd E:\数学建模agent\backend
pip install -e ".[dev]"
# 确保 pytest, pytest-asyncio, pytest-cov 已安装
```

- [ ] **Step 2: 创建 conftest.py**

```python
"""共享测试夹具"""
import pytest
import tempfile
import os
from unittest.mock import AsyncMock, MagicMock

from ultramath.memory.short_term import ShortTermMemory
from ultramath.memory.context import ContextManager
from ultramath.tools.registry import ToolRegistry
from ultramath.agent.role import RoleManager


@pytest.fixture
def tmp_work_dir(tmp_path):
    """创建临时工作目录"""
    (tmp_path / "求解").mkdir()
    (tmp_path / "数据").mkdir()
    (tmp_path / "论文").mkdir()
    return str(tmp_path)


@pytest.fixture
def mock_llm_backend():
    """模拟 LLM 后端"""
    backend = AsyncMock()
    backend.generate = AsyncMock(return_value={
        "content": "test response",
        "tool_calls": None,
        "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
    })
    backend.generate_stream = AsyncMock()
    backend.model = "test-model"
    backend.call_count = 0
    backend.total_tokens = 0
    return backend


@pytest.fixture
def memory():
    return ShortTermMemory(max_tokens=1000)


@pytest.fixture
def context_manager(tmp_path):
    return ContextManager(str(tmp_path / "context.json"))


@pytest.fixture
def tool_registry(tmp_work_dir):
    registry = ToolRegistry()
    # 注册模拟工具
    return registry


@pytest.fixture
def role_manager():
    return RoleManager()
```

- [ ] **Step 3: 提交**

```bash
git add backend/tests/
git commit -m "test: add pytest infrastructure with shared fixtures"
```

---

### Task 4.2: 状态机单元测试

**Files:**
- Create: `backend/tests/test_state_machine.py`

- [ ] **Step 1: 编写完整测试**

```python
"""状态机单元测试"""
import pytest
from ultramath.orchestration.state_machine import StateMachine, Phase


class TestStateMachine:
    def test_initial_state(self):
        sm = StateMachine()
        assert sm.current_phase == Phase.IDLE

    def test_start_transitions_to_init(self):
        sm = StateMachine()
        sm.start()
        assert sm.current_phase == Phase.INIT

    def test_normal_phase_progression(self):
        sm = StateMachine()
        sm.start()
        assert sm.current_phase == Phase.INIT

        sm.transition(success=True)
        assert sm.current_phase == Phase.ANALYSIS

        sm.transition(success=True)
        assert sm.current_phase == Phase.DERIVATION

    def test_failure_retry(self):
        sm = StateMachine()
        sm.start()
        sm.transition(success=True)  # -> ANALYSIS
        sm.transition(success=False)  # fail -> retry ANALYSIS
        assert sm.current_phase == Phase.ANALYSIS

    def test_max_retries_exceeded(self):
        sm = StateMachine(max_retries=2)
        sm.start()
        sm.transition(success=True)  # -> ANALYSIS
        sm.transition(success=False)  # retry 1
        sm.transition(success=False)  # retry 2
        sm.transition(success=False)  # max exceeded -> skip
        assert sm.current_phase != Phase.ANALYSIS

    def test_progress_percentage(self):
        sm = StateMachine()
        sm.start()
        progress = sm.get_progress()
        assert 0 <= progress <= 100

    def test_to_dict_serialization(self):
        sm = StateMachine()
        sm.start()
        data = sm.to_dict()
        assert "current_phase" in data
        assert "history" in data
        assert isinstance(data["history"], list)

    def test_skip_to_phase(self):
        sm = StateMachine()
        sm.start()
        sm.skip_to(Phase.CODING)
        assert sm.current_phase == Phase.CODING

    def test_is_done(self):
        sm = StateMachine()
        sm.start()
        assert not sm.is_done()
```

- [ ] **Step 2: 运行测试**

```bash
python -m pytest tests/test_state_machine.py -v
```

- [ ] **Step 3: 修复发现的问题并提交**

```bash
git add .
git commit -m "test: add comprehensive state machine unit tests"
```

---

### Task 4.3: 记忆系统单元测试

**Files:**
- Create: `backend/tests/test_memory.py`

- [ ] **Step 1: 编写短期记忆测试**

```python
"""记忆系统单元测试"""
import pytest
from ultramath.memory.short_term import ShortTermMemory


class TestShortTermMemory:
    def test_add_and_retrieve(self):
        mem = ShortTermMemory(max_tokens=1000)
        mem.add("user", "hello")
        messages = mem.get_messages()
        assert len(messages) == 1
        assert messages[0]["content"] == "hello"

    def test_sliding_window_trims_old(self):
        mem = ShortTermMemory(max_tokens=50)
        for i in range(20):
            mem.add("user", f"message {i} " * 5)
        messages = mem.get_messages()
        # 应该被裁剪到 token 限制内
        assert len(messages) < 20

    def test_system_messages_preserved(self):
        mem = ShortTermMemory(max_tokens=50)
        mem.add("system", "you are helpful")
        for i in range(20):
            mem.add("user", f"message {i} " * 5)
        messages = mem.get_messages()
        system_msgs = [m for m in messages if m["role"] == "system"]
        assert len(system_msgs) >= 1

    def test_clear(self):
        mem = ShortTermMemory()
        mem.add("user", "test")
        mem.clear()
        assert len(mem.get_messages()) == 0
```

- [ ] **Step 2: 编写长期记忆测试**

```python
from ultramath.memory.long_term import LongTermMemory


class TestLongTermMemory:
    def test_add_and_query(self, tmp_path):
        mem = LongTermMemory(str(tmp_path / "chroma"))
        mem.add("test document about math", metadata={"topic": "algebra"})
        results = mem.query("math topic")
        assert len(results) > 0

    def test_keyword_fallback(self, tmp_path):
        # 即使 ChromaDB 不可用，关键词搜索也应工作
        mem = LongTermMemory(str(tmp_path / "chroma"))
        mem.add("optimization problem using gradient descent")
        results = mem.query("gradient descent")
        assert len(results) > 0
```

- [ ] **Step 3: 运行测试并提交**

```bash
python -m pytest tests/test_memory.py -v
git add .
git commit -m "test: add short-term and long-term memory unit tests"
```

---

### Task 4.4: 工具单元测试

**Files:**
- Create: `backend/tests/test_tools.py`

- [ ] **Step 1: 编写工具测试**

```python
"""工具系统单元测试"""
import pytest
import os
from ultramath.tools.file_manager import FileManagerTool
from ultramath.tools.code_executor import CodeExecutorTool
from ultramath.tools.quality_checker import QualityCheckerTool


class TestFileManager:
    def test_write_and_read(self, tmp_work_dir):
        tool = FileManagerTool(work_dir=tmp_work_dir)
        result = tool.execute(action="write", path="test.txt", content="hello world")
        assert result.ok

        result = tool.execute(action="read", path="test.txt")
        assert result.ok
        assert "hello world" in result.output

    def test_path_traversal_blocked(self, tmp_work_dir):
        tool = FileManagerTool(work_dir=tmp_work_dir)
        result = tool.execute(action="read", path="../../../etc/passwd")
        assert not result.ok

    def test_list_directory(self, tmp_work_dir):
        tool = FileManagerTool(work_dir=tmp_work_dir)
        tool.execute(action="write", path="a.txt", content="a")
        tool.execute(action="write", path="b.txt", content="b")
        result = tool.execute(action="list", path=".")
        assert result.ok
        assert "a.txt" in result.output
        assert "b.txt" in result.output


class TestCodeExecutor:
    @pytest.mark.asyncio
    async def test_simple_execution(self, tmp_work_dir):
        tool = CodeExecutorTool(work_dir=tmp_work_dir)
        result = await tool.execute(code="print(42)")
        assert result.ok
        assert "42" in result.output

    @pytest.mark.asyncio
    async def test_timeout(self, tmp_work_dir):
        tool = CodeExecutorTool(work_dir=tmp_work_dir)
        result = await tool.execute(code="import time; time.sleep(100)", timeout=1)
        assert not result.ok

    @pytest.mark.asyncio
    async def test_blocked_module(self, tmp_work_dir):
        tool = CodeExecutorTool(work_dir=tmp_work_dir)
        result = await tool.execute(code="import subprocess; subprocess.call(['ls'])")
        assert not result.ok


class TestQualityChecker:
    def test_syntax_check_valid(self, tmp_work_dir):
        tool = QualityCheckerTool(work_dir=tmp_work_dir)
        # 创建一个有效的 Python 文件
        with open(os.path.join(tmp_work_dir, "test.py"), "w") as f:
            f.write("x = 1\nprint(x)\n")
        result = tool.execute(check_type="syntax", file_path="test.py")
        assert result.ok

    def test_syntax_check_invalid(self, tmp_work_dir):
        tool = QualityCheckerTool(work_dir=tmp_work_dir)
        with open(os.path.join(tmp_work_dir, "bad.py"), "w") as f:
            f.write("def foo(\n")
        result = tool.execute(check_type="syntax", file_path="bad.py")
        assert not result.ok
```

- [ ] **Step 2: 运行测试并提交**

```bash
python -m pytest tests/test_tools.py -v
git add .
git commit -m "test: add tool system unit tests (file_manager, code_executor, quality_checker)"
```

---

### Task 4.5: 前端测试基础设施

**Files:**
- Create: `frontend/vitest.config.ts`
- Create: `frontend/src/__tests__/App.test.tsx`
- Modify: `frontend/package.json`

- [ ] **Step 1: 安装测试依赖**

```bash
cd E:\数学建模agent\frontend
npm install -D vitest @testing-library/react @testing-library/jest-dom @testing-library/user-event jsdom
```

- [ ] **Step 2: 创建 vitest.config.ts**

```typescript
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/__tests__/setup.ts',
    css: true,
  },
});
```

- [ ] **Step 3: 创建 setup.ts**

```typescript
import '@testing-library/jest-dom';
```

- [ ] **Step 4: 添加 test 脚本到 package.json**

```json
{
  "scripts": {
    "test": "vitest run",
    "test:watch": "vitest",
    "test:coverage": "vitest run --coverage"
  }
}
```

- [ ] **Step 5: 编写第一个组件测试**

创建 `frontend/src/__tests__/Sidebar.test.tsx`：

```tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import Sidebar from '../components/Sidebar';

const defaultProps = {
  activeView: 'chat' as const,
  setActiveView: vi.fn(),
  isConnected: true,
  currentRole: 'LEAD',
  progress: 0,
  workDir: '/test',
};

describe('Sidebar', () => {
  it('renders all navigation items', () => {
    render(<Sidebar {...defaultProps} />);
    expect(screen.getByText('对话')).toBeInTheDocument();
    expect(screen.getByText('管线')).toBeInTheDocument();
    expect(screen.getByText('文件')).toBeInTheDocument();
    expect(screen.getByText('设置')).toBeInTheDocument();
  });

  it('calls setActiveView on click', () => {
    const setActiveView = vi.fn();
    render(<Sidebar {...defaultProps} setActiveView={setActiveView} />);
    fireEvent.click(screen.getByText('管线'));
    expect(setActiveView).toHaveBeenCalledWith('pipeline');
  });

  it('shows disconnected state', () => {
    render(<Sidebar {...defaultProps} isConnected={false} />);
    expect(screen.getByText('断开')).toBeInTheDocument();
  });
});
```

- [ ] **Step 6: 运行测试并提交**

```bash
npm test
git add .
git commit -m "test: add frontend testing infrastructure with vitest and first component test"
```

---

## 阶段五：功能补全（预计 5-7 天）

### 目标
补全缺失的核心功能，使端到端流程可以完整跑通。

---

### Task 5.1: 添加阶段输出验证

**Files:**
- Modify: `backend/src/ultramath/orchestration/engine.py`

**问题:** 各阶段（如 CODING、ONTOLOGY）信任 LLM 输出但从不验证产出物。

- [ ] **Step 1: 实现阶段验证器**

在 `engine.py` 中为每个阶段添加验证逻辑：

```python
def _validate_phase_output(self, phase: str) -> tuple[bool, str]:
    """验证阶段产出物"""
    validators = {
        "ONTOLOGY": self._validate_ontology,
        "CODING": self._validate_coding,
        "WRITING": self._validate_writing,
    }
    validator = validators.get(phase)
    if validator:
        return validator()
    return True, ""


def _validate_ontology(self) -> tuple[bool, str]:
    """验证本体论输出为有效 JSON"""
    ontology_path = os.path.join(self.work_dir, "problem-ontology.json")
    if not os.path.exists(ontology_path):
        return False, "problem-ontology.json 未生成"
    try:
        with open(ontology_path, "r", encoding="utf-8") as f:
            json.load(f)
        return True, ""
    except json.JSONDecodeError as e:
        return False, f"problem-ontology.json 格式错误: {e}"


def _validate_coding(self) -> tuple[bool, str]:
    """验证代码文件已生成"""
    solution_dir = os.path.join(self.work_dir, "求解")
    if not os.path.exists(solution_dir):
        return False, "求解目录不存在"
    py_files = [f for f in os.listdir(solution_dir) if f.endswith(".py")]
    if not py_files:
        return False, "求解目录中没有 Python 文件"
    return True, ""


def _validate_writing(self) -> tuple[bool, str]:
    """验证论文文件已生成"""
    paper_dir = os.path.join(self.work_dir, "论文")
    if not os.path.exists(paper_dir):
        return False, "论文目录不存在"
    tex_files = [f for f in os.listdir(paper_dir) if f.endswith(".tex")]
    if not tex_files:
        return False, "论文目录中没有 TeX 文件"
    return True, ""
```

- [ ] **Step 2: 在 run_auto 中集成验证**

```python
# 在每个阶段执行后
valid, error_msg = self._validate_phase_output(phase_name)
if not valid:
    yield {"type": "error", "content": f"阶段 {phase_name} 验证失败: {error_msg}"}
    # 进入重试逻辑
```

- [ ] **Step 3: 编写测试并提交**

```bash
python -m pytest tests/ -v
git add .
git commit -m "feat: add phase output validation for ontology, coding, and writing phases"
```

---

### Task 5.2: 添加取消机制

**Files:**
- Modify: `backend/src/ultramath/orchestration/engine.py`
- Modify: `backend/src/ultramath/api/server.py`

**问题:** `run_auto` 一旦启动无法停止。

- [ ] **Step 1: 添加取消标志**

```python
import asyncio

class LemmaAgent:
    def __init__(self, ...):
        ...
        self._cancel_event = asyncio.Event()

    def cancel(self):
        """取消当前自动运行"""
        self._cancel_event.set()

    def reset_cancel(self):
        """重置取消标志"""
        self._cancel_event.clear()

    async def run_auto(self, problem_text: str):
        self.reset_cancel()
        ...
        for phase_name, phase_func in phases:
            if self._cancel_event.is_set():
                yield {"type": "cancelled", "content": "用户取消了自动运行"}
                return
            # 执行阶段...
```

- [ ] **Step 2: 添加 API 端点**

```python
@app.post("/api/cancel")
async def cancel_run(api_key: str = Depends(verify_api_key)):
    if _agent:
        _agent.cancel()
        return {"status": "cancelled"}
    return {"status": "no_agent"}
```

- [ ] **Step 3: 前端添加取消按钮**

在 ChatPanel 的 auto-run 模式下显示取消按钮。

- [ ] **Step 4: 提交**

```bash
git add .
git commit -m "feat: add cancellation mechanism for auto-run pipeline"
```

---

### Task 5.3: 添加前端代码语法高亮

**Files:**
- Modify: `frontend/src/components/ChatPanel.tsx`
- Modify: `frontend/src/components/FileViewer.tsx`

**问题:** `react-syntax-highlighter` 已安装但从未使用。代码块无语法高亮。

- [ ] **Step 1: 在 ChatPanel 中添加语法高亮**

```tsx
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';

const components = {
  code({ node, inline, className, children, ...props }: any) {
    const match = /language-(\w+)/.exec(className || '');
    return !inline && match ? (
      <div className="code-block-wrapper">
        <div className="code-block-header">
          <span>{match[1]}</span>
          <button
            className="copy-button"
            onClick={() => navigator.clipboard.writeText(String(children))}
          >
            复制
          </button>
        </div>
        <SyntaxHighlighter style={oneDark} language={match[1]} PreTag="div" {...props}>
          {String(children).replace(/\n$/, '')}
        </SyntaxHighlighter>
      </div>
    ) : (
      <code className={className} {...props}>
        {children}
      </code>
    );
  },
};

// 在 ReactMarkdown 中使用
<ReactMarkdown components={components}>{message.content}</ReactMarkdown>
```

- [ ] **Step 2: 在 FileViewer 中添加语法高亮**

```tsx
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';

// 文件内容预览
const getLanguage = (filename: string) => {
  const ext = filename.split('.').pop()?.toLowerCase();
  const langMap: Record<string, string> = {
    py: 'python', js: 'javascript', ts: 'typescript',
    tsx: 'tsx', jsx: 'jsx', tex: 'latex',
    json: 'json', yaml: 'yaml', md: 'markdown',
  };
  return langMap[ext || ''] || 'text';
};

// 渲染时
<SyntaxHighlighter
  style={oneDark}
  language={getLanguage(currentFile)}
  showLineNumbers
>
  {content}
</SyntaxHighlighter>
```

- [ ] **Step 3: 提交**

```bash
git add frontend/src/components/ChatPanel.tsx frontend/src/components/FileViewer.tsx
git commit -m "feat: add syntax highlighting for code blocks in chat and file viewer"
```

---

### Task 5.4: 添加前端错误边界

**Files:**
- Create: `frontend/src/components/ErrorBoundary.tsx`
- Modify: `frontend/src/App.tsx`

- [ ] **Step 1: 创建 ErrorBoundary 组件**

```tsx
import React, { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback || (
        <div className="flex items-center justify-center h-full bg-slate-900 text-white p-8">
          <div className="text-center">
            <h2 className="text-xl font-bold mb-2">组件渲染出错</h2>
            <p className="text-slate-400 mb-4">{this.state.error?.message}</p>
            <button
              onClick={() => this.setState({ hasError: false, error: null })}
              className="px-4 py-2 bg-blue-600 rounded hover:bg-blue-700"
            >
              重试
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

export default ErrorBoundary;
```

- [ ] **Step 2: 在 App.tsx 中包裹内容区域**

```tsx
import ErrorBoundary from './components/ErrorBoundary';

// 在内容区域
<ErrorBoundary>
  {activeView === 'chat' && <ChatPanel ... />}
</ErrorBoundary>
```

- [ ] **Step 3: 提交**

```bash
git add frontend/src/components/ErrorBoundary.tsx frontend/src/App.tsx
git commit -m "feat: add React ErrorBoundary to prevent full app crash"
```

---

### Task 5.5: 实现端到端真实题目测试

**Files:**
- Create: `backend/tests/e2e/`
- Create: `backend/tests/e2e/test_full_pipeline.py`

**问题:** 从未用真实竞赛题目跑过完整流程。

- [ ] **Step 1: 准备测试题目**

创建 `backend/tests/e2e/fixtures/simple_optimization.md`：

```markdown
# 测试题目：简单优化问题

某工厂生产两种产品 A 和 B，每件 A 产品利润 3 元，每件 B 产品利润 5 元。
生产 A 需要 2 小时加工和 1 小时装配，生产 B 需要 1 小时加工和 3 小时装配。
每天可用加工时间 10 小时，装配时间 15 小时。

问：每天各生产多少件 A 和 B 可以使利润最大？
```

- [ ] **Step 2: 编写端到端测试**

```python
"""端到端测试 - 使用简单优化问题"""
import pytest
import os
import json

@pytest.mark.integration
@pytest.mark.slow
class TestFullPipeline:
    """需要配置 LLM API Key 才能运行"""

    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        self.work_dir = str(tmp_path)
        self.problem_path = os.path.join(
            os.path.dirname(__file__), "fixtures", "simple_optimization.md"
        )

    async def test_full_pipeline_produces_artifacts(self):
        """完整流程应产出：本体 JSON、Python 求解代码、LaTeX 论文"""
        from ultramath.orchestration.engine import LemmaAgent
        from ultramath.llm.backend import LLMBackend
        from ultramath.memory.short_term import ShortTermMemory
        from ultramath.memory.context import ContextManager
        from ultramath.tools.registry import ToolRegistry
        from ultramath.agent.role import RoleManager

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            pytest.skip("需要 OPENAI_API_KEY")

        backend = LLMBackend(api_key=api_key, model="gpt-4o")
        memory = ShortTermMemory()
        context = ContextManager(os.path.join(self.work_dir, "context.json"))
        tools = ToolRegistry()
        roles = RoleManager()

        agent = LemmaAgent(
            backend=backend,
            memory=memory,
            context=context,
            tools=tools,
            role_manager=roles,
            work_dir=self.work_dir,
        )

        with open(self.problem_path, "r", encoding="utf-8") as f:
            problem = f.read()

        events = []
        async for event in agent.run_auto(problem):
            events.append(event)
            if event.get("type") == "error":
                pytest.fail(f"Pipeline error: {event['content']}")

        # 验证产出物
        assert os.path.exists(os.path.join(self.work_dir, "problem-ontology.json"))

        solution_dir = os.path.join(self.work_dir, "求解")
        assert os.path.exists(solution_dir)
        py_files = [f for f in os.listdir(solution_dir) if f.endswith(".py")]
        assert len(py_files) > 0, "应生成至少一个 Python 求解文件"
```

- [ ] **Step 3: 运行测试（需要 API Key）**

```bash
OPENAI_API_KEY=sk-xxx python -m pytest tests/e2e/ -v -m integration
```

- [ ] **Step 4: 提交**

```bash
git add backend/tests/e2e/
git commit -m "test: add end-to-end pipeline test with simple optimization problem"
```

---

## 阶段六：生产化（预计 4-5 天）

### 目标
容器化、CI/CD、日志、监控，使项目可部署。

---

### Task 6.1: Docker 容器化

**Files:**
- Create: `Dockerfile`
- Create: `docker-compose.yml`
- Create: `.dockerignore`

- [ ] **Step 1: 创建后端 Dockerfile**

```dockerfile
# backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖（LaTeX、字体）
RUN apt-get update && apt-get install -y \
    texlive-xetex \
    texlive-lang-chinese \
    texlive-latex-extra \
    fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
RUN pip install --no-cache-dir .

COPY . .

EXPOSE 8765

CMD ["python", "-m", "uvicorn", "ultramath.api.server:app", "--host", "0.0.0.0", "--port", "8765"]
```

- [ ] **Step 2: 创建 docker-compose.yml**

```yaml
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8765:8765"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY}
      - ULTRAMATH_API_KEY=${ULTRAMATH_API_KEY}
    volumes:
      - ./workspace:/app/workspace
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8765/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:80"
    depends_on:
      - backend
    restart: unless-stopped
```

- [ ] **Step 3: 创建前端 Dockerfile**

```dockerfile
# frontend/Dockerfile
FROM node:20-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
```

- [ ] **Step 4: 创建 .dockerignore**

```
node_modules
__pycache__
*.pyc
.git
.env
venv
.venv
test_workspace
```

- [ ] **Step 5: 提交**

```bash
git add Dockerfile docker-compose.yml .dockerignore backend/Dockerfile frontend/Dockerfile
git commit -m "feat: add Docker containerization for backend and frontend"
```

---

### Task 6.2: GitHub Actions CI/CD

**Files:**
- Create: `.github/workflows/ci.yml`
- Create: `.github/workflows/release.yml`

- [ ] **Step 1: 创建 CI 工作流**

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  backend-lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install ruff
      - run: ruff check backend/src/
      - run: ruff format --check backend/src/

  backend-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -e "backend/.[dev]"
      - run: pytest backend/tests/ -v --ignore=backend/tests/e2e --cov=ultramath --cov-report=xml

  frontend-lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - run: cd frontend && npm ci
      - run: cd frontend && npm run lint

  frontend-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - run: cd frontend && npm ci
      - run: cd frontend && npm test

  build-docker:
    runs-on: ubuntu-latest
    needs: [backend-test, frontend-test]
    steps:
      - uses: actions/checkout@v4
      - run: docker build -t ultramath-backend ./backend
      - run: docker build -t ultramath-frontend ./frontend
```

- [ ] **Step 2: 提交**

```bash
git add .github/workflows/
git commit -m "ci: add GitHub Actions for lint, test, and Docker build"
```

---

### Task 6.3: 结构化日志

**Files:**
- Modify: `backend/src/ultramath/api/server.py`
- Create: `backend/src/ultramath/utils/logger.py`

- [ ] **Step 1: 创建日志配置**

```python
"""结构化日志配置"""
import logging
import json
import sys
from datetime import datetime


class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        if hasattr(record, "extra_data"):
            log_entry["data"] = record.extra_data
        return json.dumps(log_entry, ensure_ascii=False)


def setup_logging(level: str = "INFO"):
    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper()))

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    root.addHandler(handler)
```

- [ ] **Step 2: 在 server.py 中使用**

```python
from ..utils.logger import setup_logging

setup_logging(os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger("ultramath.api")
```

- [ ] **Step 3: 提交**

```bash
git add .
git commit -m "feat: add structured JSON logging"
```

---

## 阶段七：UX 优化（预计 3-4 天）

### 目标
提升用户体验，使产品更易用。

---

### Task 7.1: 添加 API Key 持久化

**Files:**
- Modify: `frontend/src/components/SettingsPanel.tsx`

- [ ] **Step 1: 使用 localStorage 保存 API Key**

```tsx
// 初始化时从 localStorage 读取
const [apiKey, setApiKey] = useState(() => localStorage.getItem('ultramath_api_key') || '');

// 保存时写入 localStorage
const handleSave = async () => {
  localStorage.setItem('ultramath_api_key', apiKey);
  // ... 其余保存逻辑
};
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/components/SettingsPanel.tsx
git commit -m "feat: persist API key in localStorage"
```

---

### Task 7.2: 添加 WebSocket 指数退避

**Files:**
- Modify: `frontend/src/hooks/useWebSocket.ts`

- [ ] **Step 1: 实现指数退避**

```typescript
const reconnectInterval = useRef(1000); // 初始 1 秒
const maxReconnectInterval = 30000; // 最大 30 秒

// 在重连逻辑中
const handleReconnect = () => {
  if (reconnectCount.current < maxReconnectAttempts) {
    setTimeout(() => {
      connect();
      reconnectInterval.current = Math.min(
        reconnectInterval.current * 2,
        maxReconnectInterval,
      );
    }, reconnectInterval.current);
  }
};

// 连接成功时重置
ws.onopen = () => {
  reconnectInterval.current = 1000;
  reconnectCount.current = 0;
  // ...
};
```

- [ ] **Step 2: 添加心跳检测**

```typescript
const heartbeatInterval = useRef<ReturnType<typeof setInterval>>();

ws.onopen = () => {
  heartbeatInterval.current = setInterval(() => {
    if (ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: 'ping' }));
    }
  }, 30000);
};

ws.onclose = () => {
  if (heartbeatInterval.current) {
    clearInterval(heartbeatInterval.current);
  }
};
```

- [ ] **Step 3: 提交**

```bash
git add frontend/src/hooks/useWebSocket.ts
git commit -m "feat: add exponential backoff and heartbeat to WebSocket hook"
```

---

### Task 7.3: 添加"测试连接"按钮

**Files:**
- Modify: `frontend/src/components/SettingsPanel.tsx`
- Modify: `backend/src/ultramath/api/server.py`

- [ ] **Step 1: 添加测试端点**

```python
@app.post("/api/test-connection")
async def test_connection(config: ConfigRequest):
    """测试 LLM 连接是否可用"""
    try:
        backend = LLMBackend(api_key=config.api_key, model=config.model)
        result = await backend.generate([{"role": "user", "content": "Say 'ok'"}])
        if "ok" in result.get("content", "").lower():
            return {"status": "success", "message": "连接成功"}
        return {"status": "error", "message": "模型响应异常"}
    except Exception as e:
        return {"status": "error", "message": str(e)[:200]}
```

- [ ] **Step 2: 前端添加按钮**

```tsx
const [testStatus, setTestStatus] = useState<'idle' | 'testing' | 'success' | 'error'>('idle');

const handleTestConnection = async () => {
  setTestStatus('testing');
  try {
    const res = await fetch(`${API_BASE}/api/test-connection`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ api_key: apiKey, model, api_url: apiUrl }),
    });
    const data = await res.json();
    setTestStatus(data.status === 'success' ? 'success' : 'error');
  } catch {
    setTestStatus('error');
  }
};

// 在保存按钮旁添加
<button onClick={handleTestConnection} disabled={testStatus === 'testing'}>
  {testStatus === 'testing' ? '测试中...' : '测试连接'}
</button>
```

- [ ] **Step 3: 提交**

```bash
git add .
git commit -m "feat: add test connection button in settings"
```

---

## 附录：执行顺序与依赖关系

```
阶段一 ──→ 阶段二 ──→ 阶段三 ──→ 阶段四 ──→ 阶段五 ──→ 阶段六 ──→ 阶段七
  │           │           │           │           │           │           │
  ├─ Git      ├─ 流式工具  ├─ 沙箱     ├─ 状态机   ├─ 阶段验证  ├─ Docker   ├─ Key持久化
  ├─ Lint     ├─ 多模型    ├─ 认证     ├─ 记忆     ├─ 取消机制  ├─ CI/CD    ├─ WS退避
  └─ 文档     ├─ 重试      └─ preload  ├─ 工具     ├─ 语法高亮  └─ 日志     └─ 测试连接
              └─ Bug修复               └─ 前端     ├─ 错误边界
                                                   └─ E2E测试
```

**阶段间依赖：**
- 阶段二依赖阶段一（Git + lint 工具）
- 阶段三依赖阶段二（修复后的稳定代码）
- 阶段四依赖阶段三（安全加固后的代码可测试）
- 阶段五依赖阶段四（测试保障下的功能开发）
- 阶段六依赖阶段五（功能完整后的生产化）
- 阶段七与阶段六可并行

**预估总工期：25-35 个工作日**

---

## 里程碑检查点

| 里程碑 | 验收标准 | 预计完成 |
|--------|----------|----------|
| M1: 基础设施 | Git 可用、lint 通过、文档完整 | 第 3 天 |
| M2: 核心稳定 | 流式工具调用、多模型路由、重试机制工作 | 第 6 天 |
| M3: 安全达标 | 代码沙箱、API 认证、preload 安全 | 第 10 天 |
| M4: 测试覆盖 | 核心模块单测覆盖率 >60% | 第 15 天 |
| M5: 功能完整 | 端到端跑通简单题目 | 第 22 天 |
| M6: 可部署 | Docker 镜像可构建、CI 绿灯 | 第 27 天 |
| M7: 用户体验 | 语法高亮、错误边界、连接测试 | 第 30 天 |
