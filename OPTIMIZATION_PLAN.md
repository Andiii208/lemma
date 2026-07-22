# Lemma 优化计划（审计修订版）

> **文档用途**：AI 可直接执行的详细优化计划
> **创建日期**：2026-07-07
> **前置文档**：`DEVELOPMENT_PLAN.md`（v0.1.0 → v1.0.0 四阶段开发）
> **审计来源**：3 个并行审计 Agent（Electron 层 / 前端层 / 配置 CI 层）
> **预估总工期**：4-5 周（单人开发）

---

## 审计摘要

| 类别 | 数量 | 说明 |
|------|------|------|
| 🔴 Critical | 9 | 阻断功能，导致崩溃或功能失效 |
| 🟡 Important | 15 | 方案要求但未实现的功能 |
| 🟢 Minor | 8 | 改进项 |
| ✅ 已验证正确 | 30 | 确认按方案正确实现 |

---

## 四 Sprint 实施路线

```
Sprint 0 (2天)      Sprint 1 (1周)       Sprint 2 (1.5周)      Sprint 3 (1.5周)
紧急修复       ──→  核心功能补全   ──→   功能增强      ──→   质量保障
Critical ×9        集成+Bug ×8          增强 ×7              测试+清理 ×8
     │                  │                     │                    │
     ▼                  ▼                     ▼                    ▼
  可启动运行         预设+组件联通         完整功能体验          生产就绪
```

---

## Sprint 0：紧急修复（2 天）

> **目标**：让项目可以正常启动和运行
> **完成标准**：`npm run typecheck` 零错误 + `npm run lint` 通过 + Electron 窗口可打开

---

### Task 0.1：生成 package-lock.json

**问题**：根目录无 lock 文件，CI 中 `npm ci` 直接报错
**影响**：CI 三个 job 全部失败
**文件**：根目录 `package.json`

**修复步骤**：
```bash
# 根目录执行
npm install
```

**验证**：`package-lock.json` 存在，`npm ci` 可执行

**预估工时**：10min

---

### Task 0.2：修复 ESLint 版本兼容性

**问题**：`eslint@^9.0.0` 要求 flat config（`eslint.config.js`），但项目使用旧格式 `.eslintrc.json`。且 `--ext` 标志在 ESLint 9 已废弃
**影响**：`npm run lint` 必定崩溃
**文件**：`package.json`, `frontend/.eslintrc.json`

**修复方案**：降级 ESLint 到 v8（最简方案）

```json
// package.json — 修改 devDependencies
"eslint": "^8.57.0"
```

同时修改 lint 脚本，因为旧的 `.eslintrc.json` 在 `frontend/` 目录下，需要指向它：

```json
"lint": "eslint frontend/src/ electron/ --ext .ts,.tsx --config frontend/.eslintrc.json"
```

**验证**：`npm run lint` 执行成功（或仅有 warning，无 error）

**预估工时**：15min

---

### Task 0.3：修复 electron:dev 脚本 — 编译 Electron TypeScript

**问题**：`electron .` 加载 `dist-electron/main.js`，但脚本从未调用 `tsc` 编译 Electron 代码
**影响**：`npm run electron:dev` 崩溃（dist-electron/ 不存在）
**文件**：`package.json`

**修复**：

```json
"electron:dev": "concurrently \"vite --root frontend\" \"tsc -p tsconfig.electron.json --watch\" \"wait-on http://localhost:5173 dist-electron/main.js && electron .\"",
```

> 加入 `tsc --watch` 持续编译 + `wait-on` 同时等待 Vite 和 tsc 完成

**验证**：`npm run electron:dev` 可打开 Electron 窗口

**预估工时**：15min

---

### Task 0.4：接通自动更新前后端

**问题**：三重断裂 — ① main.ts 未调用 setupAutoUpdater ② electron-updater 不在依赖 ③ preload 未暴露 IPC
**影响**：自动更新功能完全不工作
**文件**：`package.json`, `electron/main.ts`, `electron/preload.ts`

**步骤 1**：添加依赖

```json
// package.json devDependencies
"electron-updater": "^6.3.0"
```

**步骤 2**：main.ts 中调用初始化

```typescript
// electron/main.ts — 在 setupIpcHandlers() 之后添加
import { setupAutoUpdater } from './updater';

app.whenReady().then(() => {
  createWindow();
  sessionManager = new SessionManager(app.getPath('userData'));
  claudeBridge = new ClaudeSdkBridge(mainWindow!, sessionManager);
  setupIpcHandlers();
  setupAutoUpdater(mainWindow!);  // ← 新增
});
```

