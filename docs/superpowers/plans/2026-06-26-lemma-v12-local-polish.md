# Lemma v12 — 本地环境可执行优化计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在无需外部环境（无浏览器/GUI/Docker/API Key）的前提下，完成代码质量深化、测试补全、前端细节打磨和文档更新共 6 个任务。

**Architecture:** 6 个独立可交付任务。后端质量 3 项（mypy + fuzzer 测试 + LLM Judge 测试），前端打磨 2 项（Suspense fallback + vite tree-shaking），文档 1 项。

**Tech Stack:** Python 3.11+, mypy, pytest, React 18, Vite

---

## Task 1: mypy 类型检查引入

**目标：** 为核心后端模块添加 Python 类型检查，修复 0 错误。

**Files:**
- Create: `backend/mypy.ini`
- Modify: `.github/workflows/ci.yml`（添加 mypy 步骤）
- 可能需要修改若干源文件以修复类型错误

- [ ] **Step 1: 安装 mypy**

```bash
cd backend && pip install mypy
```

- [ ] **Step 2: 创建 mypy 配置**

```ini
# backend/mypy.ini
[mypy]
python_version = 3.11
strict = False
warn_return_any = True
warn_unused_configs = True
ignore_missing_imports = True
exclude = tests/

[mypy-chromadb.*]
ignore_missing_imports = True

[mypy-tiktoken.*]
ignore_missing_imports = True

[mypy-numpy.*]
ignore_missing_imports = True

[mypy-scipy.*]
ignore_missing_imports = True

[mypy-matplotlib.*]
ignore_missing_imports = True
```

- [ ] **Step 3: 先检查核心模块**

```bash
cd backend && PYTHONPATH=src mypy src/lemma/engine/ src/lemma/api/ src/lemma/tools/ --config-file mypy.ini 2>&1 | head -50
```

预期：可能有若干类型错误，逐个修复。

- [ ] **Step 4: 修复典型类型错误**

常见错误和修复方案：

```python
# 错误: Incompatible types in assignment
# 修复前:
result = None
result = {"key": "value"}

# 修复后:
from typing import Optional
result: Optional[dict] = None
result = {"key": "value"}
```

```python
# 错误: Function is missing a return type annotation
# 修复前:
def get_status(self):

# 修复后:
def get_status(self) -> dict:
```

- [ ] **Step 5: 零错误后加入 CI**

```yaml
# .github/workflows/ci.yml — 在 backend-lint job 中添加
- name: Python type check (core modules)
  run: |
    pip install mypy
    cd backend && PYTHONPATH=src mypy src/lemma/engine/ src/lemma/api/ src/lemma/tools/ --config-file mypy.ini
```

- [ ] **Step 6: 提交**

```bash
git add backend/mypy.ini .github/workflows/ci.yml
git commit -m "feat: add mypy type checking for core modules (engine/api/tools)"
```

---

## Task 2: quality/fuzzer.py 测试补全

**目标：** `quality/fuzzer.py` 从 0% 覆盖率提升至 ≥ 50%。

**Files:**
- Read: `backend/src/lemma/quality/fuzzer.py`（理解 API）
- Create: `backend/tests/test_fuzzer.py`

- [ ] **Step 1: 阅读 fuzzer.py 理解接口**

```bash
cd backend && cat src/lemma/quality/fuzzer.py
```

关注：
- Fuzzer 类或函数名
- 输入参数
- 返回值类型
- 公开 API（`__all__` 或 `__init__.py` 导出）

- [ ] **Step 2: 编写测试**

```python
# backend/tests/test_fuzzer.py
"""模糊测试器单元测试"""
import pytest
from lemma.quality.fuzzer import Fuzzer


class TestFuzzer:
    def test_fuzzer_creation(self):
        """Fuzzer 可以实例化"""
        fuzzer = Fuzzer()
        assert fuzzer is not None

    def test_generate_valid_input(self):
        """生成有效的模糊测试输入"""
        fuzzer = Fuzzer()
        inputs = fuzzer.generate(num_cases=5)
        assert isinstance(inputs, list)
        assert len(inputs) == 5

    def test_run_fuzzing(self):
        """运行模糊测试不崩溃"""
        fuzzer = Fuzzer()

        def identity(x: str) -> str:
            return x

        results = fuzzer.run(identity, num_cases=10)
        assert isinstance(results, list)
        assert len(results) == 10

    def test_fuzzer_edge_cases(self):
        """边界情况：0 条用例"""
        fuzzer = Fuzzer()
        inputs = fuzzer.generate(num_cases=0)
        assert inputs == []

    def test_fuzzer_large_input(self):
        """大量测试用例"""
        fuzzer = Fuzzer()
        inputs = fuzzer.generate(num_cases=100)
        assert len(inputs) == 100
```

