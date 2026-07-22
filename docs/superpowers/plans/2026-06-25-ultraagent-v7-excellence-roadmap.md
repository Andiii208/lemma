# Lemma v7.0 — 从"好用"到"卓越"：差异化壁垒路线图

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 v6（让产品"好用、可发布"）基础上，为 Lemma 构建难以复制的差异化壁垒——Agent 智能深水区、可观测可恢复的工程底盘、平台化与商业化能力，使其从"一个能跑的学术写作 Agent"跃升为"可被集成、可被度量、可自我进化的学术智能体平台"。

**Architecture:** 本计划是**战略级多方向路线图**，不是单一 feature 实现。分 6 个相互独立的发展维度（A-F），每个维度内含可独立交付的子方向。维度 A（智能深水区）和 B（工程底盘）是核心壁垒，优先级最高。最高优先级方向附带 TDD 风格的任务分解；中低优先级方向给出目标、关键举措与验收指标，待启动时再细化为 task。

**Tech Stack:** Python 3.11+, FastAPI, OpenAI SDK, ChromaDB, OpenTelemetry, APScheduler/Celery, Docker, React 18, TypeScript, CRDT(Yjs), MCP 协议, DSPy(可选)

---

## 0. 与既有规划的关系定位

本项目已有 7 份 roadmap 文档。**本计划不重复 v6**，而是它的"下一个台阶"。

| 文档 | 定位 | 状态 |
|------|------|------|
| `2026-06-24-lemma-v6-next-roadmap.md` | "从能跑到好用"（补测试、去 emoji、可访问性、打包、部署） | **前置依赖**，须先完成 |
| **本计划 (v7)** | "从好用到卓越"（智能深水区、平台化、商业化、自我进化） | 本文档 |

**执行前提**：v6 的 M1-M3（测试 ≥130、零 emoji、WCAG AA、可发布）是 v7 的地基。v7 的很多方向（如 evals、可观测性）依赖 v6 落地的测试与规范化。若 v6 未完成，应先回 v6。

**一个必须先纠正的事实**（2026-06-25 实地核对）：

| v6 roadmap 中的陈述 | 实际情况 | 影响 |
|---|---|---|
| "运行全量测试 ≥ 130 个" | **`pytest` 未安装**于当前开发环境，本地 `pytest --co` 返回 0；CI 中才安装 | 本地开发无法验证测试 |
| 提及 `benchmarks/quality_metrics.py` | **`benchmarks/` 目录不存在** | v6 Task 3.3 基于不存在的文件 |
| "git commit" 步骤遍布全文 | **项目根目录不是 git 仓库**（`git status` 报 fatal） | 所有 commit 流程需先 `git init` |
| "前端测试" | 前端只有 **1 个测试文件** `Sidebar.test.tsx`（65 行） | 前端近乎无保护 |

**→ 本计划 Task 0 先补这三块"地基的地基"。**

---

## 1. 现状诊断修正版（2026-06-25）

### 1.1 真实就绪度评分

| 维度 | 评分 | 证据 |
|------|------|------|
| 核心引擎功能 | 🟢 8/10 | AcademicAgent 接入 Handoff/Trust/FileVisibility/Reflector/Cost/RAG/递归分解，run_auto 可跑通 |
| API 完整性 | 🟢 8/10 | REST 12 端点 + WS 7 消息类型 + 全局异常处理 |
| 测试工程化 | 🔴 3/10 | pytest 本地不可用、前端仅 1 测试、E2E 未验证、覆盖率盲区多 |
| 版本控制 | 🔴 2/10 | 非 git 仓库，无提交历史，CHANGELOG 全靠手写 |
| 可观测性 | 🟡 4/10 | 有 CostTracker + perf_monitor，但无分布式 trace、无结构化日志聚合 |
| 可恢复性 | 🔴 2/10 | run_auto 无断点续跑，进程崩溃即丢失进度 |
| 智能化深度 | 🟡 5/10 | 有辩论/自适应参数/反思，但无评测体系证明"更好"、无自我进化 |
| 安全沙箱 | 🟡 4/10 | AST 黑名单（`sandbox.py`）可被绕过（如 `__builtins__` 间接访问），非容器隔离 |
| 平台化 | 🔴 2/10 | 领域市场仅有"入口"，无插件 SDK、无 MCP、无分发机制 |
| 商业化 | 🔴 1/10 | 纯本地桌面端，无多租户、无计费、无组织 |

### 1.2 三大"致命断点"（必须在 v7 主体之前解决）

1. **非 git 仓库** → 无法回滚、无法协作、无法做实验分支、CHANGELOG 与代码脱节
2. **测试不可运行** → 任何"重构"都是裸奔，v6 的所有质量目标无法验证
3. **沙箱可绕过** → 代码执行工具是 Agent 自主调用的高危路径，AST 黑名单防不住 `getattr(__builtins__,'eval')`

---

## 2. 总览：六大发展维度

