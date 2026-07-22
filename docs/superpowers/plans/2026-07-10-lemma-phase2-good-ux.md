# Lemma Phase 2 好用 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Lemma pleasant for daily use — long conversations stay smooth, math formulas render correctly, sidebar is flexible, and users can manage their sessions and export work.

**Architecture:** Incremental improvements on the existing stack. New dependency: `react-virtuoso` for message virtualization, `remark-math` + `rehype-katex` for LaTeX rendering.

**Tech Stack:** React 18, TypeScript, Tailwind CSS 3, Electron 39, react-virtuoso (new), remark-math (new), rehype-katex (new)

## Global Constraints

- TypeScript strict mode ON — no `any` types
- Functions ≤ 30 lines
- Commit format: Conventional Commits
- Run `npm run typecheck` after every task
- Run `cd frontend && npx vitest run` after tasks touching hooks/components
- All user-facing text in Chinese (zh-CN)

---

### Task 1: Install New Dependencies + Message Virtualization

**Files:**
- Modify: `package.json` (add react-virtuoso)
- Modify: `frontend/src/components/ChatPanel.tsx` (replace map with Virtuoso)

**Goal:** Replace the unbounded `messages.map()` rendering with `react-virtuoso`'s `Virtuoso` component so long conversations (100+ messages) don't cause scroll jank.

- [ ] **Step 1: Install react-virtuoso**

```bash
npm install react-virtuoso
```

- [ ] **Step 2: Add to vite.config.ts manualChunks**

```typescript
// In frontend/vite.config.ts manualChunks, add:
'virtuoso-vendor': ['react-virtuoso'],
```

- [ ] **Step 3: Replace messages.map with Virtuoso in ChatPanel.tsx**

Import:
```typescript
import { Virtuoso } from 'react-virtuoso';
```

Replace the message list rendering. The current structure:
```tsx
<div className="flex-1 overflow-y-auto px-4 py-6 space-y-4">
  {messages.length === 0 && <EmptyState />}
  {messages.map((message, index) => <MessageBubble ... />)}
  {/* typing indicator */}
  <div ref={messagesEndRef} />
</div>
```

Becomes:
```tsx
{messages.length === 0 ? (
  <div className="flex-1 flex items-center justify-center">
    <EmptyState />
  </div>
) : (
  <Virtuoso
    className="flex-1"
    data={messages}
    followOutput="smooth"
    itemContent={(index, message) => (
      <div className="px-4 py-2">
        <MessageBubble
          message={message}
          isExpanded={expandedTools.has(index)}
          onToggleExpand={() => toggleToolExpand(index)}
          onRetry={onRetry}
        />
      </div>
    )}
    components={{
      Footer: () => (
        <div className="px-4 py-2">
          {isStreaming && messages.length > 0 && messages[messages.length - 1]?.metadata?.role === 'user' && (
            <div className="max-w-4xl mx-auto">
              <div className="rounded-lg px-4 py-3 bg-bg-tertiary inline-block">
                <div className="typing-indicator flex items-center gap-1">
                  <span /><span /><span />
                </div>
              </div>
            </div>
          )}
        </div>
      ),
    }}
  />
)}
```

Remove `messagesEndRef` since Virtuoso handles auto-scroll via `followOutput`.

- [ ] **Step 4: Verify and commit**

```bash
npm run typecheck && cd frontend && npx vite build
git add -A
git commit -m "feat: add message virtualization with react-virtuoso for smooth long conversations"
```

---

### Task 2: LaTeX Formula Rendering

**Files:**
- Modify: `package.json` (add remark-math, rehype-katex)
- Modify: `frontend/index.html` (add KaTeX CSS)
- Modify: `frontend/src/components/ChatPanel.tsx` (add remarkPlugins/rehypePlugins)

**Goal:** Render `$inline$` and `$$block$$` LaTeX math in chat messages. Essential for an academic writing app.

- [ ] **Step 1: Install dependencies**

```bash
npm install remark-math rehype-katex
```

- [ ] **Step 2: Add KaTeX CSS to index.html**

In `frontend/index.html`, add to `<head>`:
```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css" />
```

- [ ] **Step 3: Add plugins to ReactMarkdown in ChatPanel.tsx**

```typescript
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
```

In the `<ReactMarkdown>` component inside MessageBubble:
```tsx
<ReactMarkdown
  remarkPlugins={[remarkMath]}
  rehypePlugins={[rehypeKatex]}
  components={{ /* existing code component */ }}
>
  {message.content}
</ReactMarkdown>
```

- [ ] **Step 4: Verify and commit**

```bash
npm run typecheck && cd frontend && npx vite build
git add -A
git commit -m "feat: add LaTeX math rendering with remark-math and rehype-katex"
```

---

### Task 3: Collapsible Sidebar

**Files:**
- Modify: `frontend/src/components/Sidebar.tsx`
- Modify: `frontend/src/components/App.tsx` (add toggle button or pass dispatch)