根据实际 fuzzer.py 的 API 调整以上测试的函数名和参数。

- [ ] **Step 3: 运行测试**

```bash
cd backend && PYTHONPATH=src python -m pytest tests/test_fuzzer.py -v --cov=src/lemma/quality/fuzzer --cov-report=term
```

预期：覆盖率 ≥ 50%

- [ ] **Step 4: 提交**

```bash
git add backend/tests/test_fuzzer.py
git commit -m "test: add fuzzer tests covering generation, execution, edge cases"
```

---

## Task 3: eval/llm_judge.py 测试扩展

**目标：** `eval/llm_judge.py` 从 20% 提升至 ≥ 50%。

**Files:**
- Read: `backend/src/lemma/eval/llm_judge.py`
- Modify: `backend/tests/` 中对应的测试文件（查找已有的 LLM Judge 测试）
- 或 Create: `backend/tests/test_llm_judge.py`

- [ ] **Step 1: 确认已有测试文件**

```bash
cd backend && grep -r "llm_judge\|LLMJudge" tests/ --include="*.py"
```

确认是否有 `test_llm_judge.py`，如存在则扩展，否则新建。

- [ ] **Step 2: 阅读 llm_judge.py 接口**

```bash
cd backend && cat src/lemma/eval/llm_judge.py | head -60
```

识别出：
- 类名
- `judge()` / `evaluate()` / `score()` 方法
- 输入格式（文本、评判标准）
- 输出格式（分数、详细评价）

- [ ] **Step 3: 编写 mock 测试**

```python
# backend/tests/test_llm_judge.py
"""LLM Judge 单元测试 — 用 mock 避免真实 API 调用"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from lemma.eval.llm_judge import LLMJudge


class TestLLMJudge:
    @pytest.fixture
    def mock_backend(self):
        """创建 mock LLM 后端"""
        backend = AsyncMock()
        backend.generate = AsyncMock()
        backend.generate.return_value.content = (
            '{"score": 8, "feedback": "逻辑清晰，论证充分"}'
        )
        return backend

    @pytest.mark.asyncio
    async def test_judge_returns_score(self, mock_backend):
        """评判返回合理的分数"""
        judge = LLMJudge(mock_backend)
        result = await judge.evaluate("测试文本", criteria=["清晰度", "准确性"])
        assert isinstance(result.score, (int, float))
        assert 0 <= result.score <= 10

    @pytest.mark.asyncio
    async def test_judge_handles_malformed_response(self, mock_backend):
        """LLM 返回非 JSON 时优雅降级"""
        mock_backend.generate.return_value.content = "这不是 JSON"
        judge = LLMJudge(mock_backend)
        result = await judge.evaluate("测试文本")
        assert result is not None

    @pytest.mark.asyncio
    async def test_judge_handles_empty_text(self, mock_backend):
        """空文本输入"""
        judge = LLMJudge(mock_backend)
        result = await judge.evaluate("")
        assert result is not None

    @pytest.mark.asyncio
    async def test_judge_with_custom_criteria(self, mock_backend):
        """自定义评判标准"""
        judge = LLMJudge(mock_backend)
        result = await judge.evaluate(
            "测试文本",
            criteria=["创新性", "实用性", "可复现性"],
        )
        assert result is not None
```

根据实际 API 调整类名和方法名。

- [ ] **Step 4: 运行测试**

```bash
cd backend && PYTHONPATH=src python -m pytest tests/test_llm_judge.py -v --cov=src/lemma/eval/llm_judge --cov-report=term
```

预期：覆盖率 ≥ 50%

- [ ] **Step 5: 提交**

```bash
git add backend/tests/test_llm_judge.py
git commit -m "test: expand LLM Judge test coverage with mock backend (5 tests)"
```

---

## Task 4: Suspense Fallback 改为 Skeleton

**目标：** 将 App.tsx 中 Suspense 的 "加载中…" fallback 改为 Skeleton 组件。

**Files:**
- Modify: `frontend/src/App.tsx:270-271`

- [ ] **Step 1: 找到当前 Suspense fallback**

```bash
cd frontend && grep -n "Suspense\|fallback" src/App.tsx
```

- [ ] **Step 2: 替换 fallback**

```tsx
// 修改前:
<Suspense fallback={<div className="flex items-center justify-center h-32 text-sm text-[var(--color-text-muted)]">加载中…</div>}>

// 修改后:
<Suspense fallback={<Skeleton variant="card" className="m-4" />}>
```

- [ ] **Step 3: 确认 Skeleton 已在 App.tsx 中可用**

`App.tsx` 未直接导入 Skeleton，需要添加：

```tsx
import { Skeleton } from './components/Skeleton'
```

- [ ] **Step 4: 运行前端测试确认**

```bash
cd frontend && npx vitest run
```

预期：13 files, 65 tests, all PASS