```
维度 A (核心壁垒)        维度 B (工程底盘)        维度 C (产品体验)
Agent 智能深水区         可观测·可恢复·可控        差异化交互
├─ A1 评测体系 evs       ├─ B1 OpenTelemetry       ├─ C1 文档版本树/diff
├─ A2 自我进化 prompt    ├─ B2 断点续跑/任务队列    ├─ C2 交互式公式/图表
├─ A3 动态 DAG 规划      ├─ B3 容器级沙箱           ├─ C3 实时协作 CRDT
├─ A4 工具自创           ├─ B4 审计与回放           ├─ C4 多格式导出
└─ A5 多 Agent 拓扑      └─ B5 Human-in-loop 流程   └─ C5 知识图谱可视化

维度 D (平台化)          维度 E (运营卓越)         维度 F (知识资产)
集成与生态               性能·安全·发布            结构化知识
├─ D1 工具/插件 SDK      ├─ E1 压测与 SLO           ├─ F1 知识图谱升级
├─ D2 MCP 协议接入       ├─ E2 模糊测试/对抗        ├─ F2 案例库 few-shot
├─ D3 领域市场落地       ├─ E3 灰度/实验框架        └─ F3 失败模式库
├─ D4 SaaS 多租户        └─ E4 成本治理              └─
└─ D5 用量计费
```

### 2.1 优先级矩阵（投入产出 × 壁垒价值）

| 维度/方向 | 壁垒价值 | 实现难度 | 优先级 | 依赖 |
|---|---|---|---|---|
| **A1 评测体系** | ⭐⭐⭐⭐⭐ | 中 | **P0** | Task 0 |
| **B3 容器沙箱** | ⭐⭐⭐⭐⭐ | 中 | **P0** | 无（安全） |
| **A2 自我进化** | ⭐⭐⭐⭐⭐ | 高 | P1 | A1 |
| **B1 可观测性** | ⭐⭐⭐⭐ | 中 | P1 | Task 0 |
| **B2 断点续跑** | ⭐⭐⭐⭐ | 中 | P1 | B1 |
| **D2 MCP 接入** | ⭐⭐⭐⭐ | 低-中 | P1 | 无 |
| **A3 动态规划** | ⭐⭐⭐⭐ | 高 | P2 | A1 |
| **D1 插件 SDK** | ⭐⭐⭐⭐ | 中 | P2 | v6 完成 |
| **C1 文档 diff** | ⭐⭐⭐ | 中 | P2 | 无 |
| **D3 领域市场** | ⭐⭐⭐ | 中 | P2 | D1 |
| **C3 实时协作** | ⭐⭐⭐ | 高 | P3 | D4 |
| **D4 SaaS** | ⭐⭐⭐⭐ | 高 | P3 | B1,B2,D5 |

### 2.2 里程碑

| 里程碑 | 验收标准 | 预计 |
|---|---|---|
| **M0: 地基修复** | git 仓库初始化、本地 pytest 可跑、沙箱加固 POC | 第 1 周 |
| **M1: 度量先行** | A1 评测体系上线，≥ 3 领域有 golden set + 自动评分 | 第 2-4 周 |
| **M2: 可信底盘** | B1 trace 全链路 + B2 断点续跑 + B3 容器沙箱 | 第 4-7 周 |
| **M3: 平台雏形** | D2 MCP server 可被外部调用 + D1 插件 SDK alpha | 第 7-10 周 |
| **M4: 自我进化** | A2 prompt 自动优化在评测集上可证明提升 | 第 10-14 周 |
| **M5: 商业可选** | D4 SaaS 多租户 POC + D5 计费 | 第 14 周+ |

**预估总工期：14-20 周（4-5 个月）**，可在 M3 后对外发布"平台版"。

---

## 阶段零：地基修复（M0，预计 1 周）

> 这三件事不做，后面所有"度量""安全""协作"都建立在沙地上。

### Task 0.1: 初始化 Git 仓库并建立基线

**Files:**
- Create: `.gitignore`（已有，需复核）
- Create: 首个 commit

- [ ] **Step 1: 复核 .gitignore 覆盖所有应忽略项**

```bash
cd "E:/数学建模agent"
cat .gitignore
# 确认包含: node_modules/, __pycache__/, .venv/, data/, *.egg-info/,
# dist/, .ruff_cache/, .pytest_cache/, .env, data/chromadb/
```

- [ ] **Step 2: 初始化仓库并做基线提交**

```bash
git init -b main
git add .
git status   # 人工核对：无 node_modules / .env / data/ 泄漏
git commit -m "chore: initialize repository at v5.1.0 baseline"
```

- [ ] **Step 3: 验证敏感文件未被跟踪**

```bash
git ls-files | grep -iE "\.env$|secret|key" || echo "OK: 无敏感文件"
```
预期：输出 `OK: 无敏感文件`。

### Task 0.2: 让本地 pytest 可运行

**Files:**
- Modify: `backend/pyproject.toml`（dev 依赖已含 pytest，确认安装路径）

- [ ] **Step 1: 安装开发依赖到可用的 Python 环境**

