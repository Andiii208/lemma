# Lemma 发展计划（审查修订版）

> **文档用途**：AI 可直接执行的详细开发计划
> **创建日期**：2026-07-07
> **修订日期**：2026-07-07（多维度审查后修订）
> **当前版本**：v5.2.0（旧架构）
> **目标版本**：v1.0.0（新架构发布）
> **核心定位**：基于 Claude Code 的学术写作桌面软件（类似 Open Design）
> **预估总工期**：14-16 周（单人开发）

---

## 一、架构转型说明

### 1.1 从旧架构到新架构

**旧架构（v5.x，废弃）**：
```
Electron → React → WebSocket → FastAPI(Python) → OpenAI SDK → LLM APIs
```

**新架构（v1.0，目标）**：
```
Electron → React → IPC → Node.js 主进程 → Claude Agent SDK → Claude 完成推理
```

> **审查修订**：原方案手写 `spawn('claude')` CLI 桥接。审查指出应使用 `@anthropic-ai/claude-agent-sdk` 官方 SDK——30 行代码替代 200 行手写，获得类型安全、session 管理、hooks 集成，且 SDK 内嵌平台二进制文件，**用户无需预装 CC**。

### 1.2 保留 vs 废弃

| 组件 | 处置 | 说明 |
|------|------|------|
| **Electron 壳** | ✅ 保留 | 升级到 v43（审查修订：v33 已 EOL） |
| **React SPA 前端** | ✅ 保留并重构 | 用户界面 |
| **FastAPI 后端** | ❌ 废弃 | Agent SDK 替代 |
| **OpenAI SDK 封装** | ❌ 废弃 | Agent SDK 替代 |
| **Python 科学计算工具** | ✅ 保留为 MCP Server | 审查修订：Python 在科学计算生态远强于 Node.js |
| **知识库** | ✅ 迁移 | 共享 UltraMath 的知识库 + BM25 检索 |
| **评测/进化系统** | ⚠️ 独立 CLI 工具 | 可独立使用 |

### 1.3 新项目技术栈

```
前端：React 18 + TypeScript + Vite + Tailwind CSS
桌面：Electron 43（审查修订：从 33 升级）
通信：Electron IPC
引擎：@anthropic-ai/claude-agent-sdk（审查修订：替代手写 CLI 桥接）
工具：共享 Python MCP Server（与 UltraMath 共用）
状态：useReducer + Context（零依赖，够用）
构建：electron-builder
```

### 1.4 新项目结构

```
E:\数学建模agent/
├── package.json
├── electron/
│   ├── main.ts               # Electron 主进程
│   ├── preload.ts            # 预加载脚本
│   ├── claude-sdk-bridge.ts  # 🆕 Agent SDK 桥接（30 行核心代码）
│   ├── session-manager.ts    # 会话管理
│   └── presets/              # 领域预设
├── frontend/
│   └── src/
│       ├── App.tsx
│       ├── context/AppContext.tsx
│       ├── components/
│       ├── hooks/useClaude.ts
│       └── types/
├── DEPRECATED/               # 旧代码归档
└── docs/
```

**共享组件**（不在本仓库）：
```
../lemma-mcp-server/          # 与 UltraMath 共享的 Python MCP Server
├── server.py
├── tools/
│   ├── latex_compiler.py
│   ├── figure_generator.py
│   ├── python_runner.py
│   ├── quality_checker.py
│   └── document_exporter.py
└── resources/
    └── knowledge_base.py     # BM25 检索
```

---

## 二、四阶段实施路线

```
Phase 1 (2周)      Phase 2 (4周)       Phase 3 (4-5周)      Phase 4 (3-4周)
旧代码清理   ──→  核心功能    ──→   功能完善     ──→   发布准备
+ Agent SDK       Claude 集成       UI + MCP 工具       打包 + 签名
     │                │                    │                    │
     ▼                ▼                    ▼                    ▼
  v0.1.0           v0.4.0              v0.8.0              v1.0.0
```

---

## Phase 1：旧代码清理 + 新项目骨架（2 周）→ v0.1.0

### Task 1.1：旧代码归档