**步骤 3**：preload.ts 暴露更新 IPC

```typescript
// electron/preload.ts — 在 lemmaAPI 对象中添加
onUpdateAvailable: (callback: (info: unknown) => void) => {
  const handler = (_event: unknown, info: unknown) => callback(info);
  ipcRenderer.on('update-available', handler);
  return () => ipcRenderer.removeListener('update-available', handler);
},
onUpdateDownloaded: (callback: (info: unknown) => void) => {
  const handler = (_event: unknown, info: unknown) => callback(info);
  ipcRenderer.on('update-downloaded', handler);
  return () => ipcRenderer.removeListener('update-downloaded', handler);
},
downloadUpdate: () => ipcRenderer.invoke('download-update'),
installUpdate: () => ipcRenderer.invoke('install-update'),
```

**步骤 4**：main.ts 添加 IPC handlers

```typescript
ipcMain.handle('download-update', async () => {
  const { downloadUpdate } = require('./updater');
  downloadUpdate();
});
ipcMain.handle('install-update', async () => {
  const { installUpdate } = require('./updater');
  installUpdate();
});
```

**步骤 5**：更新 `electron.d.ts` 类型定义

```typescript
// 在 LemmaAPI 接口中添加
onUpdateAvailable(callback: (info: unknown) => void): () => void;
onUpdateDownloaded(callback: (info: unknown) => void): () => void;
downloadUpdate(): Promise<void>;
installUpdate(): Promise<void>;
```

**验证**：Electron 启动后无 updater 相关报错

**预估工时**：30min

---

### Task 0.5：修复 Sidebar 预设按钮 — 添加 onClick 联动

**问题**：预设按钮没有绑定 onClick，App.tsx 的 selectedPreset 状态也未与 Sidebar 联动
**影响**：用户无法切换预设
**文件**：`frontend/src/components/Sidebar.tsx`, `frontend/src/App.tsx`

**步骤 1**：修改 Sidebar props 接口

```typescript
// Sidebar.tsx
interface SidebarProps {
  sessions: SessionInfo[];
  selectedPreset: string | null;
  onSelectPreset: (presetId: string) => void;
}
```

**步骤 2**：给预设按钮绑定 onClick

```typescript
// Sidebar.tsx — 预设列表区域
{PRESETS.map((preset) => (
  <button
    key={preset.id}
    onClick={() => onSelectPreset(preset.id)}
    className={`flex items-center gap-2 w-full px-3 py-1.5 rounded text-xs transition-colors ${
      selectedPreset === preset.id
        ? 'bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300'
        : 'text-dark-600 dark:text-dark-300 hover:bg-dark-100 dark:hover:bg-dark-700'
    }`}
    title={preset.description}
  >
    <span className="w-1.5 h-1.5 rounded-full bg-primary-400" />
    {preset.name}
  </button>
))}
```

**步骤 3**：App.tsx 传递 props

```tsx
<Sidebar
  sessions={sessions}
  selectedPreset={selectedPreset}
  onSelectPreset={setSelectedPreset}
/>
```

**验证**：点击预设按钮后高亮显示，发送消息时 systemPrompt 正确传递

**预估工时**：20min

---

### Task 0.6：修复 FileBrowser 首次加载为空

**问题**：useEffect 中调用 loadDirectory 但返回值被丢弃，tree 状态永远不被设置
**影响**：文件浏览器首次打开为空
**文件**：`frontend/src/components/FileBrowser.tsx`

**修复**：

```typescript
// FileBrowser.tsx — 修改 useEffect
useEffect(() => {
  if (workDir) {
    loadDirectory(workDir, []).then((nodes) => setTree(nodes));
  }
}, [workDir]);
```

**验证**：选择工作目录后文件树自动加载

**预估工时**：5min

---

### Task 0.7：修复 OnboardingWizard 完成后设置丢失

**问题**：引导完成后 workDir 和 selectedPreset 未回传给 AppContext
**影响**：用户在引导中选择的配置全部丢失
**文件**：`frontend/src/components/OnboardingWizard.tsx`, `frontend/src/App.tsx`

**步骤 1**：修改 OnboardingWizard 的 onComplete 回调签名

```typescript
// OnboardingWizard.tsx
interface OnboardingWizardProps {
  onComplete: (settings: { workDir: string | null; preset: string | null }) => void;
}
```

