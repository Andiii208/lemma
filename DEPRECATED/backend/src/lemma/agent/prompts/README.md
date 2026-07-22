# Agent 定义说明

## 目录结构

| 目录 | 用途 | 谁调用 |
|------|------|--------|
| `agents/` | **唯一真相源** — 所有 agent prompt 的权威定义 | sync.sh 同步到各工作区 |
| `.claude/agents/` | CC 加载位置 — 从 agents/ 单向同步 | CC 原生子 Agent（`@agent_xxx`） |

## 同步规则

- `agents/` 是唯一真相源，修改 agent prompt 只改 `agents/`
- `.claude/agents/` 由 `bash scripts/sync.sh sync` 自动同步，**不要手动编辑**
- 工作区子目录（2025A/2025B题/2025C 等）的 `.claude/agents/` 也由 sync.sh 同步

## 当前 Agent 列表（V10.0）

| Agent | 文件 | 角色 |
|-------|------|------|
| Team Lead | agent_lead.md | 团队指挥，编排全部 Phase |
| Agent M | agent_数学家.md | 双队伍数学家（Phase 1 推导） |
| Agent R | agent_审稿人.md | 审稿人（Phase 1 辩论 + Phase 4 P2P 审稿） |
| Agent E | agent_工程师.md | 工程师（Phase 2 代码实现） |
| Agent W | agent_作家.md | 作家（Phase 3 论文写作） |
| Verifier | agent_verifier.md | 第三方验算员（Phase 1 验算） |
| OntologyBuilder | agent_ontology_builder.md | 自适应本体构造（Phase 1.5） |
| Manager 精确 | agent_manager_exact.md | 精确方法组 Manager（Phase 2） |
| Manager 启发式 | agent_manager_heuristic.md | 启发式方法组 Manager（Phase 2） |
| Manager 不确定性 | agent_manager_uncertainty.md | 不确定性方法组 Manager（Phase 2） |
| Tester | agent_tester.md | 机械测试者（Phase 2.5） |
| E-Debug | agent_e_debug.md | 代码调试子代理（Agent E 内部 spawn） |
| M-Branch | agent_m_branch.md | 推导分支探索子代理（Agent M 内部 spawn） |
| R-Trace | agent_r_trace.md | 交叉验证深度追踪子代理（Agent R 内部 spawn） |