```bash
cd backend
pip install -e ".[dev]"
```

- [ ] **Step 2: 收集并运行测试**

```bash
python -m pytest tests/ -q --co | tail -3   # 应显示真实用例数
python -m pytest tests/ -q --tb=short --ignore=tests/e2e/
```
预期：本地可收集到用例，单元测试通过。

- [ ] **Step 3: 记录基线覆盖率**

```bash
python -m pytest tests/ --ignore=tests/e2e/ --cov=src/ultramath --cov-report=term
```
把基线覆盖率写入 `docs/QUALITY_BASELINE.md`，后续只许升不许降。

### Task 0.3: 沙箱加固 POC（B3 的前置验证）

> 当前 `sandbox.py` 是 AST 黑名单，`getattr(builtins,'eval')` 等可绕过。先做对抗验证，再决定是否容器化。

**Files:**
- Create: `backend/tests/test_sandbox_escape.py`
- Modify: `backend/src/ultramath/tools/sandbox.py`

- [ ] **Step 1: 写出会逃逸的失败测试（红）**

```python
# backend/tests/test_sandbox_escape.py
from ultramath.tools.sandbox import SecurityChecker

class TestSandboxEscape:
    def test_blocks_getattr_builtins_eval(self):
        """getattr(__builtins__, 'eval') 应被拦截"""
        code = "f = getattr(__builtins__, 'eval'); f('1+1')"
        errors = SecurityChecker().check(code)
        assert any("builtins" in e.lower() or "getattr" in e.lower() for e in errors), \
            f"沙箱被绕过! errors={errors}"

    def test_blocks_dunder_import_via_dict(self):
        code = "().__class__.__bases__[0].__subclasses__()"
        errors = SecurityChecker().check(code)
        assert len(errors) > 0, "通过 mro 链访问子类未被拦截"

    def test_blocks_attribute_chain_to_os(self):
        code = "x = ''; x.__class__.__mro__[-1].__subclasses__()"
        errors = SecurityChecker().check(code)
        assert len(errors) > 0
```

- [ ] **Step 2: 运行确认失败**

```bash
python -m pytest backend/tests/test_sandbox_escape.py -v
```
预期：3 个测试 FAIL（当前黑名单拦不住属性链）。

- [ ] **Step 3: 在 SecurityChecker 增加属性链检查**

在 `SecurityChecker` 中新增 visitor，拦截 `Attribute` 节点中访问 `__builtins__`/`__class__`/`__subclasses__`/`__globals__`/`__mro__` 等危险 dunder：

```python
# 在 sandbox.py 的 SecurityChecker 类中追加
DANGEROUS_DUNDERS = {
    "__builtins__", "__globals__", "__subclasses__",
    "__class__", "__mro__", "__bases__",
}

def visit_Attribute(self, node: ast.Attribute) -> None:
    if node.attr in self.DANGEROUS_DUNDERS:
        self.errors.append(f"Blocked dunder access: {node.attr}")
    self.generic_visit(node)

def visit_Call(self, node: ast.Call) -> None:
    # 拦截 getattr(x, 'eval') 这类动态获取
    if isinstance(node.func, ast.Name) and node.func.id == "getattr":
        if len(node.args) >= 2:
            arg = node.args[1]
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                if arg.value in {"eval", "exec", "compile", "__import__"}:
                    self.errors.append(f"Blocked dynamic getattr: {arg.value}")
    self.generic_visit(node)
```

- [ ] **Step 4: 测试转绿**

```bash
python -m pytest backend/tests/test_sandbox_escape.py -v
```
预期：3 PASS。

- [ ] **Step 5: 提交**

```bash
git add backend/src/ultramath/tools/sandbox.py backend/tests/test_sandbox_escape.py
git commit -m "fix(sandbox): block dunder-chain and dynamic getattr escapes"
```

> **注**：AST 黑名单本质是"封堵已知漏洞"，长期应走向容器隔离（见 B3）。

---

## 阶段一（维度 A）：Agent 智能深水区 — 构建核心壁垒

### A1: Agent 评测体系（P0，最高优先）

**为什么是最高优先**：没有度量就没有"更好"。当前所有"智能升级"（辩论、反思、自适应）都缺乏回归基准，改了 prompt 不知道是变好还是变坏。**评测体系是 v7 一切智能方向的基石。**

**现状**：v6 Task 3.3 提到的 `benchmarks/quality_metrics.py` **不存在**。系统内只有 `quality/metrics.py`（运行时质量检查），无离线评测。

**目标**：建立 `ultrath eval` 子系统，对每个领域维护 golden set + 自动评分，任何 prompt/模型/参数变更都跑回归，输出可对比的指标表。

**关键举措**：
1. 每领域 10-20 条 golden cases（输入 + 期望产出特征/参考答案）
2. 多维自动评分：结构完整性（validator 复用）、关键事实命中（LLM-as-judge + 规则）、LaTeX 编译率、成本/时延
3. 评测 runner：离线批量 + CI 集成（PR 触发回归）
4. 评测看板：版本间 diff（v5.1 vs v6 vs v7 的得分曲线）

