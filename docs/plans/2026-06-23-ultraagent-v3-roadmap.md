# Lemma v3.0 — 从数学建模 Agent 到通用学术写作平台

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 Lemma 重构为领域无关的通用学术写作引擎，支持加载不同的"领域配置文件"来适配数学建模竞赛、学术论文、实验报告、文献综述等多种场景。同时借鉴 UltraFlow 项目的精选架构模式（信息不对称、结构化交接、信任系统、固化模式）。

**Architecture:** 引入 Domain Profile 抽象层 — 一个 YAML 配置文件 + 配套 prompts/knowledge/templates 目录，将当前散落在 5 个文件中的所有数学建模特定逻辑收敛到一个 `domains/math-modeling/` 目录中。引擎层（`orchestration/engine.py`）变为纯通用的 `AcademicAgent`，运行时动态加载任意 Domain Profile。

**Tech Stack:** Python 3.11+, FastAPI, OpenAI SDK, React 18, TypeScript, Tailwind CSS, YAML domain configs, Markdown prompt templates

---

## 现有问题诊断

通过对 ultraflow 项目和当前代码库的深入分析，识别出以下核心架构问题：

### 问题 1: 领域逻辑散落 5 处，无法复用

| 散落位置 | 数学建模特定内容 |
|----------|------------------|
| `orchestration/engine.py` | 7 个阶段处理器全部硬编码中文 prompt |
| `orchestration/state_machine.py` | Phase 枚举、转换规则、名称、进度 |
| `agent/role.py` | Role 枚举、角色名、温度、工具分配 |
| `agent/prompts/*.md` | 14 个文件全部包含数学术语 |
| `frontend/src/App.tsx` | PHASES 常量硬编码为数学建模 8 阶段 |

### 问题 2: 缺少 ultraflow 的关键架构模式

| 缺失的模式 | 价值 |
|------------|------|
| 信息不对称（文件隔离） | Critic 看不到原始问题 → 真正独立的评审 |
| 结构化交接协议 | 跨 Agent 通信的标准化摘要表 |
| 模板组合工厂 | role 模板与 domain 知识分离注入 |
| 信赖阈值系统 | 根据用户接受/拒绝历史调整确认行为 |
| 固化模式 | 成功的 ad-hoc 运行自动转化为永久预设 |
| 外部化状态恢复 | 多会话工作流，重启后可恢复 |

### 问题 3: 无领域切换机制

当前系统是"单一领域、单一目的"的。要支持论文写作、实验报告等新场景，需要一个统一的领域注册和切换机制。

---

## 总体架构变更

### 变更前

```
backend/src/ultramath/
  agent/prompts/*.md          ← 硬编码数学提示
  agent/role.py               ← 硬编码角色枚举
  orchestration/engine.py     ← 硬编码阶段处理器
  orchestration/state_machine.py ← 硬编码 Phase 枚举
  data/models/, templates/    ← 硬编码数学知识
```

### 变更后

```
backend/src/lemma/            ← 重命名: ultramath → lemma
  engine/                          ← 通用引擎层
    agent.py                       ← 通用 AcademicAgent
    state_machine.py               ← 通用状态机（Phase 从 config 加载）
    domain.py                      ← NEW: DomainProfile 加载器
  roles/                           ← 通用角色模板（零领域词汇）
    generator.md                   ← NEW: 从 ultraflow 借用的角色模板
    critic.md
    executor.md
    verifier.md
    synthesizer.md
    researcher.md
  ...
  llm/                             ← 不变
  memory/                          ← 不变
  tools/                           ← 不变
  api/                             ← 微调
  ...
  
domains/                           ← NEW: 领域配置目录
  math-modeling/
    domain.yaml                    ← 定义 phases, roles, directories
    prompts/                       ← 原 agent/prompts/ 迁移至此
    knowledge/                     ← 原 data/models/, data/references/
    templates/                     ← 原 data/templates/论文/
  paper-writing/
    domain.yaml
    prompts/
    knowledge/
    templates/
  lab-report/
    domain.yaml
    prompts/
    knowledge/
    templates/
  literature-review/
    domain.yaml
    prompts/
    knowledge/
    templates/
```

---

## 阶段一: 核心架构重构 — Domain Profile 系统（预计 4-5 天）

### 目标
建立 Domain Profile 抽象，将引擎与数学建模解耦，使数学建模成为一个可加载的"领域"。

---

### Task 1.1: 创建 Domain Profile 数据模型

**Files:**
- Create: `backend/src/ultramath/engine/domain.py`
- Create: `backend/tests/test_domain.py`

**设计:** `domain.yaml` 的 Schema：

```yaml
# domains/math-modeling/domain.yaml
id: math-modeling
name: 数学建模竞赛
description: CUMCM/APMCM 数学建模竞赛自动求解
version: "2.0"

phases:
  - id: idle
    name: 空闲
    order: -1
    progress: 0
  - id: init
    name: 初始化
    order: 0
    progress: 5
    transition: { pass: analysis }
  - id: analysis
    name: 题目分析
    order: 1
    progress: 15
    transition: { pass: derivation, fail: analysis }
  - id: derivation
    name: 数学推导
    order: 2
    progress: 30
    transition: { pass: ontology, fail: derivation }
  - id: ontology
    name: 本体构造
    order: 3
    progress: 40
    transition: { pass: coding, fail: ontology }
  - id: coding
    name: 代码实现
    order: 4
    progress: 55
    transition: { pass: testing, fail: coding }
  - id: testing
    name: 测试验证
    order: 5
    progress: 65
    transition: { pass: writing, fail: coding }
  - id: writing
    name: 论文写作
    order: 6
    progress: 80
    transition: { pass: review, fail: writing }
  - id: review
    name: 交叉审稿
    order: 7
    progress: 90
    transition: { pass: done, fail: writing }
  - id: done
    name: 完成
    order: 8
    progress: 100

roles:
  - id: lead
    name: 团队指挥
    emoji: 🎯
    temperature: 0.5
    tools: [file_manager, quality_checker]
  - id: math
    name: 数学家
    emoji: 🧮
    temperature: 0.8
    tools: [file_manager]
  - id: engineer
    name: 工程师
    emoji: 💻
    temperature: 0.3
    tools: [code_executor, file_manager, figure_generator]
  - id: reviewer
    name: 审稿人
    emoji: 📝
    temperature: 0.4
    tools: [file_manager, quality_checker, latex_compiler]
  - id: writer
    name: 作家
    emoji: ✍️
    temperature: 0.6
    tools: [file_manager, latex_compiler]
  - id: verifier
    name: 验算员
    emoji: 🔍
    temperature: 0.2
    tools: [code_executor, file_manager]

directories:
  input: 题目
  output: 求解
  paper: 论文
  data: 数据

phase_handlers:  # 每个阶段的 prompt 模板（变量用 {variable_name}）
  init: |
    以下是待求解的数学建模竞赛题目：

    {problem_text}

    请开始初始化阶段。
  analysis: |
    请分析这个数学建模竞赛题目。
    判断题目类型（优化/预测/评价/图论/机理分析），
    列出需要求解的子问题，初步评估难度，并建议适用的数学方法。
    {context_sections}
  derivation: |
    请作为数学家，对这个题目进行完整的数学推导。
    生成3个不同的建模方案，评估每个方案的优劣，选择最优方案进行详细推导。
    输出包括：假设、符号定义、目标函数、约束条件、求解算法。
    {context_sections}
  # ... 其余 phase handlers

validators:
  - phase: ontology
    check: json
    path: "{output_dir}/problem-ontology.json"
  - phase: coding
    check: files_exist
    glob: "{output_dir}/*.py"
  - phase: writing
    check: files_exist
    glob: "{paper_dir}/*.tex"
```

- [ ] **Step 1: 创建 DomainProfile Pydantic 模型**

