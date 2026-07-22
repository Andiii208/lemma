# Lemma × GitHub Skills 集成计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 将 GitHub 上 4 个高星标 Agent Skills 仓库的核心方法论移植到 Lemma 的 prompt 系统、工具链和工作流中，让每个 Agent 角色获得"业界最佳实践"级别的行为约束和能力。

**Architecture:** 三个集成层——① Prompt 层注入（修改 agent_*.md 和 phase_handlers）→ ② 工具层扩展（新增 SourceTracker、EvidenceMap 工具）→ ③ 工作流升级（线性流水线 → 递归分解）。

**Tech Stack:** 同现有项目（Python 3.12+, FastAPI, React 18, TypeScript）

**参考仓库:**
- [davidamitchell/Skills](https://github.com/davidamitchell/Skills) — 20 个学术 SKILL.md 模板
- [luwill/research-skills](https://github.com/luwill/research-skills) — 5-Agent 综述系统
- [WenyuChiou/ai-research-skills](https://github.com/WenyuChiou/ai-research-skills) — 15 Skills + YAML 跨 Agent 委托
- [x1xhlol/system-prompts-and-models-of-ai-tools](https://github.com/x1xhlol/system-prompts-and-models-of-ai-tools) (60K⭐) — 7000+ 行真实 system prompt

---

## 一、Prompt 层注入：用开源 SKILL.md 增强每个 Agent 角色

### Task 1.1: 审稿人 Agent 注入 `peer-reviewer` + `speculation-control`

**参考:** [peer-reviewer SKILL.md](https://raw.githubusercontent.com/davidamitchell/Skills/main/peer-reviewer/SKILL.md)

**Files:**
- Modify: `domains/math-modeling/prompts/agent_reviewer.md`
- Modify: `domains/paper-writing/prompts/agent_reviewer.md`

**当前 prompt 问题:** 只有一句"进行五维度评分卡审稿"，没有具体的审查规则和检查清单。

**改进方案:** 在现有 reviewer prompt 末尾追加：

```markdown
## 审查纪律（从开源 peer-reviewer 技能移植）

### 维度一：逻辑连贯性与证据充分性
对每一章/每一节输出：
- PASS: 结论在正文中有对应证据支撑
- FAIL: 结论无证据支撑，或置信度与证据量不匹配

判定规则：
- 标注 High 置信度需要 ≥2 个独立来源，否则降级为 Medium
- 标注 Medium 需要 ≥1 个可信来源，否则降级为 Low
- 执行摘要中的因果断言若未标为 [inference] 且无因果证据 → FAIL

### 维度二：替代解释
- 对每个争议性结论，必须至少承认一个竞争假设
- 若只给单一解释且领域内存在公认的其他解释 → FAIL
- 驳回替代解释必须给出推理或证据

### 维度三：跨条目整合
- 结论若与前面阶段的发现矛盾、扩展或依赖，必须交叉引用
- 若缺失该引用且结论会因此改变 → FAIL

### 输出格式
对每章输出：
```
REVIEW_TARGET: <章节名>
logical-coherence: PASS | FAIL (具体违规)
alternative-explanations: PASS | FAIL (具体违规)
cross-integration: PASS | FAIL (具体违规)
OVERALL: PASS | FAIL
```

### 推测控制（speculation-control）
- 审查全文，区分 [fact]（来源可独立验证）和 [inference]（推断/解释/推测）
- 对于标记为 [fact] 但无法独立验证的断言 → 降级为 [inference]
- 对于模糊量词（"许多"、"显著"、"大多数"）→ 要求替换为具体数值或删除
```

- [ ] **Step 1: 修改 agent_reviewer.md**（两个领域各一次）
- [ ] **Step 2: 验证**：使用现有测试数据确认新 prompt 不会导致 LLM 输出混乱
- [ ] **Step 3: 提交**

```bash
git add domains/math-modeling/prompts/agent_reviewer.md domains/paper-writing/prompts/agent_reviewer.md
git commit -m "feat(reviewer): inject peer-reviewer 3-dimension audit + speculation-control from OSS skills"
```

---

### Task 1.2: 作家/数学家 Agent 注入 `citation-discipline`

**参考:** [citation-discipline SKILL.md](https://raw.githubusercontent.com/davidamitchell/Skills/main/citation-discipline/SKILL.md)

**Files:**
- Modify: `domains/math-modeling/prompts/agent_math.md`
- Modify: `domains/math-modeling/prompts/agent_writer.md`
- Modify: `domains/paper-writing/prompts/agent_writer.md`

**核心规则注入:**

```markdown
## 来源纪律

### 强制规则
1. **无来源不陈述**: 每个事实性断言必须绑定可验证来源（定理、文献、数据文件）
2. **认知标签**: 每个断言末尾标注 [fact] 或 [inference]
   - [fact]: 引用的来源直接支持该断言，且来源可由读者独立验证
   - [inference]: 基于来源的推断、解释或推测
3. **禁止模糊量词**: 不用"许多"、"显著"、"大多数"，改用具体数值或百分比
4. **禁止网络搜索合成**: 若来源是网络搜索结果，必须提供具体 URL 或替换为可验证来源
5. **范畴匹配**: 引用的来源范畴必须匹配断言范畴
   - 例：用企业版文档不能支持"公开版"的断言
6. **首次术语展开**: 每个缩写首次出现时必须"全称（缩写）"，每个非自明术语必须附权威定义链接

### 输出前自检清单
1. 扫描全文缩略词 → 确保首次展开
2. 检查每条引用 → 确保有 URL/DOI/文件路径可独立验证
3. 搜索"网络搜索合成"等表述 → 替换为具体来源
4. 审计 [fact] 标签 → 确认来源直接支持，否则降级为 [inference]
5. 检查范畴匹配 → 来源的使用范围是否与断言一致
```

- [ ] **Step 1: 修改 agent_math.md 和 agent_writer.md**
- [ ] **Step 2: 验证**
- [ ] **Step 3: 提交**

---

### Task 1.3: 指挥 Agent 注入 `research` 递归分解方法

**参考:** [research SKILL.md](https://raw.githubusercontent.com/davidamitchell/Skills/main/research/SKILL.md)

**Files:**
- Modify: `domains/math-modeling/prompts/agent_lead.md`
- Modify: `domains/paper-writing/prompts/agent_lead.md`
- Modify: `domains/lab-report/prompts/agent_lead.md`
- Modify: `domains/literature-review/prompts/agent_lead.md`

**核心规则注入:**

```markdown
## 递归问题分解

### 工作原则
遇到复杂问题时，不要线性推进，按以下算法分解：

```
RESEARCH(问题):
  subquestions = DECOMPOSE(问题)
  for each q in subquestions:
    if q 是原子问题（可用一个证据声明回答）:
      answer[q] = INVESTIGATE(q)
    else:
      answer[q] = RESEARCH(q)  ← 递归分解
  return SYNTHESISE(answer)
```

### 原子问题判断标准
一个问题可以被视为"原子"，当且仅当：
- 它只涉及单一变量或单一关系
- 它可以被一个具体的数据点、公式或引用直接回答
- 它不需要进一步的"为什么"追问

### 分解树规范
- 维护一棵分解树以保证透明度
- 每个节点包含：问题描述 → 分解策略 → 子问题 → 证据
- 叶子节点（原子问题）必须绑定 [fact] 或 [inference] 标签

### 验证循环
在输出最终结论前，执行以下检查：
1. **内部一致性**: 扫描矛盾、无支撑的逻辑跳跃
2. **来源充足性**: 每个 High 置信度结论有 ≥2 个独立来源
3. **递归审查**: 对每个子结论递归验证清晰度、证据、逻辑
   - 停止条件：所有部分有据可查、所有线索已综合、所有不确定性已明示
```

- [ ] **Step 1: 修改 4 个 agent_lead.md**
- [ ] **Step 2: 验证**
- [ ] **Step 3: 提交**

---

### Task 1.4: 从 v0/Cursor/Manus 系统 prompts 中提取角色定义模式

**参考:** [x1xhlol/system-prompts-and-models-of-ai-tools](https://github.com/x1xhlol/system-prompts-and-models-of-ai-tools) (60K⭐)

**Files:**
- Modify: 所有 16 个 `domains/*/prompts/agent_*.md`

**改进方向:** 这个仓库包含 v0、Cursor、Manus 等顶级 AI 工具的真实系统 prompt。从中学到的关键模式：

```markdown
## 角色定义增强模板

### 1. 明确的能力边界
你不是：[列出不擅长的事]
你是：[列出核心能力]
当遇到超出能力边界的问题时，你必须：[明确的行为]

### 2. 工具使用规范
- 在调用工具前，先思考该工具是否必要
- 每次调用工具后，解释调用结果如何推进当前任务
- 工具调用失败时，最多重试 1 次，然后报告失败原因

### 3. 输出质量门
- 每个阶段完成后，自检：
  ✅ 所有断言有来源
  ✅ 所有推导有步骤
  ✅ 所有数值有单位
  ✅ 所有缩写已展开
  未通过 → 修正后再输出

### 4. 不确定性处理
- 遇到不确定信息时，使用以下等级：
  [certain]: 多源验证，置信度 High
  [likely]: 单一可靠来源，置信度 Medium
  [possible]: 仅有推断或弱证据，置信度 Low
  [speculative]: 纯推测，必须标注
```

- [ ] **Step 1: 为所有 agent_*.md 注入统一的角色定义增强模板**
- [ ] **Step 2: 验证**
- [ ] **Step 3: 提交**

---

## 二、工具层扩展：新增 SourceTracker 和 EvidenceMap

### Task 2.1: 创建 SourceTracker 工具

**Files:**
- Create: `backend/src/ultramath/tools/source_tracker.py`

**设计:** 受 `citation-discipline` 的"无来源不陈述"规则驱动，Agent 需要一个工具来注册、查询和验证来源。

```python
"""来源追踪工具 — 实现 citation-discipline 的来源绑定"""
from __future__ import annotations
from .base import Tool, ToolResult
import json
from pathlib import Path


class SourceTrackerTool(Tool):
    """管理研究来源，强制执行引用纪律"""

    name = "source_tracker"
    description = "注册、查询和验证研究来源。每个事实性断言必须绑定一个已注册的来源。"
    category = "research"

    def __init__(self, work_dir: str = "."):
        self.sources_file = Path(work_dir) / ".lemma" / "sources.json"
        self.sources_file.parent.mkdir(parents=True, exist_ok=True)

    def _load(self) -> dict:
        if self.sources_file.exists():
            return json.loads(self.sources_file.read_text(encoding="utf-8"))
        return {"sources": {}, "claims": []}

    def _save(self, data: dict):
        self.sources_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    async def execute(
        self,
        action: str = "register",
        source_id: str = "",
        source_type: str = "",
        url: str = "",
        description: str = "",
        claim: str = "",
    ) -> ToolResult:
        data = self._load()

        if action == "register":
            # 注册来源：一手/二手/三手
            if not source_id:
                return ToolResult.fail("注册来源必须提供 source_id")
            data["sources"][source_id] = {
                "type": source_type or "unknown",
                "url": url,
                "description": description,
                "quality": {
                    "primary": "一手" if source_type == "primary" else "二手" if source_type == "secondary" else "三手",
                    "independent": url != "" and "arxiv" not in url.lower(),
                },
            }
            self._save(data)
            return ToolResult.ok(f"来源已注册: {source_id} ({source_type})")

        elif action == "bind":
            # 绑定断言到来源
            if not claim or not source_id:
                return ToolResult.fail("bind 需要 claim 和 source_id")
            if source_id not in data["sources"]:
                return ToolResult.fail(f"来源 {source_id} 未注册，请先 register")
            data["claims"].append({
                "claim": claim[:500],
                "source_id": source_id,
                "label": "fact" if data["sources"][source_id]["quality"]["independent"] else "inference",
            })
            self._save(data)
            return ToolResult.ok(f"断言已绑定来源 {source_id}")

        elif action == "audit":
            # 审计所有断言的来源质量
            total = len(data["claims"])
            facts = sum(1 for c in data["claims"] if c["label"] == "fact")
            inferences = total - facts
            orphans = [c for c in data["claims"] if c["source_id"] not in data["sources"]]
            return ToolResult.ok(
                f"来源审计: {total} 断言 ({facts} fact, {inferences} inference), {len(orphans)} 孤立断言"
            )

        elif action == "list":
            return ToolResult.ok(json.dumps(data, ensure_ascii=False, indent=2))

        return ToolResult.fail(f"未知 action: {action}")

    def _get_parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["register", "bind", "audit", "list"]},
                "source_id": {"type": "string", "description": "来源唯一标识"},
                "source_type": {"type": "string", "enum": ["primary", "secondary", "tertiary"]},
                "url": {"type": "string", "description": "可独立验证的 URL 或文件路径"},
                "description": {"type": "string", "description": "来源描述"},
                "claim": {"type": "string", "description": "要绑定的事实性断言"},
            },
            "required": ["action"],
        }
```

- [ ] **Step 1: 创建 source_tracker.py**
- [ ] **Step 2: 注册到 lead 和 reviewer 角色的 tools 列表**
- [ ] **Step 3: 添加测试**
- [ ] **Step 4: 提交**

---

### Task 2.2: 创建 EvidenceMap 工具

**Files:**
- Create: `backend/src/ultramath/tools/evidence_map.py`

**设计:** 受 `research` 技能的分解树方法驱动。维护一个 JSON 格式的证据地图，追踪每个子问题 → 来源 → 置信度。

```python
"""证据地图工具 — 实现递归分解树的记录与查询"""
from .base import Tool, ToolResult
import json
from pathlib import Path
from datetime import datetime


class EvidenceMapTool(Tool):
    """维护研究问题的分解树和证据链"""

    name = "evidence_map"
    description = "添加、查询研究分解树节点，维护证据链。支持递归分解和置信度追踪。"
    category = "research"

    def __init__(self, work_dir: str = "."):
        self.map_file = Path(work_dir) / ".lemma" / "evidence_map.json"

    def _load(self) -> dict:
        if self.map_file.exists():
            return json.loads(self.map_file.read_text(encoding="utf-8"))
        return {"root_id": None, "nodes": {}, "created_at": datetime.now().isoformat()}

    def _save(self, data: dict):
        self.map_file.parent.mkdir(parents=True, exist_ok=True)
        self.map_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    async def execute(
        self,
        action: str = "add_node",
        node_id: str = "",
        parent_id: str = "",
        question: str = "",
        answer: str = "",
        confidence: str = "medium",
        sources: list[str] | None = None,
        is_atomic: bool = False,
    ) -> ToolResult:
        data = self._load()

        if action == "add_node":
            if not node_id:
                return ToolResult.fail("必须提供 node_id")
            if data["root_id"] is None:
                data["root_id"] = node_id
            data["nodes"][node_id] = {
                "parent": parent_id or None,
                "question": question,
                "answer": answer,
                "confidence": confidence,
                "sources": sources or [],
                "is_atomic": is_atomic,
                "children": [],
                "label": "fact" if confidence in ("high", "medium") and len(sources or []) >= 2 else "inference",
                "updated_at": datetime.now().isoformat(),
            }
            if parent_id and parent_id in data["nodes"]:
                if node_id not in data["nodes"][parent_id]["children"]:
                    data["nodes"][parent_id]["children"].append(node_id)
            self._save(data)
            return ToolResult.ok(f"节点 {node_id} {'叶子' if is_atomic else '非叶子'} 已添加")

        elif action == "get_tree":
            if node_id and node_id in data["nodes"]:
                subtree = self._extract_subtree(data, node_id)
                return ToolResult.ok(json.dumps(subtree, ensure_ascii=False, indent=2))
            return ToolResult.ok(json.dumps(data, ensure_ascii=False, indent=2))

        elif action == "audit":
            # 审计：检查置信度与来源数的匹配
            violations = []
            for nid, node in data["nodes"].items():
                conf = node["confidence"]
                src_count = len(node.get("sources", []))
                if conf == "high" and src_count < 2:
                    violations.append(f"{nid}: High 置信度但只有 {src_count} 个来源（需 ≥2）")
                if conf == "medium" and src_count < 1:
                    violations.append(f"{nid}: Medium 置信度但无来源")
            if violations:
                return ToolResult.fail("\n".join(violations))
            return ToolResult.ok("审计通过：所有置信度与证据量匹配")

        elif action == "stats":
            total = len(data["nodes"])
            atomic = sum(1 for n in data["nodes"].values() if n.get("is_atomic"))
            high = sum(1 for n in data["nodes"].values() if n["confidence"] == "high")
            facts = sum(1 for n in data["nodes"].values() if n.get("label") == "fact")
            return ToolResult.ok(
                f"证据地图统计: {total} 节点, {atomic} 原子, "
                f"High 置信度 {high} 个, {facts} 个 fact 标签"
            )

        return ToolResult.fail(f"未知 action: {action}")

    def _extract_subtree(self, data: dict, node_id: str) -> dict:
        node = data["nodes"].get(node_id, {})
        result = dict(node)
        result["children_detail"] = [
            self._extract_subtree(data, child_id) for child_id in node.get("children", [])
        ]
        return result

    def _get_parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["add_node", "get_tree", "audit", "stats"]},
                "node_id": {"type": "string", "description": "节点唯一标识"},
                "parent_id": {"type": "string", "description": "父节点 ID"},
                "question": {"type": "string", "description": "该节点研究的问题"},
                "answer": {"type": "string", "description": "对问题的基于证据的回答"},
                "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
                "sources": {"type": "array", "items": {"type": "string"}},
                "is_atomic": {"type": "boolean"},
            },
            "required": ["action"],
        }
```

- [ ] **Step 1: 创建 evidence_map.py**
- [ ] **Step 2: 注册到所有领域 lead 角色**
- [ ] **Step 3: 添加测试**
- [ ] **Step 4: 提交**

---

## 三、工作流升级：线性流水线 → 递归分解

### Task 3.1: AcademicAgent.run_auto 支持递归分解

**Files:**
- Modify: `backend/src/ultramath/engine/agent.py`

**当前行为:** `run_auto` 按 domain.yaml 中 phases 定义的线性顺序逐个执行。

**目标行为:** 每个阶段内部允许 Agent 发起递归分解请求。如果 Agent 认为当前问题需要拆分为子问题，可以 yield 一个 `decompose` 事件。

```python
# 在 run_auto 的 _execute_phase 后添加递归处理
async def run_auto(self, input_text: str = "") -> AsyncGenerator[dict, None]:
    self.reset_cancel()
    yield {"type": "start", "message": f"🚀 {self.domain.name} 开始执行", "domain": self.domain.id}

    # 支持递归分解：用栈管理待处理的问题
    problem_stack: list[tuple[str, str, int]] = [(self.domain.get_phase_ids()[1], input_text, 0)]
    max_depth = 5

    while problem_stack:
        if self._cancel_event.is_set():
            yield {"type": "cancelled", "message": "用户取消了自动运行"}
            return

        phase_id, problem_text, depth = problem_stack.pop(0)

        if depth >= max_depth:
            yield {"type": "phase_skip", "phase": phase_id, "reason": f"超过最大递归深度 {max_depth}"}
            continue

        phase_cfg = self.domain.get_phase_by_id(phase_id)
        if not phase_cfg:
            continue

        yield {"type": "phase_start", "phase": phase_id, "name": phase_cfg.name, "depth": depth}

        try:
            result = await self._execute_phase_with_decompose(phase_id, problem_text)

            if result.get("decompose"):
                # Agent 要求分解
                sub_problems = result["decompose"]
                for sub in reversed(sub_problems):
                    problem_stack.insert(0, (sub["phase"], sub["question"], depth + 1))
                yield {"type": "decomposed", "phase": phase_id, "sub_problems": len(sub_problems)}
            else:
                # 正常完成
                self.state.transition(PhaseResult(
                    phase_id=phase_id, success=result.get("success", True),
                    summary=result.get("summary", "")[:500],
                ))
                yield {
                    "type": "phase_end", "phase": phase_id, "name": phase_cfg.name,
                    "success": result.get("success", True),
                    "summary": result.get("summary", "")[:500],
                }
        except Exception as e:
            yield {"type": "phase_error", "phase": phase_id, "error": str(e)}

    # 到达 done 阶段
    self.state.transition_to("done")
    yield {"type": "complete", "message": "✅ 所有问题已求解", "progress": 100}
```

- [ ] **Step 1: 修改 agent.py 的 run_auto 支持递归分解**
- [ ] **Step 2: 在 phase_handler 模板中添加"是否需要分解"的判断逻辑**
- [ ] **Step 3: 添加集成测试**
- [ ] **Step 4: 提交**

---

### Task 3.2: 移植 luwill/research-skills 的 5-Agent 综述系统到 literature-review 领域

**参考:** [luwill/research-skills](https://github.com/luwill/research-skills)

**Files:**
- Modify: `domains/literature-review/domain.yaml`
- Modify: `domains/literature-review/prompts/agent_*.md`

**当前 literature-review 角色:** lead + researcher + synthesizer（3 角色）

**目标: 升级为 5 角色** — 完全对齐 luwill 的 multi-agent survey 设计：

| 角色 | luwill 对应 | 当前 Lemma | 操作 |
|------|------------|-----------------|------|
| Survey Director | `survey-director` | lead | 注入 survey-director 的 prompt |
| Literature Scout | `literature-scout` | researcher | 注入 literature-scout 的 prompt |
| Paper Analyst | `paper-analyst` | **新增** | 创建 agent_analyst.md |
| Survey Writer | `survey-writer` | synthesizer | 重构为 survey-writer |
| Quality Editor | `quality-editor` | **新增** | 创建 agent_editor.md |

- [ ] **Step 1: 修改 literature-review/domain.yaml，新增 roles analyst 和 editor**
- [ ] **Step 2: 创建 agent_analyst.md 和 agent_editor.md**
- [ ] **Step 3: 更新 phase_handlers 对齐 5 角色分工**
- [ ] **Step 4: 添加 E2E 测试**
- [ ] **Step 5: 提交**

---

## 四、预期收益

| 改进项 | 当前状态 | 集成后 | 提升 |
|--------|----------|--------|------|
| **断言可追溯性** | 无来源追踪 | 每个断言绑定 SourceTracker | 从 0 到 1 |
| **审查结构化** | 主观评分卡 | PASS/FAIL × 3 维度 + 具体违规 | 可量化 |
| **问题分解** | 线性 8 阶段 | 递归分解 + evidence_map | 复杂问题处理能力 ↑ |
| **推测控制** | 无区分 | [fact] vs [inference] 标签 | 可信度透明 |
| **文献综述 Agent** | 3 角色 | 5 角色（对齐 luwill） | 分工更专业 |
| **角色定义质量** | 自写 prompt | 参照 v0/Cursor/Manus 真实 prompt | Role-playing 更稳定 |

---

## 执行路线

```
Task 1.1-1.4 (Prompt 注入, 1-2天)    Task 2.1-2.2 (工具创建, 1-2天)
└─ 审稿人/作家/指挥 prompt 增强        └─ SourceTracker + EvidenceMap

Task 3.1-3.2 (工作流升级, 2-3天)
└─ 递归分解 + 5-Agent 综述
```

**预估总工期：4-7 天**

---

> **优先级建议：** Task 1.1（审稿人注入 peer-reviewer）影响最大、改动最小，建议第一个实施。Task 1.2（citation-discipline）和 Task 2.1（SourceTracker）配合使用效果最好，建议一起做。
