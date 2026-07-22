# Lemma Phase 0 急救 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix all P0 blocking issues so that Lemma goes from "completely unusable" to "basically usable" — a user can install, configure API key, have a conversation, and not lose messages on close.

**Architecture:** Incremental fixes on the existing Electron + React + Claude Agent SDK stack. No architectural changes. Each task is independently testable and committable.

**Tech Stack:** React 18, TypeScript, Vite 5, Tailwind CSS 3, Electron 39, idb-keyval (new), react-error-boundary (new)

## Global Constraints

- TypeScript strict mode is ON — no `any` types allowed (use `unknown` instead)
- All user-facing text is in Chinese (zh-CN)
- CSS uses CSS custom properties (`--color-*`) for theming — NEVER add light/dark class pairs
- Tailwind classes must ONLY reference tokens defined in `tailwind.config.js`
- Functions must be ≤ 30 lines — extract helpers if longer
- Commit format: Conventional Commits (`fix:`, `feat:`, `refactor:`, `chore:`)
- Run `npm run typecheck` after every task before committing
- Run `cd frontend && npx vite build` after Task 3 and Task 6 to verify no build regressions

---

## File Structure

### New files to create:

| File | Responsibility |
|------|---------------|
| `frontend/src/components/ErrorBoundary.tsx` | React error boundary with fallback UI |
| `frontend/src/hooks/useMessageStore.ts` | IndexedDB persistence layer for messages |
| `frontend/src/hooks/useMessageStore.test.ts` | Tests for persistence layer |

### Files to modify:

| File | Changes |
|------|---------|
| `package.json` | Add `idb-keyval`, `react-error-boundary`; remove `framer-motion` |
| `frontend/vite.config.ts` | Remove dead `manualChunks` entries |
| `frontend/src/main.tsx` | Wrap `<App>` with `<ErrorBoundary>` |
| `frontend/src/App.tsx` | Fix CSS classes, fix useEffect, wire persistence, remove duplicate error UI |
| `frontend/src/hooks/useClaude.ts` | Refactor streaming with useRef + rAF, add persistence calls |
| `frontend/src/components/ChatPanel.tsx` | Fix CSS classes, remove inline error banner, add typing indicator, add copy button |
| `frontend/src/components/Sidebar.tsx` | Fix CSS classes |
| `frontend/src/components/TitleBar.tsx` | Fix CSS classes |
| `frontend/src/components/SettingsPanel.tsx` | Fix CSS classes |
| `frontend/src/components/FileBrowser.tsx` | Fix CSS classes |
| `frontend/src/components/CostTracker.tsx` | Fix CSS classes |
| `frontend/src/components/StatusBar.tsx` | Fix CSS classes, fix undefined token |
| `frontend/src/components/RetryBanner.tsx` | Fix CSS classes |
| `frontend/src/components/OnboardingWizard.tsx` | Fix CSS classes, fix undefined token |
| `frontend/src/components/PipelineProgress.tsx` | Fix CSS classes |
| `frontend/src/components/ClaudeMdEditor.tsx` | Fix CSS classes, fix undefined token |
| `frontend/src/components/PresetSelector.tsx` | Fix CSS classes, fix undefined token |

---

### Task 1: Clean Dead Dependencies

**Files:**
- Modify: `package.json:15-49`
- Modify: `frontend/vite.config.ts:34-45`

**Interfaces:**
- Consumes: nothing
- Produces: clean `package.json` and `vite.config.ts` for all subsequent tasks

- [ ] **Step 1: Remove `framer-motion` from dependencies**

Run:
```bash
npm uninstall framer-motion
```
Expected: `framer-motion` removed from `package.json` and `node_modules`.

- [ ] **Step 2: Remove dead entries from `vite.config.ts` manualChunks**

In `frontend/vite.config.ts`, replace lines 34-45:

```typescript
// BEFORE (lines 34-45):
      output: {
        manualChunks: {
          'react-vendor': ['react', 'react-dom'],
          'motion-vendor': ['framer-motion'],
          'ui-vendor': ['lucide-react', 'react-hot-toast'],
          'markdown-vendor': ['react-markdown', 'react-syntax-highlighter'],
          'virtuoso-vendor': ['react-virtuoso'],
        },
      },

// AFTER:
      output: {
        manualChunks: {
          'react-vendor': ['react', 'react-dom'],
          'ui-vendor': ['lucide-react'],
          'markdown-vendor': ['react-markdown', 'react-syntax-highlighter'],
        },
      },
```

Changes made:
- Removed `'motion-vendor': ['framer-motion']` — framer-motion is not used anywhere
- Removed `'react-hot-toast'` from `'ui-vendor'` — not installed, not used
- Removed `'virtuoso-vendor': ['react-virtuoso']` — not installed, not used

- [ ] **Step 3: Install new dependencies needed for subsequent tasks**

Run:
```bash
npm install idb-keyval react-error-boundary
```
Expected: Both packages added to `dependencies` in `package.json`.

- [ ] **Step 4: Verify build succeeds**

Run:
```bash
npm run typecheck && cd frontend && npx vite build
```
Expected: No errors. Build produces output in `frontend/dist/`.

- [ ] **Step 5: Commit**

```bash
git add package.json package-lock.json frontend/vite.config.ts
git commit -m "chore: clean dead deps, add idb-keyval and react-error-boundary"
```

---

### Task 2: Fix useEffect Missing Dependency Array

**Files:**
- Modify: `frontend/src/components/ChatPanel.tsx:38-42`

**Interfaces:**
- Consumes: nothing
- Produces: fixed event listener lifecycle

- [ ] **Step 1: Add missing dependency array**

In `frontend/src/components/ChatPanel.tsx`, find lines 38-42:

```typescript
// BEFORE (line 38-42):
  useEffect(() => {
    const handler = () => handleSend();
    document.addEventListener('send-message', handler);
    return () => document.removeEventListener('send-message', handler);
  });

// AFTER:
  useEffect(() => {
    const handler = () => handleSend();
    document.addEventListener('send-message', handler);
    return () => document.removeEventListener('send-message', handler);
  }, []);
```

The only change is adding `[]` as the second argument to `useEffect`.

- [ ] **Step 2: Verify typecheck**

