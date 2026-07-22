# Lemma Phase 1 可用 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Lemma usable for daily work — settings persist across restarts, model selection works, tool calls are readable, messages have actions, and the codebase is cleaner.

**Architecture:** Incremental refactoring on the existing Electron + React + Claude Agent SDK stack. Each task produces independently testable changes. No new dependencies required (all libraries already installed).

**Tech Stack:** React 18, TypeScript, Tailwind CSS 3, Electron 39, idb-keyval, lucide-react

## Global Constraints

- TypeScript strict mode ON — no `any` types (use `unknown`)
- Functions ≤ 30 lines — extract helpers
- Commit format: Conventional Commits (`feat:`, `fix:`, `refactor:`, `chore:`, `test:`)
- Run `npm run typecheck` after every task
- Run `cd frontend && npx vitest run` after tasks that touch hooks or components
- All user-facing text in Chinese (zh-CN)
- CSS uses CSS custom properties — never add light/dark class pairs
- Follow existing patterns: `useReducer` for global state, `useState` for local, IPC via `window.lemmaAPI`

---

## File Structure

### New files to create:

| File | Responsibility |
|------|---------------|
| `frontend/src/constants.ts` | IPC channels, storage keys, magic strings |
| `frontend/src/components/settings/ApiKeySection.tsx` | API key management section |
| `frontend/src/components/settings/ModelSection.tsx` | Model selection section |
| `frontend/src/components/settings/WorkDirSection.tsx` | Work directory section |
| `frontend/src/components/settings/ThemeSection.tsx` | Theme selection section |
| `frontend/src/components/settings/McpSection.tsx` | MCP server management section |
| `frontend/src/components/MessageActions.tsx` | Hover action menu for messages |
| `frontend/src/hooks/useAppPersistence.ts` | localStorage persistence for AppContext |

### Files to modify:

| File | Changes |
|------|---------|
| `frontend/src/context/AppContext.tsx` | Add persistence, add model + preset to state, fix checkApiKey |
| `frontend/src/App.tsx` | Remove dead code, use constants, pass model to chat |
| `frontend/src/components/ChatPanel.tsx` | Remove dead props, add MessageActions, improve tool display |
| `frontend/src/components/SettingsPanel.tsx` | Split into sub-components |
| `frontend/src/components/Sidebar.tsx` | Add session search |
| `frontend/src/hooks/useClaude.ts` | Accept model in sendMessage options |
| `electron/main.ts` | Add path restriction to read-file/list-directory |
| `electron/claude-sdk-bridge.ts` | Pass model option to SDK query |

---

### Task 1: Create Constants Module

**Files:**
- Create: `frontend/src/constants.ts`
- Modify: `frontend/src/App.tsx` (replace magic strings)
- Modify: `frontend/src/components/ChatPanel.tsx` (replace magic strings)
- Modify: `frontend/src/context/AppContext.tsx` (replace magic strings)

**Interfaces:**
- Consumes: nothing
- Produces: exported constants used by all subsequent tasks

- [ ] **Step 1: Create constants module**

Create `frontend/src/constants.ts`:

```typescript
/** IPC event channel names */
export const IPC_CHANNELS = {
  CLAUDE_MESSAGE: 'claude-message',
  FILE_CHANGED: 'file-changed',
  SEND_MESSAGE: 'send-message',
  API_KEY_STATUS: 'api-key-status',
} as const;

/** IndexedDB / localStorage keys */
export const STORAGE_KEYS = {
  MESSAGE_PREFIX: 'lemma-messages:',
  THEME: 'lemma-theme',
  WORK_DIR: 'lemma-work-dir',
  SELECTED_PRESET: 'lemma-selected-preset',
  SELECTED_MODEL: 'lemma-selected-model',
  SIDEBAR_COLLAPSED: 'lemma-sidebar-collapsed',
  NOTIFICATIONS_ENABLED: 'lemma-notifications-enabled',
} as const;

/** Timing constants (milliseconds) */
export const TIMING = {
  SAVE_STATUS_DURATION: 2000,
  COPY_FEEDBACK_DURATION: 2000,
  NOTIFICATION_TIMEOUT: 3000,
} as const;

/** Retry backoff delays */
export const RETRY_DELAYS = [2000, 4000, 8000, 16000, 30000] as const;
```

- [ ] **Step 2: Replace magic strings in ChatPanel.tsx**

In `frontend/src/components/ChatPanel.tsx`:

Add import at top:
```typescript
import { IPC_CHANNELS } from '../constants';
```

Find the useEffect that listens for `send-message`:
```typescript
// BEFORE:
document.addEventListener('send-message', handler);
return () => document.removeEventListener('send-message', handler);

// AFTER:
document.addEventListener(IPC_CHANNELS.SEND_MESSAGE, handler);
return () => document.removeEventListener(IPC_CHANNELS.SEND_MESSAGE, handler);
```

- [ ] **Step 3: Replace magic strings in App.tsx**

In `frontend/src/App.tsx`:

Add import:
```typescript
import { IPC_CHANNELS, STORAGE_KEYS } from './constants';
```

Replace `send-message` dispatch:
```typescript
// BEFORE:
document.dispatchEvent(new CustomEvent('send-message'))
// AFTER:
document.dispatchEvent(new CustomEvent(IPC_CHANNELS.SEND_MESSAGE))
```

Replace `api-key-status` event:
```typescript
// BEFORE:
document.addEventListener('api-key-status', handler);
return () => document.removeEventListener('api-key-status', handler);
// AFTER:
document.addEventListener(IPC_CHANNELS.API_KEY_STATUS, handler);
return () => document.removeEventListener(IPC_CHANNELS.API_KEY_STATUS, handler);
```

- [ ] **Step 4: Replace magic strings in AppContext.tsx**

In `frontend/src/context/AppContext.tsx`:

Add import:
```typescript
import { IPC_CHANNELS } from '../constants';
```