**Goal:** Allow users to collapse the 220px sidebar to a slim icon-only rail, using the existing `sidebarCollapsed` state from AppContext.

- [ ] **Step 1: Update Sidebar to support collapsed state**

In `frontend/src/components/Sidebar.tsx`:

Read `state.sidebarCollapsed` from `useApp()`. When collapsed:
- Width becomes `w-12` instead of `w-[220px]`
- Show only icons (Plus, folder icon) — hide text labels
- Add a toggle button at the top

```tsx
const { state, dispatch } = useApp();
const isCollapsed = state.sidebarCollapsed;

return (
  <aside
    className={`flex flex-col ${isCollapsed ? 'w-12' : 'w-[220px]'} bg-bg-elevated border-r border-border shrink-0 transition-all duration-200`}
    role="navigation"
    aria-label="会话列表"
  >
    {/* Toggle button */}
    <button
      onClick={() => dispatch({ type: 'TOGGLE_SIDEBAR' })}
      className="flex items-center justify-center p-2 hover:bg-bg-tertiary transition-colors"
      title={isCollapsed ? '展开侧栏' : '收起侧栏'}
    >
      {isCollapsed ? <PanelRightOpen size={16} /> : <PanelRightClose size={16} />}
    </button>

    {/* Rest of sidebar — conditionally show/hide text based on isCollapsed */}
    {!isCollapsed && (
      <>
        {/* New session button, presets, sessions, work dir — existing code */}
      </>
    )}
    {isCollapsed && (
      <div className="flex flex-col items-center gap-2 py-2">
        <button onClick={handleNewSession} className="p-2 rounded hover:bg-bg-tertiary" title="新建会话">
          <Plus size={16} />
        </button>
      </div>
    )}
  </aside>
);
```

Import `PanelRightOpen` and `PanelRightClose` from lucide-react.

- [ ] **Step 2: Verify and commit**

```bash
npm run typecheck
git add -A
git commit -m "feat: add collapsible sidebar with icon-only rail"
```

---

### Task 4: PDF Export

**Files:**
- Modify: `frontend/src/App.tsx` (add PDF export handler to export view)

**Goal:** Add a "导出为 PDF" button alongside the existing Markdown export. The `export-pdf` IPC handler already exists in Electron main process.

- [ ] **Step 1: Add PDF export function in App.tsx**