Run:
```bash
npm run typecheck
```
Expected: No errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/ChatPanel.tsx
git commit -m "fix: add missing useEffect dependency array in ChatPanel"
```

---

### Task 3: Fix Streaming Performance with useRef + rAF

**Files:**
- Modify: `frontend/src/hooks/useClaude.ts` (full rewrite)

**Interfaces:**
- Consumes: `window.lemmaAPI.onClaudeMessage` (IPC listener)
- Produces: `{ messages, isStreaming, error, sendMessage, cancelStream, clearMessages, clearError }` — same API as before, but messages update via rAF throttling instead of per-token

- [ ] **Step 1: Write the failing test**

Create `frontend/src/hooks/useClaude.test.ts`:

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useClaude } from './useClaude';

// Mock lemmaAPI
const mockOnClaudeMessage = vi.fn(() => vi.fn());
const mockChat = vi.fn(() => Promise.resolve());
const mockCancel = vi.fn(() => Promise.resolve());

vi.stubGlobal('window', {
  lemmaAPI: {
    onClaudeMessage: mockOnClaudeMessage,
    chat: mockChat,
    cancel: mockCancel,
    notify: vi.fn(),
  },
});

describe('useClaude', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should initialize with empty messages', () => {
    const { result } = renderHook(() => useClaude());
    expect(result.current.messages).toEqual([]);
    expect(result.current.isStreaming).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it('should add user message optimistically when sending', async () => {
    const { result } = renderHook(() => useClaude());
    await act(async () => {
      result.current.sendMessage('Hello');
    });
    expect(result.current.messages).toHaveLength(1);
    expect(result.current.messages[0]).toEqual({
      type: 'text',
      content: 'Hello',
      metadata: { role: 'user' },
    });
  });

  it('should set isStreaming to true when sending', async () => {
    const { result } = renderHook(() => useClaude());
    await act(async () => {
      result.current.sendMessage('Hello');
    });
    expect(result.current.isStreaming).toBe(true);
  });

  it('should clear messages and error', () => {
    const { result } = renderHook(() => useClaude());
    act(() => {
      result.current.clearMessages();
    });
    expect(result.current.messages).toEqual([]);
    expect(result.current.error).toBeNull();
  });

  it('should register IPC listener on mount', () => {
    renderHook(() => useClaude());
    expect(mockOnClaudeMessage).toHaveBeenCalledTimes(1);
  });
});
```

- [ ] **Step 2: Run test to verify basic structure**

Run:
```bash
cd frontend && npx vitest run src/hooks/useClaude.test.ts
```
Expected: Some tests may pass (the old implementation partially works), some may fail.

- [ ] **Step 3: Rewrite useClaude.ts with rAF-throttled streaming**

Replace the entire content of `frontend/src/hooks/useClaude.ts`:

```typescript
import { useState, useEffect, useCallback, useRef } from 'react';

export function useClaude() {
  const [messages, setMessages] = useState<ClaudeMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Buffer for incoming messages — flushed to state via rAF
  const messageBufferRef = useRef<ClaudeMessage[]>([]);
  const rafIdRef = useRef<number | null>(null);
  const isStreamingRef = useRef(false);

  // Flush buffered messages to React state (called via rAF)
  const flushMessages = useCallback(() => {
    rafIdRef.current = null;
    if (messageBufferRef.current.length === 0) return;

    const buffered = messageBufferRef.current;
    messageBufferRef.current = [];
    setMessages((prev) => [...prev, ...buffered]);
  }, []);

  // Schedule a flush on next animation frame
  const scheduleFlush = useCallback(() => {
    if (rafIdRef.current !== null) return;
    rafIdRef.current = requestAnimationFrame(flushMessages);
  }, [flushMessages]);

  // Add message to buffer and schedule flush
  const bufferMessage = useCallback((message: ClaudeMessage) => {
    messageBufferRef.current.push(message);
    scheduleFlush();
  }, [scheduleFlush]);

  useEffect(() => {
    if (!window.lemmaAPI) return;

    const unsubscribe = window.lemmaAPI.onClaudeMessage((message) => {
      if (message.type === 'done') {
        // Flush any remaining buffered messages
        if (rafIdRef.current !== null) {
          cancelAnimationFrame(rafIdRef.current);
          rafIdRef.current = null;
        }
        flushMessages();
        setIsStreaming(false);
        isStreamingRef.current = false;
        window.lemmaAPI?.notify('Lemma', 'Claude 已完成回复');
        return;
      }

      if (message.type === 'error' || message.type === 'recoverable_error') {
        // Flush buffer before showing error
        if (rafIdRef.current !== null) {
          cancelAnimationFrame(rafIdRef.current);
          rafIdRef.current = null;
        }
        flushMessages();
        setError(message.content);
        setIsStreaming(false);
        isStreamingRef.current = false;
        return;
      }

      // Buffer the message — will be flushed on next rAF
      bufferMessage(message);
    });

    return () => {
      unsubscribe();
      if (rafIdRef.current !== null) {
        cancelAnimationFrame(rafIdRef.current);
      }
    };
  }, [flushMessages, bufferMessage]);

  const sendMessage = useCallback(async (text: string, options?: ChatOptions) => {
    if (!window.lemmaAPI) {
      setError('Electron IPC 不可用');
      return;
    }

    setIsStreaming(true);
    isStreamingRef.current = true;
    setError(null);

    // Add user message directly to state (not buffered)
    const userMessage: ClaudeMessage = {
      type: 'text',
      content: text,
      metadata: { role: 'user' },
    };
    setMessages((prev) => [...prev, userMessage]);

    try {
      await window.lemmaAPI.chat(text, options);
    } catch (err: unknown) {
      const errorMsg = err instanceof Error ? err.message : '发送失败';
      setError(errorMsg);
      setIsStreaming(false);
      isStreamingRef.current = false;
    }
  }, []);

  const cancelStream = useCallback(async () => {
    if (!window.lemmaAPI) return;
    await window.lemmaAPI.cancel();
    // Flush remaining buffer
    if (rafIdRef.current !== null) {
      cancelAnimationFrame(rafIdRef.current);
      rafIdRef.current = null;
    }
    flushMessages();
    setIsStreaming(false);
    isStreamingRef.current = false;
  }, [flushMessages]);

  const clearMessages = useCallback(() => {
    messageBufferRef.current = [];
    setMessages([]);
    setError(null);
  }, []);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  return {
    messages,
    isStreaming,
    error,
    sendMessage,
    cancelStream,
    clearMessages,
    clearError,
  };
}
```

Key changes from the old implementation:
- Added `messageBufferRef` to accumulate incoming tokens without triggering re-renders
- Added `scheduleFlush()` using `requestAnimationFrame` to batch updates (~16ms intervals)
- User messages are added directly to state (not buffered) for immediate UI feedback
- On `done`/`error`/`cancel`, any remaining buffer is flushed synchronously
- Cleanup in useEffect cancels pending rAF

- [ ] **Step 4: Run tests**

Run:
```bash
cd frontend && npx vitest run src/hooks/useClaude.test.ts
```
Expected: All 5 tests PASS.

- [ ] **Step 5: Run typecheck**

Run:
```bash
npm run typecheck
```
Expected: No errors.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/hooks/useClaude.ts frontend/src/hooks/useClaude.test.ts
git commit -m "fix: throttle streaming updates with useRef + rAF batching"
```

---

### Task 4: Add Error Boundary

**Files:**
- Create: `frontend/src/components/ErrorBoundary.tsx`
- Modify: `frontend/src/main.tsx`

**Interfaces:**
- Consumes: `react-error-boundary` package (installed in Task 1)
- Produces: `<ErrorBoundary>` component that wraps the entire app

- [ ] **Step 1: Write the failing test**

Create `frontend/src/components/ErrorBoundary.test.tsx`:

```typescript
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ErrorBoundary } from './ErrorBoundary';

function BrokenComponent(): React.ReactElement {
  throw new Error('Test crash');
}