```python
# backend/src/ultramath/engine/domain.py
"""Domain Profile — 领域配置文件加载与验证"""
from __future__ import annotations

from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field
import yaml


class PhaseConfig(BaseModel):
    """阶段配置"""
    id: str
    name: str
    order: int
    progress: float = 0.0
    transition: dict[str, str] = Field(default_factory=dict)
    handler_prompt: str = ""


class RoleConfig(BaseModel):
    """角色配置"""
    id: str
    name: str
    emoji: str = "🤖"
    temperature: float = 0.5
    tools: list[str] = Field(default_factory=list)
    system_prompt: str = ""


class ValidatorConfig(BaseModel):
    """验证器配置"""
    phase: str
    check: str  # "json", "files_exist"
    path: str = ""
    glob: str = ""


class DomainProfile(BaseModel):
    """完整的领域配置"""
    id: str
    name: str
    description: str = ""
    version: str = "1.0"

    phases: list[PhaseConfig]
    roles: list[RoleConfig]
    directories: dict[str, str] = Field(default_factory=dict)
    phase_handlers: dict[str, str] = Field(default_factory=dict)
    validators: list[ValidatorConfig] = Field(default_factory=list)

    @classmethod
    def from_directory(cls, dir_path: str) -> "DomainProfile":
        """从领域目录加载配置"""
        yaml_path = Path(dir_path) / "domain.yaml"
        if not yaml_path.exists():
            raise FileNotFoundError(f"domain.yaml not found in {dir_path}")

        with open(yaml_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        profile = cls(**data)

        # 自动加载 prompts 目录中的 .md 文件作为角色的 system_prompt
        prompts_dir = Path(dir_path) / "prompts"
        if prompts_dir.exists():
            for role_cfg in profile.roles:
                prompt_file = prompts_dir / f"agent_{role_cfg.id}.md"
                if prompt_file.exists():
                    role_cfg.system_prompt = prompt_file.read_text(encoding="utf-8")

        return profile

    @classmethod
    def list_domains(cls, base_dir: str) -> list[dict]:
        """列出所有可用领域"""
        domains_path = Path(base_dir)
        if not domains_path.exists():
            return []

        domains = []
        for d in sorted(domains_path.iterdir()):
            if d.is_dir() and (d / "domain.yaml").exists():
                try:
                    with open(d / "domain.yaml", encoding="utf-8") as f:
                        data = yaml.safe_load(f)
                    domains.append({
                        "id": data.get("id", d.name),
                        "name": data.get("name", d.name),
                        "description": data.get("description", ""),
                        "version": data.get("version", "1.0"),
                    })
                except Exception:
                    continue
        return domains

    def get_phase_by_id(self, phase_id: str) -> Optional[PhaseConfig]:
        for p in self.phases:
            if p.id == phase_id:
                return p
        return None

    def get_role_by_id(self, role_id: str) -> Optional[RoleConfig]:
        for r in self.roles:
            if r.id == role_id:
                return r
        return None

    def get_phase_ids(self) -> list[str]:
        return [p.id for p in sorted(self.phases, key=lambda x: x.order)]

    def get_transition(self, from_phase: str, success: bool) -> str:
        """根据当前阶段和结果获取下一阶段"""
        phase = self.get_phase_by_id(from_phase)
        if not phase:
            return from_phase
        key = "pass" if success else "fail"
        return phase.transition.get(key, from_phase)
```

- [ ] **Step 2: 编写测试**

```python
# backend/tests/test_domain.py
"""领域配置加载测试"""
import pytest
import tempfile
from pathlib import Path
from ultramath.engine.domain import DomainProfile


class TestDomainProfile:
    def test_load_from_directory(self, tmp_path):
        # 创建最小 domain.yaml
        domain_dir = tmp_path / "test-domain"
        domain_dir.mkdir()
        (domain_dir / "domain.yaml").write_text("""
id: test
name: 测试领域
phases:
  - id: idle
    name: 空闲
    order: -1
    progress: 0
    transition: {pass: init}
  - id: init
    name: 初始化
    order: 0
    progress: 10
    transition: {pass: done}
  - id: done
    name: 完成
    order: 1
    progress: 100
roles:
  - id: lead
    name: 领队
    emoji: 🎯
    temperature: 0.5
    tools: []
""", encoding="utf-8")

        profile = DomainProfile.from_directory(str(domain_dir))
        assert profile.id == "test"
        assert profile.name == "测试领域"
        assert len(profile.phases) == 3
        assert len(profile.roles) == 1

    def test_get_transition(self, tmp_path):
        domain_dir = tmp_path / "test-domain"
        domain_dir.mkdir()
        (domain_dir / "domain.yaml").write_text("""
id: test
name: 测试
phases:
  - id: a
    name: A
    order: 0
    progress: 0
    transition: {pass: b, fail: a}
  - id: b
    name: B
    order: 1
    progress: 100
roles:
  - id: lead
    name: Lead
""", encoding="utf-8")

        profile = DomainProfile.from_directory(str(domain_dir))
        assert profile.get_transition("a", success=True) == "b"
        assert profile.get_transition("a", success=False) == "a"

    def test_get_phase_ids_sorted(self, tmp_path):
        domain_dir = tmp_path / "test-domain"
        domain_dir.mkdir()
        (domain_dir / "domain.yaml").write_text("""
id: test
name: 测试
phases:
  - id: c
    name: C
    order: 2
  - id: a
    name: A
    order: 0
  - id: b
    name: B
    order: 1
roles:
  - id: lead
    name: Lead
""", encoding="utf-8")

        profile = DomainProfile.from_directory(str(domain_dir))
        assert profile.get_phase_ids() == ["a", "b", "c"]

    def test_auto_loads_prompts_from_md(self, tmp_path):
        domain_dir = tmp_path / "test-domain"
        domain_dir.mkdir()
        prompts_dir = domain_dir / "prompts"
        prompts_dir.mkdir()
        (prompts_dir / "agent_lead.md").write_text("You are a helpful assistant.", encoding="utf-8")
        (domain_dir / "domain.yaml").write_text("""
id: test
name: 测试
phases:
  - id: idle
    name: 空闲
    order: -1
roles:
  - id: lead
    name: Lead
""", encoding="utf-8")

        profile = DomainProfile.from_directory(str(domain_dir))
        role = profile.get_role_by_id("lead")
        assert role is not None
        assert role.system_prompt == "You are a helpful assistant."

    def test_list_domains(self, tmp_path):
        domains_dir = tmp_path / "domains"
        domains_dir.mkdir()
        d1 = domains_dir / "math"
        d1.mkdir()
        (d1 / "domain.yaml").write_text("id: math\nname: 数学建模\nphases: []\nroles: []")
        d2 = domains_dir / "paper"
        d2.mkdir()
        (d2 / "domain.yaml").write_text("id: paper\nname: 论文写作\nphases: []\nroles: []")

        domains = DomainProfile.list_domains(str(domains_dir))
        assert len(domains) == 2
        assert domains[0]["id"] == "math"
        assert domains[1]["id"] == "paper"
```

- [ ] **Step 3: 运行测试**

```bash
python -m pytest backend/tests/test_domain.py -v
```

- [ ] **Step 4: 提交**

```bash
git add backend/src/ultramath/engine/domain.py backend/tests/test_domain.py
git commit -m "feat: add DomainProfile model with YAML loading and auto prompt injection"
```

---

### Task 1.2: 重构 StateMachine 为领域无关

**Files:**
- Modify: `backend/src/ultramath/orchestration/state_machine.py`

**设计:** 将硬编码的 `Phase` 枚举和 `TRANSITIONS` 改为从 `DomainProfile` 动态生成。

- [ ] **Step 1: 编写新版 StateMachine**

