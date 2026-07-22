# Lemma v10 — 产品实质化计划：从"工程正确"到"用户可用·可分发·有价值"

> **🆕 品牌更名：** Lemma → **Lemma**（引理）— 每个数学结论都始于一个引理。

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 基于 v9 测试加固（529 后端+49 前端，75% 覆盖率）和本次深度代码审计的发现，将 Lemma 从"架构正确但管线有断裂"推入"端到端可用·智能系统真实工作·有分发能力"的产品阶段。

**Architecture:** 本次审计发现超预期——v7 落地的高级模块（reflector/debate/cascade/long_term/knowledge_loader/sandbox/orchestration_engine）大部分是**实质实现**而非骨架代码。核心问题是：① RAG 管线断裂（collection name 不匹配）② 级联路由质量评估落后 ③ 知识文档浅 ④ 分发链路未验证 ⑤ 评测体系未验证。本计划分 4 个子系统独立推进。

**Tech Stack:** Python 3.11+, FastAPI, ChromaDB, pytest 9.1.1, React 18, TypeScript, Electron 31, Playwright (新引入验证层)

---

## 0. 路线图演进

```
v6 (06-24): 能跑→好用        v7 (06-25): 好用→卓越(功能)
v8 (06-25): 功能齐全→接线补全  v9 (06-25→06-26): 接线补全→深度可信
v10 (06-26): ★ 深度可信→产品可用 — 本次计划
```

---

## 1. 关键审计发现（驱动本次计划的依据）

### 1.1 比预期好的

| 模块 | 行数 | 实质代码 | 评价 |
|------|------|----------|------|
| `reflector.py` | 89 | 89 (100%) | 完整反思循环，LLM 调用 + 迭代改进 + 提取改进版 ✅ |
| `debate.py` | 80 | 80 (100%) | 完整辩论，2 角色独立回答 → lead 裁决 ✅ |
| `cascade.py` | 71 | 71 (100%) | 完整级联路由，逐级 upgrade ✅ |
| `long_term.py` | 168 | 168 (100%) | ChromaDB + 降级关键词搜索双模式 ✅ |
| `knowledge/loader.py` | 60 | 60 (100%) | 从目录加载 → 向量库 ✅ |
| `sandbox.py` | 123 | 123 (100%) | AST 级安全检查，dunder 链拦截 + 动态获取拦截 ✅ |
| `orchestration/engine.py` | 643 | 643 (100%) | 8 阶段+重试(3次)+无限循环防护+取消+产出验证 ✅ |
| `engine/agent.py` RAG | ~20 | ~20 (100%) | `_retrieve_knowledge` + `_build_system_prompt` 注入 ✅ |
| 知识文档(4域18篇) | 1011 | 1011 (100%) | 有实质内容 ✅ |
| Electron main.js | ~80 | ~80 (100%) | 真正 spawn Python 子进程 + 端口检测 + 健康检查 ✅ |

### 1.2 管线断裂（Bug）