describe('ErrorBoundary', () => {
  it('renders children when no error', () => {
    render(
      <ErrorBoundary>
        <div>正常内容</div>
      </ErrorBoundary>
    );
    expect(screen.getByText('正常内容')).toBeTruthy();
  });

  it('renders fallback UI when child throws', () => {
    // Suppress console.error from React error boundary
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

    render(
      <ErrorBoundary>
        <BrokenComponent />
      </ErrorBoundary>
    );

    expect(screen.getByText('出错了')).toBeTruthy();
    expect(screen.getByText(/Test crash/)).toBeTruthy();

    consoleSpy.mockRestore();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run:
```bash
cd frontend && npx vitest run src/components/ErrorBoundary.test.tsx
```
Expected: FAIL — `ErrorBoundary` module not found.

- [ ] **Step 3: Create ErrorBoundary component**

Create `frontend/src/components/ErrorBoundary.tsx`:

```typescript
import { ErrorBoundary as ReactErrorBoundary } from 'react-error-boundary';
import { AlertTriangle, RefreshCw } from 'lucide-react';

interface ErrorFallbackProps {
  error: Error;
  resetErrorBoundary: () => void;
}

function ErrorFallback({ error, resetErrorBoundary }: ErrorFallbackProps) {
  return (
    <div className="flex flex-col items-center justify-center h-screen bg-bg-secondary text-text p-8">
      <AlertTriangle size={48} className="text-error mb-4" />
      <h1 className="text-h2 font-display mb-2">出错了</h1>
      <p className="text-body text-text-secondary mb-4 text-center max-w-md">
        Lemma 遇到了意外错误。你可以尝试重新加载，或重启应用。
      </p>
      <pre className="text-caption text-text-muted bg-bg-tertiary p-4 rounded-lg max-w-lg w-full overflow-auto mb-6">
        {error.message}
      </pre>
      <button
        onClick={resetErrorBoundary}
        className="flex items-center gap-2 px-5 py-2.5 rounded-lg bg-accent text-white hover:bg-accent-hover text-ui font-medium transition-colors"
      >
        <RefreshCw size={14} />
        重新加载
      </button>
    </div>
  );
}

export function ErrorBoundary({ children }: { children: React.ReactNode }) {
  return (
    <ReactErrorBoundary
      FallbackComponent={ErrorFallback}
      onReset={() => window.location.reload()}
    >
      {children}
    </ReactErrorBoundary>
  );
}
```

- [ ] **Step 4: Run test to verify it passes**

Run:
```bash
cd frontend && npx vitest run src/components/ErrorBoundary.test.tsx
```
Expected: Both tests PASS.

- [ ] **Step 5: Wrap App with ErrorBoundary in main.tsx**

In `frontend/src/main.tsx`, replace the full content:

```typescript
import React from 'react';
import ReactDOM from 'react-dom/client';
import { AppProvider } from './context/AppContext';
import { ErrorBoundary } from './components/ErrorBoundary';
import App from './App';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ErrorBoundary>
      <AppProvider>
        <App />
      </AppProvider>
    </ErrorBoundary>
  </React.StrictMode>,
);
```

Changes: Added `import { ErrorBoundary }` and wrapped `<AppProvider><App /></AppProvider>` with `<ErrorBoundary>`.

- [ ] **Step 6: Run all tests + typecheck**

Run:
```bash
npm run typecheck && cd frontend && npx vitest run
```
Expected: No typecheck errors. All tests pass.

- [ ] **Step 7: Commit**

```bash
git add frontend/src/components/ErrorBoundary.tsx frontend/src/components/ErrorBoundary.test.tsx frontend/src/main.tsx
git commit -m "feat: add ErrorBoundary to prevent white screen crashes"
```

---

### Task 5: Unify Error UI

**Files:**
- Modify: `frontend/src/components/ChatPanel.tsx:73-81`
- Modify: `frontend/src/App.tsx:193-199`

**Interfaces:**
- Consumes: `RetryBanner` component (already exists)
- Produces: single error display via `RetryBanner` only — no inline error banner in ChatPanel

- [ ] **Step 1: Remove inline error banner from ChatPanel**

In `frontend/src/components/ChatPanel.tsx`, delete lines 73-81 (the error banner block):

```typescript
// DELETE these lines (73-81):
      {/* 错误横幅 */}
      {error && (
        <div className="flex items-center gap-2 px-4 py-2 bg-red-50 bg-red-900/20 border-b border-red-200 border-red-800 text-red-700 text-red-300 text-sm">
          <AlertCircle size={16} />
          <span className="flex-1">{error}</span>
          <button onClick={onClearError} className="text-red-500 hover:text-red-700">
            ✕
          </button>
        </div>
      )}
```

After deletion, the ChatPanel component starts directly with the message list `<div className="flex-1 overflow-y-auto ...">`.

Also remove the now-unused `AlertCircle` import from line 5:

```typescript
// BEFORE:
import { Send, Square, AlertCircle, Trash2, ChevronDown, ChevronRight, RefreshCw } from 'lucide-react';

// AFTER:
import { Send, Square, Trash2, ChevronDown, ChevronRight, RefreshCw } from 'lucide-react';
```

- [ ] **Step 2: Verify RetryBanner is properly wired in App.tsx**

Confirm that `App.tsx` lines 193-199 already show `RetryBanner`:

```tsx
{claude.error && (
  <div className="px-4 py-2 border-t border-border">
    <RetryBanner
      error={claude.error}
      isRecoverable={isRecoverable}
      onRetry={() => {
        const lastUserMsg = [...claude.messages].reverse().find(
          (message) => message.metadata?.role === 'user'
        );
        if (lastUserMsg) handleSend(lastUserMsg.content);
      }}
      onDismiss={claude.clearError}
    />
  </div>
)}
```

Note: The `onRetry` handler here needs to actually retry, not just dismiss. Updated above to find the last user message and re-send it.

- [ ] **Step 3: Run typecheck**

Run:
```bash
npm run typecheck
```
Expected: No errors.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/ChatPanel.tsx frontend/src/App.tsx
git commit -m "fix: unify error UI — remove duplicate inline banner, keep RetryBanner only"
```

---

### Task 6: Fix All CSS Class Conflicts

**Files:**
- Modify: 15 component files (listed below)

**Interfaces:**
- Consumes: CSS custom properties defined in `index.css` (`--color-bg`, `--color-bg-secondary`, etc.)
- Produces: clean, non-conflicting Tailwind class usage across all components

**CSS Token Reference** (defined in `tailwind.config.js`):

Valid background tokens: `bg-bg`, `bg-bg-secondary`, `bg-bg-tertiary`, `bg-bg-elevated`
Valid text tokens: `text-text`, `text-text-secondary`, `text-text-muted`
Valid accent tokens: `text-accent`, `bg-accent`, `bg-accent-soft`, `text-accent-hover`
Valid border tokens: `border-border`, `border-border-strong`

**UNDEFINED tokens that must be replaced:**
- `bg-bg-secondary-light` → use `bg-bg-elevated`
- `bg-accent-light` → use `bg-accent-soft`
- `text-semantic-warning` → use `text-warning`
- `disabled:bg-warm-300` → use `disabled:opacity-50`
- `hover:border-warm-500` → use `hover:border-border-strong`

**Fix rule:** When two classes conflict (e.g., `bg-bg bg-bg-secondary`), keep the MORE SPECIFIC one (the one that describes the actual visual intent). Remove the generic `bg-bg` since `bg-bg-secondary` already maps to a CSS variable that handles both themes.

- [ ] **Step 1: Fix App.tsx CSS classes**

In `frontend/src/App.tsx`:

```typescript
// Line 123 — root container:
// BEFORE:
<div className="flex flex-col h-screen bg-bg bg-bg-secondary text-text text-text">
// AFTER:
<div className="flex flex-col h-screen bg-bg-secondary text-text">

// Line 133 — SDK warning banner:
// BEFORE:
<div className="px-4 py-2 bg-amber-50 bg-amber-900/20 text-amber-700 text-amber-300 text-xs text-center">
// AFTER:
<div className="px-4 py-2 bg-amber-900/20 text-amber-300 text-xs text-center">

// Line 177 — export button (primary):
// BEFORE:
className="px-5 py-2.5 rounded-editorial bg-accent text-white hover:bg-accent disabled:opacity-50 text-ui font-medium press-scale"
// AFTER:
className="px-5 py-2.5 rounded-editorial bg-accent text-white hover:bg-accent-hover disabled:opacity-50 text-ui font-medium press-scale"

// Line 183 — copy button (secondary):
// BEFORE:
className="px-5 py-2.5 rounded-editorial border border-border border-border-strong hover:bg-bg-elevated hover:bg-bg-tertiary disabled:opacity-50 text-ui font-medium press-scale"
// AFTER:
className="px-5 py-2.5 rounded-editorial border border-border-strong hover:bg-bg-tertiary disabled:opacity-50 text-ui font-medium press-scale"

// Line 194 — error container border:
// BEFORE:
<div className="px-4 py-2 border-t border-border border-border">
// AFTER:
<div className="px-4 py-2 border-t border-border">
```

- [ ] **Step 2: Fix ChatPanel.tsx CSS classes**

In `frontend/src/components/ChatPanel.tsx`:

```typescript
// Line 86 — empty state text:
// BEFORE:
<div className="flex flex-col items-center justify-center h-full text-text-muted text-text-secondary">
// AFTER:
<div className="flex flex-col items-center justify-center h-full text-text-muted">

// Line 107 — input area border:
// BEFORE:
<div className="border-t border-border border-border p-4">
// AFTER:
<div className="border-t border-border p-4">

// Line 116 — textarea background:
// BEFORE:
className="flex-1 resize-none rounded-lg border border-border border-border-strong bg-bg bg-bg-secondary-light px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-accent focus:border-transparent"
// AFTER:
className="flex-1 resize-none rounded-lg border border-border-strong bg-bg-secondary px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-accent focus:border-transparent"

// Line 132 — send button disabled state:
// BEFORE:
className="flex items-center gap-1 px-4 py-3 rounded-lg bg-accent hover:bg-accent disabled:bg-warm-300 disabled:cursor-not-allowed text-white text-sm transition-colors"
// AFTER:
className="flex items-center gap-1 px-4 py-3 rounded-lg bg-accent hover:bg-accent-hover disabled:opacity-50 disabled:cursor-not-allowed text-white text-sm transition-colors"

// Line 142 — clear button hover:
// BEFORE:
className="p-3 rounded-lg hover:bg-bg-tertiary hover:bg-bg-elevated text-text-muted transition-colors"
// AFTER:
className="p-3 rounded-lg hover:bg-bg-tertiary text-text-muted transition-colors"

// Line 174 — tool call text:
// BEFORE:
className="flex items-center gap-1 text-xs text-text-muted hover:text-text-secondary hover:text-text-secondary"
// AFTER:
className="flex items-center gap-1 text-xs text-text-muted hover:text-text-secondary"

// Line 180 — tool call pre background:
// BEFORE:
<pre className="mt-1 p-2 rounded text-xs bg-bg-tertiary bg-bg-elevated overflow-x-auto">
// AFTER:
<pre className="mt-1 p-2 rounded text-xs bg-bg-tertiary overflow-x-auto">

// Line 194 — assistant message background:
// BEFORE:
: 'bg-bg-tertiary bg-bg-elevated'
// AFTER:
: 'bg-bg-tertiary'
```

- [ ] **Step 3: Fix Sidebar.tsx CSS classes**

In `frontend/src/components/Sidebar.tsx`:

```typescript
// Line 31 — sidebar container:
// BEFORE:
className="flex flex-col w-[220px] bg-bg-secondary bg-bg-elevated border-r border-border border-border shrink-0"
// AFTER:
className="flex flex-col w-[220px] bg-bg-elevated border-r border-border shrink-0"

// Line 39 — new session button (fix redundant hover):
// BEFORE:
className="flex items-center gap-2 w-full px-3 py-2 rounded-editorial text-ui font-medium bg-accent hover:bg-accent text-white transition-colors press-scale"
// AFTER:
className="flex items-center gap-2 w-full px-3 py-2 rounded-editorial text-ui font-medium bg-accent hover:bg-accent-hover text-white transition-colors press-scale"

// Line 48 — section heading:
// BEFORE:
className="text-caption font-semibold uppercase tracking-wider text-text-secondary text-text-muted mb-2"
// AFTER:
className="text-caption font-semibold uppercase tracking-wider text-text-muted mb-2"

// Line 57 — selected preset:
// BEFORE:
'bg-accent-soft bg-accent-soft text-accent text-accent font-medium border-l-2 border-accent border-accent'
// AFTER:
'bg-accent-soft text-accent font-medium border-l-2 border-accent'

// Line 59 — unselected preset:
// BEFORE:
'text-text-secondary text-text-muted hover:bg-bg-tertiary hover:bg-bg-tertiary border-l-2 border-transparent'
// AFTER:
'text-text-muted hover:bg-bg-tertiary border-l-2 border-transparent'

// Line 81 — selected session:
// BEFORE:
'bg-bg-tertiary bg-bg-tertiary text-text text-text font-medium border-l-2 border-accent'
// AFTER:
'bg-bg-tertiary text-text font-medium border-l-2 border-accent'

// Line 83 — unselected session:
// BEFORE:
'text-text-secondary text-text-muted hover:bg-bg-tertiary hover:bg-bg-tertiary border-l-2 border-transparent'
// AFTER:
'text-text-muted hover:bg-bg-tertiary border-l-2 border-transparent'

// Line 93 — bottom border:
// BEFORE:
<div className="p-3 border-t border-border border-border">
// AFTER:
<div className="p-3 border-t border-border">

// Line 99 — work dir button:
// BEFORE:
className="flex items-center gap-2 w-full px-3 py-2 rounded-editorial text-ui text-text-secondary text-text-muted hover:bg-bg-tertiary hover:bg-bg-tertiary transition-colors"
// AFTER:
className="flex items-center gap-2 w-full px-3 py-2 rounded-editorial text-ui text-text-muted hover:bg-bg-tertiary transition-colors"
```

- [ ] **Step 4: Fix TitleBar.tsx CSS classes**

In `frontend/src/components/TitleBar.tsx`:

```typescript
// Line 20 — header:
// BEFORE:
className="drag-region flex items-center h-12 px-4 border-b border-border border-border bg-bg-secondary bg-bg-elevated shrink-0"
// AFTER:
className="drag-region flex items-center h-12 px-4 border-b border-border bg-bg-elevated shrink-0"

// Line 23 — logo:
// BEFORE:
className="text-base font-display font-semibold tracking-tight text-accent text-accent"
// AFTER:
className="text-base font-display font-semibold tracking-tight text-accent"

// Line 40 — inactive nav item (the false branch):
// BEFORE:
'text-text-muted text-text-secondary hover:text-text hover:text-text-secondary hover:bg-bg-elevated hover:bg-bg-tertiary'
// AFTER:
'text-text-muted hover:text-text-secondary hover:bg-bg-tertiary'
```

- [ ] **Step 5: Fix SettingsPanel.tsx CSS classes**

In `frontend/src/components/SettingsPanel.tsx`:

```typescript
// Line 75 — section heading:
// BEFORE:
className="flex items-center gap-2 text-sm font-semibold text-text text-text"
// AFTER (apply to ALL section headings: lines 75, 107, 127, 157, 174, 197, 243):
className="flex items-center gap-2 text-sm font-semibold text-text"

// Line 85 — API key input:
// BEFORE:
className="flex-1 px-3 py-2 rounded-lg border border-border border-border-strong bg-bg bg-bg-secondary-light text-sm focus:outline-none focus:ring-2 focus:ring-accent"
// AFTER:
className="flex-1 px-3 py-2 rounded-lg border border-border-strong bg-bg-secondary text-sm focus:outline-none focus:ring-2 focus:ring-accent"

// Line 91 — save button disabled:
// BEFORE:
className="px-4 py-2 rounded-lg bg-accent hover:bg-accent disabled:bg-warm-300 text-white text-sm transition-colors"
// AFTER:
className="px-4 py-2 rounded-lg bg-accent hover:bg-accent-hover disabled:opacity-50 text-white text-sm transition-colors"

// Line 114 — model select:
// BEFORE:
className="w-full px-3 py-2 rounded-lg border border-border border-border-strong bg-bg bg-bg-secondary-light text-sm focus:outline-none focus:ring-2 focus:ring-accent"
// AFTER:
className="w-full px-3 py-2 rounded-lg border border-border-strong bg-bg-secondary text-sm focus:outline-none focus:ring-2 focus:ring-accent"

// Line 137 — work dir input:
// BEFORE:
className="flex-1 px-3 py-2 rounded-lg border border-border border-border-strong bg-bg bg-bg-elevated text-sm"
// AFTER:
className="flex-1 px-3 py-2 rounded-lg border border-border-strong bg-bg-elevated text-sm"

// Line 141 — browse button hover:
// BEFORE:
className="px-4 py-2 rounded-lg border border-border border-border-strong hover:bg-bg-tertiary hover:bg-bg-elevated text-sm transition-colors"
// AFTER:
className="px-4 py-2 rounded-lg border border-border-strong hover:bg-bg-tertiary text-sm transition-colors"

// Line 185 — theme button border:
// BEFORE:
'border border-border border-border-strong hover:bg-bg-tertiary hover:bg-bg-elevated'
// AFTER:
'border border-border-strong hover:bg-bg-tertiary'

// Line 220, 227 — MCP inputs:
// BEFORE:
className="... border border-border border-border-strong bg-bg bg-bg-secondary-light ..."
// AFTER:
className="... border border-border-strong bg-bg-secondary ..."

// Line 204 — MCP server card background:
// BEFORE:
<div className="flex items-center justify-between px-3 py-2 rounded bg-bg bg-bg-elevated">
// AFTER:
<div className="flex items-center justify-between px-3 py-2 rounded bg-bg-elevated">

// Line 234 — MCP add button disabled:
// BEFORE:
className="px-3 py-2 rounded-lg bg-accent hover:bg-accent disabled:bg-warm-300 text-white text-sm"
// AFTER:
className="px-3 py-2 rounded-lg bg-accent hover:bg-accent-hover disabled:opacity-50 text-white text-sm"

// Line 243 — about section border:
// BEFORE:
<section className="space-y-3 pt-4 border-t border-border border-border">
// AFTER:
<section className="space-y-3 pt-4 border-t border-border">
```

- [ ] **Step 6: Fix FileBrowser.tsx CSS classes**

In `frontend/src/components/FileBrowser.tsx`:

```typescript
// Line 98 — file node button hover:
// BEFORE:
className={`flex items-center gap-1 w-full px-2 py-1 text-xs hover:bg-bg-tertiary hover:bg-bg-elevated rounded transition-colors ${
// AFTER:
className={`flex items-center gap-1 w-full px-2 py-1 text-xs hover:bg-bg-tertiary rounded transition-colors ${

// Line 99 — selected file:
// BEFORE:
selectedFile === node.path ? 'bg-accent-soft bg-accent-soft text-accent text-accent' : ''
// AFTER:
selectedFile === node.path ? 'bg-accent-soft text-accent' : ''

// Line 129 — file tree border:
// BEFORE:
<div className="w-64 border-r border-border border-border overflow-y-auto">
// AFTER:
<div className="w-64 border-r border-border overflow-y-auto">

// Line 130 — file tree header border:
// BEFORE:
<div className="flex items-center justify-between px-3 py-2 border-b border-border border-border">
// AFTER:
<div className="flex items-center justify-between px-3 py-2 border-b border-border">

// Line 155 — file content text:
// BEFORE:
<pre className="p-4 text-xs font-mono whitespace-pre-wrap text-text text-text-secondary">
// AFTER:
<pre className="p-4 text-xs font-mono whitespace-pre-wrap text-text-secondary">
```

- [ ] **Step 7: Fix CostTracker.tsx CSS classes**

In `frontend/src/components/CostTracker.tsx`:

```typescript
// Line 65 — token card background:
// BEFORE:
<div className="p-3 rounded-lg bg-bg bg-bg-elevated">
// AFTER (apply to both cards at lines 65 and 72):
<div className="p-3 rounded-lg bg-bg-elevated">

// Line 82 — cost card:
// BEFORE:
<div className="p-3 rounded-lg bg-accent-soft bg-accent-soft border border-accent border-accent">
// AFTER:
<div className="p-3 rounded-lg bg-accent-soft border border-accent">

// Line 83 — cost label:
// BEFORE:
<div className="flex items-center gap-1 text-xs text-accent text-accent mb-1">
// AFTER:
<div className="flex items-center gap-1 text-xs text-accent mb-1">

// Line 87 — cost value:
// BEFORE:
<p className="text-2xl font-bold text-accent text-accent">
// AFTER:
<p className="text-2xl font-bold text-accent">
```

- [ ] **Step 8: Fix StatusBar.tsx CSS classes**

In `frontend/src/components/StatusBar.tsx`:

```typescript
// Line 15 — status bar container:
// BEFORE:
className="flex items-center justify-between px-4 h-7 bg-bg-secondary bg-bg-elevated border-t border-border border-border shrink-0"
// AFTER:
className="flex items-center justify-between px-4 h-7 bg-bg-elevated border-t border-border shrink-0"

// Line 19 — left section text:
// BEFORE:
<div className="flex items-center gap-3 text-caption text-text-secondary text-text-muted">
// AFTER:
<div className="flex items-center gap-3 text-caption text-text-muted">

// Line 21 — offline text (fix undefined token):
// BEFORE:
<span className="flex items-center gap-1 text-semantic-warning">
// AFTER:
<span className="flex items-center gap-1 text-warning">

// Line 26 — streaming text:
// BEFORE:
<span className="flex items-center gap-1 text-accent text-accent">
// AFTER:
<span className="flex items-center gap-1 text-accent">

// Line 38 — right section text:
// BEFORE:
<div className="flex items-center gap-4 text-caption text-text-secondary text-text-muted">
// AFTER:
<div className="flex items-center gap-4 text-caption text-text-muted">
```

- [ ] **Step 9: Fix RetryBanner.tsx CSS classes**

In `frontend/src/components/RetryBanner.tsx`:

```typescript
// Line 44 — online state:
// BEFORE:
? 'bg-amber-50 bg-amber-900/20 border border-amber-200 border-amber-800'
// AFTER:
? 'bg-amber-900/20 border border-amber-800'

// Line 45 — offline state:
// BEFORE:
: 'bg-red-50 bg-red-900/20 border border-red-200 border-red-800'
// AFTER:
: 'bg-red-900/20 border border-red-800'

// Line 54 — error text:
// BEFORE:
<p className="text-sm text-text text-text">
// AFTER:
<p className="text-sm text-text">

// Line 77 — dismiss button hover:
// BEFORE:
className="text-text-muted hover:text-text-secondary hover:text-text text-sm"
// AFTER:
className="text-text-muted hover:text-text-secondary text-sm"
```

- [ ] **Step 10: Fix OnboardingWizard.tsx CSS classes**

In `frontend/src/components/OnboardingWizard.tsx`:

```typescript
// Line 58 — page background:
// BEFORE:
className="flex flex-col items-center justify-center min-h-screen bg-bg bg-bg-secondary p-8"
// AFTER:
className="flex flex-col items-center justify-center min-h-screen bg-bg-secondary p-8"

// Line 66 — progress bar (fix undefined token):
// BEFORE:
index <= stepIndex ? 'bg-accent-light' : 'bg-bg-tertiary bg-bg-elevated'
// AFTER:
index <= stepIndex ? 'bg-accent' : 'bg-bg-tertiary'

// Line 76 — welcome text:
// BEFORE:
<p className="text-text-secondary text-text-muted">
// AFTER:
<p className="text-text-muted">

// Lines 82, 114, 147, 166, 181 — all primary buttons have redundant hover
// (bg-accent + hover:bg-accent produces no visual change on hover):
// BEFORE (repeated 5 times):
className="px-6 py-3 rounded-lg bg-accent text-white hover:bg-accent text-sm"
className="px-6 py-2 rounded-lg bg-accent text-white hover:bg-accent disabled:opacity-50 text-sm"
className="px-6 py-2 rounded-lg bg-accent text-white hover:bg-accent text-sm"
className="px-6 py-2 rounded-lg bg-accent text-white hover:bg-accent text-sm"
className="px-6 py-3 rounded-lg bg-accent text-white hover:bg-accent text-sm"
// AFTER (fix all to hover:bg-accent-hover for actual hover feedback):
className="px-6 py-3 rounded-lg bg-accent text-white hover:bg-accent-hover text-sm"
className="px-6 py-2 rounded-lg bg-accent text-white hover:bg-accent-hover disabled:opacity-50 text-sm"
className="px-6 py-2 rounded-lg bg-accent text-white hover:bg-accent-hover text-sm"
className="px-6 py-2 rounded-lg bg-accent text-white hover:bg-accent-hover text-sm"
className="px-6 py-3 rounded-lg bg-accent text-white hover:bg-accent-hover text-sm"

// Line 103 — API key input:
// BEFORE:
className="w-full px-4 py-3 rounded-lg border border-border border-border-strong bg-bg bg-bg-secondary focus:outline-none focus:ring-2 focus:ring-accent"
// AFTER:
className="w-full px-4 py-3 rounded-lg border border-border-strong bg-bg-secondary focus:outline-none focus:ring-2 focus:ring-accent"

// Line 137 — work dir input:
// BEFORE:
className="flex-1 px-4 py-3 rounded-lg border border-border border-border-strong bg-bg bg-bg-elevated text-sm"
// AFTER:
className="flex-1 px-4 py-3 rounded-lg border border-border-strong bg-bg-elevated text-sm"

// Line 139 — browse button:
// BEFORE:
className="px-4 py-3 rounded-lg border border-border border-border-strong hover:bg-bg-tertiary hover:bg-bg-elevated text-sm"
// AFTER:
className="px-4 py-3 rounded-lg border border-border-strong hover:bg-bg-tertiary text-sm"
```

- [ ] **Step 11: Fix PipelineProgress.tsx CSS classes**

In `frontend/src/components/PipelineProgress.tsx`:

```typescript
// Line 51 — heading:
// BEFORE:
<h3 className="text-sm font-semibold text-text text-text">
// AFTER:
<h3 className="text-sm font-semibold text-text">

// Line 62 — progress bar (fix undefined token):
// BEFORE:
className="h-full rounded-full bg-accent-light transition-all duration-500"
// AFTER:
className="h-full rounded-full bg-accent transition-all duration-500"

// Line 62 — progress track:
// BEFORE:
<div className="h-2 rounded-full bg-bg-tertiary bg-bg-elevated overflow-hidden">
// AFTER:
<div className="h-2 rounded-full bg-bg-tertiary overflow-hidden">

// Line 79 — stage button hover:
// BEFORE:
className="flex items-center gap-2 w-full px-3 py-2 text-sm transition-colors hover:bg-bg hover:bg-bg-secondary-light"
// AFTER:
className="flex items-center gap-2 w-full px-3 py-2 text-sm transition-colors hover:bg-bg-secondary"

// Line 93 — output pre:
// BEFORE:
<pre className="px-3 py-2 text-xs font-mono bg-bg bg-bg-secondary-light border-t border-border border-border overflow-x-auto">
// AFTER:
<pre className="px-3 py-2 text-xs font-mono bg-bg-secondary-light border-t border-border overflow-x-auto">

Wait — `bg-bg-secondary-light` is still undefined. Replace with:
<pre className="px-3 py-2 text-xs font-mono bg-bg-secondary border-t border-border overflow-x-auto">
```

- [ ] **Step 12: Fix ClaudeMdEditor.tsx CSS classes**

In `frontend/src/components/ClaudeMdEditor.tsx`:

```typescript
// Line 57 — content preview:
// BEFORE:
<pre className="p-3 rounded-lg bg-bg bg-bg-elevated text-xs overflow-auto max-h-48 whitespace-pre-wrap">
// AFTER:
<pre className="p-3 rounded-lg bg-bg-elevated text-xs overflow-auto max-h-48 whitespace-pre-wrap">

// Line 73 — textarea (fix undefined token):
// BEFORE:
className="w-full p-3 rounded-lg border border-border border-border-strong bg-bg bg-bg-secondary-light text-xs font-mono focus:outline-none focus:ring-2 focus:ring-accent"
// AFTER:
className="w-full p-3 rounded-lg border border-border-strong bg-bg-secondary text-xs font-mono focus:outline-none focus:ring-2 focus:ring-accent"

// Line 85 — cancel button:
// BEFORE:
className="px-3 py-1.5 rounded text-xs border border-border border-border-strong hover:bg-bg-tertiary hover:bg-bg-elevated"
// AFTER:
className="px-3 py-1.5 rounded text-xs border border-border-strong hover:bg-bg-tertiary"
```

- [ ] **Step 13: Fix PresetSelector.tsx CSS classes**

In `frontend/src/components/PresetSelector.tsx`:

```typescript
// Line 18 — selected preset (fix undefined token + duplicate):
// BEFORE:
'bg-accent-soft bg-accent-soft border-2 border-accent'
// AFTER:
'bg-accent-soft border-2 border-accent'

// Line 19 — unselected preset (fix undefined token + duplicate):
// BEFORE:
'bg-bg bg-bg-elevated border-2 border-transparent hover:border-border hover:border-warm-500'
// AFTER:
'bg-bg-elevated border-2 border-transparent hover:border-border-strong'
```

- [ ] **Step 14: Run typecheck + build**

Run:
```bash
npm run typecheck && cd frontend && npx vite build
```
Expected: No errors. Build succeeds.

- [ ] **Step 15: Commit**

```bash
git add frontend/src/components/ frontend/src/App.tsx
git commit -m "fix: resolve all Tailwind class conflicts across 15 components"
```

---

### Task 7: Implement Message Persistence with IndexedDB

**Files:**
- Create: `frontend/src/hooks/useMessageStore.ts`
- Create: `frontend/src/hooks/useMessageStore.test.ts`
- Modify: `frontend/src/hooks/useClaude.ts`
- Modify: `frontend/src/App.tsx`

**Interfaces:**
- Consumes: `idb-keyval` package (installed in Task 1)
- Produces: `useMessageStore()` hook returning `{ saveMessages, loadMessages, deleteMessages }`

- [ ] **Step 1: Write the failing test**

Create `frontend/src/hooks/useMessageStore.test.ts`:

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useMessageStore } from './useMessageStore';

// Mock idb-keyval
vi.mock('idb-keyval', () => ({
  get: vi.fn(() => Promise.resolve(undefined)),
  set: vi.fn(() => Promise.resolve()),
  del: vi.fn(() => Promise.resolve()),
}));

describe('useMessageStore', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should load empty array when no stored messages', async () => {
    const { result } = renderHook(() => useMessageStore('test-session'));
    await act(async () => {
      await result.current.loadMessages();
    });
    expect(result.current.messages).toEqual([]);
  });

  it('should save and expose messages', async () => {
    const { result } = renderHook(() => useMessageStore('test-session'));
    const testMessages: ClaudeMessage[] = [
      { type: 'text', content: 'hello', metadata: { role: 'user' } },
    ];
    await act(async () => {
      await result.current.saveMessages(testMessages);
    });
    expect(result.current.messages).toEqual(testMessages);
  });

  it('should provide deleteMessages function', () => {
    const { result } = renderHook(() => useMessageStore('test-session'));
    expect(typeof result.current.deleteMessages).toBe('function');
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run:
```bash
cd frontend && npx vitest run src/hooks/useMessageStore.test.ts
```
Expected: FAIL — `useMessageStore` module not found.

- [ ] **Step 3: Create useMessageStore hook**

Create `frontend/src/hooks/useMessageStore.ts`:

```typescript
import { useState, useCallback } from 'react';
import { get, set, del } from 'idb-keyval';

const MESSAGE_KEY_PREFIX = 'lemma-messages:';

function storageKey(sessionId: string): string {
  return `${MESSAGE_KEY_PREFIX}${sessionId}`;
}

export function useMessageStore(sessionId: string | null) {
  const [messages, setMessages] = useState<ClaudeMessage[]>([]);

  const loadMessages = useCallback(async () => {
    if (!sessionId) return;
    const stored = await get<ClaudeMessage[]>(storageKey(sessionId));
    if (stored) {
      setMessages(stored);
    }
  }, [sessionId]);

  const saveMessages = useCallback(async (newMessages: ClaudeMessage[]) => {
    if (!sessionId) return;
    setMessages(newMessages);
    await set(storageKey(sessionId), newMessages);
  }, [sessionId]);

  const deleteMessages = useCallback(async () => {
    if (!sessionId) return;
    setMessages([]);
    await del(storageKey(sessionId));
  }, [sessionId]);

  return { messages, loadMessages, saveMessages, deleteMessages };
}
```

- [ ] **Step 4: Run test to verify it passes**

Run:
```bash
cd frontend && npx vitest run src/hooks/useMessageStore.test.ts
```
Expected: All 3 tests PASS.

- [ ] **Step 5: Wire persistence into App.tsx**

In `frontend/src/App.tsx`, add the import and hook usage:

```typescript
// Add import (near existing imports):
import { useMessageStore } from './hooks/useMessageStore';

// Inside the App component, after existing state declarations, add:
const sessionId = state.currentSessionId ?? 'default';
const messageStore = useMessageStore(sessionId);
```

Then modify the `handleSend` function to persist after sending:

```typescript
// Replace the handleSend callback:
const handleSend = useCallback((text: string) => {
  const options: ChatOptions = {};
  if (state.workDir) options.workDir = state.workDir;
  if (selectedPreset) options.presetId = selectedPreset;
  claude.sendMessage(text, options);
}, [state.workDir, selectedPreset, claude]);

// Add a new useEffect to persist messages whenever they change:
useEffect(() => {
  if (claude.messages.length > 0) {
    messageStore.saveMessages(claude.messages);
  }
}, [claude.messages, messageStore]);

// Add a useEffect to restore messages on session change:
useEffect(() => {
  messageStore.loadMessages().then(() => {
    // After loading, set them into claude state
    // This requires exposing a setMessages from useClaude
  });
}, [sessionId, messageStore]);
```

Actually, the cleaner approach is to modify `useClaude` to accept an initial messages array and a persist callback. Let me revise:

In `frontend/src/hooks/useClaude.ts`, modify the function signature:

```typescript
// Change the function signature to accept initial messages:
export function useClaude(initialMessages: ClaudeMessage[] = []) {
  const [messages, setMessages] = useState<ClaudeMessage[]>(initialMessages);
  // ... rest stays the same
}
```

In `frontend/src/App.tsx`:

```typescript
// Load persisted messages on mount
const [persistedMessages, setPersistedMessages] = useState<ClaudeMessage[]>([]);
const sessionId = state.currentSessionId ?? 'default';

useEffect(() => {
  const key = `lemma-messages:${sessionId}`;
  get<ClaudeMessage[]>(key).then((stored) => {
    if (stored) setPersistedMessages(stored);
  });
}, [sessionId]);

// Pass to useClaude:
const claude = useClaude(persistedMessages);

// Persist whenever messages change:
useEffect(() => {
  if (claude.messages.length > 0) {
    const key = `lemma-messages:${sessionId}`;
    set(key, claude.messages);
  }
}, [claude.messages, sessionId]);

// On clear, also delete from store:
const handleClearAndPersist = useCallback(() => {
  claude.clearMessages();
  const key = `lemma-messages:${sessionId}`;
  del(key);
}, [claude, sessionId]);
```

Update the clear keyboard shortcut to use `handleClearAndPersist` instead of `claude.clearMessages`.

- [ ] **Step 6: Run all tests + typecheck**

Run:
```bash
npm run typecheck && cd frontend && npx vitest run
```
Expected: No errors. All tests pass.

- [ ] **Step 7: Commit**

```bash
git add frontend/src/hooks/useMessageStore.ts frontend/src/hooks/useMessageStore.test.ts frontend/src/hooks/useClaude.ts frontend/src/App.tsx
git commit -m "feat: persist chat messages to IndexedDB via idb-keyval"
```

---

### Task 8: Enable Typing Indicator

**Files:**
- Modify: `frontend/src/components/ChatPanel.tsx`

**Interfaces:**
- Consumes: `isStreaming` prop, `.typing-indicator` CSS class (already defined in `index.css`)
- Produces: animated three-dot indicator shown while waiting for first token

- [ ] **Step 1: Add typing indicator to ChatPanel**

In `frontend/src/components/ChatPanel.tsx`, inside the message list `<div>`, after the `messages.map(...)` block and before `<div ref={messagesEndRef} />`, add:

```tsx
{/* 打字指示器 — 流式传输中且最后一条消息是用户消息时显示 */}
{isStreaming && messages.length > 0 && messages[messages.length - 1]?.metadata?.role === 'user' && (
  <div className="max-w-4xl mx-auto">
    <div className="rounded-lg px-4 py-3 bg-bg-tertiary inline-block">
      <div className="typing-indicator flex items-center gap-1">
        <span />
        <span />
        <span />
      </div>
    </div>
  </div>
)}
```

- [ ] **Step 2: Verify visually**

Run:
```bash
npm run electron:dev
```

Send a message and observe: before the first token arrives, three pulsing dots should appear in a bubble below the user message. Once tokens start flowing, the indicator disappears and the actual response shows.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/ChatPanel.tsx
git commit -m "feat: enable typing indicator during streaming wait"
```

---

### Task 9: Enable Code Block Copy Button

**Files:**
- Modify: `frontend/src/components/ChatPanel.tsx` (the `MessageBubble` component's ReactMarkdown `code` render prop)

**Interfaces:**
- Consumes: `navigator.clipboard.writeText` API, `.code-block-wrapper` and `.copy-button` CSS classes (already defined in `index.css`)
- Produces: hover-to-reveal copy button on code blocks

- [ ] **Step 1: Add copy button to code blocks**

In `frontend/src/components/ChatPanel.tsx`, find the `ReactMarkdown` `components` prop inside `MessageBubble`. Replace the entire `code` render function:

```tsx
// BEFORE (inside ReactMarkdown components):
code({ className, children, ...props }) {
  const match = /language-(\w+)/.exec(className || '');
  const codeString = String(children).replace(/\n$/, '');
  if (match) {
    return (
      <SyntaxHighlighter
        style={oneDark}
        language={match[1]}
        PreTag="div"
      >
        {codeString}
      </SyntaxHighlighter>
    );
  }
  return (
    <code className={className} {...props}>
      {children}
    </code>
  );
},

// AFTER:
code({ className, children, ...props }) {
  const match = /language-(\w+)/.exec(className || '');
  const codeString = String(children).replace(/\n$/, '');
  if (match) {
    return (
      <CodeBlock language={match[1]} code={codeString} />
    );
  }
  return (
    <code className={className} {...props}>
      {children}
    </code>
  );
},
```

Then, add the `CodeBlock` component (inside the same file, before the export, or as a separate file):

```typescript
import { useState } from 'react';
import { Copy, Check } from 'lucide-react';

function CodeBlock({ language, code }: { language: string; code: string }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Clipboard API may fail in some contexts
    }
  };

  return (
    <div className="code-block-wrapper">
      <SyntaxHighlighter
        style={oneDark}
        language={language}
        PreTag="div"
      >
        {code}
      </SyntaxHighlighter>
      <button
        onClick={handleCopy}
        className="copy-button absolute top-2 right-2 p-1.5 rounded bg-bg-tertiary hover:bg-bg-elevated text-text-muted hover:text-text transition-opacity"
        title="复制代码"
      >
        {copied ? <Check size={14} className="text-success" /> : <Copy size={14} />}
      </button>
    </div>
  );
}
```

Add the required import for `Copy` and `Check` from `lucide-react` at the top of ChatPanel.tsx:

```typescript
import { Send, Square, Trash2, ChevronDown, ChevronRight, RefreshCw, Copy, Check } from 'lucide-react';
```

- [ ] **Step 2: Verify visually**

Run:
```bash
npm run electron:dev
```

Send a message that triggers code output (e.g., "写一个 Python hello world"). Hover over the code block — a copy button should appear in the top-right corner. Click it — icon changes to a checkmark for 2 seconds.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/ChatPanel.tsx
git commit -m "feat: add copy button to code blocks"
```

---

### Task 10: Final Build Verification

**Files:**
- No code changes
- Verify: entire build pipeline

- [ ] **Step 1: Run full test suite**

Run:
```bash
cd frontend && npx vitest run
```
Expected: All tests pass. Print the count.

- [ ] **Step 2: Run typecheck**

Run:
```bash
npm run typecheck
```
Expected: No errors.

- [ ] **Step 3: Run production build**

Run:
```bash
cd frontend && npx vite build
```
Expected: Build succeeds. Check output chunks — should be:
- `index.html`
- `index-*.css`
- `index-*.js` (main app)
- `react-vendor-*.js`
- `ui-vendor-*.js`
- `markdown-vendor-*.js`
- `SettingsPanel-*.js`

No `motion-vendor` or `virtuoso-vendor` chunks.

- [ ] **Step 4: Run Electron dev to verify end-to-end**

Run:
```bash
npm run electron:dev
```

Manual checklist:
- [ ] App launches without console errors
- [ ] Onboarding wizard shows (if no API key configured)
- [ ] After entering API key, main chat view loads
- [ ] Sending a message shows typing indicator → streaming response
- [ ] Code blocks have copy button on hover
- [ ] Switching theme (light/dark) works correctly — no visual glitches
- [ ] Closing and reopening app preserves messages
- [ ] Error boundary works (try with invalid API key)
- [ ] RetryBanner shows on connection error (try disconnecting network)
- [ ] All keyboard shortcuts work (Ctrl+N, Ctrl+K, Ctrl+,, etc.)

- [ ] **Step 5: Commit final verification**

```bash
git add -A
git commit -m "chore: phase 0 complete — all emergency fixes verified"
```

---

## Task Dependency Graph

```
Task 1 (deps)
  ├──→ Task 2 (useEffect fix)
  ├──→ Task 3 (streaming perf) ──→ Task 7 (persistence, needs useClaude changes)
  ├──→ Task 4 (ErrorBoundary)
  ├──→ Task 5 (error UI)
  ├──→ Task 6 (CSS cleanup)
  ├──→ Task 8 (typing indicator, needs ChatPanel changes)
  └──→ Task 9 (copy button, needs ChatPanel changes)

Task 10 (final verification) ← depends on ALL above
```

**Recommended execution order:**
1 → 2 → 3 → 4 → 5 → 6 → 8 → 9 → 7 → 10

Task 7 (persistence) is last before verification because it modifies both `useClaude.ts` and `App.tsx`, which other tasks also touch.

---

## Estimated Effort

| Task | Est. Time | Risk |
|------|-----------|------|
| Task 1: Clean deps | 5 min | Low |
| Task 2: useEffect fix | 2 min | Low |
| Task 3: Streaming perf | 30 min | Medium (core hook rewrite) |
| Task 4: ErrorBoundary | 15 min | Low |
| Task 5: Error UI | 10 min | Low |
| Task 6: CSS cleanup | 45 min | Low (mechanical but tedious) |
| Task 7: Persistence | 30 min | Medium (new data layer) |
| Task 8: Typing indicator | 10 min | Low |
| Task 9: Copy button | 15 min | Low |
| Task 10: Verification | 15 min | Low |
| **Total** | **~3 hours** | |