在 `done` 步骤调用：

```typescript
// OnboardingWizard.tsx — handleComplete
const handleComplete = () => {
  onComplete({ workDir, preset: selectedPreset });
};
```

**步骤 2**：App.tsx 处理回调

```tsx
// App.tsx
const handleOnboardingComplete = (settings: { workDir: string | null; preset: string | null }) => {
  if (settings.workDir) {
    dispatch({ type: 'SET_WORK_DIR', payload: settings.workDir });
  }
  if (settings.preset) {
    setSelectedPreset(settings.preset);
  }
  setShowOnboarding(false);
};

// 渲染
<OnboardingWizard onComplete={handleOnboardingComplete} />
```

**验证**：引导完成后工作目录和预设正确显示在 UI 中

**预估工时**：20min

---

### Task 0.8：核对并修正 SDK query API 签名

**问题**：`sdk.query({ prompt, options })` 的参数名和结构可能与实际 SDK API 不匹配
**影响**：运行时调用 Claude 时崩溃
**文件**：`electron/claude-sdk-bridge.ts`

**修复步骤**：

1. 安装 SDK 后查看类型定义：
```bash
npm install @anthropic-ai/claude-agent-sdk
cat node_modules/@anthropic-ai/claude-agent-sdk/dist/index.d.ts
```

2. 根据实际 API 修正 `sendMessage` 方法中的 `sdk.query()` 调用参数

3. 如果 SDK 使用不同 API（如 `createConversation` + `sendMessage`），重写 bridge 的调用逻辑

**验证**：输入消息后能成功调用 Claude 并收到流式响应

**预估工时**：1h

---

### Task 0.9：修复 listSessions JSON 解析无容错

**问题**：sessions 目录中若有损坏的 JSON 文件，JSON.parse 抛异常导致整个列表加载失败
**影响**：会话列表功能崩溃
**文件**：`electron/session-manager.ts`

**修复**：

```typescript
// session-manager.ts — 修改 listSessions 方法
listSessions(): SessionInfo[] {
  return fs.readdirSync(this.sessionsDir)
    .filter((fileName) => fileName.endsWith('.json'))
    .map((fileName) => {
      try {
        const filePath = path.join(this.sessionsDir, fileName);
        return JSON.parse(fs.readFileSync(filePath, 'utf-8')) as SessionInfo;
      } catch {
        return null;
      }
    })
    .filter((session): session is SessionInfo => session !== null)
    .sort((sessionA, sessionB) =>
      sessionB.lastUsedAt.localeCompare(sessionA.lastUsedAt)
    );
}
```

**验证**：在 sessions 目录放入损坏 JSON 文件后 listSessions 仍正常返回

**预估工时**：10min

---

### Sprint 0 里程碑检查清单

- [ ] `package-lock.json` 已生成
- [ ] `npm run lint` 通过
- [ ] `npm run electron:dev` 可打开窗口
- [ ] 自动更新 IPC 已接通
- [ ] 预设按钮可点击切换
- [ ] 文件浏览器首次加载正确
- [ ] 引导完成后设置保留
- [ ] SDK API 签名已校准
- [ ] session 列表容错

---

## Sprint 1：核心功能补全（1 周）

> **目标**：补全预设系统、组件集成、Bug 修复
> **完成标准**：所有核心交互流程可用

---

### Task 1.1：实现 UltraMath Prompt 复用

**问题**：计划要求 math-modeling 预设使用 `systemPromptSource: 'ultramath'` 并读取外部 .md 文件，实际全部 5 个预设都是 builtin
**文件**：`electron/presets/index.ts`, `electron/main.ts`

**修复步骤**：

```typescript
// electron/presets/index.ts — 修改 math-modeling 预设
{
  id: 'math-modeling',
  name: '数学建模',
  description: '数学建模竞赛全自动求解',
  systemPromptSource: 'ultramath',
  ultramathAgentPath: '../数学建模/.claude/agents/coordinator.md',
  icon: '📐',
},
```

在 main.ts 的 `chat` handler 中添加预设解析逻辑：