```bash
mkdir DEPRECATED
git mv backend/ DEPRECATED/backend/
git mv server_main.py DEPRECATED/ 2>/dev/null
git mv start.bat DEPRECATED/ 2>/dev/null
git mv start.sh DEPRECATED/ 2>/dev/null
git mv start.py DEPRECATED/ 2>/dev/null
```

**预估工时**：1h

---

### Task 1.2：新项目 package.json

**重写文件**：`package.json`

```json
{
  "name": "lemma",
  "version": "0.1.0",
  "description": "基于 Claude Code 的学术写作桌面软件",
  "main": "dist-electron/main.js",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build && tsc -p tsconfig.electron.json",
    "electron:dev": "concurrently \"vite\" \"wait-on http://localhost:5173 && electron .\"",
    "electron:build": "npm run build && electron-builder",
    "lint": "eslint src/ electron/ --ext .ts,.tsx",
    "typecheck": "tsc --noEmit && tsc -p tsconfig.electron.json --noEmit",
    "test": "vitest"
  },
  "dependencies": {
    "@anthropic-ai/claude-agent-sdk": "latest",
    "react": "^18.3.0",
    "react-dom": "^18.3.0",
    "framer-motion": "^11.0.0",
    "lucide-react": "^0.400.0",
    "react-markdown": "^9.0.0",
    "react-hot-toast": "^2.4.0"
  },
  "devDependencies": {
    "@types/react": "^18.3.0",
    "@types/react-dom": "^18.3.0",
    "@vitejs/plugin-react": "^4.3.0",
    "autoprefixer": "^10.4.0",
    "concurrently": "^9.0.0",
    "electron": "^43.0.0",
    "electron-builder": "^25.0.0",
    "eslint": "^9.0.0",
    "postcss": "^8.4.0",
    "tailwindcss": "^3.4.0",
    "typescript": "^5.5.0",
    "vite": "^6.0.0",
    "vitest": "^2.0.0",
    "wait-on": "^8.0.0"
  },
  "build": {
    "appId": "com.lemma.app",
    "productName": "Lemma",
    "directories": { "output": "dist" },
    "files": ["dist/**/*", "dist-electron/**/*"],
    "mac": { "category": "public.app-category.productivity", "target": ["dmg", "zip"] },
    "linux": { "target": ["AppImage", "deb"], "category": "Office" },
    "win": { "target": ["nsis", "portable"] }
  }
}
```

> **审查修订**：Electron 33→43，添加 `@anthropic-ai/claude-agent-sdk`

**创建文件**：`tsconfig.electron.json`

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "commonjs",
    "lib": ["ES2022"],
    "outDir": "dist-electron",
    "rootDir": "electron",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true
  },
  "include": ["electron/**/*"]
}
```

**预估工时**：3h

---

### Task 1.3：Electron 主进程

**创建文件**：`electron/main.ts`

```typescript
import { app, BrowserWindow, ipcMain, dialog, safeStorage } from 'electron';
import * as path from 'path';
import { ClaudeSdkBridge } from './claude-sdk-bridge';
import { SessionManager } from './session-manager';

let mainWindow: BrowserWindow | null = null;
let claudeBridge: ClaudeSdkBridge | null = null;
let sessionManager: SessionManager | null = null;

function createWindow(): void {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 800,
    minHeight: 600,
    title: 'Lemma',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
    },
  });

  if (process.env.NODE_ENV === 'development') {
    mainWindow.loadURL('http://localhost:5173');
  } else {
    mainWindow.loadFile(path.join(__dirname, '../dist/index.html'));
  }
}

app.whenReady().then(() => {
  createWindow();
  sessionManager = new SessionManager(app.getPath('userData'));
  claudeBridge = new ClaudeSdkBridge(mainWindow, sessionManager);
  setupIpcHandlers();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', () => {
  claudeBridge?.dispose();
  if (process.platform !== 'darwin') app.quit();
});