```python
# backend/src/ultramath/orchestration/state_machine.py
"""状态机 — 通用状态机，阶段从 DomainProfile 加载"""
from __future__ import annotations

from dataclasses import dataclass, field
from pydantic import BaseModel

from ..engine.domain import DomainProfile


class PhaseResult(BaseModel):
    """阶段执行结果"""
    phase_id: str
    success: bool = True
    summary: str = ""
    artifacts: dict[str, str] = {}
    issues: list[str] = []
    gate_passed: bool = True
    metrics: dict[str, float] = {}


@dataclass
class StateMachine:
    """通用状态机"""

    profile: DomainProfile
    current_phase: str = "idle"
    history: list[dict] = field(default_factory=list)
    _phase_results: dict[str, PhaseResult] = field(default_factory=dict)

    def __post_init__(self):
        # 确保 current_phase 是 profile 中的有效阶段
        if not self.profile.get_phase_by_id(self.current_phase):
            phase_ids = self.profile.get_phase_ids()
            self.current_phase = phase_ids[0] if phase_ids else "idle"

    def transition(self, result: PhaseResult) -> str:
        """根据阶段结果执行状态转换"""
        self._phase_results[result.phase_id] = result

        next_phase = self.profile.get_transition(
            result.phase_id,
            success=result.success and result.gate_passed,
        )

        current_cfg = self.profile.get_phase_by_id(result.phase_id)
        next_cfg = self.profile.get_phase_by_id(next_phase)

        self.history.append({
            "from": result.phase_id,
            "from_name": current_cfg.name if current_cfg else result.phase_id,
            "to": next_phase,
            "to_name": next_cfg.name if next_cfg else next_phase,
            "success": result.success,
            "summary": result.summary,
        })
        self.current_phase = next_phase
        return next_phase

    def skip_to(self, phase_id: str) -> None:
        if self.profile.get_phase_by_id(phase_id):
            self.current_phase = phase_id

    @property
    def is_done(self) -> bool:
        return self.current_phase == "done"

    @property
    def is_idle(self) -> bool:
        return self.current_phase == "idle"

    @property
    def progress(self) -> float:
        phase = self.profile.get_phase_by_id(self.current_phase)
        return phase.progress if phase else 0.0

    @property
    def phase_name(self) -> str:
        phase = self.profile.get_phase_by_id(self.current_phase)
        return phase.name if phase else "未知"

    def get_phase_result(self, phase_id: str) -> PhaseResult | None:
        return self._phase_results.get(phase_id)

    def to_dict(self) -> dict:
        return {
            "current_phase": self.current_phase,
            "current_phase_name": self.phase_name,
            "progress": self.progress,
            "is_done": self.is_done,
            "domain_id": self.profile.id,
            "domain_name": self.profile.name,
            "history": self.history,
        }
```

- [ ] **Step 2: 更新已有测试**

更新 `backend/tests/test_state_machine.py` 使用新的 API：

```python
class TestStateMachine:
    @pytest.fixture
    def sample_profile(self, tmp_path):
        domain_dir = tmp_path / "test"
        domain_dir.mkdir()
        (domain_dir / "domain.yaml").write_text("""
id: test
name: 测试
phases:
  - id: idle
    name: 空闲
    order: -1
    progress: 0
    transition: {pass: init}
  - id: init
    name: 初始化
    order: 0
    progress: 5
    transition: {pass: analysis, fail: init}
  - id: analysis
    name: 分析
    order: 1
    progress: 30
    transition: {pass: done, fail: analysis}
  - id: done
    name: 完成
    order: 2
    progress: 100
roles:
  - id: lead
    name: Lead
""", encoding="utf-8")
        return DomainProfile.from_directory(str(domain_dir))

    def test_initial_state(self, sample_profile):
        sm = StateMachine(profile=sample_profile)
        assert sm.current_phase == "idle"

    def test_normal_progression(self, sample_profile):
        sm = StateMachine(profile=sample_profile)
        sm.transition(PhaseResult(phase_id="idle", success=True))
        assert sm.current_phase == "init"
        sm.transition(PhaseResult(phase_id="init", success=True))
        assert sm.current_phase == "analysis"
```

- [ ] **Step 3: 运行测试并提交**

```bash
python -m pytest backend/tests/test_state_machine.py -v --tb=short
git add .
git commit -m "refactor: make StateMachine domain-agnostic, load phases from DomainProfile"
```

---

### Task 1.3: 创建通用 AcademicAgent 引擎

**Files:**
- Create: `backend/src/ultramath/engine/agent.py` (新文件，通用引擎)
- Modify: `backend/src/ultramath/orchestration/__init__.py`

**设计:** 新的 `AcademicAgent` 接受一个 `DomainProfile`，所有领域特定逻辑通过 profile 驱动。保留原有 `LemmaAgent` 作为向后兼容的包装。

- [ ] **Step 1: 创建 AcademicAgent**

