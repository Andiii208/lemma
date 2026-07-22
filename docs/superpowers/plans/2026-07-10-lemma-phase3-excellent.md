# Lemma Phase 3 优秀 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Lemma a smarter academic tool — intelligent model routing, workflow visualization, richer system prompts, context awareness, and extensibility.

**Architecture:** Frontend-focused improvements + Electron main process enhancements. No Python backend rewrite (that's a future Phase 4). All changes within the existing TypeScript/React stack.

**Tech Stack:** React 18, TypeScript, Tailwind CSS 3, Electron 39

## Global Constraints

- TypeScript strict mode ON — no `any` types
- Functions ≤ 30 lines
- Commit format: Conventional Commits
- Run `npm run typecheck` after every task
- Run `cd frontend && npx vitest run` after tasks touching hooks/components
- All user-facing text in Chinese (zh-CN)

---

### Task 1: Smart Model Routing

**Files:**
- Modify: `frontend/src/config.ts` (add model tier info)
- Modify: `frontend/src/context/AppContext.tsx` (add auto-routing state)
- Modify: `frontend/src/components/settings/ModelSection.tsx` (add auto mode)
- Modify: `frontend/src/App.tsx` (pass model to chat with auto-selection logic)

**Goal:** Add an "自动" (Auto) model mode that uses Haiku for short queries and Sonnet for complex ones. User can still manually select a specific model.

- [ ] **Step 1: Add model tier info to config.ts**

```typescript
export const AVAILABLE_MODELS = [
  { id: 'claude-sonnet-4-20250514', name: 'Claude Sonnet 4', tier: 'standard' },
  { id: 'claude-opus-4-20250514', name: 'Claude Opus 4', tier: 'premium' },
  { id: 'claude-haiku-4-20250514', name: 'Claude Haiku 4', tier: 'fast' },
] as const;

export const AUTO_MODEL = 'auto' as const;

/** Estimate query complexity based on message length */
export function selectAutoModel(messageLength: number): string {
  if (messageLength < 100) return 'claude-haiku-4-20250514';
  return 'claude-sonnet-4-20250514';
}
```

- [ ] **Step 2: Add auto mode to AppContext**

Add `'auto'` as a valid value for `selectedModel`. Update the initial state default to `'auto'`.

- [ ] **Step 3: Update ModelSection to show Auto option**

Add an "自动选择" option at the top of the model dropdown:

```tsx
<option value="auto">🤖 自动选择 (推荐)</option>
{AVAILABLE_MODELS.map((model) => (
  <option key={model.id} value={model.id}>
    {model.name}
  </option>
))}
```

- [ ] **Step 4: Wire auto-routing in App.tsx handleSend**

```typescript
const effectiveModel = state.selectedModel === 'auto'
  ? selectAutoModel(text.length)
  : state.selectedModel;
options.model = effectiveModel;
```

- [ ] **Step 5: Verify and commit**

```bash
npm run typecheck
git add -A
git commit -m "feat: add smart model routing with auto-selection based on query complexity"
```

---

### Task 2: PipelineProgress Integration

**Files:**
- Modify: `frontend/src/App.tsx` (wire PipelineProgress to chat view)
- Modify: `frontend/src/components/ChatPanel.tsx` (detect pipeline stages from messages)

**Goal:** Show the PipelineProgress component when a multi-stage workflow is active. Detect stages from system prompt or preset configuration.

- [ ] **Step 1: Add pipeline state to AppContext**

Add to AppState:
```typescript
pipelineStages: PipelineStage[] | null;
currentStage: string | null;
```

Add actions:
```typescript
| { type: 'SET_PIPELINE'; payload: { stages: PipelineStage[]; currentStage: string } }
| { type: 'ADVANCE_PIPELINE'; payload: string }
| { type: 'CLEAR_PIPELINE' }
```

Import `PipelineStage` type from PipelineProgress.tsx (export it).

- [ ] **Step 2: Show PipelineProgress in chat view when active**

In App.tsx, when `state.pipelineStages` is not null, render PipelineProgress above the ChatPanel:

```tsx
{state.currentView === 'chat' && state.pipelineStages && (
  <PipelineProgress
    stages={state.pipelineStages}
    currentStage={state.currentStage ?? undefined}
  />
)}
```

- [ ] **Step 3: Auto-initialize pipeline for math-modeling preset**

When the user selects the math-modeling preset, initialize the pipeline stages:

```typescript
const MATH_MODELING_STAGES: PipelineStage[] = [
  { id: 'analyze', name: '分析', status: 'pending' },
  { id: 'derive', name: '推导', status: 'pending' },
  { id: 'code', name: '编码', status: 'pending' },
  { id: 'test', name: '测试', status: 'pending' },
  { id: 'write', name: '写作', status: 'pending' },
  { id: 'review', name: '审稿', status: 'pending' },
];
```

In the preset selection handler, set pipeline when math-modeling is chosen, clear it otherwise.

- [ ] **Step 4: Verify and commit**

```bash
npm run typecheck
git add -A
git commit -m "feat: integrate PipelineProgress for math-modeling workflow visualization"
```

---

### Task 3: Enhanced System Prompts

**Files:**
- Modify: `electron/presets/index.ts` (enrich system prompts with domain knowledge)

**Goal:** Make system prompts significantly richer — include domain-specific knowledge, output format expectations, and quality guidelines.

- [ ] **Step 1: Enrich the math-modeling prompt**

Replace the current basic prompt with a comprehensive one that includes:
- Problem analysis methodology
- Expected output format (structured phases)
- LaTeX output expectations
- Code generation guidelines
- Quality criteria

```typescript
const MATH_MODELING_PROMPT = `你是一位数学建模竞赛专家，具备以下核心能力：

## 方法论
- 优化模型：线性/非线性规划、整数规划、动态规划、多目标优化
- 预测模型：时间序列、回归分析、灰色预测、马尔可夫链
- 评价模型：层次分析法(AHP)、TOPSIS、熵权法、模糊综合评价
- 图论与网络：最短路径、最大流、最小生成树

## 工作流程
请按以下阶段处理每个问题：
1. **问题分析** — 识别关键变量、约束条件、目标函数
2. **模型建立** — 用数学语言描述问题，给出假设条件
3. **模型求解** — 选择算法，给出 Python/MATLAB 代码
4. **结果验证** — 灵敏度分析、误差分析
5. **论文撰写** — LaTeX 格式，含摘要、模型描述、结果讨论

## 输出要求
- 数学公式使用 LaTeX 格式（$行内$ 或 $$块级$$）
- 代码使用 Python，附带注释
- 重要结论加粗标注
- 每个阶段结束时给出阶段小结

## 质量标准
- 数学推导必须严谨，每步有依据
- 代码可运行，有输入输出示例
- 论文结构符合竞赛规范（如全国大学生数学建模竞赛）

请用中文回复，数学符号和代码可使用英文。`;
```

- [ ] **Step 2: Enrich all 5 preset prompts**

Apply similar enrichment to: paper-writing, lab-report, literature-review, data-mining. Each should have:
- Domain expertise listing
- Structured workflow phases
- Output format expectations
- Quality criteria

- [ ] **Step 3: Verify and commit**

```bash
npm run typecheck
git add -A
git commit -m "feat: enrich system prompts with domain knowledge and structured workflows"
```

---

### Task 4: Context Window Awareness

**Files:**
- Create: `frontend/src/components/ContextIndicator.tsx`
- Modify: `frontend/src/components/StatusBar.tsx` (show context usage)
- Modify: `frontend/src/hooks/useClaude.ts` (track token counts)

**Goal:** Show a small indicator of how much of the context window is being used. Helps users understand when to start a new conversation.

- [ ] **Step 1: Create ContextIndicator component**

```typescript
interface ContextIndicatorProps {
  inputTokens: number;
  outputTokens: number;
  maxTokens?: number;
}

const DEFAULT_MAX = 200_000; // Claude's context window

export default function ContextIndicator({ inputTokens, outputTokens, maxTokens = DEFAULT_MAX }: ContextIndicatorProps) {
  const totalTokens = inputTokens + outputTokens;
  const percent = Math.min(100, Math.round((totalTokens / maxTokens) * 100));

  const barColor = percent > 80 ? 'bg-error' : percent > 50 ? 'bg-warning' : 'bg-success';

  const formatCount = (count: number): string => {
    if (count >= 1_000_000) return `${(count / 1_000_000).toFixed(1)}M`;
    if (count >= 1_000) return `${(count / 1_000).toFixed(1)}K`;
    return count.toString();
  };

  return (
    <div className="flex items-center gap-2 text-caption text-text-muted" title={`上下文: ${formatCount(totalTokens)} / ${formatCount(maxTokens)} tokens`}>
      <div className="w-16 h-1.5 rounded-full bg-bg-tertiary overflow-hidden">
        <div className={`h-full rounded-full ${barColor} transition-all duration-300`} style={{ width: `${percent}%` }} />
      </div>
      <span>{percent}%</span>
    </div>
  );
}
```

- [ ] **Step 2: Track token counts in useClaude**

Add `totalInputTokens` and `totalOutputTokens` state to useClaude. Update them from message metadata:

```typescript
const [tokenCounts, setTokenCounts] = useState({ input: 0, output: 0 });

// In the message handler, when metadata contains usage info:
if (message.metadata?.tokens) {
  const usage = message.metadata.tokens as { input_tokens?: number; output_tokens?: number };
  setTokenCounts((prev) => ({
    input: prev.input + (usage.input_tokens || 0),
    output: prev.output + (usage.output_tokens || 0),
  }));
}
```

Expose `tokenCounts` in the return value.

- [ ] **Step 3: Add ContextIndicator to StatusBar**

```tsx
<ContextIndicator
  inputTokens={tokenCounts.input}
  outputTokens={tokenCounts.output}
/>
```

Pass `tokenCounts` from App.tsx to StatusBar via a new prop.

- [ ] **Step 4: Verify and commit**

```bash
npm run typecheck
git add -A
git commit -m "feat: add context window usage indicator in status bar"
```

---

### Task 5: JSON Conversation Export

**Files:**
- Modify: `frontend/src/utils/export.ts` (add JSON format)
- Modify: `frontend/src/App.tsx` (add JSON export button)

**Goal:** Add structured JSON export for programmatic use — includes timestamps, roles, token counts, and message types.

- [ ] **Step 1: Add JSON export to export.ts**

```typescript
export function exportMessagesJson(messages: ClaudeMessage[]): string {
  const exportData = {
    version: '1.0',
    exportedAt: new Date().toISOString(),
    messageCount: messages.length,
    messages: messages.map((message, index) => ({
      index,
      type: message.type,
      role: message.metadata?.role || 'assistant',
      content: message.content,
      timestamp: new Date().toISOString(),
    })),
  };
  return JSON.stringify(exportData, null, 2);
}
```

- [ ] **Step 2: Add JSON export button in App.tsx**

```typescript
const handleExportJson = useCallback(() => {
  const content = exportMessagesJson(claude.messages);
  downloadFile(content, `lemma-export-${Date.now()}.json`, 'application/json');
}, [claude.messages]);
```

Add button in export view.

- [ ] **Step 3: Verify and commit**

```bash
npm run typecheck
git add -A
git commit -m "feat: add JSON conversation export for programmatic use"
```

---

### Task 6: Final Phase 3 Verification

- [ ] **Step 1: Full test suite + typecheck + build**

```bash
npm run typecheck && cd frontend && npx vitest run && npx vite build
```

- [ ] **Step 2: Commit**

```bash
echo "Phase 3 complete" >> .superpowers/sdd/progress.md
git add -A
git commit -m "chore: phase 3 verification complete — all systems green"
```

---

## Task Dependency Graph

```
Task 1 (model routing) ── independent
Task 2 (pipeline) ── independent
Task 3 (prompts) ── independent
Task 4 (context) ── independent
Task 5 (JSON export) ── independent
Task 6 (verify) ← after ALL

Recommended order: 1 → 2 → 3 → 4 → 5 → 6
```

## Estimated Effort

| Task | Est. Time | Complexity |
|------|-----------|------------|
| Task 1: Smart Model Routing | 20 min | Medium |
| Task 2: Pipeline Integration | 20 min | Medium |
| Task 3: Enhanced Prompts | 15 min | Low |
| Task 4: Context Awareness | 20 min | Medium |
| Task 5: JSON Export | 10 min | Low |
| Task 6: Verify | 10 min | Low |
| **Total** | **~1.5 hours** | |