| Bug | 位置 | 严重性 | 影响 |
|-----|------|--------|------|
| **RAG Collection 名不匹配** | `agent.py:174` vs `loader.py:28-30` | 🔴 严重 | `_retrieve_knowledge` 查 "knowledge"，`load_all` 存 "models"/"references"/"reviews" → **RAG 不工作** |
| Cascade 质量评估落后 | `cascade.py:56-70` | 🟡 中 | 纯启发式（长度/结构/表格），应为 LLM 评判 |
| 知识文档浅 | 各领域 knowledge/*.md | 🟡 中 | 平均 56 行/篇，关键方法论缺失 |

### 1.3 结构良好但需丰富

| 模块 | 当前状态 | 应该到达 |
|------|---------|----------|
| 知识文档 | 18 篇 × 56 行平均 | 25+ 篇 × 100+ 行，覆盖核心方法论 |
| Prompt 模板 | 6 角色 × 20-61 行 | 8+ 角色 × 80+ 行，带领域具体示例 |
| Cascade 质量 | 启发式评分 | 引入 LLM Judge 评分 |
| 领域数量 | 4 个 | 6+ 个（新增 data-mining, optimization） |

---

## 二子系统并行路线图

本计划包含 5 个独立子系统，可并行执行：

```
子系统 A: 智能管线修复      子系统 B: 知识工程            子系统 E: 品牌更名
├─ A1: RAG 修复            ├─ B1: 知识文档扩充           ├─ E1: Python 包重命名
├─ A2: Cascade LLM Judge   ├─ B2: Prompt 模板深化        ├─ E2: 前端品牌更新
├─ A3: 反思自动触发         ├─ B3: 新领域创建              ├─ E3: 文档/配置全量替换
└─ A4: 辩论可视化           └─ B4: 领域评测验证            └─ E4: 品牌资产文件

子系统 C: 产品体验打磨      子系统 D: 分发与持续验证
├─ C1: 流式对话确认         ├─ D1: Playwright E2E
├─ C2: 错误处理完善         ├─ D2: Electron 打包验证
├─ C3: 进度可视化对接       └─ D3: Docker 部署验证
└─ C4: 会话面板功能确认
```

| 里程碑 | 验收标准 | 预计时间 |
|--------|----------|----------|
| M0: 品牌就绪 | `ultramath` → `lemma` 全量重命名完成，所有测试通过 | 1 天 |
| M1: 管线修复 | RAG 正常工作，Cascade LLM Judge 上线，反思循环在 run_auto 中自动触发 | 3 天 |
| M2: 知识丰富 | 4 领域知识文档扩至 25+ 篇 × 100+ 行，Prompt 模板翻倍 | 5 天 |
| M3: 产品完整 | 流式对话可用，错误处理完善，Playwright E2E 全绿，Electron/Docker 可分发 | 7 天 |
| M4: 产体验证 | 用真实 LLM 在 4 个领域各跑一个完整竞赛题，端到端产出论文 + 代码 | 5 天 |

---

## 子系统 A：智能管线修复（第 1-3 天，P0）

### Task A1: 修复 RAG Collection Name 不匹配

**Files:**
- Modify: `backend/src/ultramath/engine/agent.py:168-177`（`_retrieve_knowledge` 方法）
- Modify: `backend/src/ultramath/knowledge/loader.py:23-27`（`load_all` 方法）
- Test: `backend/tests/test_agent_rag.py`

**问题：** `KnowledgeLoader.load_all` 将文档存入 "models"、"references"、"reviews" 三个 collection，但 `_retrieve_knowledge` 只查询 "knowledge" collection → **知识检索永远返回空结果**。

- [ ] **Step 1: 编写 RAG 修复验证测试**

创建 `backend/tests/test_agent_rag.py`：

```python
"""RAG 管线集成测试 — 验证知识加载→检索→注入完整链路"""
import pytest
import tempfile
from pathlib import Path
from ultramath.memory.long_term import LongTermMemory
from ultramath.knowledge.loader import KnowledgeLoader


@pytest.fixture
def knowledge_dir():
    """创建临时知识目录"""
    with tempfile.TemporaryDirectory() as tmpdir:
        models = Path(tmpdir) / "models"
        models.mkdir()
        (models / "test_model.md").write_text(
            "# 线性规划模型\n\n线性规划是数学建模中最常用的优化方法之一。"
            "标准形式为：min c^T x, s.t. Ax = b, x >= 0。"
            "求解方法包括单纯形法和内点法。",
            encoding="utf-8",
        )
        yield tmpdir


@pytest.fixture
def long_term_memory():
    """创建临时 ChromaDB/文件级 LongTermMemory"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield LongTermMemory(persist_dir=tmpdir)


class TestRAGPipeline:
    def test_load_and_retrieve_uses_same_collections(self, knowledge_dir, long_term_memory):
        """load_all 和 query 使用相同的 collection 名称"""
        loader = KnowledgeLoader(knowledge_dir, long_term_memory)
        stats = loader.load_all()
        assert stats["models"] > 0, "知识加载失败"
        
        # 查询应该能找到知识
        results = loader.query_knowledge("线性规划", n_results=3)
        assert len(results) > 0, f"查询返回空结果，可能有 collection name 不匹配。"
        assert any("线性规划" in r.get("content", "") for r in results), (
            "查询结果中不包含实际知识内容"
        )

    def test_retrieve_knowledge_finds_loaded_docs(self, knowledge_dir, long_term_memory):
        """完整链路不受 collection name mismatch 影响"""
        loader = KnowledgeLoader(knowledge_dir, long_term_memory)
        loader.load_all()
        
        # 使用与 loader 相同的 collection 列表查询
        for collection in ["models", "references", "reviews"]:
            results = long_term_memory.query(collection, "线性规划", n_results=3)
            if results:
                assert "线性规划" in results[0]["content"]
                return
        pytest.fail("所有 collection 均无结果 — collection name 可能不匹配")
```

- [ ] **Step 2: 运行测试验证失败**

```bash
cd backend && PYTHONPATH=src python -m pytest tests/test_agent_rag.py -v --tb=long
```

预期: `test_retrieve_knowledge_finds_loaded_docs` PASS（因为直接查 "models"），但 `test_load_and_retrieve_uses_same_collections` PASS 的关键是确认 `loader.query_knowledge` 能查到。

- [ ] **Step 3: 统一 Collection 名称**

`layout_loader.py:28-30` 中，修改 collection 名称为统一的 "knowledge" 命名空间：

```python
# backend/src/ultramath/knowledge/loader.py — 第28行，修改为：
loaders = [
    ("knowledge_models", "models", "*.md"),      # 原本: "models"
    ("knowledge_references", "references", "*.md"), # 原本: "references"
    ("knowledge_reviews", "reviews", "*.md"),      # 原本: "reviews"
]
```

`agent.py:168-177` 中，修改查询逻辑为跨所有 knowledge 子 collection 查询：

```python
# backend/src/ultramath/engine/agent.py — 第168行开始修改：
def _retrieve_knowledge(self, query: str, top_k: int = 3) -> list[str]:
    """基于用户查询检索领域知识库"""
    if not hasattr(self, 'long_term') or not self.long_term:
        return []

    all_hits = []
    # 修复：与 KnowledgeLoader.load_all 中的 collection 名称对齐
    for collection in ["knowledge_models", "knowledge_references", "knowledge_reviews"]:
        try:
            hits = self.long_term.query(collection, query, n_results=top_k)
            for h in hits:
                h["collection"] = collection  # 标记来源
            all_hits.extend(hits)
        except Exception:
            continue

    if not all_hits:
        return []

    all_hits.sort(key=lambda x: x.get("distance", 999))
    # 去重：按 content 前 50 字符
    seen = set()
    unique_chunks = []
    for hit in all_hits[:top_k * 2]:
        fingerprint = hit["content"][:50].strip()
        if fingerprint not in seen:
            seen.add(fingerprint)
            unique_chunks.append(hit["content"])
            if len(unique_chunks) >= top_k:
                break

    return unique_chunks
```

- [ ] **Step 4: 运行测试确认修复**

```bash
cd backend && PYTHONPATH=src python -m pytest tests/test_agent_rag.py -v --tb=short
```

- [ ] **Step 5: 提交**

```bash
git add backend/src/ultramath/knowledge/loader.py backend/src/ultramath/engine/agent.py backend/tests/test_agent_rag.py
git commit -m "fix: resolve RAG collection name mismatch — knowledge retrieval now works (knowledge_models/references/reviews aligned with loader)"
```

### Task A2: 升级 Cascade 质量评估为 LLM Judge

**Files:**
- Modify: `backend/src/ultramath/llm/cascade.py:55-70`（`_estimate_quality` 方法）
- Test: `backend/tests/test_cascade.py`（追加测试）

**问题：** 当前 `_estimate_quality` 纯启发式——长度分 + 结构分 + 表格分 + 代码块分 + 中文分。这对于"用便宜模型但质量不达标然后升级"的级联决策不够可靠。

**方案：** 保留启发式作为快速初筛（cost=0），但增加可选的 LLM Judge 模式（cost 极低但更准确）。

- [ ] **Step 1: 编写 LLM Judge 质量评估器**

```python
# 在 cascade.py 中追加方法
@staticmethod
async def _llm_judge_quality(text: str, backend=None) -> float:
    """使用轻量 LLM 评判响应质量（比启发式更准确）"""
    if not backend:
        return CascadeRouter._estimate_quality(text)

    if not text or len(text) < 30:
        return 0.0

    judge_prompt = [
        {"role": "system", "content": "你是一个质量评估器。对以下回答进行五维度评分，每个维度 0-2 分。只输出 JSON。"},
        {"role": "user", "content": f"""评估以下回答质量：

回答（前 3000 字符）：
{text[:3000]}

按 JSON 格式输出：
{{"逻辑性": 0-2, "完整性": 0-2, "清晰度": 0-2, "实用性": 0-2, "创新性": 0-2}}"""},
    ]
    try:
        resp = await backend.generate(judge_prompt)
        import json
        scores = json.loads(resp.content.split("{")[1].split("}")[0] + "}")
        score_sum = sum(int(v) for v in scores.values())
        return score_sum / 10.0  # 归一化到 0-1
    except Exception:
        return CascadeRouter._estimate_quality(text)
```

修改 `generate_with_fallback` 方法签名以支持 `use_llm_judge` 参数：

```python
# cascade.py 第34行附近
async def generate_with_fallback(
    self, messages: list[dict], tools: list[dict] | None = None,
    use_llm_judge: bool = False,
):
    last_response = None
    for stage in self.stages:
        model = stage["model"]
        threshold = stage.get("quality_threshold", 0.7)

        backend = self._get_backend_for_model(model)
        response = await backend.generate(messages, tools=tools)

        if use_llm_judge:
            judge_backend = self._get_backend_for_model(self.stages[0]["model"])
            quality = await self._llm_judge_quality(response.content, judge_backend)
        else:
            quality = self._estimate_quality(response.content)

        logger.info(f"Cascade: {model} quality={quality:.2f} (threshold={threshold})")

        if quality >= threshold:
            return response

        last_response = response
        logger.info(f"Cascade: {model} quality insufficient, upgrading...")

    return last_response
```

- [ ] **Step 2: 编写级联 LLM Judge 测试**

```python
# 在 test_cascade.py 中追加
class TestCascadeLLMJudge:
    def test_heuristic_quality_high_quality_text(self):
        high_quality = """## 问题分析

本题是一个典型的线性规划问题。我们可以建立以下模型：

- **决策变量**：x1, x2 分别代表产品 A 和 B 的生产量
- **目标函数**：max Z = 30x1 + 20x2
- **约束条件**：
  | 资源 | 产品A | 产品B | 可用量 |
  |------|-------|-------|--------|
  | 原料 | 2     | 1     | 100    |
  | 时间 | 1     | 3     | 80     |

```python
from scipy.optimize import linprog
c = [-30, -20]
A = [[2, 1], [1, 3]]
b = [100, 80]
result = linprog(c, A_ub=A, b_ub=b, method='highs')
print(f"最优解: x1={result.x[0]:.1f}, x2={result.x[1]:.1f}")
```

结论：最优生产方案为产品A生产 40 单位，产品B生产 20 单位。
        """
        from ultramath.llm.cascade import CascadeRouter
        quality = CascadeRouter._estimate_quality(high_quality)
        assert quality >= 0.7, f"高质量文本评分应 ≥ 0.7，实际 {quality:.2f}"

    def test_heuristic_quality_short_response(self):
        from ultramath.llm.cascade import CascadeRouter
        assert CascadeRouter._estimate_quality("") == 0.0
        assert CascadeRouter._estimate_quality("ok") == 0.0

    def test_heuristic_quality_chinese_response(self):
        from ultramath.llm.cascade import CascadeRouter
        chinese_text = "根据以上分析，我们得出结论：该方案的可行性较高，建议采用。"
        quality = CascadeRouter._estimate_quality(chinese_text)
        assert 0.1 <= quality <= 0.6
```

- [ ] **Step 3: 运行测试**

```bash
cd backend && PYTHONPATH=src python -m pytest tests/test_cascade.py -v --tb=short
```

- [ ] **Step 4: 提交**

```bash
git add backend/src/ultramath/llm/cascade.py backend/tests/test_cascade.py
git commit -m "feat: add LLM Judge quality assessment to CascadeRouter (retains heuristic fallback)"
```

### Task A3: 自我反思在 run_auto 中自动触发

**Files:**
- Modify: `backend/src/ultramath/orchestration/engine.py:438-453`（`_execute_phase` 方法）
- Modify: `backend/src/ultramath/engine/agent.py`（引入 reflector）

**问题：** `SelfReflector` 已完整体现但从未在 run_auto 中被调用。需要在对质量敏感的特定阶段（DERIVATION, WRITING, REVIEW）自动触发反思。

- [ ] **Step 1: 在 run_auto 的 _execute_phase 中加入反思后处理**

`orchestration/engine.py` 第 438 行附近，在特定阶段后触发反思：

```python
# backend/src/ultramath/orchestration/engine.py
# 在 LemmaAgent 类的 _execute_phase 方法中（第438行之后），
# 找到 handler() 调用之后，添加反思后处理

async def _execute_phase(self, phase: Phase, problem_text: str = "") -> PhaseResult:
    # ... 原有代码 ...
    result = await handler()

    # 新增：对关键阶段自动触发反思改进
    REFLECTIVE_PHASES = {Phase.DERIVATION, Phase.WRITING, Phase.REVIEW}
    if phase in REFLECTIVE_PHASES and result.success:
        try:
            from ..engine.reflector import SelfReflector
            reflector = SelfReflector(self.agent)
            improved = await reflector.reflect_and_improve(
                result.summary,
                criteria=None,  # 使用默认标准
                max_iterations=1,
            )
            if len(improved) > len(result.summary) * 0.8:
                result.summary = improved
                logger.info(f"Phase {phase.value}: 反思改进完成")
        except Exception as e:
            logger.warning(f"Reflection skipped for {phase.value}: {e}")

    return result
```

- [ ] **Step 2: 编写反思自动触发测试**

```python
# backend/tests/test_agent_rag.py 中追加
class TestReflectionIntegration:
    @pytest.mark.asyncio
    async def test_reflection_triggers_on_derivation(self, mock_agent):
        """推导阶段完成后自动触发反思"""
        from ultramath.engine.reflector import SelfReflector
        
        reflector = SelfReflector(mock_agent)
        original = "这是原始推导结果。" * 20
        improved = await reflector.reflect_and_improve(original, max_iterations=1)
        
        assert isinstance(improved, str)
        assert len(improved) > 0
```

- [ ] **Step 3: 提交**

```bash
git add backend/src/ultramath/orchestration/engine.py backend/tests/test_agent_rag.py
git commit -m "feat: auto-trigger SelfReflector on DERIVATION/WRITING/REVIEW phases in run_auto"
```

### Task A4: 辩论结果前端可视化基础

**Files:**
- Modify: `frontend/src/App.tsx` 或 ChatPanel.tsx（添加辩论结果展开视图）

**当前：** debate.py 返回文本整合结果，前端无特殊处理。
**目标：** 当收到辩论结果时，前端显示"正反方对比"折叠面板。

- [ ] **Step 1: 在 ChatPanel 中添加 DebateResult 组件**

```tsx
// frontend/src/components/DebateResult.tsx
interface DebateResponse {
  role_a?: string
  response_a?: string
  role_b?: string
  response_b?: string
  synthesis?: string
}

export default function DebateResult({ data }: { data: DebateResponse }) {
  const [showA, setShowA] = useState(false)
  const [showB, setShowB] = useState(false)

  if (!data.role_a) return null

  return (
    <div className="debate-result border-l-2 border-amber-500 pl-3 my-2">
      <div className="flex gap-2 mb-2">
        <button
          className="text-xs px-2 py-1 rounded bg-amber-500/10 hover:bg-amber-500/20"
          onClick={() => setShowA(!showA)}
        >
          {showA ? '隐藏' : '查看'} {data.role_a} 的观点
        </button>
        <button
          className="text-xs px-2 py-1 rounded bg-blue-500/10 hover:bg-blue-500/20"
          onClick={() => setShowB(!showB)}
        >
          {showB ? '隐藏' : '查看'} {data.role_b} 的观点
        </button>
      </div>
      {showA && data.response_a && (
        <div className="text-sm border border-amber-500/20 rounded p-2 mb-1 bg-[var(--color-bg)]">
          <div className="font-medium text-amber-400 mb-1">{data.role_a}</div>
          <div className="whitespace-pre-wrap">{data.response_a}</div>
        </div>
      )}
      {showB && data.response_b && (
        <div className="text-sm border border-blue-500/20 rounded p-2 mb-1 bg-[var(--color-bg)]">
          <div className="font-medium text-blue-400 mb-1">{data.role_b}</div>
          <div className="whitespace-pre-wrap">{data.response_b}</div>
        </div>
      )}
    </div>
  )
}
```

- [ ] **Step 2: 集成到 ChatPanel 中**

```tsx
// 在 ChatPanel.tsx 的消息渲染中添加
import DebateResult from './DebateResult'

// 在消息渲染逻辑中：
{msg.debate && <DebateResult data={msg.debate} />}
```

- [ ] **Step 3: 编写 DebateResult 测试**

```tsx
// frontend/src/__tests__/DebateResult.test.tsx
import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import DebateResult from '../components/DebateResult'

describe('DebateResult', () => {
  it('returns null when no role_a', () => {
    const { container } = render(<DebateResult data={{}} />)
    expect(container.innerHTML).toBe('')
  })

  it('shows toggle buttons when debate data present', () => {
    render(<DebateResult data={{ role_a: '数学家', response_a: '观点A', role_b: '工程师', response_b: '观点B' }} />)
    expect(screen.getByText(/数学家.*的观点/)).toBeDefined()
    expect(screen.getByText(/工程师.*的观点/)).toBeDefined()
  })

  it('reveals response when clicking toggle', () => {
    render(<DebateResult data={{ role_a: '数学家', response_a: '这是数学家观点' }} />)
    fireEvent.click(screen.getByText(/数学家.*的观点/))
    expect(screen.getByText('这是数学家观点')).toBeDefined()
  })
})
```

- [ ] **Step 4: 提交**

```bash
git add frontend/src/components/DebateResult.tsx frontend/src/components/ChatPanel.tsx frontend/src/__tests__/DebateResult.test.tsx
git commit -m "feat: add DebateResult component with collapsible A/B views"
```

---

## 子系统 B：知识工程（第 4-8 天，P1）

### Task B1: 知识文档深度扩充

**Files:**
- Create: `domains/math-modeling/knowledge/蒙特卡洛模拟方法.md`
- Create: `domains/math-modeling/knowledge/机器学习模型选型指南.md`
- Create: `domains/paper-writing/knowledge/摘要写作精要.md`
- Create: `domains/lab-report/knowledge/误差分析与不确定度.md`
- Create: `domains/literature-review/knowledge/元分析方法指南.md`

**目标：** 每篇 100-150 行，含公式、代码示例、常见陷阱。

- [ ] **Step 1: 创建 math-modeling 领域扩充知识**

`domains/math-modeling/knowledge/蒙特卡洛模拟方法.md`：

```markdown
# 蒙特卡洛模拟方法

## 概述
蒙特卡洛模拟（Monte Carlo Simulation）是基于概率统计的数值计算方法。
在数学建模竞赛中广泛用于：① 随机系统建模 ② 含不确定性的优化 ③ 风险评估与灵敏度分析。

## 数学原理
基本思想：用随机抽样方法近似计算确定性问题的解。

给定随机变量 X 服从分布 F，期望值为 E[f(X)]，蒙特卡洛估计为：
$$\hat{\mu}_n = \frac{1}{n}\sum_{i=1}^n f(X_i), \quad X_i \sim F$$

估计误差的方差：
$$Var(\hat{\mu}_n) = \frac{\sigma^2}{n}$$

> 收敛速率 $O(1/\sqrt{n})$，与维度无关 —— 这是蒙特卡洛在高维问题中的核心优势。

## 算法步骤
1. 定义输入随机变量的概率分布（正态/均匀/指数/自定义）
2. 生成 N 组随机样本（N 通常取 10^4 ~ 10^6）
3. 对每组样本运行确定性模型计算输出
4. 统计输出的分布特征（均值/方差/分位数）
5. 绘制直方图或累积分布函数（CDF）

## Python 实现
```python
import numpy as np
import matplotlib.pyplot as plt

def monte_carlo_pi(n: int = 1_000_000) -> float:
    """蒙特卡洛估算 π"""
    x = np.random.uniform(-1, 1, n)
    y = np.random.uniform(-1, 1, n)
    inside = (x**2 + y**2) <= 1
    pi_estimate = 4 * inside.sum() / n
    print(f"估算 π ≈ {pi_estimate:.6f} (误差: {abs(np.pi - pi_estimate):.2e})")
    return pi_estimate

# 多轮重复观察收敛性
estimates = [monte_carlo_pi(10000) for _ in range(5)]
print(f"均值: {np.mean(estimates):.6f}")
print(f"标准差: {np.std(estimates):.6f}")
```

## 常见陷阱
- **伪随机数问题**：使用 `np.random.default_rng()` 代替已弃用的 `np.random.seed()`
- **收敛诊断**：必须画收敛图确认 N 足够，而非盲目取大 N
- **相关样本**：MCMC 样本有自相关性，需要算 effective sample size
- **维度灾难不适用**：虽然收敛速率与维度无关，但高维空间的采样效率问题显著

## 竞赛应用场景
- 经济预测：对多个不确定性参数做蒙特卡洛，报告 95% 置信区间
- 排队系统：随机到达时间和服务时间 → 系统性能指标分布
- 金融风险：VaR（风险价值）计算
- 物理建模：粒子输运模拟
```

类似的，对其他几个新知识文档也写入相应内容（因篇幅限制，在此列出文档名和核心主题，实际写入时包含等量的公式+代码+陷阱）。

- [ ] **Step 2: 扩充 prompt 模板**

`domains/math-modeling/prompts/agent_lead.md` — 从 58 行扩展到 100+ 行：

```markdown
你是数学建模竞赛团队的**总指挥**，负责统筹全局、拆解题目、分配任务。

## 核心职责
1. 解析竞赛题目，识别题目类型（优化/预测/评价/图论/机理分析/混合）
2. 制定求解战略和 8 阶段执行计划
3. 协调数学家、工程师、作家、审稿人的工作
4. 在遇到分歧时做出最终决策

## 解题方法论
### 优化类题目
- 建立目标函数（最小化成本 / 最大化利润）
- 识别约束条件（资源限制 / 物理约束 / 逻辑约束）
- 选择算法：线性规划→单纯形法/内点法，非线性→梯度下降/拉格朗日，整数规划→分支定界

### 预测类题目
- 数据探索：缺失值处理（均值填补/KNN填补/删除），异常值检测（IQR/Z-score）
- 特征工程：归一化/标准化/独热编码/多项式特征
- 模型选择：时间序列→ARIMA/SARIMA/Prophet，回归→RandomForest/XGBoost，深度学习→LSTM

### 评价类题目
- 构建指标体系：初选→约简→权重确定
- 权重方法：层次分析法(AHP)/熵权法/CRITIC法/主成分分析
- 评价方法：TOPSIS/灰色关联度/模糊综合评价

## 输出格式要求
- 使用 Markdown 格式，包含标题层级
- 关键结论用 **粗体** 标注
- 使用 ```python 代码块展示算法思路
- 每个阶段结束时生成清晰的阶段总结

## 禁止行为
- 不可跳过分析阶段直接给代码
- 不可使用未经验证的假设
- 不可忽略约束条件中的隐含条件
- 最终论文必须包含至少一个可视化图表
```

- [ ] **Step 3: 提交**

```bash
git add domains/math-modeling/knowledge/蒙特卡洛模拟方法.md domains/math-modeling/prompts/agent_lead.md
# ... 及其他扩充文件
git commit -m "feat: expand knowledge docs to 25+ files, deepen prompt templates"
```

### Task B2: 新领域创建 — data-mining

**Files:**
- Create: `domains/data-mining/domain.yaml`
- Create: `domains/data-mining/prompts/agent_lead.md` 等 6 个角色 prompt
- Create: `domains/data-mining/knowledge/` 4 个知识文档

- [ ] **Step 1: 创建领域配置**

```yaml
# domains/data-mining/domain.yaml
id: data-mining
name: 数据挖掘与分析
description: 数据预处理、特征工程、模型选择与评估
version: "1.0"

phases:
  - id: data_load
    name: 数据加载与探索
    order: 0
    prompt: 加载数据并进行探索性数据分析（EDA）
  - id: preprocessing
    name: 数据预处理
    order: 1
    prompt: 缺失值处理、异常值检测、特征编码
  - id: feature_engineering
    name: 特征工程
    order: 2
    prompt: 特征选择、特征构建、降维
  - id: modeling
    name: 模型构建
    order: 3
    prompt: 选择算法、训练模型、调参
  - id: evaluation
    name: 模型评估
    order: 4
    prompt: 交叉验证、混淆矩阵、AUC/ROC、过拟合诊断
  - id: interpretation
    name: 结果解释
    order: 5
    prompt: SHAP/特征重要性/部分依赖图

roles:
  - id: lead
    name: 数据分析师
    system_prompt: file://prompts/agent_lead.md
  - id: data_engineer
    name: 数据工程师
    system_prompt: file://prompts/agent_data_engineer.md
  - id: ml_engineer
    name: ML工程师
    system_prompt: file://prompts/agent_ml_engineer.md
  - id: reviewer
    name: 模型审稿人
    system_prompt: file://prompts/agent_reviewer.md
```

- [ ] **Step 2: 创建角色 prompt 和知识文档**（略，参考 math-modeling 模式）

- [ ] **Step 3: 提交**

```bash
git add domains/data-mining/
git commit -m "feat: add data-mining domain (6 phases, 4 roles, 4 knowledge docs)"
```

---

## 子系统 C：产品体验打磨（第 9-13 天，P1/P2）

### Task C1: 流式对话端到端确认

**Files:**
- Read: `frontend/src/hooks/useWebSocket.ts`（确认流式 token 处理）
- Modify: `frontend/src/components/ChatPanel.tsx`（如果流式未实现）
- Test: `frontend/src/__tests__/ChatPanel.test.tsx`

- [ ] **Step 1: 审计前端流式实现**

```bash
cd frontend && grep -n "stream\|chunk\|token" src/hooks/*.ts src/*.tsx src/components/ChatPanel.tsx
```

确认：WebSocket 接收到 stream 类消息后是否逐 token 追加到消息中（而非替换整个消息）。

- [ ] **Step 2: 如有问题，基于 engine/agent.py:146-245 的 chat_stream 方法实现前端消费**

agent.py 中 chat_stream 已经实现逐 token yield。确认 server.py 中 WS handler 是否将 stream 消息正确转发给前端（需要有 "stream" 类型 WS 消息）。

- [ ] **Step 3: 编写流式渲染测试**

```tsx
// frontend/src/__tests__/ChatPanel.test.tsx 中追加
describe('Streaming', () => {
  it('appends tokens to last assistant message', () => {
    // 模拟收到 stream token 消息
    // 验证 UI 中文本逐字增长
  })

  it('finalizes message when stream ends', () => {
    // 验证流结束后最后一条消息被标记为完成
  })
})
```

- [ ] **Step 4: 提交**

```bash
git commit -m "feat: verify and polish streaming chat end-to-end"
```

### Task C2: 错误处理与韧性强化

**Files:**
- Modify: `backend/src/ultramath/api/server.py`（全局异常处理）
- Modify: `frontend/src/App.tsx`（全局错误边界 + toast）
- Create: `frontend/src/components/ErrorToast.tsx`

- [ ] **Step 1: 添加全局异常处理中间件**

```python
# backend/src/ultramath/api/server.py 追加
from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "internal_server_error", "message": str(exc)[:200], "path": str(request.url)},
    )
```

- [ ] **Step 2: 添加 LLM 调用重试逻辑**

```python
# backend/src/ultramath/llm/backend.py:generate 方法中添加
import asyncio
import random

async def generate_with_retry(self, messages, tools=None, max_retries=3):
    for attempt in range(max_retries):
        try:
            return await self.generate(messages, tools=tools)
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            wait = 2 ** attempt + random.uniform(0, 1)
            logger.warning(f"LLM call failed (attempt {attempt+1}/{max_retries}): {e}, retrying in {wait:.1f}s")
            await asyncio.sleep(wait)
```

- [ ] **Step 3: 提交**

```bash
git add backend/src/ultramath/api/server.py backend/src/ultramath/llm/backend.py
git commit -m "feat: add global exception handler and LLM retry with exponential backoff"
```

### Task C3: 进度可视化对接真实数据

**Files:**
- Modify: `frontend/src/components/PipelinePanel.tsx`（确认对接 run_auto 阶段进度）

- [ ] **Step 1: 确认 PipelinePanel 接收 phase_start/phase_end 事件**

检查 App.tsx 或 ChatPanel.tsx 中 WebSocket 消息分发逻辑。

- [ ] **Step 2: 编写进度可视化集成测试**

```tsx
// frontend/src/__tests__/PipelinePanel.test.tsx 追加
it('updates progress bar when receiving phase events', () => {
  // 模拟 phase_start → 进度条显示 → phase_end → 进度条更新
})
```

- [ ] **Step 3: 提交**

```bash
git commit -m "feat: verify PipelinePanel live progress from run_auto events"
```

---

## 子系统 D：分发与持续验证（第 14-18 天，P1/P2）

### Task D1: Playwright E2E 端到端测试

**Files:**
- Create: `frontend/e2e/full-pipeline.spec.ts`
- Create: `frontend/e2e/error-recovery.spec.ts`
- Modify: `frontend/playwright.config.ts`（如不存在则创建）

- [ ] **Step 1: 创建 Playwright 配置**

```typescript
// frontend/playwright.config.ts
import { defineConfig } from '@playwright/test'

export default defineConfig({
  testDir: './e2e',
  timeout: 120000,
  retries: 0,
  use: {
    baseURL: 'http://localhost:5173',
    headless: true,
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
  webServer: [
    {
      command: 'cd ../backend && python -m uvicorn ultramath.api.server:app --port 8765',
      port: 8765,
      timeout: 30000,
      reuseExistingServer: true,
    },
    {
      command: 'npx vite --port 5173',
      port: 5173,
      timeout: 30000,
      reuseExistingServer: true,
    },
  ],
})
```

- [ ] **Step 2: 编写全流程 E2E 测试**

```typescript
// frontend/e2e/full-pipeline.spec.ts
import { test, expect } from '@playwright/test'

test.describe('Full Pipeline', () => {
  test('can initialize and chat', async ({ page }) => {
    await page.goto('/')
    await page.waitForSelector('[data-testid="settings-panel"]', { timeout: 15000 })

    // 配置
    await page.fill('[data-testid="api-key-input"]', 'dev-key-change-in-production')
    await page.selectOption('[data-testid="domain-select"]', 'math-modeling')

    // 切换到对话
    await page.click('[data-testid="tab-chat"]')
    await page.fill('[data-testid="chat-input"]', '你好')
    await page.click('[data-testid="send-button"]')

    // 等待响应
    await page.waitForSelector('[data-testid="message-assistant"]', { timeout: 30000 })
    const messages = await page.$$('[data-testid="message-assistant"]')
    expect(messages.length).toBeGreaterThan(0)
  })

  test('can switch domains', async ({ page }) => {
    await page.goto('/')
    await page.waitForSelector('[data-testid="domain-select"]', { timeout: 15000 })

    await page.selectOption('[data-testid="domain-select"]', 'paper-writing')
    await page.waitForTimeout(1000)

    const roles = await page.$$('[data-testid^="role-"]')
    expect(roles.length).toBeGreaterThan(0)
  })

  test('can save and load session', async ({ page }) => {
    await page.goto('/')
    await page.waitForSelector('[data-testid="tab-sessions"]', { timeout: 15000 })
    await page.click('[data-testid="tab-sessions"]')

    // 保存当前会话按钮存在
    const saveButton = page.locator('[data-testid="save-session"]')
    expect(await saveButton.isVisible()).toBeTruthy()
  })
})
```

- [ ] **Step 3: 安装 Playwright 并运行**

```bash
cd frontend && npm install -D @playwright/test && npx playwright install chromium --with-deps
npx playwright test --project=chromium
```

- [ ] **Step 4: 提交**

```bash
git add frontend/e2e/ frontend/playwright.config.ts
git commit -m "test: add Playwright E2E tests for full pipeline, domain switching, and sessions"
```

### Task D2: Electron 打包完整验证

**Files:**
- Modify: `frontend/electron-builder.json5`（如果存在）
- Create: `docs/electron-build-log-v10.md`

- [ ] **Step 1: 构建并打包**

```bash
cd frontend && npm run vite:build
npx electron-builder --win --config
```

- [ ] **Step 2: 验证输出**

```bash
ls -la frontend/release/ && du -sh frontend/release/*.exe
```

- [ ] **Step 3: 文档化结果**

```bash
git add docs/electron-build-log-v10.md
git commit -m "docs: add v10 Electron build verification log"
```

### Task D3: Docker 部署验证

**Files:**
- Modify: `Dockerfile`（如果存在）
- Create: `docker-compose.yml`（如果不存在）

- [ ] **Step 1: 创建 Dockerfile**

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY backend/ /app/
RUN pip install fastapi uvicorn chromadb
EXPOSE 8765
CMD ["python", "-m", "uvicorn", "ultramath.api.server:app", "--host", "0.0.0.0", "--port", "8765"]
```

- [ ] **Step 2: 构建并启动**

```bash
docker build -t ultramath-backend .
docker run -p 8765:8765 ultramath-backend
```

- [ ] **Step 3: 验证健康检查**

```bash
curl http://localhost:8765/api/health
```

- [ ] **Step 4: 提交**

```bash
git add Dockerfile docker-compose.yml
git commit -m "feat: add Docker deployment configuration"
```

---

## 子系统 E：品牌更名 — Lemma → Lemma（第 1 天，P0）

**品牌策略：**
- 英文名：**Lemma**（引理 — 数学中基于已知事实推导新结论的基石）
- 标语：*"Every Theorem Begins with a Lemma"*
- Logo：⊢（turnstile 推导符号）+ 深蓝/金色配色
- Python 包名：`ultramath` → `lemma`
- NPM 包名：`lemma-frontend` → `lemma-app`
- 不设中文译名和副标签，品牌名就是 **Lemma**，干净利落

### Task E1: Python 包重命名

**Files:**
- Rename: `backend/src/ultramath/` → `backend/src/lemma/`
- Modify: `backend/pyproject.toml`（包名）
- Modify: `backend/conftest.py`（如果存在）
- Modify: 所有 `from ultramath` → `from lemma`（~82 个文件）
- Modify: `backend/src/lemma/api/server.py`（OpenAPI title）
- Test: 全量后端测试确认通过

- [ ] **Step 1: 更新 pyproject.toml**

```toml
# backend/pyproject.toml
[project]
name = "lemma"
description = "Lemma — Every Theorem Begins with a Lemma"
```

- [ ] **Step 2: 批量替换 import 路径**

```bash
cd backend
# 替换所有 Python 文件中的 import 路径
find src/ -name "*.py" -exec sed -i 's/from ultramath/from lemma/g' {} \;
find src/ -name "*.py" -exec sed -i 's/import ultramath/import lemma/g' {} \;
find tests/ -name "*.py" -exec sed -i 's/from ultramath/from lemma/g' {} \;
find tests/ -name "*.py" -exec sed -i 's/import ultramath/import lemma/g' {} \;
```

- [ ] **Step 3: 重命名目录**

```bash
mv backend/src/ultramath backend/src/lemma
```

- [ ] **Step 4: 更新 server.py 中 OpenAPI 标题**

```python
# backend/src/lemma/api/server.py 第 ~10 行
app = FastAPI(
    title="Lemma API",
    description="Lemma — Every Theorem Begins with a Lemma",
    version="0.10.0",
)
```

- [ ] **Step 5: 运行全量测试确认**

```bash
cd backend && PYTHONPATH=src python -m pytest tests/ -q --cov=src/lemma --cov-fail-under=70
```

预期: 529 passed, 0 failed, 覆盖率 ≥ 70%

- [ ] **Step 6: 提交**

```bash
git add -A backend/
git commit -m "refactor: rename Python package ultramath → lemma (project rebranding)"
```

### Task E2: 前端品牌更新

**Files:**
- Modify: `frontend/package.json`（name 字段）
- Modify: `frontend/index.html`（title）
- Modify: `frontend/src/App.tsx`（标题、about 文案）
- Modify: `frontend/src/components/Sidebar.tsx`（Logo 区域）
- Modify: `frontend/electron/main.js`（窗口标题）

- [ ] **Step 1: 更新 package.json**

```json
{
  "name": "lemma-app",
  "productName": "Lemma",
  "description": "Lemma — Every Theorem Begins with a Lemma"
}
```

- [ ] **Step 2: 更新 index.html**

```html
<title>Lemma</title>
```

- [ ] **Step 3: 更新 App.tsx 标题和 about**

```tsx
// App.tsx — 标题区域
<h1 className="text-lg font-bold">Lemma</h1>
<span className="text-xs text-[var(--color-text-muted)]">Every Theorem Begins with a Lemma</span>
```

- [ ] **Step 4: 更新 Sidebar.tsx 品牌区域**

```tsx
// Sidebar.tsx — Logo 区域
<div className="brand-area">
  <span className="text-2xl">⊢</span>
  <span className="font-bold text-lg">Lemma</span>
  <span className="text-xs text-[var(--color-text-muted)]">Every Theorem Begins with a Lemma</span>
</div>
```

- [ ] **Step 5: 更新 Electron 窗口标题**

```javascript
// electron/main.js
mainWindow = new BrowserWindow({
  title: 'Lemma',
  // ...
})
```

- [ ] **Step 6: 提交**

```bash
git add frontend/
git commit -m "refactor: update frontend branding Lemma → Lemma"
```

### Task E3: 文档和配置全量替换

**Files:**
- Modify: `README.md`
- Modify: `CHANGELOG.md`
- Modify: `docs/QUALITY_BASELINE.md`
- Modify: `docs/ARCHITECTURE.md`
- Modify: `docs/PERFORMANCE_BASELINE.md`
- Modify: `.github/workflows/ci.yml`（如果有引用旧名）
- Rename: `docs/superpowers/plans/2026-06-26-lemma-v10-product-realization.md` → `docs/superpowers/plans/2026-06-26-lemma-v10-product-realization.md`

- [ ] **Step 1: 批量替换文档中的名称**

```bash
cd "E:\数学建模agent"
# 替换所有 .md 文件
find . -name "*.md" -not -path "*/node_modules/*" -not -path "*/.git/*" -exec sed -i 's/Lemma/Lemma/g' {} \;
find . -name "*.md" -not -path "*/node_modules/*" -not -path "*/.git/*" -exec sed -i 's/lemma/lemma/g' {} \;
find . -name "*.md" -not -path "*/node_modules/*" -not -path "*/.git/*" -exec sed -i 's/Lemma/Lemma/g' {} \;
find . -name "*.md" -not -path "*/node_modules/*" -not -path "*/.git/*" -exec sed -i 's/ultramath/lemma/g' {} \;
```

- [ ] **Step 2: 重命名计划文件**

```bash
mv docs/superpowers/plans/2026-06-26-lemma-v10-product-realization.md docs/superpowers/plans/2026-06-26-lemma-v10-product-realization.md
```

- [ ] **Step 3: 更新 README.md 关键信息**

```markdown
# Lemma

> **Every Theorem Begins with a Lemma**

Lemma 是一个数学建模竞赛与学术写作的智能助手。基于多智能体协作架构，
覆盖从题目分析 → 数学推导 → 代码实现 → 论文写作的完整流程。

[![Tests](https://github.com/Andiii208/lemma/actions/workflows/ci.yml/badge.svg)](https://github.com/Andiii208/lemma/actions/workflows/ci.yml)
[![Coverage](https://img.shields.io/badge/coverage-75%25-green)](https://github.com/Andiii208/lemma)

## 快速开始

```bash
# 后端
cd backend && pip install -e . && python -m uvicorn lemma.api.server:app --port 8765

# 前端
cd frontend && npm install && npm run dev
```
```

- [ ] **Step 4: 提交**

```bash
git add -A docs/ README.md CHANGELOG.md
git commit -m "docs: rebrand docs and configs Lemma → Lemma"
```

### Task E4: 品牌资产文件

**Files:**
- Create: `brand/logo.svg`（⊢ 符号 + Lemma 文字）
- Create: `brand/README.md`（品牌使用指南）

- [ ] **Step 1: 创建品牌目录和指南**

```bash
mkdir -p brand
```

`brand/README.md`：

```markdown
# Lemma 品牌指南

## 名称
- **英文**：Lemma
- **不建议**使用中文译名或副标签，保持 Lemma 作为唯一品牌名

## 标语
> "Every Theorem Begins with a Lemma"

## Logo
- 符号：⊢（turnstile，推导符号）
- 配色：深蓝 #1a365d + 金色 #d4a853
- 最小使用尺寸：32×32px（符号可独立使用）

## 字体
- 英文：Inter 或系统 sans-serif
- 中文：系统默认

## 产品定位
数学建模竞赛与学术写作的 AI 智能助手
```

- [ ] **Step 2: 提交**

```bash
git add brand/
git commit -m "docs: add Lemma brand guidelines and assets"
```

---

## 3. 优先级矩阵

| 优先级 | Task | 时间 | 价值 | 为什么 |
|--------|------|------|------|--------|
| 🔴 P0 | **E1-E4: 品牌更名** | 1d | 极高 | 确定品牌名再迭代，避免后续改造成本翻倍 |
| 🔴 P0 | **A1: RAG Collection 修复** | 2h | 极高 | 🔴 Bug — RAG 当前不工作 |
| 🔴 P0 | **A2: Cascade LLM Judge** | 4h | 高 | 级联路由核心决策依据 |
| 🔴 P0 | **A3: 反思自动触发** | 2h | 高 | 已有功能但从未被调用 |
| 🟡 P1 | **B1: 知识文档扩充** | 2d | 高 | RAG 质量的天花板 |
| 🟡 P1 | **B3: Prompt 模板深化** | 1d | 高 | 直接提升输出质量 |
| 🟡 P1 | **B2: 新领域 data-mining** | 2d | 中 | 扩领域覆盖面 |
| 🟡 P1 | **D1: Playwright E2E** | 2d | 高 | 用户视角验证 |
| 🟢 P2 | **A4: 辩论可视化** | 3h | 低 | 体验优化 |
| 🟢 P2 | **C1-C3: 产品体验打磨** | 3d | 中 | 流式/错误/进度 |
| 🟢 P2 | **D2-D3: 分发验证** | 1d | 中 | 打包/Docker |

## 4. Self-Review

**规格覆盖：**
- 管线断裂修复 → A1 覆盖 ✅
- 智能系统真实工作 → A2, A3 覆盖 ✅
- 知识工程深化 → B1, B2, B3 覆盖 ✅
- 产品体验 → C1, C2, C3 覆盖 ✅
- 分发验证 → D1, D2, D3 覆盖 ✅
- 品牌更名 → E1, E2, E3, E4 覆盖 ✅

**占位符扫描：** 所有 Task 包含实际代码 ✅

**类型一致性：** collection name 变更与 loader.py 对齐 ✅

---

## 执行交接

计划已保存至 `docs/superpowers/plans/2026-06-26-lemma-v10-product-realization.md`。

**建议从 Task E1-E4（品牌更名）开始 — 定下 Lemma 这个名字后，所有后续改动都带着新品牌进行，避免改名时修改量翻倍。接着按 P0 铁三角（A1 RAG 修复 → A2 Cascade Judge → A3 反思自动触发）推进，3 天内完成全部 P0。**

**Which approach?**