**File Structure:**

```
backend/src/ultramath/eval/
├── __init__.py
├── dataset.py          # GoldenDataset 加载/管理
├── scorers.py          # 各维度 Scorer（结构/事实/编译/成本）
├── llm_judge.py        # LLM-as-judge 抽象（带缓存防成本爆炸）
├── runner.py           # 批量评测执行器
└── report.py           # 评测报告生成 + 版本对比

backend/tests/eval/
├── fixtures/math-modeling/golden.jsonl
├── fixtures/paper-writing/golden.jsonl
└── test_runner.py

domains/<each>/golden.jsonl   # 每领域的 golden set（与领域配置同级）

backend/eval_cli.py    # python -m ultramath.eval.runner --domain math-modeling
```

### Task A1.1: 评测数据集加载器（TDD）

**Files:**
- Create: `backend/src/ultramath/eval/__init__.py`
- Create: `backend/src/ultramath/eval/dataset.py`
- Create: `backend/tests/eval/test_dataset.py`

- [ ] **Step 1: 定义数据格式并写失败测试**

golden.jsonl 每行格式：
```json
{"id":"mm_001","input":"2017 B题 VR...","expected":{"keywords":["排队论","灵敏度分析"],"must_compile":true,"min_length":2000}}
```

```python
# backend/tests/eval/test_dataset.py
import json
from pathlib import Path
from ultramath.eval.dataset import GoldenDataset, GoldenCase

class TestGoldenDataset:
    def test_load_jsonl(self, tmp_path):
        f = tmp_path / "golden.jsonl"
        f.write_text(json.dumps({
            "id": "t1", "input": "问题",
            "expected": {"keywords": ["模型"], "min_length": 10}
        }), ensure_ascii=False)
        ds = GoldenDataset.from_jsonl(str(f))
        assert len(ds) == 1
        assert ds[0].id == "t1"
        assert ds[0].expected["keywords"] == ["模型"]

    def test_empty_file_returns_empty(self, tmp_path):
        f = tmp_path / "empty.jsonl"
        f.write_text("")
        assert len(GoldenDataset.from_jsonl(str(f))) == 0

    def test_invalid_line_skipped(self, tmp_path):
        f = tmp_path / "bad.jsonl"
        f.write_text("not json\n" + json.dumps({"id":"x","input":"","expected":{}}))
        ds = GoldenDataset.from_jsonl(str(f))
        assert len(ds) == 1  # 坏行跳过
```

- [ ] **Step 2: 运行确认失败** → `pytest tests/eval/test_dataset.py -v` FAIL（模块不存在）

- [ ] **Step 3: 实现 dataset.py**

```python
# backend/src/ultramath/eval/dataset.py
from __future__ import annotations
import json
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class GoldenCase:
    id: str
    input: str
    expected: dict

class GoldenDataset:
    def __init__(self, cases: list[GoldenCase]):
        self._cases = cases

    def __len__(self) -> int:
        return len(self._cases)

    def __getitem__(self, i: int) -> GoldenCase:
        return self._cases[i]

    def __iter__(self):
        return iter(self._cases)

    @classmethod
    def from_jsonl(cls, path: str) -> GoldenDataset:
        cases: list[GoldenCase] = []
        for line in Path(path).read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            if "id" in obj and "input" in obj and "expected" in obj:
                cases.append(GoldenCase(obj["id"], obj["input"], obj["expected"]))
        return cls(cases)
```

- [ ] **Step 4: 测试转绿 + 提交**

```bash
pytest tests/eval/test_dataset.py -v
git add backend/src/ultramath/eval/ backend/tests/eval/
git commit -m "feat(eval): add golden dataset loader for evaluation system"
```

### Task A1.2: 多维度 Scorer（TDD，核心）

**Files:**
- Create: `backend/src/ultramath/eval/scorers.py`
- Create: `backend/tests/eval/test_scorers.py`

- [ ] **Step 1: 写失败测试（关键词命中、长度、结构）**

```python
# backend/tests/eval/test_scorers.py
from ultramath.eval.scorers import KeywordScorer, LengthScorer, StructureScorer

class TestScorers:
    def test_keyword_scorer_all_hit(self):
        s = KeywordScorer(required=["排队论", "灵敏度分析"])
        result = s.score("本文使用排队论，并做了灵敏度分析")
        assert result.score == 1.0
        assert result.passed is True

    def test_keyword_scorer_partial(self):
        s = KeywordScorer(required=["排队论", "马尔可夫"])
        r = s.score("只提了排队论")
        assert 0.4 < r.score < 0.6

    def test_length_scorer_below_min(self):
        s = LengthScorer(min_length=100)
        r = s.score("短")
        assert r.score == 0.0 and r.passed is False

    def test_structure_scorer_has_sections(self):
        s = StructureScorer(required_sections=["摘要", "问题重述", "模型"])
        text = "## 摘要\n...\n## 问题重述\n...\n## 模型建立\n..."
        r = s.score(text)
        assert r.passed is True
```