```typescript
// electron/main.ts — chat handler 中
ipcMain.handle('chat', async (_event, message: string, options?: ChatOptions) => {
  let systemPrompt = options?.systemPrompt;

  // 如果指定了 presetId，查找预设并读取 systemPrompt
  if (options?.presetId) {
    const preset = getPresetById(options.presetId);
    if (preset) {
      if (preset.systemPromptSource === 'ultramath' && preset.ultramathAgentPath) {
        // 读取外部 .md 文件作为 systemPrompt
        const fs = require('fs');
        const resolvedPath = path.resolve(__dirname, preset.ultramathAgentPath);
        if (fs.existsSync(resolvedPath)) {
          systemPrompt = fs.readFileSync(resolvedPath, 'utf-8');
        }
      } else if (preset.systemPrompt) {
        systemPrompt = preset.systemPrompt;
      }
    }
  }

  return claudeBridge?.sendMessage(message, { ...options, systemPrompt });
});
```

**预估工时**：1h

---

### Task 1.2：集成 ClaudeMdEditor 到 SettingsPanel

**问题**：ClaudeMdEditor 组件已实现但未集成，用户无法触达
**文件**：`frontend/src/components/SettingsPanel.tsx`

**修复**：

```typescript
// SettingsPanel.tsx — 导入并使用 ClaudeMdEditor
import ClaudeMdEditor from './ClaudeMdEditor';

// 在"工作目录"section 之后添加
{state.workDir && (
  <section className="space-y-3">
    <ClaudeMdEditor workDir={state.workDir} />
  </section>
)}
```

**预估工时**：10min

---

### Task 1.3：修复 RetryBanner 内存泄漏

**问题**：使用 useState 注册事件监听器，cleanup 不会执行
**文件**：`frontend/src/components/RetryBanner.tsx`

**修复**：

```typescript
// RetryBanner.tsx — 将事件监听从 useState 改为 useEffect
import { useState, useEffect } from 'react';

export default function RetryBanner(...) {
  const [retryCount, setRetryCount] = useState(0);
  const [isRetrying, setIsRetrying] = useState(false);
  const [isOnline, setIsOnline] = useState(navigator.onLine);

  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  // ... 其余不变
}
```

**预估工时**：10min

---

### Task 1.4：修复 version-checker 始终返回 unknown

**问题**：SDK 可能不导出 `version` 字段
**文件**：`electron/version-checker.ts`

**修复**：

```typescript
// version-checker.ts — 改为从 package.json 读取版本
export async function checkSdkVersion(): Promise<VersionInfo> {
  try {
    // 优先尝试读取 SDK 的 package.json
    const sdkPackageJson = require('@anthropic-ai/claude-agent-sdk/package.json');
    const sdkVersion = sdkPackageJson.version ?? 'unknown';
    const supported = isVersionInRange(sdkVersion, SUPPORTED_RANGE.min, SUPPORTED_RANGE.max);

    return {
      sdkVersion,
      supported,
      warning: supported ? null : `Agent SDK 版本 ${sdkVersion} 不在支持范围...`,
    };
  } catch {
    return { sdkVersion: 'not-installed', supported: false, warning: 'Claude Agent SDK 未安装' };
  }
}
```

**预估工时**：15min

---

### Task 1.5：注册 send 快捷键 + Electron 全局快捷键

**问题**：Ctrl+Enter 发送消息的快捷键定义了但未注册
**文件**：`frontend/src/App.tsx`, `electron/main.ts`

**步骤 1**：App.tsx 中注册 send 快捷键

```typescript
// App.tsx — useKeyboardShortcuts 调用中添加 send
useKeyboardShortcuts([
  // ... 已有的快捷键
  {
    ...DEFAULT_SHORTCUTS.send,
    action: () => {
      // 触发当前输入框的发送
      document.dispatchEvent(new CustomEvent('send-message'));
    },
  },
]);
```

**步骤 2**：ChatPanel 监听 send-message 事件

```typescript
// ChatPanel.tsx — useEffect 中
useEffect(() => {
  const handler = () => handleSend();
  document.addEventListener('send-message', handler);
  return () => document.removeEventListener('send-message', handler);
}, [handleSend]);
```

**步骤 3**：Electron 全局快捷键（可选）

```typescript
// electron/main.ts — app.whenReady() 中
import { globalShortcut } from 'electron';

app.whenReady().then(() => {
  // ... 现有代码
  globalShortcut.register('CommandOrControl+Shift+L', () => {
    mainWindow?.show();
    mainWindow?.focus();
  });
});
```

**预估工时**：30min

---

### Task 1.6：添加长任务完成通知 + 通知开关