```python
# backend/src/ultramath/engine/agent.py
"""AcademicAgent — 领域无关的通用学术写作引擎"""
from __future__ import annotations

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, AsyncGenerator, Callable

from ..memory.short_term import ShortTermMemory, Message
from ..memory.long_term import LongTermMemory
from ..memory.context import ContextManager
from ..llm.backend import LLMBackend
from ..llm.router import ModelRouter, TaskType
from ..tools.registry import ToolRegistry
from ..tools.base import ToolResult
from ..tools.sandbox import SecurityChecker
from .domain import DomainProfile, PhaseConfig, RoleConfig
from .state_machine import StateMachine, PhaseResult


class AcademicAgent:
    """通用学术写作 Agent"""

    def __init__(
        self,
        work_dir: str,
        domain: DomainProfile,
        llm_router: ModelRouter,
        tool_registry: ToolRegistry,
    ):
        self.work_dir = Path(work_dir)
        self.work_dir.mkdir(parents=True, exist_ok=True)
        self.domain = domain
        self.router = llm_router
        self.tools = tool_registry

        self.memory = ShortTermMemory(max_tokens=128000)
        self.long_term = LongTermMemory(persist_dir=str(self.work_dir / "data" / "chromadb"))
        self.context = ContextManager(str(work_dir))

        self.state = StateMachine(profile=domain)
        self.current_role_id = domain.roles[0].id if domain.roles else "lead"

        # 事件回调
        self._on_message: Callable | None = None
        self._on_phase_change: Callable | None = None
        self._on_tool_call: Callable | None = None

        # 取消标志
        self._cancel_event = asyncio.Event()

        # 根据 domain.directories 创建必要目录
        for dir_name in domain.directories.values():
            (self.work_dir / dir_name).mkdir(parents=True, exist_ok=True)

    # ========== 回调和生命周期 ==========
    def set_callbacks(self, on_message=None, on_phase_change=None, on_tool_call=None):
        self._on_message = on_message
        self._on_phase_change = on_phase_change
        self._on_tool_call = on_tool_call

    def cancel(self) -> None:
        self._cancel_event.set()

    def reset_cancel(self) -> None:
        self._cancel_event.clear()

    # ========== 角色管理 ==========
    def switch_role(self, role_id: str) -> None:
        if self.domain.get_role_by_id(role_id):
            self.current_role_id = role_id

    def get_current_role(self) -> RoleConfig | None:
        return self.domain.get_role_by_id(self.current_role_id)

    # ========== 阶段管理 ==========
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
        return "\n".join(parts)

    def _ensure_system_message(self) -> None:
        system_prompt = self._build_system_prompt()
        has_system = any(m.role == "system" for m in self.memory.get_raw_messages())
        if not has_system:
            self.memory.add("system", system_prompt)
        else:
            raw = self.memory.get_raw_messages()
            for i in range(len(raw) - 1, -1, -1):
                if raw[i].role == "system":
                    raw[i].content = system_prompt
                    break

    def _get_backend(self) -> LLMBackend:
        return self.router.get_default_backend()

    # ========== 对话 ==========
    async def chat(self, user_message: str) -> str:
        self._ensure_system_message()
        self.memory.add("user", user_message)

        await self._emit("message", {
            "role": "user", "content": user_message,
            "timestamp": datetime.now().isoformat(),
        })

        response_text = await self._generate_with_tools()
        self.memory.add("assistant", response_text)

        await self._emit("message", {
            "role": "assistant", "content": response_text,
            "agent_role": self.current_role_id,
            "agent_name": self.get_current_role().name if self.get_current_role() else "",
            "timestamp": datetime.now().isoformat(),
        })
        return response_text

    async def _generate_with_tools(self) -> str:
        backend = self._get_backend()
        messages = self.memory.get_messages()
        tools = self.tools.to_openai_tools()

        max_rounds = 10
        full_response = ""
        for _ in range(max_rounds):
            response = await backend.generate(messages=messages, tools=tools if tools else None)
            if response.content:
                full_response += response.content
            if not response.tool_calls:
                break
            # 工具调用处理...
            for tc in response.tool_calls:
                try:
                    args = json.loads(tc["arguments"]) if tc["arguments"] else {}
                except json.JSONDecodeError:
                    args = {}
                await self._emit("tool_call", {
                    "name": tc["name"], "arguments": args,
                    "timestamp": datetime.now().isoformat(),
                })
                result = await self.tools.execute(tc["name"], **args)
                await self._emit("tool_call", {
                    "name": tc["name"], "result": result.to_display(),
                    "success": result.success,
                    "timestamp": datetime.now().isoformat(),
                })
                messages.append({
                    "role": "tool", "tool_call_id": tc["id"],
                    "content": result.to_display(),
                })
        return full_response or "(无响应)"

    # ========== 自动执行 ==========
    async def run_auto(self, input_text: str = "") -> AsyncGenerator[dict, None]:
        self.reset_cancel()
        yield {"type": "start", "message": f"🚀 {self.domain.name} 开始执行", "domain": self.domain.id}

        max_retries = 3
        phase_retries: dict[str, int] = {}
        phase_ids = self.domain.get_phase_ids()

        while not self.state.is_done:
            if self._cancel_event.is_set():
                yield {"type": "cancelled", "message": "用户取消了自动运行"}
                return

            phase_id = self.state.current_phase
            phase_cfg = self.domain.get_phase_by_id(phase_id)
            if not phase_cfg:
                self.state.transition(PhaseResult(phase_id=phase_id, success=True, summary="跳过"))
                continue

            retries = phase_retries.get(phase_id, 0)
            if retries >= max_retries:
                yield {"type": "phase_error", "phase": phase_id, "name": phase_cfg.name,
                       "error": f"阶段 {phase_cfg.name} 已重试 {max_retries} 次，跳过"}
                next_id = self.profile.get_transition(phase_id, success=True)
                self.state.transition(PhaseResult(phase_id=phase_id, success=True, summary="跳过"))
                continue

            yield {"type": "phase_start", "phase": phase_id, "name": phase_cfg.name}

            try:
                result = await self._execute_phase(phase_id, input_text)
                if result.success and self.domain.validators:
                    for validator in self.domain.validators:
                        if validator.phase == phase_id:
                            valid, msg = self._run_validator(validator)
                            if not valid:
                                result = PhaseResult(phase_id=phase_id, success=False, summary=f"验证失败: {msg}")
                                break

                if not result.success:
                    phase_retries[phase_id] = phase_retries.get(phase_id, 0) + 1

                self.state.transition(result)
                self.context.update_phase(phase_id, phase_name=phase_cfg.name,
                    status="completed" if result.success else "failed", summary=result.summary)

                yield {"type": "phase_end", "phase": phase_id, "name": phase_cfg.name,
                    "success": result.success, "summary": result.summary, "progress": self.state.progress}
            except Exception as e:
                phase_retries[phase_id] = phase_retries.get(phase_id, 0) + 1
                self.state.transition(PhaseResult(phase_id=phase_id, success=False, summary=f"错误: {e}"))
                yield {"type": "phase_error", "phase": phase_id, "name": phase_cfg.name, "error": str(e)}

        yield {"type": "complete", "message": "✅ 所有阶段执行完成", "progress": 100}

    async def _execute_phase(self, phase_id: str, input_text: str = "") -> PhaseResult:
        phase_cfg = self.domain.get_phase_by_id(phase_id)
        if not phase_cfg:
            return PhaseResult(phase_id=phase_id, success=True, summary="无处理程序")

        # 从 phase_handlers 获取 prompt 模板
        template = self.domain.phase_handlers.get(phase_id, "请完成当前阶段的工作。")
        # 填充变量
        prompt = template.format(
            problem_text=input_text[:10000],
            context_sections=self.context.get_all_summaries() or "",
            output_dir=self.domain.directories.get("output", "output"),
            paper_dir=self.domain.directories.get("paper", "paper"),
        )

        response = await self.chat(prompt)
        return PhaseResult(phase_id=phase_id, success=True, summary=response[:500])

    def _run_validator(self, validator_config) -> tuple[bool, str]:
        """运行验证器"""
        output_dir = self.domain.directories.get("output", "output")
        paper_dir = self.domain.directories.get("paper", "paper")
        path_template = validator_config.path.format(
            output_dir=output_dir, paper_dir=paper_dir)
        target = self.work_dir / path_template

        if validator_config.check == "json":
            if not target.exists():
                return False, f"{target.name} 未生成"
            try:
                json.loads(target.read_text(encoding="utf-8"))
                return True, ""
            except json.JSONDecodeError as e:
                return False, f"JSON 格式错误: {e}"
        elif validator_config.check == "files_exist":
            glob_pattern = validator_config.glob.format(
                output_dir=output_dir, paper_dir=paper_dir)
            matched = list(self.work_dir.glob(glob_pattern))
            if not matched:
                return False, f"未生成匹配 {validator_config.glob} 的文件"
            return True, ""
        return True, ""

    # ========== 辅助 ==========
    async def _emit(self, event: str, data: dict) -> None:
        if event == "message" and self._on_message:
            await self._on_message(data)
        elif event == "phase_change" and self._on_phase_change:
            await self._on_phase_change(data)
        elif event == "tool_call" and self._on_tool_call:
            await self._on_tool_call(data)

    def get_status(self) -> dict:
        role = self.get_current_role()
        return {
            "state": self.state.to_dict(),
            "current_role": self.current_role_id,
            "current_role_name": role.name if role else "",
            "memory_tokens": self.memory.get_token_count(),
            "memory_messages": self.memory.length,
            "tools": self.tools.tool_names,
            "context": self.context.get_all_summaries(),
        }

    def reset(self) -> None:
        self.memory.clear(keep_system=False)
        self.state = StateMachine(profile=self.domain)
        self.current_role_id = self.domain.roles[0].id if self.domain.roles else "lead"
        self.context = ContextManager(str(self.work_dir))
        self.reset_cancel()
```

- [ ] **Step 2: 编写集成测试**

```python
# backend/tests/test_academic_agent.py
class TestAcademicAgent:
    @pytest.fixture
    def minimal_profile(self, tmp_path):
        domain_dir = tmp_path / "domain"
        domain_dir.mkdir()
        (domain_dir / "domain.yaml").write_text("""
id: test
name: 测试领域
phases:
  - id: idle
    name: 空闲
    order: -1
    progress: 0
    transition: {pass: init}
  - id: init
    name: 初始化
    order: 0
    progress: 50
    transition: {pass: done}
  - id: done
    name: 完成
    order: 1
    progress: 100
roles:
  - id: lead
    name: Lead
    emoji: 🎯
    temperature: 0.5
    tools: []
directories:
  output: output
""", encoding="utf-8")
        return DomainProfile.from_directory(str(domain_dir))

    def test_agent_creation(self, tmp_path, minimal_profile, mock_llm_config):
        router = ModelRouter.from_single_config(mock_llm_config)
        tools = ToolRegistry()
        agent = AcademicAgent(
            work_dir=str(tmp_path / "workspace"),
            domain=minimal_profile,
            llm_router=router,
            tool_registry=tools,
        )
        assert agent.domain.id == "test"
        assert agent.state.current_phase == "idle"
        assert agent.current_role_id == "lead"
        assert (tmp_path / "workspace" / "output").exists()
```

- [ ] **Step 3: 运行测试并提交**

```bash
python -m pytest backend/tests/test_academic_agent.py -v --tb=short
python -m pytest backend/tests/ -v --tb=short  # 确保已有测试不受影响
git add .
git commit -m "feat: add AcademicAgent - domain-agnostic engine driven by DomainProfile"
```

---

### Task 1.4: 迁移数学建模为第一个 Domain Profile

**Files:**
- Create: `domains/math-modeling/domain.yaml`
- Move: `backend/src/ultramath/agent/prompts/*.md` → `domains/math-modeling/prompts/`
- Move: `backend/data/models/*.md` → `domains/math-modeling/knowledge/models/`
- Move: `backend/data/templates/论文/` → `domains/math-modeling/templates/paper/`
- Modify: `backend/src/ultramath/api/server.py` (支持 domain 参数)

- [ ] **Step 1: 创建目录结构**

```bash
mkdir -p domains/math-modeling/prompts
mkdir -p domains/math-modeling/knowledge/models
mkdir -p domains/math-modeling/knowledge/references
mkdir -p domains/math-modeling/templates/paper
```

- [ ] **Step 2: 创建 domain.yaml**

完成 `domains/math-modeling/domain.yaml`（完整内容如 Task 1.1 所示）。

- [ ] **Step 3: 迁移文件**