- [ ] **Step 2: 实现 scorers.py**

```python
# backend/src/ultramath/eval/scorers.py
from __future__ import annotations
from dataclasses import dataclass

@dataclass
class ScoreResult:
    name: str
    score: float        # 0.0-1.0
    passed: bool
    detail: str = ""

class KeywordScorer:
    def __init__(self, required: list[str]):
        self.required = required
    def score(self, text: str) -> ScoreResult:
        hits = sum(1 for kw in self.required if kw in text)
        ratio = hits / len(self.required) if self.required else 1.0
        return ScoreResult("keyword", ratio, ratio >= 0.6,
                           detail=f"{hits}/{len(self.required)} 命中")

class LengthScorer:
    def __init__(self, min_length: int):
        self.min_length = min_length
    def score(self, text: str) -> ScoreResult:
        n = len(text)
        ok = n >= self.min_length
        return ScoreResult("length", min(1.0, n / self.min_length), ok,
                           detail=f"{n}/{self.min_length} 字符")

class StructureScorer:
    def __init__(self, required_sections: list[str]):
        self.required_sections = required_sections
    def score(self, text: str) -> ScoreResult:
        hits = sum(1 for sec in self.required_sections if sec in text)
        ratio = hits / len(self.required_sections) if self.required_sections else 1.0
        return ScoreResult("structure", ratio, ratio >= 0.6,
                           detail=f"{hits}/{len(self.required_sections)} 章节")
```

- [ ] **Step 3: 转绿 + 提交** → `feat(eval): add multi-dimensional scorers`

### Task A1.3: LLM-as-Judge（带缓存）

> 事实性/连贯性等难量化的维度交给 LLM 评分，但必须缓存防成本爆炸。

**Files:**
- Create: `backend/src/ultramath/eval/llm_judge.py`

**关键设计**：
- 评分结果按 `(model, prompt_hash, output_hash)` 缓存到 `data/eval_cache/`
- Judge prompt 固定（避免漂移），输出 JSON `{"score":0.8,"reason":"..."}`
- 复用现有 `LLMBackend`，Judge 模型应与被评模型不同（避免自夸）

- [ ] **Step 1: 写失败测试**（mock backend，验证缓存命中第二次不调用 LLM）
- [ ] **Step 2: 实现 `LLMJudge.score(output, criteria) -> ScoreResult`**
- [ ] **Step 3: 实现磁盘缓存 `_cache_key` + hit/miss 计数**
- [ ] **Step 4: 转绿 + 提交** → `feat(eval): add LLM-as-judge with disk cache`

### Task A1.4: 评测 Runner + CLI

**Files:**
- Create: `backend/src/ultramath/eval/runner.py`
- Create: `backend/src/ultramath/eval/report.py`
- Create: `backend/eval_cli.py`

- [ ] **Step 1: Runner 对每条 case 跑 `agent.run_auto`（mock 或真实），收集产出，过所有 scorer，汇总**

```python
# runner.py 核心（伪代码骨架）
async def evaluate(domain_id: str, use_mock: bool = True) -> EvalReport:
    dataset = GoldenDataset.from_jsonl(f"domains/{domain_id}/golden.jsonl")
    results = []
    for case in dataset:
        output = await run_agent_for_case(domain_id, case, use_mock)
        case_scores = [scorer(output) for scorer in build_scorers(case.expected)]
        results.append(CaseResult(case.id, case_scores))
    return EvalReport(domain_id, results)
```

- [ ] **Step 2: Report 支持版本对比** → `report.compare(old_report, new_report)` 输出 diff 表
- [ ] **Step 3: CLI** → `python -m ultramath.eval.runner --domain math-modeling --mock`
- [ ] **Step 4: 为 math-modeling 编写 10 条 golden case**（用历史竞赛题）
- [ ] **Step 5: 跑通并产出首份基线报告 `docs/eval-baseline-math-modeling.md`**
- [ ] **Step 6: 提交** → `feat(eval): runnable evaluation pipeline with baseline report`

**CI 集成（Task A1.5）**：在 `.github/workflows/ci.yml` 增加 `eval-regression` job，PR 时跑 mock 评测，得分下降则 fail。

---

### A2: 自我进化与 Prompt 自动优化（P1）

**为什么**：当前 prompt 是手写死文件，改进靠人工试错。引入自动优化后，Agent 能在评测集上自动搜索更优 prompt 变体，这是真正的"自我进化"壁垒。

**目标**：`ultrath optimize` 命令，对指定角色的 prompt，用"变异 → 评测 → 保留最优"的进化搜索，在 A1 评测集上证明提升。

**关键举措**：
1. Prompt 视为可优化对象（`OptimizablePrompt`：模板 + 插槽）
2. 变异策略：同义改写、增删指令、调整顺序（LLM 生成变体）
3. 优化循环：生成 N 个变体 → 评测 → 取 top-K → 再变异（DSPy 风格，但自实现避免重依赖）
4. 安全校验：变体必须通过沙箱 + 不含注入指令
5. 产出：`prompts/optimized/agent_lead.v7.md` + 评测对比