**问题**：对话完成时无系统通知，设置面板无通知开关
**文件**：`frontend/src/hooks/useClaude.ts`, `frontend/src/components/SettingsPanel.tsx`, `frontend/src/context/AppContext.tsx`

**步骤 1**：AppContext 添加通知开关状态

```typescript
// AppContext.tsx — AppState 中添加
notificationsEnabled: boolean;  // 默认 true

// AppAction 中添加
| { type: 'SET_NOTIFICATIONS'; payload: boolean }
```

**步骤 2**：useClaude 中对话完成时发送通知

```typescript
// useClaude.ts — onClaudeMessage 回调中
if (message.type === 'done') {
  setIsStreaming(false);
  // 发送通知
  window.lemmaAPI?.notify('Lemma', 'Claude 已完成回复');
}
```

**步骤 3**：SettingsPanel 添加通知开关

```tsx
<section className="space-y-3">
  <h3 className="flex items-center gap-2 text-sm font-semibold">
    <Bell size={16} /> 通知
  </h3>
  <label className="flex items-center gap-2 text-sm">
    <input
      type="checkbox"
      checked={state.notificationsEnabled}
      onChange={(e) => dispatch({ type: 'SET_NOTIFICATIONS', payload: e.target.checked })}
    />
    启用系统通知
  </label>
</section>
```

**预估工时**：30min

---

### Task 1.7：添加失败消息重试按钮

**问题**：普通错误消息没有重试按钮
**文件**：`frontend/src/components/ChatPanel.tsx`

**修复**：在错误消息气泡旁添加重试按钮

```tsx
// ChatPanel.tsx — MessageBubble 中
{message.type === 'error' && (
  <button
    onClick={onRetry}
    className="mt-2 flex items-center gap-1 text-xs text-primary-500 hover:text-primary-600"
  >
    <RefreshCw size={12} /> 重试
  </button>
)}
```

需要向 ChatPanel props 添加 `onRetry: () => void`。

**预估工时**：20min

---

### Task 1.8：清理 main.ts 动态 require

**问题**：多处 `const fs = require('fs')` 而非顶层 import
**文件**：`electron/main.ts`

**修复**：

```typescript
// electron/main.ts — 顶部添加
import * as fs from 'fs';

// 删除所有函数内的 const fs = require('fs')
```

**预估工时**：10min

---

### Sprint 1 里程碑检查清单

- [ ] UltraMath prompt 复用可用
- [ ] ClaudeMdEditor 在设置页面可访问
- [ ] RetryBanner 无内存泄漏
- [ ] SDK 版本检测正确
- [ ] Ctrl+Enter 发送消息
- [ ] 对话完成时系统通知
- [ ] 失败消息可重试
- [ ] main.ts 无动态 require

---

## Sprint 2：功能增强（1.5 周）

> **目标**：实现计划中要求但缺失的增强功能
> **完成标准**：所有 UI 增强功能可用

---

### Task 2.1：chokidar 文件变更监听

**问题**：计划明确要求文件变更监听，当前只有手动刷新
**文件**：`electron/main.ts`, `frontend/src/components/FileBrowser.tsx`, `package.json`

**步骤 1**：添加 chokidar 依赖

```json
"chokidar": "^4.0.0"
```

**步骤 2**：main.ts 添加文件监听 IPC

```typescript
// electron/main.ts
import * as chokidar from 'chokidar';

let fileWatcher: chokidar.FSWatcher | null = null;

ipcMain.handle('watch-directory', async (_event, dirPath: string) => {
  fileWatcher?.close();
  fileWatcher = chokidar.watch(dirPath, {
    ignored: /(^|[\/\\])\.|node_modules/,
    persistent: true,
    ignoreInitial: true,
  });

  fileWatcher.on('all', (eventName, filePath) => {
    mainWindow?.webContents.send('file-changed', { eventName, filePath });
  });

  return { success: true };
});

// window-all-closed 时清理
fileWatcher?.close();
```

**步骤 3**：preload.ts 暴露

```typescript
watchDirectory: (dirPath: string) => ipcRenderer.invoke('watch-directory', dirPath),
onFileChanged: (callback: (info: unknown) => void) => {
  const handler = (_event: unknown, info: unknown) => callback(info);
  ipcRenderer.on('file-changed', handler);
  return () => ipcRenderer.removeListener('file-changed', handler);
},
```

**步骤 4**：FileBrowser 监听变更自动刷新