```bash
# 迁移 prompts
cp backend/src/ultramath/agent/prompts/*.md domains/math-modeling/prompts/

# 迁移 knowledge
cp backend/data/models/*.md domains/math-modeling/knowledge/models/

# 迁移 templates
cp -r backend/data/templates/论文/* domains/math-modeling/templates/paper/
```

- [ ] **Step 4: 更新 server.py 支持 domain 参数**

在 `server.py` 的 `create_agent` 函数中，接受可选的 `domain_id` 参数：

```python
def create_agent(work_dir: str, config: ConfigRequest | None = None, domain_id: str = "math-modeling") -> AcademicAgent:
    domains_base = Path(__file__).parent.parent.parent.parent / "domains"
    profile = DomainProfile.from_directory(str(domains_base / domain_id))
    
    # 根据 profile 注册工具（而非硬编码）
    tool_registry = ToolRegistry()
    # ... register tools based on profile
    
    agent = AcademicAgent(work_dir, profile, router, tool_registry)
    # ... setup callbacks
    return agent
```

- [ ] **Step 5: 运行全套测试确保不破坏已有功能**

```bash
python -m pytest backend/tests/ -v --tb=short
```

- [ ] **Step 6: 提交**

```bash
git add -A
git commit -m "refactor: migrate math-modeling to Domain Profile pattern, extract AcademicAgent"
```

---

## 阶段二: 借鉴 UltraFlow 核心模式（预计 3-4 天）

### 目标
引入 ultraflow 的 4 个关键架构模式，无需依赖 Claude Code。

---

### Task 2.1: 结构化交接协议

**Files:**
- Create: `backend/src/ultramath/engine/handoff.py`
- Create: `backend/tests/test_handoff.py`

**设计:** 每个 Agent 响应自动附加一个标准化的 Handoff 表格。引擎在阶段间传递时只传递 handoff 摘要而非完整上下文。

```python
# backend/src/ultramath/engine/handoff.py
"""结构化交接协议 — 跨 Agent 通信的标准化摘要"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Confidence(Enum):
    GREEN = "green"   # 高置信，可下游使用
    YELLOW = "yellow" # 中等置信，需标注不确定
    RED = "red"       # 低置信，仅供参考


@dataclass
class HandoffSummary:
    """标准交接摘要表"""
    agent_role: str
    agent_name: str
    conclusion: str            # 一句话结论
    confidence: Confidence
    unresolved_disagreements: list[str] = field(default_factory=list)
    key_data_referenced: list[str] = field(default_factory=list)
    downstream_warnings: list[str] = field(default_factory=list)
    artifacts_produced: dict[str, str] = field(default_factory=dict)

    def to_context_block(self) -> str:
        """渲染为可以注入下游 Agent context 的文本块"""
        lines = [
            f"## 来自 {self.agent_name} ({self.agent_role}) 的交接",
            f"| 字段 | 内容 |",
            f"|------|------|",
            f"| 结论 | {self.conclusion} |",
            f"| 置信度 | {self.confidence.value} |",
        ]
        if self.unresolved_disagreements:
            lines.append(f"| 未解决分歧 | {'; '.join(self.unresolved_disagreements)} |")
        if self.key_data_referenced:
            lines.append(f"| 关键数据引用 | {'; '.join(self.key_data_referenced)} |")
        if self.downstream_warnings:
            lines.append(f"| 下游警告 | {'; '.join(self.downstream_warnings)} |")
        return "\n".join(lines)


def parse_handoff_from_text(text: str) -> HandoffSummary | None:
    """尝试从 LLM 输出中解析交接表（Markdown 表格格式）"""
    import re
    # 匹配 Markdown 表格
    table_match = re.search(r'\| 字段 \| 内容 \|.*?(?=\n\n|\Z)', text, re.DOTALL)
    if not table_match:
        return None

    table_text = table_match.group(0)
    fields: dict[str, str] = {}
    for line in table_text.split('\n'):
        match = re.match(r'\|\s*(.+?)\s*\|\s*(.+?)\s*\|', line)
        if match and match.group(1) not in ('字段', '---'):
            fields[match.group(1)] = match.group(2)

    if '结论' not in fields:
        return None

    return HandoffSummary(
        agent_role="unknown",
        agent_name="unknown",
        conclusion=fields.get('结论', ''),
        confidence=Confidence.GREEN if 'green' in fields.get('置信度', '').lower() else
                   Confidence.YELLOW if 'yellow' in fields.get('置信度', '').lower() else
                   Confidence.RED,
        unresolved_disagreements=[fields.get('未解决分歧', '')] if fields.get('未解决分歧') else [],
        key_data_referenced=[fields.get('关键数据引用', '')] if fields.get('关键数据引用') else [],
        downstream_warnings=[fields.get('下游警告', '')] if fields.get('下游警告') else [],
    )
```

- [ ] **Step 1: 编写测试**

```python
# backend/tests/test_handoff.py
class TestHandoff:
    def test_parse_from_markdown_table(self):
        text = """一些其他内容...
| 字段 | 内容 |
|------|------|
| 结论 | 模型A优于模型B |
| 置信度 | green |
| 未解决分歧 | 参数X取值存在争议 |
| 关键数据引用 | data.csv, config.json |
| 下游警告 | 线性假设可能不成立 |

后续内容..."""

        handoff = parse_handoff_from_text(text)
        assert handoff is not None
        assert handoff.conclusion == "模型A优于模型B"
        assert handoff.confidence == Confidence.GREEN
        assert "参数X取值存在争议" in handoff.unresolved_disagreements

    def test_parse_no_table_returns_none(self):
        assert parse_handoff_from_text("普通文本，没有表格。") is None

    def test_to_context_block(self):
        handoff = HandoffSummary(
            agent_role="critic",
            agent_name="审稿人",
            conclusion="代码可以运行但效率低",
            confidence=Confidence.YELLOW,
            downstream_warnings=["需要优化循环"],
        )
        block = handoff.to_context_block()
        assert "审稿人" in block
        assert "yellow" in block
        assert "需要优化循环" in block
```

- [ ] **Step 2: 运行测试并提交**

```bash
python -m pytest backend/tests/test_handoff.py -v --tb=short
git add .
git commit -m "feat: add structured handoff protocol with markdown table parsing"
```

---

### Task 2.2: 信赖阈值系统

**Files:**
- Create: `backend/src/ultramath/engine/trust.py`
- Create: `backend/tests/test_trust.py`

**设计:** 记录用户接受/拒绝历史，动态调整是否需要用户确认每个步骤。

```python
# backend/src/ultramath/engine/trust.py
"""信赖阈值系统 — 根据用户反馈历史调整确认行为"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path


class TrustLevel(enum.Enum):
    LOOSE = "loose"       # 连续 5+ 接受 → 跳过确认
    RELAXED = "relaxed"   # 连续 3+ 接受 
    NORMAL = "normal"     # 默认
    TIGHTEN = "tighten"   # 连续 2 拒绝
    RESET = "reset"       # corrected_later 触发 → 最保守


@dataclass
class TrustRecord:
    """一次信赖记录"""
    phase_id: str
    accepted: bool        # True=接受, False=拒绝
    corrected_later: bool = False  # 后来被纠正
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class TrustManager:
    """信赖管理器"""

    MAX_HISTORY = 20

    def __init__(self, storage_path: str):
        self.storage_path = Path(storage_path)
        self.records: list[TrustRecord] = []
        self._load()

    def record(self, phase_id: str, accepted: bool, corrected_later: bool = False) -> None:
        """记录一次用户反馈"""
        self.records.append(TrustRecord(phase_id=phase_id, accepted=accepted, corrected_later=corrected_later))
        if len(self.records) > self.MAX_HISTORY:
            self.records = self.records[-self.MAX_HISTORY:]
        self._save()

    def get_trust_level(self) -> TrustLevel:
        """根据最近反馈计算信赖级别"""
        recent = self.records[-10:]

        # corrected_later 立即重置
        if any(r.corrected_later for r in recent[-3:]):
            return TrustLevel.RESET

        accepts = sum(1 for r in recent if r.accepted)
        rejects = sum(1 for r in recent if not r.accepted)

        if accepts >= 5 and rejects == 0:
            return TrustLevel.LOOSE
        if accepts >= 3 and rejects == 0:
            return TrustLevel.RELAXED
        if rejects >= 2:
            return TrustLevel.TIGHTEN
        return TrustLevel.NORMAL

    def should_confirm(self, phase_id: str) -> bool:
        """判断当前阶段是否需要用户确认"""
        level = self.get_trust_level()
        if level in (TrustLevel.LOOSE, TrustLevel.RELAXED):
            return False
        return True  # NORMAL / TIGHTEN / RESET 都需要确认

    def _save(self) -> None:
        data = [{"phase_id": r.phase_id, "accepted": r.accepted,
                 "corrected_later": r.corrected_later, "timestamp": r.timestamp}
                for r in self.records]
        self.storage_path.write_text(json.dumps(data, ensure_ascii=False, indent=2))

    def _load(self) -> None:
        if self.storage_path.exists():
            try:
                data = json.loads(self.storage_path.read_text())
                self.records = [TrustRecord(**r) for r in data]
            except Exception:
                self.records = []
```