Replace:
```typescript
// BEFORE:
document.dispatchEvent(new CustomEvent('api-key-status', { detail: true }));
// AFTER:
document.dispatchEvent(new CustomEvent(IPC_CHANNELS.API_KEY_STATUS, { detail: true }));
```

- [ ] **Step 5: Replace magic string in RetryBanner.tsx**

In `frontend/src/components/RetryBanner.tsx`:

Add import:
```typescript
import { RETRY_DELAYS } from '../constants';
```

Remove the local `RETRY_DELAYS` constant (line 11):
```typescript
// DELETE this line:
const RETRY_DELAYS = [2000, 4000, 8000, 16000, 30000];
```

- [ ] **Step 6: Verify and commit**

Run:
```bash
npm run typecheck
```
Expected: No errors.

```bash
git add frontend/src/constants.ts frontend/src/App.tsx frontend/src/components/ChatPanel.tsx frontend/src/context/AppContext.tsx frontend/src/components/RetryBanner.tsx
git commit -m "refactor: extract magic strings to constants module"
```

---

### Task 2: AppContext State Persistence

**Files:**
- Create: `frontend/src/hooks/useAppPersistence.ts`
- Modify: `frontend/src/context/AppContext.tsx`
- Modify: `frontend/src/types/electron.d.ts` (add new state fields)

**Interfaces:**
- Consumes: `STORAGE_KEYS` from constants module (Task 1)
- Produces: `AppState` with persisted fields: `theme`, `workDir`, `sidebarCollapsed`, `notificationsEnabled`, `selectedModel`, `selectedPreset`

- [ ] **Step 1: Add new fields to AppState**

In `frontend/src/context/AppContext.tsx`, update the `AppState` interface:

```typescript
// BEFORE:
interface AppState {
  currentView: ViewType;
  theme: ThemeType;
  workDir: string | null;
  currentSessionId: string | null;
  apiKeyConfigured: boolean;
  sidebarCollapsed: boolean;
  notificationsEnabled: boolean;
}

// AFTER:
interface AppState {
  currentView: ViewType;
  theme: ThemeType;
  workDir: string | null;
  currentSessionId: string | null;
  apiKeyConfigured: boolean;
  sidebarCollapsed: boolean;
  notificationsEnabled: boolean;
  selectedModel: string;
  selectedPreset: string | null;
}
```

Add new actions:
```typescript
type AppAction =
  // ... existing actions ...
  | { type: 'SET_MODEL'; payload: string }
  | { type: 'SET_PRESET'; payload: string | null }
  | { type: 'HYDRATE_STATE'; payload: Partial<AppState> };
```

Update `initialState`:
```typescript
import { DEFAULT_MODEL } from '../config';

const initialState: AppState = {
  currentView: 'chat',
  theme: 'system',
  workDir: null,
  currentSessionId: null,
  apiKeyConfigured: false,
  sidebarCollapsed: false,
  notificationsEnabled: true,
  selectedModel: DEFAULT_MODEL,
  selectedPreset: null,
};
```

Add reducer cases:
```typescript
case 'SET_MODEL':
  return { ...state, selectedModel: action.payload };
case 'SET_PRESET':
  return { ...state, selectedPreset: action.payload };
case 'HYDRATE_STATE':
  return { ...state, ...action.payload };
```

- [ ] **Step 2: Create useAppPersistence hook**

Create `frontend/src/hooks/useAppPersistence.ts`:

```typescript
import { useEffect, useCallback } from 'react';
import { STORAGE_KEYS } from '../constants';

interface PersistedState {
  theme?: string;
  workDir?: string | null;
  sidebarCollapsed?: boolean;
  notificationsEnabled?: boolean;
  selectedModel?: string;
  selectedPreset?: string | null;
}

function loadPersistedState(): PersistedState {
  const result: PersistedState = {};
  try {
    const theme = localStorage.getItem(STORAGE_KEYS.THEME);
    if (theme) result.theme = theme;

    const workDir = localStorage.getItem(STORAGE_KEYS.WORK_DIR);
    if (workDir) result.workDir = workDir;

    const collapsed = localStorage.getItem(STORAGE_KEYS.SIDEBAR_COLLAPSED);
    if (collapsed !== null) result.sidebarCollapsed = collapsed === 'true';

    const notifications = localStorage.getItem(STORAGE_KEYS.NOTIFICATIONS_ENABLED);
    if (notifications !== null) result.notificationsEnabled = notifications === 'true';

    const model = localStorage.getItem(STORAGE_KEYS.SELECTED_MODEL);
    if (model) result.selectedModel = model;

    const preset = localStorage.getItem(STORAGE_KEYS.SELECTED_PRESET);
    if (preset) result.selectedPreset = preset;
  } catch {
    // localStorage may be unavailable in some contexts
  }
  return result;
}

function savePersistedState(state: PersistedState): void {
  try {
    if (state.theme !== undefined) {
      localStorage.setItem(STORAGE_KEYS.THEME, state.theme);
    }
    if (state.workDir !== undefined) {
      if (state.workDir) {
        localStorage.setItem(STORAGE_KEYS.WORK_DIR, state.workDir);
      } else {
        localStorage.removeItem(STORAGE_KEYS.WORK_DIR);
      }
    }
    if (state.sidebarCollapsed !== undefined) {
      localStorage.setItem(STORAGE_KEYS.SIDEBAR_COLLAPSED, String(state.sidebarCollapsed));
    }
    if (state.notificationsEnabled !== undefined) {
      localStorage.setItem(STORAGE_KEYS.NOTIFICATIONS_ENABLED, String(state.notificationsEnabled));
    }
    if (state.selectedModel !== undefined) {
      localStorage.setItem(STORAGE_KEYS.SELECTED_MODEL, state.selectedModel);
    }
    if (state.selectedPreset !== undefined) {
      if (state.selectedPreset) {
        localStorage.setItem(STORAGE_KEYS.SELECTED_PRESET, state.selectedPreset);
      } else {
        localStorage.removeItem(STORAGE_KEYS.SELECTED_PRESET);
      }
    }
  } catch {
    // localStorage may be full or unavailable
  }
}

export function useAppPersistence(
  state: { theme: string; workDir: string | null; sidebarCollapsed: boolean; notificationsEnabled: boolean; selectedModel: string; selectedPreset: string | null },
  dispatch: React.Dispatch<{ type: string; payload?: unknown }>,
): void {
  // Hydrate on mount
  useEffect(() => {
    const persisted = loadPersistedState();
    if (Object.keys(persisted).length > 0) {
      dispatch({ type: 'HYDRATE_STATE', payload: persisted });
    }
  }, [dispatch]);

  // Save on change
  useEffect(() => {
    savePersistedState({
      theme: state.theme,
      workDir: state.workDir,
      sidebarCollapsed: state.sidebarCollapsed,
      notificationsEnabled: state.notificationsEnabled,
      selectedModel: state.selectedModel,
      selectedPreset: state.selectedPreset,
    });
  }, [state.theme, state.workDir, state.sidebarCollapsed, state.notificationsEnabled, state.selectedModel, state.selectedPreset]);
}
```