function setupIpcHandlers(): void {
  // API Key 安全存储（审查修订：使用 Electron safeStorage）
  ipcMain.handle('store-api-key', async (_event, key: string) => {
    if (safeStorage.isEncryptionAvailable()) {
      const encrypted = safeStorage.encryptString(key);
      // 存储加密后的 key
      return { success: true, encrypted: true };
    }
    return { success: false, reason: 'Encryption not available' };
  });

  ipcMain.handle('chat', async (_event, message: string, options?: ChatOptions) => {
    return claudeBridge?.sendMessage(message, options);
  });

  ipcMain.handle('cancel', async () => claudeBridge?.cancel());

  ipcMain.handle('select-directory', async () => {
    const result = await dialog.showOpenDialog({ properties: ['openDirectory'] });
    return result.filePaths[0] || null;
  });

  // 会话管理
  ipcMain.handle('list-sessions', async () => sessionManager?.listSessions());
  ipcMain.handle('load-session', async (_event, id: string) => sessionManager?.loadSession(id));

  // 系统通知
  ipcMain.handle('notify', async (_event, title: string, body: string) => {
    const { Notification } = require('electron');
    if (Notification.isSupported()) {
      new Notification({ title, body }).show();
    }
  });
}

interface ChatOptions {
  workDir?: string;
  model?: string;
  systemPrompt?: string;
  presetId?: string;
}
```

**预估工时**：6h

---

### Task 1.4：Claude Agent SDK 桥接层（核心）

> **审查修订**：使用官方 SDK 替代手写 CLI spawn。30 行核心代码，自动处理 session、流式输出、错误恢复。

**创建文件**：`electron/claude-sdk-bridge.ts`

```typescript
import { BrowserWindow } from 'electron';
import { query } from '@anthropic-ai/claude-agent-sdk';
import type { SessionManager } from './session-manager';

interface ChatOptions {
  workDir?: string;
  model?: string;
  systemPrompt?: string;
  presetId?: string;
}

export class ClaudeSdkBridge {
  private mainWindow: BrowserWindow;
  private sessionManager: SessionManager;
  private abortController: AbortController | null = null;

  constructor(mainWindow: BrowserWindow, sessionManager: SessionManager) {
    this.mainWindow = mainWindow;
    this.sessionManager = sessionManager;
  }

  async sendMessage(message: string, options?: ChatOptions): Promise<void> {
    // 取消上一次任务
    this.cancel();
    this.abortController = new AbortController();

    try {
      const response = query({
        prompt: message,
        options: {
          cwd: options?.workDir,
          model: options?.model,
          systemPrompt: options?.systemPrompt,
          maxTurns: 50,
          abortController: this.abortController,
        },
      });

      // 流式处理响应
      for await (const event of response) {
        if (this.abortController.signal.aborted) break;

        this.sendToRenderer({
          type: this.mapEventType(event),
          content: this.extractContent(event),
          metadata: this.extractMetadata(event),
        });
      }

      // 完成
      this.sendToRenderer({ type: 'done', content: '' });

    } catch (error: unknown) {
      const errorMsg = error instanceof Error ? error.message : 'Unknown error';
      this.sendToRenderer({
        type: 'error',
        content: `Claude 调用失败: ${errorMsg}`,
      });

      // 崩溃自动重连提示（审查新增）
      if (this.isRecoverable(error)) {
        this.sendToRenderer({
          type: 'recoverable_error',
          content: '连接中断，点击重试',
        });
      }
    } finally {
      this.abortController = null;
    }
  }

  cancel(): void {
    if (this.abortController) {
      this.abortController.abort();
      this.abortController = null;
    }
  }

  dispose(): void {
    this.cancel();
  }

  private mapEventType(event: unknown): string {
    // SDK 事件类型映射
    const eventType = (event as Record<string, unknown>)?.type;
    switch (eventType) {
      case 'text': return 'text';
      case 'tool_use': return 'tool_use';
      case 'tool_result': return 'tool_result';
      default: return 'text';
    }
  }

  private extractContent(event: unknown): string {
    const data = event as Record<string, unknown>;
    if (typeof data?.text === 'string') return data.text;
    if (typeof data?.content === 'string') return data.content;
    return '';
  }

  private extractMetadata(event: unknown): Record<string, unknown> {
    const data = event as Record<string, unknown>;
    return {
      model: data?.model,
      tokens: data?.usage,
      cost: data?.cost_usd,
    };
  }