```typescript
const handleExportPdf = useCallback(async () => {
  const content = exportMessages(claude.messages, {
    format: 'markdown',
    includeTimestamps: true,
    includeMetadata: false,
  });
  // Convert markdown to basic HTML for PDF
  const html = `
    <!DOCTYPE html>
    <html><head><meta charset="utf-8"><style>
      body { font-family: serif; max-width: 800px; margin: 40px auto; padding: 20px; }
      h1 { font-size: 24px; } h3 { font-size: 18px; color: #333; }
      pre { background: #f5f5f5; padding: 12px; overflow-x: auto; }
      code { font-family: monospace; font-size: 13px; }
    </style></head><body>
    <h1>Lemma 对话导出</h1>
    ${claude.messages.map((message) => {
      const isUser = message.metadata?.role === 'user';
      return `<h3>${isUser ? '用户' : 'Claude'}</h3><div>${message.content}</div>`;
    }).join('\n')}
    </body></html>`;

  await window.lemmaAPI?.exportPdf(html);
}, [claude.messages]);
```

- [ ] **Step 2: Add PDF export button to export view**

In the export view JSX in App.tsx, add a third button:

```tsx
<button
  onClick={handleExportPdf}
  disabled={claude.messages.length === 0}
  className="px-5 py-2.5 rounded-editorial border border-border-strong hover:bg-bg-tertiary disabled:opacity-50 text-ui font-medium press-scale"
>
  导出为 PDF
</button>
```

- [ ] **Step 3: Verify and commit**

```bash
npm run typecheck
git add -A
git commit -m "feat: add PDF export alongside Markdown export"
```

---

### Task 5: Session Rename and Delete

**Files:**
- Modify: `frontend/src/components/Sidebar.tsx`

**Goal:** Add right-click or hover-revealed actions to rename and delete sessions.

- [ ] **Step 1: Add delete button to session items**

In the session list rendering in Sidebar.tsx, add a delete button that appears on hover:

```tsx
{filteredSessions.map((session) => (
  <div key={session.id} className="group flex items-center">
    <button
      onClick={() => handleSelectSession(session.id)}
      className={`flex items-center gap-2 flex-1 px-3 py-1.5 rounded-editorial text-ui transition-colors ${
        state.currentSessionId === session.id
          ? 'bg-bg-tertiary text-text font-medium border-l-2 border-accent'
          : 'text-text-muted hover:bg-bg-tertiary border-l-2 border-transparent'
      }`}
    >
      <Clock size={11} className="shrink-0" />
      <span className="truncate">{session.title}</span>
    </button>
    <button
      onClick={async () => {
        await window.lemmaAPI?.deleteSession(session.id);
        loadSessions();
      }}
      className="p-1 rounded opacity-0 group-hover:opacity-100 hover:bg-bg-tertiary text-text-muted hover:text-error transition-all"
      title="删除会话"
    >
      <Trash2 size={11} />
    </button>
  </div>
))}
```

Import `Trash2` from lucide-react (already imported in Sidebar).

Add `loadSessions` function reference (it should already be available from App.tsx via props or context).

- [ ] **Step 2: Verify and commit**

```bash
npm run typecheck
git add -A
git commit -m "feat: add session delete with hover-revealed action button"
```

---

### Task 6: Code Block Language Label + Enhanced Display

**Files:**
- Modify: `frontend/src/components/ChatPanel.tsx` (CodeBlock component)

**Goal:** Show the language name as a label on code blocks and improve the copy button positioning.

- [ ] **Step 1: Update CodeBlock component**

```typescript
function CodeBlock({ language, code }: { language: string; code: string }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      setTimeout(() => setCopied(false), TIMING.COPY_FEEDBACK_DURATION);
    } catch {
      // Clipboard may fail
    }
  };

  return (
    <div className="code-block-wrapper relative">
      <div className="flex items-center justify-between px-3 py-1 bg-bg-elevated border-b border-border rounded-t text-xs">
        <span className="text-text-muted font-mono">{language}</span>
        <button
          onClick={handleCopy}
          className="flex items-center gap-1 px-2 py-0.5 rounded hover:bg-bg-tertiary text-text-muted hover:text-text-secondary transition-colors"
          title="复制代码"
        >
          {copied ? <Check size={12} className="text-success" /> : <Copy size={12} />}
          <span>{copied ? '已复制' : '复制'}</span>
        </button>
      </div>
      <SyntaxHighlighter style={oneDark} language={language} PreTag="div" customStyle={{ margin: 0, borderRadius: '0 0 4px 4px' }}>
        {code}
      </SyntaxHighlighter>
    </div>
  );
}
```

- [ ] **Step 2: Verify and commit**

```bash
npm run typecheck
git add -A
git commit -m "feat: add language label and improved copy button to code blocks"
```

---

### Task 7: Markdown Table Enhancement

**Files:**
- Modify: `frontend/src/index.css` (enhanced table styles)

**Goal:** Improve table rendering in Markdown to be more readable with alternating row colors and better spacing.

- [ ] **Step 1: Enhance table styles in index.css**

Add/update in the `.markdown-body` section of `index.css`:

```css
.markdown-body table {
  border-collapse: collapse;
  margin: 0.75rem 0;
  width: 100%;
  font-size: 14px;
}
.markdown-body th {
  background: var(--color-bg-tertiary);
  font-weight: 600;
  font-family: system-ui, sans-serif;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  font-size: 11px;
  padding: 0.5rem 0.75rem;
  border: 1px solid var(--color-border);
  text-align: left;
}
.markdown-body td {
  padding: 0.5rem 0.75rem;
  border: 1px solid var(--color-border);
}
.markdown-body tr:nth-child(even) td {
  background: var(--color-bg-secondary);
}
```

- [ ] **Step 2: Verify and commit**

```bash
npm run typecheck && cd frontend && npx vite build
git add -A
git commit -m "feat: enhance markdown table rendering with alternating rows"
```

---

### Task 8: Final Phase 2 Verification

**Files:**
- No code changes — verification only

- [ ] **Step 1: Full test suite**

```bash
cd frontend && npx vitest run
```
Expected: All tests pass.

- [ ] **Step 2: Typecheck**

```bash
npm run typecheck
```
Expected: No errors.

- [ ] **Step 3: Production build**

```bash
cd frontend && npx vite build
```
Expected: Build succeeds. Check for virtuoso-vendor chunk.

- [ ] **Step 4: Commit verification**

```bash
echo "Phase 2 complete" >> .superpowers/sdd/progress.md
git add -A
git commit -m "chore: phase 2 verification complete — all systems green"
```

---

## Task Dependency Graph

```
Task 1 (virtuoso) ── independent
Task 2 (LaTeX) ── independent
Task 3 (sidebar) ── independent
Task 4 (PDF export) ── independent
Task 5 (session delete) ── independent
Task 6 (code block) ── independent
Task 7 (table CSS) ── independent
Task 8 (verify) ← after ALL

Recommended order: 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8
```

## Estimated Effort

| Task | Est. Time | Complexity |
|------|-----------|------------|
| Task 1: Virtuoso | 20 min | Medium |
| Task 2: LaTeX | 10 min | Low |
| Task 3: Sidebar | 20 min | Medium |
| Task 4: PDF Export | 10 min | Low |
| Task 5: Session Delete | 15 min | Low |
| Task 6: Code Block | 10 min | Low |
| Task 7: Table CSS | 5 min | Low |
| Task 8: Verify | 10 min | Low |
| **Total** | **~1.5 hours** | |