- [ ] **Step 5: 提交**

```bash
git add frontend/src/App.tsx
git commit -m "refactor: replace Suspense fallback text with Skeleton shimmer"
```

---

## Task 5: Vite 构建优化 (manualChunks)

**目标：** 配置 `vite.config.ts` 的 `manualChunks`，将大型依赖拆分为独立 chunk。

**Files:**
- Modify: `frontend/vite.config.ts`

- [ ] **Step 1: 阅读当前 vite.config.ts**

```bash
cd frontend && cat vite.config.ts
```

- [ ] **Step 2: 添加 rollupOptions**

```typescript
// frontend/vite.config.ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          'react-vendor': ['react', 'react-dom'],
          'motion-vendor': ['framer-motion'],
          'ui-vendor': ['lucide-react', 'react-hot-toast'],
          'markdown-vendor': ['react-markdown', 'react-syntax-highlighter'],
          'virtuoso-vendor': ['react-virtuoso'],
        },
      },
    },
  },
})
```

- [ ] **Step 3: 测试构建**

```bash
cd frontend && npm run vite:build 2>&1 | tail -10
```

检查 `dist/` 目录下的 chunk 拆分是否正确：

```bash
ls -la dist/assets/ | grep ".js"
```

预期看到多个 vendor chunk（react-vendor-xxx.js, motion-vendor-xxx.js 等）

- [ ] **Step 4: 提交**

```bash
git add frontend/vite.config.ts
git commit -m "perf: add manualChunks to vite build for better code splitting"
```

---

## Task 6: 文档更新

**目标：** 更新 USER_GUIDE.md、CHANGELOG.md 和 README.md。

**Files:**
- Modify: `docs/USER_GUIDE.md`
- Modify: `CHANGELOG.md`
- Modify: `README.md`

- [ ] **Step 1: 更新 CHANGELOG.md**

在 CHANGELOG.md 顶部添加 v11 条目：

```markdown
## [5.2.0] - 2026-06-26

### Added
- **前端设计系统**: Toast 通知、Skeleton 骨架屏、ConfirmDialog 确认框
- **学术字体**: Crimson Pro (标题) + Atkinson Hyperlegible (正文)
- **品牌升级**: Logo ⊢ 符号，全部 Emoji 替换为 SVG 图标
- **亮色主题**: Sun/Moon 切换器 + 系统主题跟随
- **页面转场**: framer-motion 平滑视图切换
- **代码分割**: React.lazy + Suspense 按需加载
- **高对比度模式**: @media (prefers-contrast: high) 支持
- **SVG 可访问性**: 8 个 Agent 角色全部添加 role="img" + aria-label

### Changed
- 品牌更名：UltraAgent/UltraMath → Lemma
- Python 包名：ultramath → lemma
- "加载中…" 全部替换为 Skeleton 骨架屏
- 删除会话需 ConfirmDialog 二次确认

### Fixed
- RAG Collection Name 不匹配导致知识检索不工作
- 前端视图切换无转场动画
```

- [ ] **Step 2: 更新 README.md 功能列表**

在 README.md 的"功能"部分添加新特性：

```markdown
- 🎨 **亮色/暗色双主题**：一键切换，跟随系统偏好
- 🔔 **Toast 通知系统**：成功/错误/警告/信息四种反馈
- 💀 **Skeleton 骨架屏**：加载时展示优雅占位动画
- ⚠️ **确认对话框**：破坏性操作二次确认
- ✨ **页面转场**：平滑视图切换动画
- 🎯 **学术字体**：Crimson Pro + Atkinson Hyperlegible 专业排版
- 📦 **代码分割**：按需加载，首屏更快
```

- [ ] **Step 3: 运行前端测试确认文档不影响代码**

```bash
cd frontend && npx vitest run
```

- [ ] **Step 4: 提交**

```bash
git add CHANGELOG.md README.md docs/USER_GUIDE.md
git commit -m "docs: update CHANGELOG for v5.2.0, README features, and user guide"
```

---

## Self-Review

**规格覆盖:**
- mypy 类型检查 → Task 1 ✅
- fuzzer 测试 → Task 2 ✅
- LLM Judge 测试 → Task 3 ✅
- Suspense fallback → Task 4 ✅
- vite tree-shaking → Task 5 ✅
- 文档更新 → Task 6 ✅

**占位符扫描:** 无 TBD/TODO。测试代码需要根据实际 API 调整函数名（已在 Task 2/3 中标注）✅

---

## 执行交接

计划已保存至 `docs/superpowers/plans/2026-06-26-lemma-v12-local-polish.md`。

6 个任务完全独立，可任意顺序执行。建议先 Task 1 (mypy) → Task 2 (fuzzer) → Task 3 (LLM Judge) 完成后端质量三件套，再处理前端和文档。