- [ ] **Step 1: 编写测试**

```python
class TestTrustManager:
    @pytest.fixture
    def trust_file(self, tmp_path):
        return str(tmp_path / "trust.json")

    def test_default_level(self, trust_file):
        tm = TrustManager(trust_file)
        assert tm.get_trust_level() == TrustLevel.NORMAL

    def test_five_accepts_reaches_loose(self, trust_file):
        tm = TrustManager(trust_file)
        for _ in range(5):
            tm.record("analysis", accepted=True)
        assert tm.get_trust_level() == TrustLevel.LOOSE

    def test_two_rejects_tighten(self, trust_file):
        tm = TrustManager(trust_file)
        tm.record("analysis", accepted=False)
        tm.record("analysis", accepted=False)
        assert tm.get_trust_level() == TrustLevel.TIGHTEN

    def test_corrected_later_resets(self, trust_file):
        tm = TrustManager(trust_file)
        for _ in range(5):
            tm.record("analysis", accepted=True)
        tm.record("analysis", accepted=True, corrected_later=True)
        assert tm.get_trust_level() == TrustLevel.RESET

    def test_persistence(self, trust_file):
        tm1 = TrustManager(trust_file)
        tm1.record("analysis", accepted=True)
        tm1.record("analysis", accepted=True)

        tm2 = TrustManager(trust_file)
        assert len(tm2.records) == 2
```

- [ ] **Step 2: 运行测试并提交**

```bash
python -m pytest backend/tests/test_trust.py -v --tb=short
git add .
git commit -m "feat: add trust manager with adaptive confirmation thresholds"
```

---

### Task 2.3: 外部化状态 + 会话恢复

**Files:**
- Modify: `backend/src/ultramath/memory/context.py`

**设计:** 将当前已有的 `ContextManager` 扩展为支持会话恢复的完整状态外部化方案。

- [ ] **Step 1: 扩展 ContextManager**

在 `ContextManager` 中添加 `save_checkpoint` 和 `restore_checkpoint` 方法：

```python
# 在 ContextManager 中添加
def save_checkpoint(self, agent_state: dict) -> None:
    """保存完整检查点"""
    checkpoint = {
        "timestamp": datetime.now().isoformat(),
        "agent_state": agent_state,
        "phases": self.project.phases,
    }
    checkpoint_path = self.context_file.parent / "checkpoint.json"
    checkpoint_path.write_text(json.dumps(checkpoint, ensure_ascii=False, indent=2))

def restore_checkpoint(self) -> dict | None:
    """恢复检查点"""
    checkpoint_path = self.context_file.parent / "checkpoint.json"
    if not checkpoint_path.exists():
        return None
    try:
        return json.loads(checkpoint_path.read_text(encoding="utf-8"))
    except Exception:
        return None

def cleanup_old_checkpoints(self, max_age_days: int = 7) -> int:
    """清理过期检查点"""
    checkpoint_path = self.context_file.parent / "checkpoint.json"
    if not checkpoint_path.exists():
        return 0
    age = datetime.now() - datetime.fromtimestamp(checkpoint_path.stat().st_mtime)
    if age.days > max_age_days:
        checkpoint_path.unlink(missing_ok=True)
        return 1
    return 0
```

- [ ] **Step 2: 提交**

```bash
git add backend/src/ultramath/memory/context.py
git commit -m "feat: add checkpoint save/restore for session recovery"
```

---

### Task 2.4: 固化模式 — 成功的运行自动转化为领域预设

**Files:**
- Create: `backend/src/ultramath/engine/solidify.py`

**设计:** 一次成功的运行后，用户可以"固化" — 将本次运行的配置（prompts、phases、knowledge）保存为一个新的领域预设。

```python
# backend/src/ultramath/engine/solidify.py
"""固化模式 — 将成功的 ad-hoc 运行转化为永久领域预设"""
from __future__ import annotations

import json
import shutil
from pathlib import Path
from datetime import datetime

from .domain import DomainProfile


def solidify_session(
    source_work_dir: str,
    target_domain_name: str,
    domains_base_dir: str,
) -> str:
    """将一次成功运行的产出固化到新的领域预设目录"""
    source = Path(source_work_dir)
    target = Path(domains_base_dir) / target_domain_name

    if target.exists():
        raise FileExistsError(f"领域 {target_domain_name} 已存在")

    # 创建领域目录结构
    target.mkdir(parents=True)
    (target / "prompts").mkdir()
    (target / "knowledge").mkdir()
    (target / "templates").mkdir()

    # 复制上下文中的 phase 信息构建 domain.yaml
    context_file = source / "context.json"
    if context_file.exists():
        context_data = json.loads(context_file.read_text(encoding="utf-8"))
        domain_cfg = {
            "id": target_domain_name,
            "name": target_domain_name,
            "description": f"固化于 {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "version": "1.0",
            "solidified_from": str(source),
            "phases": _build_phases_from_context(context_data),
            "roles": [{"id": "lead", "name": "Lead", "temperature": 0.5, "tools": []}],
            "directories": {"output": "output"},
        }
        (target / "domain.yaml").write_text(
            json.dumps(domain_cfg, ensure_ascii=False, indent=2))

    # 复制产出的 prompts（如果有保存）
    prompts_source = source / "agent_prompts"
    if prompts_source.exists():
        shutil.copytree(prompts_source, target / "prompts", dirs_exist_ok=True)

    # 复制 knowledge 产出
    knowledge_source = source / "knowledge"
    if knowledge_source.exists():
        shutil.copytree(knowledge_source, target / "knowledge", dirs_exist_ok=True)

    return str(target)


def _build_phases_from_context(context_data: dict) -> list[dict]:
    """从上下文中提取阶段定义"""
    phases = []
    phase_entries = context_data.get("phases", {})
    for phase_id, phase_info in sorted(phase_entries.items()):
        phases.append({
            "id": phase_id,
            "name": phase_info.get("phase_name", phase_id),
            "order": len(phases),
            "progress": (len(phases) + 1) * 10,
            "transition": {"pass": "done"} if len(phases) > 3 else {"pass": f"phase_{len(phases) + 1}"},
        })
    return phases
```

- [ ] **Step 1: 编写测试**

```python
class TestSolidify:
    def test_solidify_creates_domain_structure(self, tmp_path):
        source_dir = tmp_path / "workspace"
        source_dir.mkdir()
        (source_dir / "context.json").write_text(json.dumps({
            "phases": {
                "init": {"phase_name": "初始化"},
                "analysis": {"phase_name": "分析"},
            }
        }), encoding="utf-8")

        domains_dir = tmp_path / "domains"
        domains_dir.mkdir()

        result = solidify_session(str(source_dir), "my-domain", str(domains_dir))
        assert (domains_dir / "my-domain" / "domain.yaml").exists()
        assert (domains_dir / "my-domain" / "prompts").exists()
```

- [ ] **Step 2: 提交**

```bash
git add backend/src/ultramath/engine/solidify.py backend/tests/test_solidify.py
git commit -m "feat: add solidify mode - convert successful run to permanent domain preset"
```

---

## 阶段三: 新领域预设 — 论文/实验报告/综述（预计 4-5 天）

### 目标
创建 3 个新的 Domain Profile，证明系统的泛化能力。

---

### Task 3.1: 学术论文写作领域

**Files:**
- Create: `domains/paper-writing/domain.yaml`
- Create: `domains/paper-writing/prompts/agent_lead.md`
- Create: `domains/paper-writing/prompts/agent_writer.md`
- Create: `domains/paper-writing/prompts/agent_reviewer.md`
- Create: `domains/paper-writing/templates/paper-template.tex`