**File Structure:**
```
backend/src/ultramath/evolve/
├── __init__.py
├── prompt_object.py    # OptimizablePrompt
├── mutator.py          # 变异策略
├── optimizer.py        # 进化搜索循环（调用 A1 评测）
└── safety.py           # 变体安全检查（复用 sandbox + 注入检测）
```

**验收指标**：对至少 1 个角色，优化后 prompt 在 golden set 上综合分提升 ≥ 5%，且有评测报告佐证。

> **依赖**：必须先完成 A1。优化无度量 = 无意义。

---

### A3: 动态 DAG 规划（P2）

**现状**：`run_auto` 是**线性流水线**（按 domain.yaml 的 phase 顺序执行），虽支持 `[DECOMPOSE]` 递归分解，但无真正的动态规划。

**目标**：引入 Plan-and-Execute，Agent 先产出执行 DAG（节点=任务，边=依赖），调度器并行/重排执行，失败可局部重试而非整链重来。

**关键举措**：
1. `Plan` 数据结构（DAG，每节点带 retry/policy）
2. Planner：Lead 角色产出 plan（结构化输出）
3. DAG 调度器：拓扑排序 + 并行就绪节点 + 节点级超时/重试
4. 与 B2 断点续跑结合：DAG 状态可序列化

**验收**：复杂问题（需并行子任务）的端到端耗时下降 ≥ 30%（评测集对比）。

> **依赖**：A1（度量）、B2（持久化）。

---

### A4: 工具自创（P2）

**目标**：Agent 在发现现有 9 工具不足时，能自己编写 Python 工具代码 → 过沙箱 → 注册到 ToolRegistry → 立即可用。

**关键举措**：
1. `ToolForgeTool`（元工具）：接收"工具描述 + 签名"，生成代码
2. 生成的代码强制过 `SecurityChecker`（B3 加固版）
3. 注册为临时工具，会话级生命周期
4. 限制：只能 import allowlist 模块

**风险**：自创代码安全性 → 必须 B3 先完成。

---

### A5: 多 Agent 拓扑升级（P2）

**现状**：有 `debate.py`（两角色辩论 + lead 裁决）。但拓扑单一。

**目标**：支持可配置的多 Agent 拓扑：supervisor/worker、辩论树（多轮多角色）、投票委员会、critic-actor 循环。

**关键举措**：在 domain.yaml 增加 `topology` 段，定义阶段用哪种拓扑。复用 A1 评测对比不同拓扑的产出质量。

---

## 阶段二（维度 B）：可信、可观测、可控的工程底盘

### B1: 全链路可观测性（P1）

**现状**：有 `perf_monitor`（函数级计时）和 `CostTracker`，但无跨阶段、跨工具调用的**分布式 trace**，出问题难以定位是哪个阶段/哪次 LLM 调用。

**目标**：接入 OpenTelemetry，每次 `run_auto` 是一个 trace，每个 phase/tool/LLM 调用是一个 span，可导出到 Jaeger/本地查看。

**关键举措**：
1. `engine/observability.py`：封装 tracer，`@trace_span` 装饰器
2. 装饰 `run_auto`/`_execute_phase`/`_generate_with_tools`/各 tool 的 `execute`
3. span 属性：cost、tokens、model、phase、role
4. 本地导出 JSON（不强制部署 Jaeger），前端 PipelinePanel 可渲染时间轴
5. 日志结构化（JSON lines），便于检索

**File Structure:**
```
backend/src/ultramath/observability/
├── __init__.py
├── tracer.py           # OTel tracer 封装 + 本地 JSON exporter
├── decorators.py       # @trace_span
└── logging_config.py   # 结构化日志
```

### Task B1.1: 轻量 trace 装饰器（不强制 OTel 依赖）

> 为降低部署门槛，先自实现一个最小 trace（JSON spans），OTel 作为可选后端。

- [ ] **Step 1: 失败测试** → 装饰一个函数后，调用产生含 name/duration/children 的 span 树
- [ ] **Step 2: 实现 `tracer.py`**（线程/任务本地 span 栈，`@trace_span("name")`）
- [ ] **Step 3: 在 `_execute_phase` 加 `@trace_span`，span 携带 phase_id**
- [ ] **Step 4: 提供 `get_current_trace() -> dict` 供 API 暴露**
- [ ] **Step 5: 新增 `GET /api/trace/{run_id}`**（B2 持久化后可查历史）
- [ ] **Step 6: 转绿 + 提交**

### B2: 断点续跑与持久化任务队列（P1）

**现状**：`run_auto` 是内存中的一次性协程，进程崩溃/网络断开则全部重来。对长耗时（论文生成可能 10+ 分钟）场景致命。

**目标**：run_auto 的进度（DAG/phase 状态、已完成产出）持久化到磁盘，支持 resume/重试单阶段。