```typescript
useEffect(() => {
  if (!workDir || !window.lemmaAPI?.watchDirectory) return;
  window.lemmaAPI.watchDirectory(workDir);
  const unsubscribe = window.lemmaAPI.onFileChanged(() => {
    loadDirectory(workDir, []).then(setTree);
  });
  return unsubscribe;
}, [workDir]);
```

**预估工时**：2h

---

### Task 2.2：Electron 端指数退避重试

**问题**：计划要求 2s→4s→8s→16s→30s 指数退避，仅前端有退避 UI
**文件**：`electron/claude-sdk-bridge.ts`

**修复**：

```typescript
// claude-sdk-bridge.ts — sendMessage 方法中添加重试逻辑
private readonly RETRY_DELAYS = [2000, 4000, 8000, 16000, 30000];
private retryCount = 0;

async sendMessage(message: string, options?: ChatOptions): Promise<void> {
  this.retryCount = 0;
  await this.attemptSend(message, options);
}

private async attemptSend(message: string, options?: ChatOptions): Promise<void> {
  // ... 现有的 try/catch 逻辑

  catch (error: unknown) {
    if (this.isRecoverable(error) && this.retryCount < this.RETRY_DELAYS.length) {
      const delay = this.RETRY_DELAYS[this.retryCount];
      this.retryCount++;
      this.sendToRenderer({
        type: 'text',
        content: `连接中断，${delay / 1000}s 后第 ${this.retryCount} 次重试...`,
      });
      await new Promise((resolve) => setTimeout(resolve, delay));
      if (!this.abortController?.signal.aborted) {
        return this.attemptSend(message, options);
      }
    }
    // ... 现有的错误处理
  }
}
```

**预估工时**：1h

---

### Task 2.3：PDF 导出

**问题**：计划要求导出为 PDF，当前仅支持 Markdown/文本
**文件**：`electron/main.ts`, `frontend/src/components/` (新建 ExportPanel 或修改现有)

**方案**：使用 Electron 内置的 `webContents.printToPDF()`

```typescript
// electron/main.ts
ipcMain.handle('export-pdf', async (_event, htmlContent: string) => {
  const result = await dialog.showSaveDialog({
    filters: [{ name: 'PDF', extensions: ['pdf'] }],
  });
  if (result.canceled || !result.filePath) return { success: false };

  // 创建隐藏窗口渲染 HTML
  const pdfWindow = new BrowserWindow({ show: false });
  await pdfWindow.loadURL(`data:text/html;charset=utf-8,${encodeURIComponent(htmlContent)}`);
  const pdfData = await pdfWindow.webContents.printToPDF({ printBackground: true });
  fs.writeFileSync(result.filePath, pdfData);
  pdfWindow.close();

  return { success: true, path: result.filePath };
});
```

**预估工时**：2h

---

### Task 2.4：Markdown 文件预览

**问题**：文件浏览器中 .md 文件以纯文本显示
**文件**：`frontend/src/components/FileBrowser.tsx`

**修复**：对 .md 文件使用 ReactMarkdown 渲染

```tsx
// FileBrowser.tsx — 文件内容区域
{selectedFile?.endsWith('.md') ? (
  <div className="p-4 prose prose-sm dark:prose-invert max-w-none">
    <ReactMarkdown>{fileContent}</ReactMarkdown>
  </div>
) : (
  <pre className="p-4 text-xs font-mono">{fileContent}</pre>
)}
```

**预估工时**：30min

---

### Task 2.5：离线自动重连

**问题**：wasOffline flag 未用于触发重连
**文件**：`frontend/src/hooks/useNetworkStatus.ts`, `frontend/src/App.tsx`

**修复**：

```typescript
// useNetworkStatus.ts — 返回重连回调接口
export function useNetworkStatus(onReconnect?: () => void) {
  // ...
  useEffect(() => {
    const handleOnline = () => {
      setIsOnline(true);
      if (wasOffline) {
        onReconnect?.();
        window.lemmaAPI?.notify('Lemma', '网络连接已恢复');
      }
    };
    // ...
  }, [wasOffline, onReconnect]);
}

// App.tsx — 传入重连回调
const network = useNetworkStatus(() => {
  // 网络恢复后的重连逻辑
  if (claude.isStreaming) {
    claude.clearError();
    // 重新发送最后一条消息
  }
});
```

**预估工时**：30min

---

### Task 2.6：历史成本统计持久化

**问题**：成本数据关闭会话即丢失
**文件**：`electron/session-manager.ts`, `frontend/src/components/CostTracker.tsx`