- [ ] **Step 1: 创建 domain.yaml**

```yaml
# domains/paper-writing/domain.yaml
id: paper-writing
name: 学术论文写作
description: 从研究大纲到完整学术论文的自动撰写
version: "1.0"

phases:
  - id: idle
    name: 空闲
    order: -1
    progress: 0
    transition: {pass: outline}
  - id: outline
    name: 大纲构建
    order: 0
    progress: 10
    transition: {pass: drafting, fail: outline}
  - id: drafting
    name: 正文撰写
    order: 1
    progress: 40
    transition: {pass: formatting, fail: drafting}
  - id: formatting
    name: 格式编排
    order: 2
    progress: 70
    transition: {pass: review, fail: formatting}
  - id: review
    name: 审稿与润色
    order: 3
    progress: 90
    transition: {pass: done, fail: drafting}
  - id: done
    name: 完成
    order: 4
    progress: 100

roles:
  - id: lead
    name: 论文主编
    emoji: 📄
    temperature: 0.5
    tools: [file_manager, quality_checker]
  - id: writer
    name: 章节作者
    emoji: ✍️
    temperature: 0.7
    tools: [file_manager, latex_compiler]
  - id: reviewer
    name: 学术审稿人
    emoji: 🔍
    temperature: 0.3
    tools: [file_manager, quality_checker]
  - id: formatter
    name: 格式编排
    emoji: 📐
    temperature: 0.2
    tools: [file_manager, latex_compiler]

directories:
  output: sections
  paper: paper

phase_handlers:
  outline: |
    请根据以下研究大纲，构建完整论文的章节结构。
    包括：Introduction, Related Work, Method, Experiments, Discussion, Conclusion。
    确定每章的核心内容、关键引用、图表计划。
    
    {input_text}
    
    {context_sections}
  drafting: |
    请逐章撰写正文。要求：
    1. 每章独立成文，逻辑连贯
    2. 引用格式统一
    3. 图表编号连续
    4. 术语一致
    
    {context_sections}
  formatting: |
    请将撰写好的章节整合到 LaTeX 模板中，统一格式。
    
    {context_sections}
  review: |
    请作为审稿人，从以下维度评审：
    1. 论证逻辑完整性
    2. 实验可复现性
    3. 文献覆盖度
    4. 语言表达质量
    5. 格式规范性
    
    {context_sections}

validators:
  - phase: drafting
    check: files_exist
    glob: "{output_dir}/*.tex"
  - phase: formatting
    check: files_exist
    glob: "{paper_dir}/*.tex"
```

- [ ] **Step 2: 创建角色 prompts**

`domains/paper-writing/prompts/agent_lead.md`:

```markdown
# 论文主编 -- Academic Writing Lead

你是学术论文写作流程的协调者。你负责：
1. 理解用户的研究大纲和核心贡献
2. 拆解为可执行的章节计划
3. 调度章节作者和审稿人
4. 全局一致性检查

## 工作原则
- 始终以研究贡献为核心，所有章节服务于论证主线
- 实验部分要求可复现性检查
- 引用格式统一（默认 APA）
- 图表必须有完整的 caption 和交叉引用

## 交接格式
每次完成任务后，输出以下表格：

| 字段 | 内容 |
|------|------|
| 结论 | [一句话总结当前进度] |
| 置信度 | green/yellow/red |
| 未解决分歧 | [...] |
| 关键数据引用 | [...] |
| 下游警告 | [...] |
```

`domains/paper-writing/prompts/agent_writer.md`:

```markdown
# 章节作者 -- Academic Writer

你是学术论文的章节作者。你的职责：
1. 根据大纲撰写指定章节的完整正文
2. 确保与前后章节的逻辑连贯
3. 所有声明需要文献支持或实验验证
4. 图表编号和引用准确

## 写作规范
- 段落主旨句前置
- 每个声明必须有引用或论证
- 避免模糊语言（"可能"、"似乎"需要标注置信度）
- 图表的 caption 需独立可理解

## 交接格式
| 字段 | 内容 |
|------|------|
| 结论 | [...] |
| 置信度 | green/yellow/red |
| 未解决分歧 | [...] |
| 关键数据引用 | [...] |
| 下游警告 | [...] |
```

- [ ] **Step 3: 创建 LaTeX 模板**

`domains/paper-writing/templates/paper-template.tex`:

```latex
\documentclass[11pt,a4paper]{article}
\usepackage[utf8]{inputenc}
\usepackage{amsmath,amssymb}
\usepackage{graphicx}
\usepackage{hyperref}
\usepackage{booktabs}
\usepackage{natbib}

\title{Your Paper Title}
\author{Author Name}
\date{\today}

\begin{document}
\maketitle

\begin{abstract}
% ABSTRACT_PLACEHOLDER
\end{abstract}

\section{Introduction}
% INTRODUCTION_PLACEHOLDER

\section{Related Work}
% RELATED_WORK_PLACEHOLDER

\section{Method}
% METHOD_PLACEHOLDER

\section{Experiments}
% EXPERIMENTS_PLACEHOLDER

\section{Discussion}
% DISCUSSION_PLACEHOLDER

\section{Conclusion}
% CONCLUSION_PLACEHOLDER

\bibliographystyle{plainnat}
\bibliography{references}
\end{document}
```

- [ ] **Step 4: 运行验证**

```bash
# 确保 domain 可以加载
python -c "
from ultramath.engine.domain import DomainProfile
p = DomainProfile.from_directory('domains/paper-writing')
assert p.id == 'paper-writing'
assert len(p.phases) == 6
assert len(p.roles) == 4
print('OK: paper-writing domain loaded successfully')
"
```

- [ ] **Step 5: 提交**

```bash
git add domains/paper-writing/
git commit -m "feat: add paper-writing domain profile"
```

---

### Task 3.2: 实验报告领域

**Files:**
- Create: `domains/lab-report/domain.yaml`
- Create: `domains/lab-report/prompts/agent_lead.md` (3 个 roles)
- Create: `domains/lab-report/templates/lab-report.tex`

**domain.yaml** (phases: design → methods → results → discussion → conclusion):

```yaml
id: lab-report
name: 实验报告
description: 从实验数据和假设到完整实验报告
version: "1.0"

phases:
  - id: idle
    name: 空闲
    order: -1
    progress: 0
    transition: {pass: design}
  - id: design
    name: 实验设计
    order: 0
    progress: 15
    transition: {pass: methods, fail: design}
  - id: methods
    name: 方法描述
    order: 1
    progress: 35
    transition: {pass: results, fail: methods}
  - id: results
    name: 结果分析
    order: 2
    progress: 60
    transition: {pass: discussion, fail: results}
  - id: discussion
    name: 讨论与结论
    order: 3
    progress: 85
    transition: {pass: done, fail: results}
  - id: done
    name: 完成
    order: 4
    progress: 100

roles:
  - id: lead
    name: 实验指导
    emoji: 🧪
    temperature: 0.5
    tools: [file_manager]
  - id: analyst
    name: 数据分析师
    emoji: 📊
    temperature: 0.3
    tools: [code_executor, figure_generator, file_manager]
  - id: writer
    name: 报告撰写
    emoji: 📝
    temperature: 0.6
    tools: [file_manager, latex_compiler]

directories:
  output: results
  paper: report
  data: data

phase_handlers:
  design: |
    请根据实验目标设计实验方案：
    1. 明确自变量、因变量、控制变量
    2. 确定样本量和分组
    3. 预期结果和假设
    
    {input_text}
  methods: |
    请详细描述实验方法，包括：
    1. 实验材料和设备
    2. 实验步骤（可复现）
    3. 数据分析方法（统计检验、效应量）
  results: |
    请分析实验数据并呈现结果：
    1. 描述性统计
    2. 统计检验结果
    3. 图表可视化
  discussion: |
    请讨论结果并得出结论：
    1. 假设验证情况
    2. 与已有研究对比
    3. 局限性
    4. 结论

validators:
  - phase: results
    check: files_exist
    glob: "{output_dir}/*.png"
```

### Task 3.3: 文献综述领域