  private isRecoverable(error: unknown): boolean {
    const msg = error instanceof Error ? error.message : '';
    return msg.includes('timeout') ||
           msg.includes('connection') ||
           msg.includes('ECONNREFUSED');
  }

  private sendToRenderer(message: { type: string; content: string; metadata?: Record<string, unknown> }): void {
    if (this.mainWindow && !this.mainWindow.isDestroyed()) {
      this.mainWindow.webContents.send('claude-message', message);
    }
  }
}
```

**优势（对比手写 CLI spawn）**：
- ✅ 无需用户预装 Claude Code（SDK 内嵌平台二进制）
- ✅ 原生 session 管理（`--resume` 由 SDK 处理）
- ✅ 类型安全的 async generator 接口
- ✅ 内置 hooks 集成
- ✅ 官方维护和版本兼容

**预估工时**：6h

---

### Task 1.5：Preload 脚本 + IPC 类型

**创建文件**：`electron/preload.ts`

```typescript
import { contextBridge, ipcRenderer } from 'electron';

contextBridge.exposeInMainWorld('lemmaAPI', {
  // Claude 操作
  chat: (message: string, options?: unknown) => ipcRenderer.invoke('chat', message, options),
  cancel: () => ipcRenderer.invoke('cancel'),

  // 安全存储
  storeApiKey: (key: string) => ipcRenderer.invoke('store-api-key', key),

  // 文件系统
  selectDirectory: () => ipcRenderer.invoke('select-directory'),

  // 会话
  listSessions: () => ipcRenderer.invoke('list-sessions'),
  loadSession: (id: string) => ipcRenderer.invoke('load-session', id),

  // 通知
  notify: (title: string, body: string) => ipcRenderer.invoke('notify', title, body),

  // 监听
  onClaudeMessage: (callback: (message: unknown) => void) => {
    const handler = (_event: unknown, message: unknown) => callback(message);
    ipcRenderer.on('claude-message', handler);
    return () => ipcRenderer.removeListener('claude-message', handler);
  },
});
```

**创建文件**：`frontend/src/types/electron.d.ts`

```typescript
interface LemmaAPI {
  chat(message: string, options?: ChatOptions): Promise<void>;
  cancel(): Promise<void>;
  storeApiKey(key: string): Promise<{ success: boolean; encrypted?: boolean }>;
  selectDirectory(): Promise<string | null>;
  listSessions(): Promise<SessionInfo[]>;
  loadSession(id: string): Promise<SessionData | null>;
  notify(title: string, body: string): Promise<void>;
  onClaudeMessage(callback: (message: ClaudeMessage) => void): () => void;
}

interface ClaudeMessage {
  type: 'text' | 'tool_use' | 'tool_result' | 'error' | 'recoverable_error' | 'done';
  content: string;
  metadata?: Record<string, unknown>;
}

interface ChatOptions {
  workDir?: string;
  model?: string;
  systemPrompt?: string;
  presetId?: string;
}

interface SessionInfo {
  id: string;
  title: string;
  workDir: string;
  createdAt: string;
  lastUsedAt: string;
}

declare global {
  interface Window {
    lemmaAPI: LemmaAPI;
  }
}
```

**预估工时**：3h

---

### Task 1.6：前端基础骨架

**创建文件**：
```
frontend/src/
├── App.tsx
├── main.tsx
├── context/AppContext.tsx
├── components/
│   ├── ChatPanel.tsx
│   ├── Sidebar.tsx
│   ├── SettingsPanel.tsx
│   └── StatusBar.tsx
├── hooks/
│   ├── useClaude.ts
│   └── useMessages.ts
└── types/
```

**`hooks/useClaude.ts`**（使用 SDK 而非 CLI）：
```typescript
import { useState, useEffect, useCallback } from 'react';