**修复**：在 SessionInfo 中增加 cost 字段

```typescript
// session-manager.ts — SessionInfo 扩展
interface SessionInfo {
  // ... 现有字段
  totalInputTokens?: number;
  totalOutputTokens?: number;
  estimatedCost?: number;
  model?: string;
}

// 新增方法
updateSessionCost(id: string, cost: { input: number; output: number; cost: number; model: string }): void {
  const session = this.loadSession(id);
  if (session) {
    session.totalInputTokens = cost.input;
    session.totalOutputTokens = cost.output;
    session.estimatedCost = cost.cost;
    session.model = cost.model;
    this.saveSession(session);
  }
}
```

CostTracker 从 session 加载历史数据并在会话结束时保存。

**预估工时**：1h

---

### Task 2.7：generateTemplate 消费预设内容

**问题**：不同预设生成的 CLAUDE.md 模板完全相同
**文件**：`electron/claude-md-manager.ts`

**修复**：

```typescript
// claude-md-manager.ts
import { getPresetById } from './presets';

export function generateTemplate(presetId: string, workDir: string): string {
  const dirName = path.basename(workDir);
  const preset = getPresetById(presetId);
  const presetSection = preset
    ? `## 当前预设: ${preset.name}\n${preset.description}\n\n## 行为规范\n${preset.systemPrompt?.slice(0, 200) || ''}...`
    : `## 预设: ${presetId}`;

  return `# ${dirName}\n\n## 项目描述\n<!-- 描述项目目标 -->\n\n${presetSection}\n`;
}
```

**预估工时**：15min

---

### Sprint 2 里程碑检查清单

- [ ] 文件浏览器自动刷新（chokidar）
- [ ] Claude 调用失败时自动指数退避重试
- [ ] 对话可导出为 PDF
- [ ] .md 文件可预览渲染
- [ ] 网络恢复后自动重连
- [ ] 成本数据跨会话持久化
- [ ] CLAUDE.md 模板包含预设内容

---

## Sprint 3：质量保障（1.5 周）

> **目标**：测试覆盖、缺失组件、代码清理
> **完成标准**：测试覆盖率 > 60% + 无 dead code

---

### Task 3.1：PipelineProgress 组件

**问题**：计划要求流水线进度面板，完全缺失
**文件**：新建 `frontend/src/components/PipelineProgress.tsx`

```typescript
// PipelineProgress.tsx — 基础结构
interface PipelineStage {
  id: string;
  name: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  output?: string;
  startedAt?: string;
  completedAt?: string;
}

const STAGES: PipelineStage[] = [
  { id: 'analyze', name: '分析', status: 'pending' },
  { id: 'derive', name: '推导', status: 'pending' },
  { id: 'code', name: '编码', status: 'pending' },
  { id: 'test', name: '测试', status: 'pending' },
  { id: 'write', name: '写作', status: 'pending' },
  { id: 'review', name: '审稿', status: 'pending' },
];

// 实现：线性进度条 + 各阶段状态图标 + 点击查看产出
```

**预估工时**：3h

---

### Task 3.2：MCP Server 集成配置

**问题**：计划要求 MCP Server 管理，无任何实现
**文件**：新建 `electron/mcp-config-manager.ts`, 修改 `SettingsPanel.tsx`

**方案**：
- 在 SettingsPanel 中添加 MCP Server 管理区域
- 支持添加/删除/编辑 MCP Server 配置
- 配置写入工作目录的 `.claude/settings.json`

```typescript
// electron/mcp-config-manager.ts
interface McpServerConfig {
  name: string;
  command: string;
  args: string[];
  env?: Record<string, string>;
}