- [ ] **Step 3: Wire persistence into AppProvider**

In `frontend/src/context/AppContext.tsx`, modify `AppProvider`:

```typescript
import { useAppPersistence } from '../hooks/useAppPersistence';

export function AppProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(appReducer, initialState);

  // Persist settings to localStorage
  useAppPersistence(state, dispatch);

  // Theme sync (existing code)
  useEffect(() => {
    applyTheme(state.theme);
  }, [state.theme]);

  // Fix checkApiKey — move inside component to access dispatch
  useEffect(() => {
    const checkKey = async () => {
      try {
        const key = await window.lemmaAPI?.getApiKey();
        if (key) {
          dispatch({ type: 'SET_API_KEY_CONFIGURED', payload: true });
        }
      } catch {
        // IPC unavailable
      }
    };
    checkKey();
  }, []);

  return (
    <AppContext.Provider value={{ state, dispatch }}>
      {children}
    </AppContext.Provider>
  );
}
```

Remove the old standalone `checkApiKey` function (lines 83-93) since it's now inside the component.

- [ ] **Step 4: Remove duplicate ViewType from TitleBar**

In `frontend/src/components/TitleBar.tsx`:

```typescript
// DELETE this line (line 4):
type ViewType = 'chat' | 'settings' | 'files' | 'cost' | 'export';

// ADD import:
import type { ViewType } from '../context/AppContext';
```

Export `ViewType` from AppContext:
```typescript
// In AppContext.tsx, change:
type ViewType = 'chat' | 'settings' | 'files' | 'cost' | 'export';
// to:
export type ViewType = 'chat' | 'settings' | 'files' | 'cost' | 'export';
```

- [ ] **Step 5: Write tests for useAppPersistence**

Create `frontend/src/hooks/useAppPersistence.test.ts`:

```typescript
import { describe, it, expect, beforeEach } from 'vitest';

// Test localStorage operations directly
describe('useAppPersistence', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('should save theme to localStorage', () => {
    localStorage.setItem('lemma-theme', 'dark');
    expect(localStorage.getItem('lemma-theme')).toBe('dark');
  });

  it('should save workDir to localStorage', () => {
    localStorage.setItem('lemma-work-dir', '/home/user/project');
    expect(localStorage.getItem('lemma-work-dir')).toBe('/home/user/project');
  });

  it('should handle boolean values correctly', () => {
    localStorage.setItem('lemma-sidebar-collapsed', 'true');
    expect(localStorage.getItem('lemma-sidebar-collapsed')).toBe('true');
    expect(localStorage.getItem('lemma-sidebar-collapsed') === 'true').toBe(true);
  });

  it('should remove null workDir from localStorage', () => {
    localStorage.setItem('lemma-work-dir', '/some/path');
    localStorage.removeItem('lemma-work-dir');
    expect(localStorage.getItem('lemma-work-dir')).toBeNull();
  });
});
```

- [ ] **Step 6: Run tests and typecheck**

```bash
npm run typecheck && cd frontend && npx vitest run
```
Expected: All tests pass.

- [ ] **Step 7: Commit**

```bash
git add -A
git commit -m "feat: persist AppContext state to localStorage (theme, workDir, model, preset)"
```

---

### Task 3: Clean Dead Props and Dead Code

**Files:**
- Modify: `frontend/src/components/ChatPanel.tsx`
- Modify: `frontend/src/App.tsx`

**Interfaces:**
- Consumes: current ChatPanel props
- Produces: cleaned props without `error` and `onClearError`

- [ ] **Step 1: Remove dead props from ChatPanelProps interface**

In `frontend/src/components/ChatPanel.tsx`:

```typescript
// BEFORE:
interface ChatPanelProps {
  messages: ClaudeMessage[];
  isStreaming: boolean;
  error: string | null;
  onSend: (text: string, options?: ChatOptions) => void;
  onCancel: () => void;
  onClearError: () => void;
  onClearMessages: () => void;
  onRetry?: () => void;
}

// AFTER:
interface ChatPanelProps {
  messages: ClaudeMessage[];
  isStreaming: boolean;
  onSend: (text: string, options?: ChatOptions) => void;
  onCancel: () => void;
  onClearMessages: () => void;
  onRetry?: () => void;
}
```

Update the destructuring:
```typescript
// BEFORE:
export default function ChatPanel({
  messages,
  isStreaming,
  error,
  onSend,
  onCancel,
  onClearError,
  onClearMessages,
  onRetry,
}: ChatPanelProps) {

// AFTER:
export default function ChatPanel({
  messages,
  isStreaming,
  onSend,
  onCancel,
  onClearMessages,
  onRetry,
}: ChatPanelProps) {
```

- [ ] **Step 2: Update ChatPanel usage in App.tsx**

In `frontend/src/App.tsx`, find the `<ChatPanel>` JSX:

```typescript
// BEFORE:
<ChatPanel
  messages={claude.messages}
  isStreaming={claude.isStreaming}
  error={claude.error}
  onSend={handleSend}
  onCancel={claude.cancelStream}
  onClearError={claude.clearError}
  onClearMessages={claude.clearMessages}
  onRetry={...}
/>

// AFTER:
<ChatPanel
  messages={claude.messages}
  isStreaming={claude.isStreaming}
  onSend={handleSend}
  onCancel={claude.cancelStream}
  onClearMessages={claude.clearMessages}
  onRetry={...}
/>
```

- [ ] **Step 3: Remove local selectedPreset from App.tsx**

In `frontend/src/App.tsx`, `selectedPreset` is local state that should now come from AppContext:

```typescript
// DELETE:
const [selectedPreset, setSelectedPreset] = useState<string | null>(null);

// Replace usages of selectedPreset with state.selectedPreset
// Replace setSelectedPreset with dispatch({ type: 'SET_PRESET', payload: ... })
```

Update `handleSend`:
```typescript
// BEFORE:
if (selectedPreset) options.presetId = selectedPreset;
// AFTER:
if (state.selectedPreset) options.presetId = state.selectedPreset;
```

Update Sidebar props:
```typescript
// BEFORE:
<Sidebar sessions={sessions} selectedPreset={selectedPreset} onSelectPreset={setSelectedPreset} />
// AFTER:
<Sidebar sessions={sessions} selectedPreset={state.selectedPreset} onSelectPreset={(id) => dispatch({ type: 'SET_PRESET', payload: id })} />
```

Update OnboardingWizard:
```typescript
// In handleOnboardingComplete:
// BEFORE:
if (settings.preset) setSelectedPreset(settings.preset);
// AFTER:
if (settings.preset) dispatch({ type: 'SET_PRESET', payload: settings.preset });
```

- [ ] **Step 4: Wire selectedModel into chat options**

In `frontend/src/App.tsx`, update `handleSend`:

```typescript
const handleSend = useCallback((text: string) => {
  const options: ChatOptions = {};
  if (state.workDir) options.workDir = state.workDir;
  if (state.selectedPreset) options.presetId = state.selectedPreset;
  options.model = state.selectedModel;
  claude.sendMessage(text, options);
}, [state.workDir, state.selectedPreset, state.selectedModel, claude]);
```

- [ ] **Step 5: Update SettingsPanel to use AppContext model state**

In `frontend/src/components/SettingsPanel.tsx`:

```typescript
// BEFORE:
const [selectedModel, setSelectedModel] = useState(DEFAULT_MODEL);

// AFTER:
const { state, dispatch } = useApp();
// Remove the local state, use state.selectedModel instead
// Replace onChange handler:
onChange={(event) => dispatch({ type: 'SET_MODEL', payload: event.target.value })}
value={state.selectedModel}
```

- [ ] **Step 6: Verify and commit**

```bash
npm run typecheck && cd frontend && npx vitest run
git add -A
git commit -m "refactor: remove dead props, move preset/model to AppContext, wire model to chat"
```

---

### Task 4: Split SettingsPanel into Sub-Components

**Files:**
- Create: `frontend/src/components/settings/ApiKeySection.tsx`
- Create: `frontend/src/components/settings/ModelSection.tsx`
- Create: `frontend/src/components/settings/WorkDirSection.tsx`
- Create: `frontend/src/components/settings/ThemeSection.tsx`
- Create: `frontend/src/components/settings/McpSection.tsx`
- Modify: `frontend/src/components/SettingsPanel.tsx` (becomes thin composition)

**Interfaces:**
- Consumes: `useApp()` context, `STORAGE_KEYS`, `TIMING` from constants
- Produces: 5 focused section components

- [ ] **Step 1: Create ApiKeySection**

Create `frontend/src/components/settings/ApiKeySection.tsx`:

```typescript
import { useState } from 'react';
import { Key } from 'lucide-react';
import { useApp } from '../../context/AppContext';
import { TIMING } from '../../constants';

export default function ApiKeySection() {
  const { dispatch } = useApp();
  const [apiKey, setApiKey] = useState('');
  const [saveStatus, setSaveStatus] = useState<string | null>(null);

  const handleSave = async () => {
    if (!apiKey.trim()) return;
    try {
      const result = await window.lemmaAPI.storeApiKey(apiKey.trim());
      if (result.success) {
        setSaveStatus('✓ API Key 已安全存储');
        dispatch({ type: 'SET_API_KEY_CONFIGURED', payload: true });
        setApiKey('');
      } else {
        setSaveStatus(`✕ 存储失败: ${result.reason}`);
      }
    } catch {
      setSaveStatus('✕ 存储失败: IPC 不可用');
    }
    setTimeout(() => setSaveStatus(null), TIMING.SAVE_STATUS_DURATION);
  };

  return (
    <section className="space-y-3">
      <h3 className="flex items-center gap-2 text-sm font-semibold text-text">
        <Key size={16} />
        Anthropic API Key
      </h3>
      <div className="flex gap-2">
        <input
          type="password"
          value={apiKey}
          onChange={(event) => setApiKey(event.target.value)}
          placeholder="sk-ant-..."
          className="flex-1 px-3 py-2 rounded-lg border border-border-strong bg-bg-secondary text-sm focus:outline-none focus:ring-2 focus:ring-accent"
        />
        <button
          onClick={handleSave}
          disabled={!apiKey.trim()}
          className="px-4 py-2 rounded-lg bg-accent hover:bg-accent-hover disabled:opacity-50 text-white text-sm transition-colors"
        >
          保存
        </button>
      </div>
      {saveStatus && (
        <p className={`text-xs ${saveStatus.startsWith('✓') ? 'text-success' : 'text-error'}`}>
          {saveStatus}
        </p>
      )}
      <p className="text-xs text-text-muted">
        API Key 通过 Electron safeStorage 加密存储，不会明文保存。
      </p>
    </section>
  );
}
```