**Files:**
- Create: `domains/literature-review/domain.yaml`
- Create: `domains/literature-review/prompts/agent_lead.md` (3 roles)
- Create: `domains/literature-review/prompts/agent_researcher.md`

**domain.yaml** (phases: search → screen → synthesize → draft → review):

```yaml
id: literature-review
name: 文献综述
description: 系统性文献综述的半自动撰写
version: "1.0"

phases:
  - id: idle
    name: 空闲
    order: -1
    progress: 0
    transition: {pass: search}
  - id: search
    name: 文献检索策略
    order: 0
    progress: 10
    transition: {pass: screen, fail: search}
  - id: screen
    name: 文献筛选
    order: 1
    progress: 25
    transition: {pass: synthesize, fail: screen}
  - id: synthesize
    name: 文献综合
    order: 2
    progress: 50
    transition: {pass: draft, fail: synthesize}
  - id: draft
    name: 综述撰写
    order: 3
    progress: 75
    transition: {pass: review, fail: draft}
  - id: review
    name: 质量审查
    order: 4
    progress: 90
    transition: {pass: done, fail: draft}
  - id: done
    name: 完成
    order: 5
    progress: 100

roles:
  - id: lead
    name: 综述主编
    emoji: 📚
    temperature: 0.5
    tools: [file_manager, quality_checker]
  - id: researcher
    name: 文献研究员
    emoji: 🔬
    temperature: 0.4
    tools: [file_manager]
  - id: synthesizer
    name: 综合分析
    emoji: 🧩
    temperature: 0.6
    tools: [file_manager, latex_compiler]

directories:
  output: review-sections
  paper: paper

phase_handlers:
  search: |
    请制定系统性的文献检索策略：
    1. 关键词组合和检索式
    2. 数据库选择（Web of Science, Scopus, etc.）
    3. 纳入/排除标准
    {input_text}
  screen: |
    请根据 PRISMA 框架进行文献筛选：
    1. 去除重复文献
    2. 标题/摘要筛选
    3. 全文筛选
    4. 生成 PRISMA 流程图数据
  synthesize: |
    请综合筛选后的文献：
    1. 按主题聚类
    2. 提取关键发现
    3. 识别研究空白
    4. 评估方法学质量
  draft: |
    请撰写完整的文献综述：
    1. Introduction（研究背景和意义）
    2. 检索策略和筛选结果
    3. 主题分析与综合
    4. Discussion（研究空白、未来方向）
    5. Conclusion

validators:
  - phase: draft
    check: files_exist
    glob: "{paper_dir}/*.tex"
```

---

## 阶段四: 前端领域切换 + UI/UX 优化（预计 2-3 天）

### Task 4.1: 领域切换 UI

**Files:**
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/components/Sidebar.tsx`
- Modify: `frontend/src/components/SettingsPanel.tsx`

**设计:** 
- 启动时从后端 `/api/domains` 获取可用领域列表
- Sidebar 顶部添加领域选择下拉框
- SettingsPanel 中领域作为项目初始化的一部分
- 切换领域时自动重新加载 phases 和 roles

- [ ] **Step 1: 添加 REST 端点**

```python
# 在 server.py 中添加
@app.get("/api/domains")
async def list_domains():
    """列出所有可用领域"""
    domains_base = Path(__file__).parent.parent.parent.parent / "domains"
    return {"domains": DomainProfile.list_domains(str(domains_base))}
```

- [ ] **Step 2: 前端 fetcher**

```typescript
// 在 App.tsx 中添加
useEffect(() => {
  fetch(`${API_BASE_URL}/api/domains`)
    .then(res => res.json())
    .then(data => setDomains(data.domains || []));
}, [isConnected]);
```

- [ ] **Step 3: Sidebar 添加领域图标**

在 Sidebar Logo 下方添加：

```tsx
{domain && (
  <div className="px-3 py-2 border-b border-[var(--color-border)]">
    <div className="text-[10px] text-[var(--color-text-secondary)]/50 uppercase tracking-wider mb-1">
      当前领域
    </div>
    <div className="text-xs font-medium text-[var(--color-text)]">
      {domain.name}
    </div>
  </div>
)}
```

- [ ] **Step 4: 提交**

```bash
git add frontend/src/App.tsx frontend/src/components/Sidebar.tsx
git add backend/src/ultramath/api/server.py
git commit -m "feat: add domain switching UI and API endpoint"
```

---

## 阶段五: 信息不对称 + 门禁系统（预计 2-3 天）

### Task 5.1: 文件隔离执行模式

**Files:**
- Create: `backend/src/ultramath/engine/isolation.py`

**设计:** 借鉴 ultraflow 的信息不对称模式。不同 Agent 看到不同的文件集，通过文件级别隔离实现真正的独立评审。

```python
# backend/src/ultramath/engine/isolation.py
"""Agent 文件隔离 — 不同 Agent 看到不同的文件集"""
from __future__ import annotations

from pathlib import Path


class FileVisibility:
    """控制 Agent 对工作目录中文件的可见性"""

    def __init__(self, work_dir: Path, agent_role: str, isolation_rules: dict[str, list[str]]):
        """
        isolation_rules: {role_id: ["glob_pattern", ...]}
        """
        self.work_dir = work_dir
        self.agent_role = agent_role
        self.rules = isolation_rules

    def get_visible_files(self) -> list[Path]:
        """获取当前 Agent 可见的文件列表"""
        allowed = self.rules.get(self.agent_role, ["*"])
        if "*" in allowed:
            return list(self.work_dir.rglob("*"))

        visible = []
        for pattern in allowed:
            visible.extend(self.work_dir.glob(pattern))
        return [f for f in visible if f.is_file()]

    def filter_system_prompt(self, prompt: str) -> str:
        """在 system prompt 中注入可见文件列表"""
        visible = self.get_visible_files()
        file_list = "\n".join(str(f.relative_to(self.work_dir)) for f in visible[:50])
        return prompt + f"\n\n## 你可访问的文件:\n{file_list}"
```

- [ ] **Step 1: 编写测试**

```python
class TestFileVisibility:
    def test_critic_sees_only_generator_output(self, tmp_path):
        work_dir = tmp_path / "workspace"
        work_dir.mkdir()
        (work_dir / "generator_output.md").write_text("gen content")
        (work_dir / "original_problem.md").write_text("problem")

        rules = {
            "generator": ["original_problem.md"],
            "critic": ["generator_output.md"],  # 审稿人看不到原题
        }

        critic_vis = FileVisibility(work_dir, "critic", rules)
        visible = critic_vis.get_visible_files()
        visible_names = [f.name for f in visible]
        assert "generator_output.md" in visible_names
        assert "original_problem.md" not in visible_names
```

---

## 总结: 执行路线图

```
阶段一 (4-5天)          阶段二 (3-4天)          阶段三 (4-5天)
核心架构重构 ─────────→ 借鉴 UltraFlow 模式 ───→ 新领域预设
                                                        │
┌─ DomainProfile 模型     ┌─ 结构化交接协议          ├─ paper-writing
├─ StateMachine 重构      ├─ 信赖阈值系统            ├─ lab-report
├─ AcademicAgent 引擎     ├─ 会话恢复                └─ literature-review
└─ math-modeling 迁移     └─ 固化模式
                                    ↓
                              阶段四 (2-3天)          阶段五 (2-3天)
                              前端领域切换 ───────→ 信息不对称门禁
                              ├─ /api/domains           ├─ FileVisibility
                              ├─ Sidebar 领域选择       └─ 隔离执行
                              └─ Settings 集成
```

**预估总工期: 15-20 个工作日**

---

## 验收标准

| 里程碑 | 验收标准 |
|--------|----------|
| M1: 架构重构完成 | 数学建模作为 Domain Profile 加载运行，与原 LemmaAgent 行为一致 |
| M2: UltraFlow 模式集成 | 移交协议可自动解析、信赖阈值可调整确认行为、会话可恢复 |
| M3: 新领域可用 | paper-writing + lab-report + literature-review 三个领域全部加载无报错 |
| M4: 前端可用 | 领域切换 UI 正常工作，切换后 phases/roles 随之变化 |
| M5: 端到端 | 用数学建模领域完成一次完整自动执行（与 v2.0 行为一致）|
| M6: 代码质量 | 所有测试通过、lint 零错误、新增代码覆盖率 >70% |