export function getMcpConfig(workDir: string): McpServerConfig[] { /* ... */ }
export function addMcpServer(workDir: string, config: McpServerConfig): void { /* ... */ }
export function removeMcpServer(workDir: string, name: string): void { /* ... */ }
```

**预估工时**：3h

---

### Task 3.3：测试覆盖

**问题**：测试覆盖率 0%，计划要求 9 个测试文件
**文件**：新建测试文件

**优先级排序**：

| 优先级 | 测试文件 | 说明 |
|--------|----------|------|
| P0 | `electron/__tests__/session-manager.test.ts` | 纯逻辑，无依赖 |
| P0 | `electron/__tests__/version-checker.test.ts` | 纯逻辑 |
| P1 | `frontend/src/__tests__/useClaude.test.ts` | mock lemmaAPI |
| P1 | `frontend/src/__tests__/ChatPanel.test.tsx` | 核心组件 |
| P1 | `frontend/src/__tests__/Sidebar.test.tsx` | 核心组件 |
| P2 | `frontend/src/__tests__/SettingsPanel.test.tsx` | |
| P2 | `frontend/src/__tests__/FileBrowser.test.tsx` | |
| P2 | `frontend/src/__tests__/AppContext.test.tsx` | |
| P3 | `electron/__tests__/claude-sdk-bridge.test.ts` | mock SDK |

**每个测试文件至少覆盖**：
- 正常流程（happy path）
- 边界情况（空输入、异常数据）
- 错误处理

**预估工时**：16h

---

### Task 3.4：代码清理

**Dead Code 删除**：
- 删除 `frontend/src/hooks/useMessages.ts`（未被任何组件使用）
- 清理 `PresetSelector.tsx` 中未使用的 `useState` 和 `useEffect` 导入

**package.json 优化**：
```json
// 锁定 SDK 版本
"@anthropic-ai/claude-agent-sdk": "^0.2.0"  // 替换 "latest"

// 更新 electron-builder
"electron-builder": "^26.0.0"  // 替换 "^25.0.0"
```

**release.yml 修复**：
```yaml
# Linux 构建添加系统依赖
- name: Install Linux dependencies
  if: matrix.os == 'ubuntu-latest'
  run: sudo apt-get install -y libxml2-utils rpm
```

**mainWindow 非空断言**：
```typescript
// electron/main.ts — 替换 mainWindow!
if (!mainWindow) return;
claudeBridge = new ClaudeSdkBridge(mainWindow, sessionManager);
```

**预估工时**：2h

---

### Sprint 3 里程碑检查清单

- [ ] PipelineProgress 组件可用
- [ ] MCP Server 可添加/管理
- [ ] 测试覆盖率 > 60%
- [ ] Dead code 已清理
- [ ] SDK 版本已锁定
- [ ] release.yml Linux 构建可工作
- [ ] 无非空断言

---

## 附录：修复优先级速查表

| 编号 | 任务 | Sprint | 工时 | 依赖 |
|------|------|--------|------|------|
| 0.1 | package-lock.json | 0 | 10min | 无 |
| 0.2 | ESLint 版本 | 0 | 15min | 无 |
| 0.3 | electron:dev 脚本 | 0 | 15min | 0.1 |
| 0.4 | 自动更新接通 | 0 | 30min | 0.1 |
| 0.5 | Sidebar 预设 onClick | 0 | 20min | 无 |
| 0.6 | FileBrowser 首次加载 | 0 | 5min | 无 |
| 0.7 | Onboarding 设置保留 | 0 | 20min | 无 |
| 0.8 | SDK API 校准 | 0 | 1h | 0.1 |
| 0.9 | session 容错 | 0 | 10min | 无 |
| 1.1 | UltraMath prompt | 1 | 1h | 无 |
| 1.2 | ClaudeMdEditor 集成 | 1 | 10min | 无 |
| 1.3 | RetryBanner 泄漏 | 1 | 10min | 无 |
| 1.4 | version-checker 修复 | 1 | 15min | 0.1 |
| 1.5 | 快捷键注册 | 1 | 30min | 无 |
| 1.6 | 通知系统 | 1 | 30min | 无 |
| 1.7 | 失败重试按钮 | 1 | 20min | 无 |
| 1.8 | main.ts require 清理 | 1 | 10min | 无 |
| 2.1 | chokidar 监听 | 2 | 2h | 0.1 |
| 2.2 | 指数退避重试 | 2 | 1h | 无 |
| 2.3 | PDF 导出 | 2 | 2h | 无 |
| 2.4 | Markdown 预览 | 2 | 30min | 无 |
| 2.5 | 离线重连 | 2 | 30min | 无 |
| 2.6 | 成本持久化 | 2 | 1h | 无 |
| 2.7 | 模板消费预设 | 2 | 15min | 无 |
| 3.1 | PipelineProgress | 3 | 3h | 无 |
| 3.2 | MCP Server 配置 | 3 | 3h | 无 |
| 3.3 | 测试覆盖 | 3 | 16h | 0.1-0.9 |
| 3.4 | 代码清理 | 3 | 2h | 无 |

**总计预估**：~35h（约 4-5 周全职工时）