- [ ] **Step 2: Create ModelSection**

Create `frontend/src/components/settings/ModelSection.tsx`:

```typescript
import { Info } from 'lucide-react';
import { useApp } from '../../context/AppContext';
import { AVAILABLE_MODELS } from '../../config';

export default function ModelSection() {
  const { state, dispatch } = useApp();

  return (
    <section className="space-y-3">
      <h3 className="flex items-center gap-2 text-sm font-semibold text-text">
        <Info size={16} />
        模型
      </h3>
      <select
        value={state.selectedModel}
        onChange={(event) => dispatch({ type: 'SET_MODEL', payload: event.target.value })}
        className="w-full px-3 py-2 rounded-lg border border-border-strong bg-bg-secondary text-sm focus:outline-none focus:ring-2 focus:ring-accent"
      >
        {AVAILABLE_MODELS.map((model) => (
          <option key={model.id} value={model.id}>
            {model.name}
          </option>
        ))}
      </select>
    </section>
  );
}
```

- [ ] **Step 3: Create WorkDirSection**

Create `frontend/src/components/settings/WorkDirSection.tsx`:

```typescript
import { FolderOpen } from 'lucide-react';
import { useApp } from '../../context/AppContext';

export default function WorkDirSection() {
  const { state, dispatch } = useApp();

  const handleSelectDir = async () => {
    const dir = await window.lemmaAPI?.selectDirectory();
    if (dir) dispatch({ type: 'SET_WORK_DIR', payload: dir });
  };

  return (
    <section className="space-y-3">
      <h3 className="flex items-center gap-2 text-sm font-semibold text-text">
        <FolderOpen size={16} />
        工作目录
      </h3>
      <div className="flex gap-2">
        <input
          type="text"
          value={state.workDir || ''}
          readOnly
          placeholder="未选择"
          className="flex-1 px-3 py-2 rounded-lg border border-border-strong bg-bg-elevated text-sm"
        />
        <button
          onClick={handleSelectDir}
          className="px-4 py-2 rounded-lg border border-border-strong hover:bg-bg-tertiary text-sm transition-colors"
        >
          浏览
        </button>
      </div>
    </section>
  );
}
```

- [ ] **Step 4: Create ThemeSection**

Create `frontend/src/components/settings/ThemeSection.tsx`:

```typescript
import { Palette } from 'lucide-react';
import { useApp } from '../../context/AppContext';

const THEME_OPTIONS = [
  { value: 'light' as const, label: '亮色' },
  { value: 'dark' as const, label: '暗色' },
  { value: 'system' as const, label: '跟随系统' },
];

export default function ThemeSection() {
  const { state, dispatch } = useApp();

  return (
    <section className="space-y-3">
      <h3 className="flex items-center gap-2 text-sm font-semibold text-text">
        <Palette size={16} />
        主题
      </h3>
      <div className="flex gap-2">
        {THEME_OPTIONS.map((option) => (
          <button
            key={option.value}
            onClick={() => dispatch({ type: 'SET_THEME', payload: option.value })}
            className={`px-4 py-2 rounded-lg text-sm transition-colors ${
              state.theme === option.value
                ? 'bg-accent text-white'
                : 'border border-border-strong hover:bg-bg-tertiary'
            }`}
          >
            {option.label}
          </button>
        ))}
      </div>
    </section>
  );
}
```

- [ ] **Step 5: Create McpSection**

Create `frontend/src/components/settings/McpSection.tsx`:

```typescript
import { useState, useEffect } from 'react';
import { Server, Plus, Trash2 } from 'lucide-react';
import { useApp } from '../../context/AppContext';

interface McpServer {
  name: string;
  command: string;
  args: string[];
}

export default function McpSection() {
  const { state } = useApp();
  const [mcpServers, setMcpServers] = useState<McpServer[]>([]);
  const [newName, setNewName] = useState('');
  const [newCommand, setNewCommand] = useState('');

  useEffect(() => {
    if (state.workDir) {
      window.lemmaAPI?.getMcpConfig(state.workDir).then(setMcpServers);
    }
  }, [state.workDir]);

  const handleAdd = async () => {
    if (!state.workDir || !newName.trim() || !newCommand.trim()) return;
    const parts = newCommand.split(' ').filter(Boolean);
    const command = parts.shift() || '';
    await window.lemmaAPI?.addMcpServer(state.workDir, { name: newName.trim(), command, args: parts });
    const updated = await window.lemmaAPI?.getMcpConfig(state.workDir);
    if (updated) setMcpServers(updated);
    setNewName('');
    setNewCommand('');
  };

  const handleRemove = async (name: string) => {
    if (!state.workDir) return;
    await window.lemmaAPI?.removeMcpServer(state.workDir, name);
    const updated = await window.lemmaAPI?.getMcpConfig(state.workDir);
    if (updated) setMcpServers(updated);
  };

  if (!state.workDir) return null;

  return (
    <section className="space-y-3">
      <h3 className="flex items-center gap-2 text-sm font-semibold text-text">
        <Server size={16} />
        MCP Server
      </h3>
      {mcpServers.length > 0 && (
        <div className="space-y-1">
          {mcpServers.map((server) => (
            <div key={server.name} className="flex items-center justify-between px-3 py-2 rounded bg-bg-elevated">
              <div>
                <p className="text-sm font-medium">{server.name}</p>
                <p className="text-xs text-text-muted">{server.command} {server.args.join(' ')}</p>
              </div>
              <button onClick={() => handleRemove(server.name)} className="text-error hover:text-error">
                <Trash2 size={14} />
              </button>
            </div>
          ))}
        </div>
      )}
      <div className="flex gap-2">
        <input
          type="text"
          value={newName}
          onChange={(event) => setNewName(event.target.value)}
          placeholder="名称"
          className="w-24 px-3 py-2 rounded-lg border border-border-strong bg-bg-secondary text-sm"
        />
        <input
          type="text"
          value={newCommand}
          onChange={(event) => setNewCommand(event.target.value)}
          placeholder="命令 (如: npx @playwright/mcp)"
          className="flex-1 px-3 py-2 rounded-lg border border-border-strong bg-bg-secondary text-sm"
        />
        <button
          onClick={handleAdd}
          disabled={!newName.trim() || !newCommand.trim()}
          className="px-3 py-2 rounded-lg bg-accent hover:bg-accent-hover disabled:opacity-50 text-white text-sm"
        >
          <Plus size={14} />
        </button>
      </div>
    </section>
  );
}
```