**关键举措**：
1. `RunState` 序列化（JSON）：已完成 phases、各 phase 产出快照、当前进度
2. 每 phase 完成后 checkpoint
3. `POST /api/run/{run_id}/resume`
4. 与 A3 DAG 结合：节点级 checkpoint
5. 幂等：重跑已完成 phase 默认跳过（可强制 `--rerun`）

### B3: 容器级沙箱（P0 安全，A4 前置）

**现状**：`sandbox.py` AST 黑名单（Task 0.3 已加固，但仍是黑名单哲学）。

**目标**：高危代码执行（A4 自创工具、用户脚本）走容器隔离，而非进程内执行。

**关键举措**：
1. 抽象 `CodeRunner` 接口：`InProcessRunner`（现状）vs `ContainerRunner`
2. `ContainerRunner`：用 Docker（或 Windows 下 fallback 到子进程 + 严格 seccomp/Job Object）
3. 资源限制：CPU/内存/时间/无网络/只读根 + 只写工作卷
4. 配置开关 `sandbox.mode: ast|subprocess|container`

> **注意**：Windows 为主平台，Docker Desktop 未必可用。`ContainerRunner` 在 Windows 上 fallback 到"受限子进程 + Job Object 限额"。

### B4: 审计与回放（P2）

**目标**：全量审计日志（谁、何时、用了哪个工具、传了什么参数、LLM 返回什么），支持操作回放（调试/合规）。

**关键举措**：结构化审计事件流 → 持久化 → `GET /api/audit` 查询 + 时间轴回放 UI。

### B5: Human-in-the-Loop 流程化（P2）

**现状**：有 `_wait_confirmation`/`TrustManager` 雏形，但前端无"等待人类确认"的交互闭环。

**目标**：关键节点（如发表前终审、高危工具调用前）自动暂停，推送确认卡片到前端，用户 approve/reject/edit 后继续。

---

## 阶段三（维度 C）：差异化产品体验

### C1: 文档版本树与 Diff 可视化（P2）

**为什么对学术写作领域是壁垒**：写作类领域的产出是"文档"，用户核心诉求是"看 Agent 改了什么、回滚到某个版本"。当前每次写作覆盖文件，无版本历史。

**关键举措**：
1. 每次写作产出自动存版本（content-addressed，`sha256` 命名）
2. `GET /api/document/{doc}/versions`
3. 前端 diff 视图（react-diff-viewer）
4. 任意版本可"设为当前"

### C2: 交互式公式/图表编辑（P3）

KaTeX 实时渲染 + 点击公式可要求 Agent 解释/修改；图表可标注让 Agent 重新生成。

### C3: 实时协作 CRDT（P3）

Yjs + y-websocket，多人同会话。前置：D4 SaaS 多租户。

### C4: 多格式导出（P2）

现仅 Markdown。增加 Word（python-docx）、LaTeX（已有 compiler，补组装）、PDF（LaTeX→PDF）、PPT（python-pptx）。

### C5: 领域知识图谱可视化（P3）

把 `domains/*/knowledge/*.md` 抽取为实体关系图，前端力导向图展示，点击节点注入到对话。

---

## 阶段四（维度 D）：平台化与商业化

### D1: 工具/插件 SDK（P2）

**目标**：外部开发者能用 SDK 写工具插件，`tool.yaml` + `tool.py` 放进 `plugins/` 即被自动发现注册。

**关键举措**：
1. `plugins/` 目录 + 自动发现（基于 entry_points 或 manifest 扫描）
2. SDK 包 `ultrath-plugin`（独立 PyPI 包，含 `Tool` 基类、装饰器、CLI 脚手架）
3. 插件沙箱：第三方工具默认低权限，需用户批准

### D2: MCP 协议接入（P1，高性价比）

**为什么优先**：MCP（Model Context Protocol）正成为 Agent 互操作标准。**让 Lemma 成为 MCP server**，即可被 Claude Desktop / Cursor / 其他 MCP client 调用其工具与领域知识——零成本打开分发渠道。

**目标**：
- 对外：作为 MCP server，暴露工具（code_executor/latex_compiler 等）和领域知识为 MCP resources
- 对内：作为 MCP client，可调用外部 MCP server 的工具（扩展能力边界）

**关键举措**：
1. `backend/src/ultramath/mcp/server.py`：把 ToolRegistry 适配为 MCP tools
2. `backend/src/ultramath/mcp/client.py`：把外部 MCP server 注册为本地工具
3. 配置 `mcp_servers.yaml`
4. 提供 `ultramath mcp serve` 启动 stdio/http MCP server

### Task D2.1: MCP Server 适配（POC）

- [ ] **Step 1: 失败测试** → MCP server 启动后，list_tools 返回 9 个工具
- [ ] **Step 2: 实现 `mcp/server.py`**（基于官方 `mcp` python sdk）
- [ ] **Step 3: 手动用 `mcp inspector` 验证**
- [ ] **Step 4: 文档 `docs/MCP_INTEGRATION.md`**
- [ ] **Step 5: 提交** → `feat(mcp): expose tools as MCP server`