export function useClaude() {
  const [messages, setMessages] = useState<ClaudeMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);

  useEffect(() => {
    const unsubscribe = window.lemmaAPI.onClaudeMessage((message) => {
      setMessages((prev) => [...prev, message]);
      if (message.type === 'done' || message.type === 'error') {
        setIsStreaming(false);
      }
      // 可恢复错误：显示重试按钮
      if (message.type === 'recoverable_error') {
        // 触发 UI 重试提示
      }
    });
    return unsubscribe;
  }, []);

  const sendMessage = useCallback(async (text: string, options?: ChatOptions) => {
    setIsStreaming(true);
    setMessages((prev) => [
      ...prev,
      { type: 'text', content: text, metadata: { role: 'user' } },
    ]);
    await window.lemmaAPI.chat(text, options);
  }, []);

  const cancelStream = useCallback(async () => {
    await window.lemmaAPI.cancel();
    setIsStreaming(false);
  }, []);

  return { messages, isStreaming, sendMessage, cancelStream };
}
```

**验证**：`npm run electron:dev` 窗口正常显示

**预估工时**：8h

---

### Task 1.7：会话管理

**创建文件**：`electron/session-manager.ts`

```typescript
import * as fs from 'fs';
import * as path from 'path';

interface SessionInfo {
  id: string;
  title: string;
  workDir: string;
  createdAt: string;
  lastUsedAt: string;
  claudeSessionId?: string;  // Agent SDK 的 session ID
}

export class SessionManager {
  private sessionsDir: string;

  constructor(userDataDir: string) {
    this.sessionsDir = path.join(userDataDir, 'sessions');
    fs.mkdirSync(this.sessionsDir, { recursive: true });
  }

  createSession(workDir: string, title: string): SessionInfo {
    const info: SessionInfo = {
      id: `session-${Date.now()}`,
      title,
      workDir,
      createdAt: new Date().toISOString(),
      lastUsedAt: new Date().toISOString(),
    };
    this.saveSession(info);
    return info;
  }

  saveSession(info: SessionInfo): void {
    const filePath = path.join(this.sessionsDir, `${info.id}.json`);
    info.lastUsedAt = new Date().toISOString();
    fs.writeFileSync(filePath, JSON.stringify(info, null, 2));
  }

  listSessions(): SessionInfo[] {
    return fs.readdirSync(this.sessionsDir)
      .filter((f) => f.endsWith('.json'))
      .map((f) => JSON.parse(fs.readFileSync(path.join(this.sessionsDir, f), 'utf-8')))
      .sort((a, b) => b.lastUsedAt.localeCompare(a.lastUsedAt));
  }

  loadSession(id: string): SessionInfo | null {
    const filePath = path.join(this.sessionsDir, `${id}.json`);
    if (!fs.existsSync(filePath)) return null;
    return JSON.parse(fs.readFileSync(filePath, 'utf-8'));
  }
}
```

**预估工时**：4h

---

### Phase 1 里程碑检查清单

- [ ] 旧代码归档到 `DEPRECATED/`
- [ ] `npm install` + `npm run typecheck` 无错误
- [ ] Electron 43 窗口可打开
- [ ] Agent SDK 桥接层可编译
- [ ] IPC 通信正常
- [ ] API Key 通过 safeStorage 加密存储

---

## Phase 2：Claude 深度集成（4 周）→ v0.4.0

### Task 2.1：完整对话流程

- 消息输入框（多行 + Shift+Enter）
- 流式文本渲染（Markdown + 代码高亮）
- 工具调用显示（可折叠面板）
- 停止/重试按钮
- 崩溃自动重连提示（审查新增）

**预估工时**：14h

### Task 2.2：工作目录管理

- 目录选择 UI
- 传递 cwd 给 Agent SDK
- 检测目录下是否有 CLAUDE.md

**预估工时**：4h

### Task 2.3：System Prompt 预设管理

**复用 UltraMath 的 prompt**（审查新增的协同设计）：

```typescript
// electron/presets/index.ts
export interface Preset {
  id: string;
  name: string;
  description: string;
  systemPromptSource: 'builtin' | 'ultramath' | 'custom';
  systemPrompt?: string;
  ultramathAgentPath?: string;  // 引用 UltraMath 的 Agent prompt
}