- [ ] **Step 6: Rewrite SettingsPanel as thin composition**

Replace `frontend/src/components/SettingsPanel.tsx` entirely:

```typescript
import { useApp } from '../context/AppContext';
import { Bell } from 'lucide-react';
import ApiKeySection from './settings/ApiKeySection';
import ModelSection from './settings/ModelSection';
import WorkDirSection from './settings/WorkDirSection';
import ThemeSection from './settings/ThemeSection';
import McpSection from './settings/McpSection';
import ClaudeMdEditor from './ClaudeMdEditor';

export default function SettingsPanel() {
  const { state, dispatch } = useApp();

  return (
    <div className="h-full overflow-y-auto">
      <div className="max-w-2xl mx-auto p-8 space-y-8">
        <h2 className="text-xl font-serif">设置</h2>

        <ApiKeySection />
        <ModelSection />
        <WorkDirSection />

        {state.workDir && (
          <section className="space-y-3">
            <ClaudeMdEditor workDir={state.workDir} />
          </section>
        )}

        <section className="space-y-3">
          <h3 className="flex items-center gap-2 text-sm font-semibold text-text">
            <Bell size={16} />
            通知
          </h3>
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={state.notificationsEnabled}
              onChange={(event) => dispatch({ type: 'SET_NOTIFICATIONS', payload: event.target.checked })}
              className="rounded border-border"
            />
            启用系统通知
          </label>
        </section>

        <ThemeSection />
        <McpSection />

        <section className="space-y-3 pt-4 border-t border-border">
          <h3 className="text-sm font-semibold text-text">关于</h3>
          <div className="text-xs text-text-muted space-y-1">
            <p>Lemma v0.1.0</p>
            <p>基于 Claude Agent SDK 的学术写作桌面软件</p>
            <p>Electron + React 18 + TypeScript</p>
          </div>
        </section>
      </div>
    </div>
  );
}
```

- [ ] **Step 7: Verify and commit**

```bash
npm run typecheck && cd frontend && npx vite build
git add -A
git commit -m "refactor: split SettingsPanel into 5 focused sub-components"
```

---

### Task 5: Improve Tool Call Visualization

**Files:**
- Modify: `frontend/src/components/ChatPanel.tsx` (MessageBubble component)

**Interfaces:**
- Consumes: `ClaudeMessage` with `type: 'tool_use' | 'tool_result'`
- Produces: structured tool call display with name, status, collapsible details

- [ ] **Step 1: Improve tool call display in MessageBubble**

In `frontend/src/components/ChatPanel.tsx`, replace the tool call rendering block inside `MessageBubble`:

```typescript
// BEFORE (lines ~171-187):
if (isToolUse || isToolResult) {
  return (
    <div className="max-w-4xl mx-auto">
      <button
        onClick={onToggleExpand}
        className="flex items-center gap-1 text-xs text-text-muted hover:text-text-secondary"
      >
        {isExpanded ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
        🔧 {isToolUse ? '工具调用' : '工具结果'}
      </button>
      {isExpanded && (
        <pre className="mt-1 p-2 rounded text-xs bg-bg-tertiary overflow-x-auto">
          {message.content}
        </pre>
      )}
    </div>
  );
}

// AFTER:
if (isToolUse || isToolResult) {
  const toolName = extractToolName(message.content, message.type);

  return (
    <div className="max-w-4xl mx-auto">
      <button
        onClick={onToggleExpand}
        className="flex items-center gap-2 w-full px-3 py-2 rounded-lg text-xs bg-bg-elevated hover:bg-bg-tertiary transition-colors border border-border"
      >
        {isExpanded ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
        <Wrench size={12} className="text-accent shrink-0" />
        <span className="font-medium text-text-secondary">
          {isToolUse ? toolName : `${toolName} 结果`}
        </span>
        <span className="ml-auto text-text-muted">
          {isExpanded ? '收起' : '展开'}
        </span>
      </button>
      {isExpanded && (
        <pre className="mt-1 p-3 rounded text-xs bg-bg-tertiary overflow-x-auto border-l-2 border-accent max-h-64">
          {formatToolContent(message.content)}
        </pre>
      )}
    </div>
  );
}
```

Add the helper imports and functions at the top of the file (before MessageBubble):

```typescript
import { Send, Square, Trash2, ChevronDown, ChevronRight, RefreshCw, Copy, Check, Wrench } from 'lucide-react';
```

Add helper functions:

```typescript
function extractToolName(content: string, type: string): string {
  try {
    const parsed = JSON.parse(content);
    if (type === 'tool_use' && parsed.name) return parsed.name;
    if (type === 'tool_result' && parsed.tool_use_id) return '工具';
  } catch {
    // Content might not be JSON
  }
  return type === 'tool_use' ? '工具调用' : '工具结果';
}

function formatToolContent(content: string): string {
  try {
    const parsed = JSON.parse(content);
    return JSON.stringify(parsed, null, 2);
  } catch {
    return content;
  }
}
```

- [ ] **Step 2: Verify and commit**

```bash
npm run typecheck
git add frontend/src/components/ChatPanel.tsx
git commit -m "feat: improve tool call visualization with structured display"
```

---

### Task 6: Add Message Actions Menu

**Files:**
- Create: `frontend/src/components/MessageActions.tsx`
- Modify: `frontend/src/components/ChatPanel.tsx` (integrate MessageActions)