### D3: 领域市场落地（P2）

**现状**：v5.1 仅在 SettingsPanel 加了"领域市场链接"，无实际分发。

**关键举措**：
1. 领域打包格式（`.ultrath-domain` = zip：domain.yaml + prompts + knowledge + golden）
2. 安装：`ultrath install <url>`
3. 市场索引（GitHub repo 或静态 JSON）
4. 评分/下载量（社区驱动）

### D4: SaaS 多租户（P3）

桌面端 → 云端。租户隔离、并发 agent 池、API key 托管。

### D5: 用量计费（P3）

token 计量（已有 CostTracker）→ 配额 → 计费（Stripe）。预算上限触发自动降级（便宜模型）。

---

## 阶段五（维度 E）：运营卓越

### E1: 性能压测与 SLO（P2）

定义 SLO：单 phase P95 < 60s、首 token < 3s、并发 10 会话稳定。用 locust 压测。

### E2: 模糊测试与对抗（P2）

对 API/WebSocket 做 fuzz（随机畸形输入）、对 sandbox 做对抗样本集（持续收集绕过尝试，见 F3）。

### E3: 灰度与实验框架（P3）

prompt/模型变更灰度发布（部分会话用新版本），用 A1 评测 + 线上指标双门控。

### E4: 成本治理（P2）

预算上限、超额自动从 GPT-4o 降级到 mini、单会话成本告警。

---

## 阶段六（维度 F）：知识资产

### F1: 知识库结构化升级（P2）

现状：`knowledge/*.md` 平铺。升级为：实体-关系-属性三元组 + 向量，支持图谱检索（C5 可视化的数据源）。

### F2: 案例库与自动 few-shot（P2）

积累高质量历史产出为案例，按相似度自动注入 few-shot，提升产出质量（可被 A2 优化验证）。

### F3: 失败模式库（P2）

收集评测失败 case、sandbox 绕过样本、用户报错，形成回归测试集，持续喂养 A1 评测与 E2 对抗。

---

## 3. 推荐执行序列（关键路径）

```
Week 1:  [Task 0.1-0.3 地基]  ─────────────────────────────────────► M0
Week 2-4:[A1.1-A1.5 评测体系]  ────────────────────────────────────► M1
              │
              ├──[B3 容器沙箱] (并行, 安全无依赖)
              │
Week 5-7:[B1 可观测] → [B2 断点续跑]  ──────────────────────────────► M2
              │
              ├──[D2 MCP] (并行, 高性价比)
              │
Week 8-10:[A2 自我进化] (依赖 M1) + [D1 插件SDK] + [C1 文档diff] ──► M3
              │
Week 11-14:[A3 动态规划] + [D3 领域市场] ───────────────────────────► M4
              │
Week 14+: [D4 SaaS] + [C3 协作] + [E1-4 运营] ─────────────────────► M5
```

**第一动作**：完成 Task 0.1-0.3，然后立即启动 A1（评测体系）。A1 是后续所有"证明变好"的前提。

---

## 4. Self-Review 自检

**1. 规格覆盖**：
- 智能深化（辩论/RAG/自适应）v6 已有 → 本计划升级为 A1-A5（评测/进化/规划/工具自创/拓扑），✅ 不重复且更深入
- 工程底盘 v6 几乎未涉及 → B1-B5 全新覆盖
- 平台化 v6 仅"领域市场入口" → D1-D5 体系化
- 商业化 v6 无 → D4/D5 新增

**2. 占位符扫描**：高优先级方向（Task 0、A1）已给出完整 TDD 代码与命令；P2+ 方向给出目标/举措/验收指标（战略文档合理粒度，非占位）。✅

**3. 类型/命名一致性**：
- `GoldenCase`/`GoldenDataset`/`ScoreResult` 在 dataset.py / scorers.py / runner.py 间一致
- `SecurityChecker.DANGEROUS_DUNDERS` 与 test_sandbox_escape 引用一致
- `@trace_span` 在 B1 各 Task 间一致

**4. 与现实的校准**（本计划独有）：
- 已标注 v6 中 benchmarks 不存在、git 未初始化、pytest 未装、前端仅 1 测试 —— 全部有 Task 0 修复 ✅

---

## 5. 执行交接

计划已保存至 `docs/superpowers/plans/2026-06-25-lemma-v7-excellence-roadmap.md`。

**两种执行方式：**

**1. Subagent-Driven（推荐）** — 每个 Task 派发独立子 agent，任务间审查，快速迭代。适合 Task 0 与 A1 这类边界清晰的实现。

**2. Inline Execution** — 在当前会话内按 executing-plans 批量执行，设检查点审查。适合先跑通 Task 0 三个小任务建立信心。

**建议从哪里开始**：先执行 **Task 0.1（git init）→ Task 0.2（pytest 可跑）→ Task 0.3（沙箱加固）**，这是整份计划的承重墙。完成后立即进入 A1 评测体系。

**Which approach?**