export const presets: Preset[] = [
  {
    id: 'math-modeling',
    name: '数学建模',
    description: '数学建模竞赛全自动求解',
    systemPromptSource: 'ultramath',
    ultramathAgentPath: '../数学建模/.claude/agents/coordinator.md',
  },
  {
    id: 'paper-writing',
    name: '论文写作',
    description: '学术论文撰写助手',
    systemPromptSource: 'builtin',
    systemPrompt: '你是一个学术论文写作专家...',
  },
  // ...
];
```

**预估工时**：6h

### Task 2.4：CLAUDE.md 管理

- 检测/创建/编辑工作目录的 CLAUDE.md
- 根据预设自动生成模板

**预估工时**：4h

### Task 2.5：错误恢复与状态提示

> **审查新增**

- CC 崩溃 → 显示"连接中断"提示 + 重试按钮
- 超时 → 显示"响应超时，是否继续等待？"
- 网络断开 → 离线模式（支持浏览历史会话）
- 指数退避重试（2s → 4s → 8s → 16s → 最大 30s）

**预估工时**：6h

### Task 2.6：版本兼容检测

> **审查新增**

```typescript
// 启动时检测 SDK 版本
async function checkSdkCompatibility(): Promise<void> {
  const sdkVersion = await getSdkVersion();
  const supportedRange = '>=1.0.0 <2.0.0';
  if (!semver.satisfies(sdkVersion, supportedRange)) {
    showWarning(`Agent SDK 版本 ${sdkVersion} 不在支持范围 ${supportedRange}，请更新 Lemma`);
  }
}
```

**预估工时**：3h

---

### Phase 2 里程碑检查清单

- [ ] 完整对话流程（输入→流式响应→Markdown 渲染）
- [ ] 工作目录选择
- [ ] 至少 4 个预设可选（含 UltraMath 复用）
- [ ] CLAUDE.md 可查看和编辑
- [ ] 崩溃自动重连
- [ ] SDK 版本检测

---

## Phase 3：功能完善 — MCP 工具 + UI 增强（4-5 周）→ v0.8.0

### Task 3.1：共享 MCP Server 集成

> **审查修订**：使用共享的 Python MCP Server（不重新用 TypeScript 写）

**配置**：
```json
// 自动写入工作目录的 .claude/settings.json
{
  "mcpServers": {
    "lemma-tools": {
      "command": "python",
      "args": ["path/to/lemma-mcp-server/server.py"]
    }
  }
}
```

**工具列表**（确定性操作，不含 AI 推理）：
- `compile_latex` — XeLaTeX 编译
- `run_python` — 安全沙箱执行
- `generate_figure` — 出版级图表
- `quality_check` — 多维度质量检查
- `export_document` — Markdown → PDF/DOCX
- `search_knowledge` — BM25 知识库检索

**预估工时**：8h

---

### Task 3.2：文件浏览器面板

- 显示工作目录文件树
- 点击文件查看内容
- Markdown 预览
- 文件变更监听（chokidar）（审查新增）

**预估工时**：10h

### Task 3.3：流水线进度面板

- 可视化各阶段进度
- 标记当前/已完成/失败阶段
- 点击阶段查看产出

**预估工时**：6h

### Task 3.4：成本追踪面板

- 当前会话 token 消耗
- 估算成本
- 历史统计

**预估工时**：4h

### Task 3.5：主题系统 + UI 打磨

- 亮色/暗色主题
- 动画过渡
- 响应式布局

**预估工时**：8h

### Task 3.6：快捷键系统

> **审查新增**

| 快捷键 | 功能 |
|--------|------|
| `Cmd/Ctrl + N` | 新会话 |
| `Cmd/Ctrl + O` | 选择工作目录 |
| `Cmd/Ctrl + Enter` | 发送消息 |
| `Cmd/Ctrl + .` | 停止生成 |
| `Cmd/Ctrl + K` | 清空对话 |
| `Cmd/Ctrl + ,` | 设置 |
| `Cmd/Ctrl + Shift + E` | 导出对话 |

**预估工时**：4h

### Task 3.7：系统通知

> **审查新增**

- 长任务完成时发送系统通知
- 错误时发送通知
- 可选关闭

**预估工时**：2h

### Task 3.8：对话导出

> **审查新增**

- 导出为 Markdown
- 导出为 PDF
- 复制到剪贴板

**预估工时**：4h

---

### Phase 3 里程碑检查清单

- [ ] 共享 MCP Server 6 个工具可调用
- [ ] 文件浏览器 + 变更监听
- [ ] 流水线进度可视化
- [ ] 成本追踪面板
- [ ] 亮色/暗色主题
- [ ] 快捷键系统
- [ ] 系统通知
- [ ] 对话导出

---

## Phase 4：发布准备（3-4 周）→ v1.0.0

### Task 4.1：打包配置 + 图标

- 应用图标（icon.png / icon.icns）
- Windows NSIS + macOS DMG + Linux AppImage
- Electron 43 最新配置

**预估工时**：8h

### Task 4.2：自动更新

```typescript
// electron/updater.ts
import { autoUpdater } from 'electron-updater';