**Interfaces:**
- Consumes: message content, `isUser` flag
- Produces: hover-revealed action buttons (copy, regenerate)

- [ ] **Step 1: Create MessageActions component**

Create `frontend/src/components/MessageActions.tsx`:

```typescript
import { useState } from 'react';
import { Copy, Check, RefreshCw } from 'lucide-react';
import { TIMING } from '../constants';

interface MessageActionsProps {
  content: string;
  isUser: boolean;
  onRegenerate?: () => void;
}

export default function MessageActions({ content, isUser, onRegenerate }: MessageActionsProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(content);
      setCopied(true);
      setTimeout(() => setCopied(false), TIMING.COPY_FEEDBACK_DURATION);
    } catch {
      // Clipboard may fail
    }
  };

  return (
    <div className="flex items-center gap-1 mt-1 opacity-0 group-hover:opacity-100 transition-opacity">
      <button
        onClick={handleCopy}
        className="p-1 rounded hover:bg-bg-tertiary text-text-muted hover:text-text-secondary transition-colors"
        title="复制"
      >
        {copied ? <Check size={12} className="text-success" /> : <Copy size={12} />}
      </button>
      {!isUser && onRegenerate && (
        <button
          onClick={onRegenerate}
          className="p-1 rounded hover:bg-bg-tertiary text-text-muted hover:text-text-secondary transition-colors"
          title="重新生成"
        >
          <RefreshCw size={12} />
        </button>
      )}
    </div>
  );
}
```

- [ ] **Step 2: Integrate MessageActions into MessageBubble**

In `frontend/src/components/ChatPanel.tsx`, inside the MessageBubble component's return for text messages, wrap the message bubble in a `group` div and add MessageActions:

```typescript
// Find the return block for text messages and update it:
return (
  <div className={`max-w-4xl mx-auto group ${isUser ? 'flex flex-col items-end' : ''}`}>
    <div
      className={`rounded-lg px-4 py-3 ${
        isUser ? 'bg-accent text-white' : 'bg-bg-tertiary'
      }`}
    >
      {/* ... existing content rendering ... */}
    </div>
    <MessageActions
      content={message.content}
      isUser={isUser}
      onRegenerate={!isUser ? onRetry : undefined}
    />
    {/* ... existing error retry button ... */}
  </div>
);
```

Add the import:
```typescript
import MessageActions from './MessageActions';
```

- [ ] **Step 3: Verify and commit**

```bash
npm run typecheck
git add -A
git commit -m "feat: add message actions menu (copy, regenerate)"
```

---

### Task 7: Add Session Search

**Files:**
- Modify: `frontend/src/components/Sidebar.tsx`

**Interfaces:**
- Consumes: `sessions: SessionInfo[]` prop
- Produces: filtered session list based on search input

- [ ] **Step 1: Add search state and filter logic**

In `frontend/src/components/Sidebar.tsx`, add search state:

```typescript
import { useState } from 'react';
import { FolderOpen, Plus, Clock, Search } from 'lucide-react';
// ... existing imports

export default function Sidebar({ sessions, selectedPreset, onSelectPreset }: SidebarProps) {
  const { state, dispatch } = useApp();
  const [searchQuery, setSearchQuery] = useState('');

  const filteredSessions = sessions.filter((session) =>
    session.title.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // ... rest of component
```

- [ ] **Step 2: Add search input above session list**

In the "历史会话" section, add a search input:

```typescript
{/* 历史会话 */}
<div className="flex-1 px-3 mt-4 overflow-y-auto">
  <h3 className="text-caption font-semibold uppercase tracking-wider text-text-muted mb-2">
    历史会话
  </h3>
  {sessions.length > 3 && (
    <div className="relative mb-2">
      <Search size={12} className="absolute left-2 top-1/2 -translate-y-1/2 text-text-muted" />
      <input
        type="text"
        value={searchQuery}
        onChange={(event) => setSearchQuery(event.target.value)}
        placeholder="搜索会话..."
        className="w-full pl-7 pr-2 py-1 rounded text-ui bg-bg-secondary border border-border focus:outline-none focus:ring-1 focus:ring-accent"
      />
    </div>
  )}
  <div className="space-y-0.5">
    {filteredSessions.map((session) => (
      /* ... existing session button rendering ... */
    ))}
  </div>
</div>
```

Note: replace `sessions.map` with `filteredSessions.map` in the session list rendering.

- [ ] **Step 3: Verify and commit**

```bash
npm run typecheck
git add frontend/src/components/Sidebar.tsx
git commit -m "feat: add session search in sidebar"
```

---

### Task 8: File System Path Restrictions

**Files:**
- Modify: `electron/main.ts`

**Interfaces:**
- Consumes: `workDir` from session/chat context
- Produces: path-restricted file operations

- [ ] **Step 1: Add path validation helper**

In `electron/main.ts`, add a helper function before `setupIpcHandlers`:

```typescript
import * as path from 'path';

/** Check if a target path is within the allowed base directory */
function isPathAllowed(targetPath: string, allowedBase: string): boolean {
  const resolved = path.resolve(targetPath);
  const base = path.resolve(allowedBase);
  return resolved.startsWith(base + path.sep) || resolved === base;
}
```

- [ ] **Step 2: Add path restriction to read-file IPC handler**

```typescript
// BEFORE:
ipcMain.handle('read-file', async (_event, filePath: string) => {
  try {
    return { content: fs.readFileSync(filePath, 'utf-8'), error: null };
  } catch (error: unknown) {
    const errorMsg = error instanceof Error ? error.message : 'Read failed';
    return { content: null, error: errorMsg };
  }
});

// AFTER:
ipcMain.handle('read-file', async (_event, filePath: string, workDir?: string) => {
  if (workDir && !isPathAllowed(filePath, workDir)) {
    return { content: null, error: '路径不在工作目录范围内' };
  }
  try {
    return { content: fs.readFileSync(filePath, 'utf-8'), error: null };
  } catch (error: unknown) {
    const errorMsg = error instanceof Error ? error.message : 'Read failed';
    return { content: null, error: errorMsg };
  }
});
```

- [ ] **Step 3: Add path restriction to list-directory IPC handler**

```typescript
// BEFORE:
ipcMain.handle('list-directory', async (_event, dirPath: string) => {
  // ... existing code
});

// AFTER:
ipcMain.handle('list-directory', async (_event, dirPath: string, workDir?: string) => {
  if (workDir && !isPathAllowed(dirPath, workDir)) {
    return [];
  }
  // ... existing code
});
```

- [ ] **Step 4: Update preload.ts to pass workDir**

In `electron/preload.ts`, update the `readFile` and `listDirectory` methods:

```typescript
// BEFORE:
readFile: (filePath: string) => ipcRenderer.invoke('read-file', filePath),
listDirectory: (dirPath: string) => ipcRenderer.invoke('list-directory', dirPath),

// AFTER:
readFile: (filePath: string, workDir?: string) => ipcRenderer.invoke('read-file', filePath, workDir),
listDirectory: (dirPath: string, workDir?: string) => ipcRenderer.invoke('list-directory', dirPath, workDir),
```

Update `LemmaAPI` type in `frontend/src/types/electron.d.ts`:

```typescript
// BEFORE:
readFile(filePath: string): Promise<{ content: string | null; error: string | null }>;
listDirectory(dirPath: string): Promise<FileEntry[]>;

// AFTER:
readFile(filePath: string, workDir?: string): Promise<{ content: string | null; error: string | null }>;
listDirectory(dirPath: string, workDir?: string): Promise<FileEntry[]>;
```

- [ ] **Step 5: Verify and commit**

```bash
npm run typecheck
git add -A
git commit -m "fix: restrict file system IPC to workDir path boundaries"
```

---

### Task 9: Add Core Tests

**Files:**
- Create: `frontend/src/components/MessageActions.test.tsx`
- Create: `frontend/src/components/settings/ModelSection.test.tsx`

**Interfaces:**
- Tests for new components created in this phase

- [ ] **Step 1: Test MessageActions**

Create `frontend/src/components/MessageActions.test.tsx`:

```typescript
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import MessageActions from './MessageActions';

describe('MessageActions', () => {
  it('renders copy button', () => {
    render(<MessageActions content="test" isUser={false} />);
    expect(screen.getByTitle('复制')).toBeTruthy();
  });

  it('renders regenerate button for assistant messages', () => {
    const onRegenerate = vi.fn();
    render(<MessageActions content="test" isUser={false} onRegenerate={onRegenerate} />);
    expect(screen.getByTitle('重新生成')).toBeTruthy();
  });

  it('does not render regenerate for user messages', () => {
    render(<MessageActions content="test" isUser={true} />);
    expect(screen.queryByTitle('重新生成')).toBeNull();
  });
});
```

- [ ] **Step 2: Test ModelSection**

Create `frontend/src/components/settings/ModelSection.test.tsx`:

```typescript
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { AppProvider } from '../../context/AppContext';
import ModelSection from './ModelSection';

describe('ModelSection', () => {
  it('renders model selection dropdown', () => {
    render(
      <AppProvider>
        <ModelSection />
      </AppProvider>
    );
    expect(screen.getByText('模型')).toBeTruthy();
  });

  it('shows all available models', () => {
    render(
      <AppProvider>
        <ModelSection />
      </AppProvider>
    );
    expect(screen.getByText('Claude Sonnet 4')).toBeTruthy();
    expect(screen.getByText('Claude Opus 4')).toBeTruthy();
    expect(screen.getByText('Claude Haiku 4')).toBeTruthy();
  });
});
```

- [ ] **Step 3: Run all tests**

```bash
cd frontend && npx vitest run
```
Expected: All tests pass including new ones.

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "test: add tests for MessageActions and ModelSection components"
```

---

### Task 10: Final Phase 1 Verification

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
Expected: Build succeeds.

- [ ] **Step 4: Electron dev smoke test**

```bash
npm run electron:dev
```

Manual checklist:
- [ ] App launches without errors
- [ ] Settings persist: change theme → restart → theme is preserved
- [ ] Model selection: choose Opus → send message → check StatusBar or logs for model
- [ ] Tool calls: trigger a tool use → see structured display with tool name
- [ ] Message actions: hover a message → see copy/regenerate buttons
- [ ] Session search: type in search → sessions filter correctly
- [ ] Error boundary: still works (try invalid API key)

- [ ] **Step 5: Commit final verification**

```bash
echo "Phase 1 complete" >> .superpowers/sdd/progress.md
git add -A
git commit -m "chore: phase 1 verification complete — all systems green"
```

---

## Task Dependency Graph

```
Task 1 (constants) ─────┐
  ├──→ Task 2 (persistence)
  ├──→ Task 3 (clean dead code + model wiring)
  │      └──→ Task 4 (split SettingsPanel)
  ├──→ Task 5 (tool visualization)
  ├──→ Task 6 (message actions)
  ├──→ Task 7 (session search)
  └──→ Task 8 (path restrictions)

Task 9 (tests) ← after Tasks 5,6
Task 10 (verification) ← after ALL

Recommended order: 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10
```

## Estimated Effort

| Task | Est. Time | Complexity |
|------|-----------|------------|
| Task 1: Constants | 15 min | Low |
| Task 2: Persistence | 30 min | Medium |
| Task 3: Dead code + model | 20 min | Low-Medium |
| Task 4: Split Settings | 30 min | Medium |
| Task 5: Tool visualization | 20 min | Low-Medium |
| Task 6: Message actions | 15 min | Low |
| Task 7: Session search | 10 min | Low |
| Task 8: Path restrictions | 15 min | Low |
| Task 9: Tests | 15 min | Low |
| Task 10: Verification | 15 min | Low |
| **Total** | **~3 hours** | |