export function setupAutoUpdater(mainWindow: BrowserWindow): void {
  autoUpdater.on('update-available', (info) => {
    mainWindow.webContents.send('update-available', info);
  });
  autoUpdater.on('update-downloaded', (info) => {
    mainWindow.webContents.send('update-downloaded', info);
  });
}
```

**预估工时**：4h

### Task 4.3：首次运行引导

**步骤**：
1. 欢迎
2. **无需安装 Claude Code**（审查修订：SDK 内嵌）
3. 输入 Anthropic API Key（safeStorage 加密存储）
4. 选择工作目录
5. 选择预设
6. 完成

**预估工时**：6h

### Task 4.4：测试覆盖（> 60%）

```
frontend/src/__tests__/
├── useClaude.test.ts
├── useMessages.test.ts
├── ChatPanel.test.tsx
├── Sidebar.test.tsx
├── AppContext.test.tsx
└── SettingsPanel.test.tsx

electron/__tests__/
├── claude-sdk-bridge.test.ts
├── session-manager.test.ts
└── presets.test.ts
```

**预估工时**：16h

### Task 4.5：离线降级

> **审查新增**

- 断网时：支持浏览历史会话、编辑本地文件
- 重连后：自动恢复 Claude 连接
- 状态栏显示网络状态

**预估工时**：4h

### Task 4.6：文档 + LICENSE

- `README.md`（全新）
- `docs/ARCHITECTURE.md`
- `docs/USER_GUIDE.md`
- `docs/MCP_TOOLS.md`
- `LICENSE`（MIT）

**预估工时**：8h

### Task 4.7：CI + 代码签名

```yaml
# .github/workflows/release.yml
name: Release
on:
  push:
    tags: ['v*']
jobs:
  build:
    strategy:
      matrix:
        os: [windows-latest, macos-latest, ubuntu-latest]
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20' }
      - run: npm ci
      - run: npm run typecheck
      - run: npm test
      - run: npm run electron:build
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

**预估工时**：8h

---

### Phase 4 里程碑检查清单

- [ ] 三平台打包成功
- [ ] 自动更新可用
- [ ] 首次引导流程（无需预装 CC）
- [ ] 测试覆盖率 > 60%
- [ ] 离线降级可用
- [ ] 文档完善
- [ ] CI 全绿

---

## 四、版本里程碑

| 版本 | 时间 | 核心目标 |
|------|------|---------|
| v0.1.0 | 2 周 | 新项目骨架 + Agent SDK 桥接 |
| v0.4.0 | 6 周 | 完整对话 + 会话管理 + 预设 + 错误恢复 |
| v0.8.0 | 10-11 周 | MCP 工具 + UI 增强 + 快捷键 + 通知 |
| v1.0.0 | 14-16 周 | 三平台发布 + 自动更新 + 离线降级 |

---

## 五、核心原则

1. **不自建 LLM 后端**：通过 Agent SDK 获得所有推理能力
2. **用户无需预装**：SDK 内嵌二进制，安装 Lemma 即可使用
3. **GUI 是增值层**：价值在体验、工具集成、预设管理
4. **共享优先**：MCP Server、知识库与 UltraMath 共享
5. **安全底线**：safeStorage 加密 API Key、CSP、contextIsolation
6. **优雅降级**：断网可浏览历史、崩溃可重连、错误有提示
7. **Electron 43**：使用最新维护版本
