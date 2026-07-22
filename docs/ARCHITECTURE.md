# Lemma 架构文档

## 架构概览

```
┌────────────────────────────────────────────────────┐
│                  Electron 39                       │
│  ┌─────────────────┐   ┌────────────────────────┐  │
│  │  Renderer        │   │  Main Process          │  │
│  │                  │   │                        │  │
│  │  React 18        │   │  claude-sdk-bridge.ts  │  │
│  │  + TypeScript    │   │  session-manager.ts    │  │
│  │  + Tailwind CSS  │   │  domains/registry.ts   │  │
│  │                  │   │  claude-md-manager.ts  │  │
│  │  ChatPanel       │   │  version-checker.ts    │  │
│  │  Sidebar         │   │  updater.ts            │  │
│  │  SettingsPanel   │   │  security.ts           │  │
│  │  FileBrowser     │   │  authorized-paths.ts   │  │
│  │  CostTracker     │   │                        │  │
│  │  StatusBar       │   │  ┌──────────────────┐  │  │
│  │                  │   │  │ Claude Agent SDK │  │  │
│  └────────┬─────────┘   │  └────────┬─────────┘  │  │
│           │ IPC          │           │            │  │
│  ┌────────▼─────────┐   │           ▼            │  │
│  │  Preload Script   │◄──┤  ┌──────────────────┐  │  │
│  │  (contextBridge)  │   │  │ Claude API       │  │  │
│  └──────────────────┘   │  └──────────────────┘  │  │
└────────────────────────────────────────────────────┘
```

## 核心组件

### Domain Registry

Domain Registry 负责从 `domains/` 目录加载领域配置。每个领域包含：

- `domain.yaml` — Zod schema 校验的配置文件
- `prompts/` — 角色系统提示词
- `knowledge/` — 领域知识文档
- `templates/` — 输出模板（可选）

```typescript
// electron/domains/registry.ts
export interface DomainRegistry {
  listDomains(): DomainConfig[];
  getDomain(id: string): DomainConfig | null;
  getPresetFromDomain(id: string): PresetSummary | null;
}
```

### Session Lifecycle

会话管理通过 `SessionManager` 类实现：

```
创建 → 加载 → 活跃 → 保存 → 归档
  │      │      │      │      │
  └──────┴──────┴──────┴──────┘
         {userData}/sessions/
         每个会话一个 JSON 文件
```

支持操作：`createSession`、`listSessions`、`loadSession`、`deleteSession`

### SDK Bridge

`ClaudeSdkBridge` 封装了 Claude Agent SDK 的调用：

```
Renderer → IPC invoke → Main Process → ClaudeSdkBridge.sendMessage()
    → Agent SDK query → Claude API
    → Async generator → webContents.send → IPC on → useClaude hook
```

关键特性：
- 流式响应处理
- 请求取消（AbortController）
- 错误恢复（指数退避重试）
- 会话状态追踪

### 安全边界

多层安全机制确保渲染进程与主进程隔离：

```
┌─────────────────────────────────────────┐
│ 安全层                                  │
├─────────────────────────────────────────┤
│ contextIsolation: true                  │
│ nodeIntegration: false                  │
│ sandbox: true (Chromium 沙箱)           │
│ assertTrustedSender() — IPC 来源验证    │
│ AuthorizedPaths — 文件路径授权          │
│ safeStorage — API Key 加密存储          │
│ isTrustedAppUrl() — 导航拦截           │
│ isSafeExternalUrl() — 外部链接过滤     │
└─────────────────────────────────────────┘
```

## 通信流程

### 用户发送消息

1. 用户在 ChatPanel 输入消息，点击发送
2. React 通过 `window.lemmaAPI.chat()` 调用 IPC
3. Electron 主进程接收 IPC，验证发送者身份
4. `dispatchChat()` 读取 API Key，调用 `ClaudeSdkBridge.sendMessage()`
5. SDK Bridge 通过 Agent SDK 的 `query()` 发起请求
6. 流式响应通过 `mainWindow.webContents.send('claude-message')` 回传
7. React 的 `useClaude` hook 监听消息并更新 UI

### 会话管理

- 会话数据存储在 `{userData}/sessions/` 目录
- 每个会话一个 JSON 文件
- 支持创建、列表、加载、删除操作
- 原子写入防止数据损坏

### API Key 安全

- 使用 Electron `safeStorage` 加密
- 存储在 `{userData}/api-key.encrypted`
- 明文 Key 仅在调用 Claude SDK 时解密
- 通过 `registerTrustedHandler` 确保只有可信来源可访问

## 数据流

```
用户输入 → React state → IPC invoke → Main process
    → dispatchChat() → ClaudeSdkBridge.sendMessage()
    → Agent SDK query → Claude API
    → Async generator → webContents.send → IPC on
    → useClaude hook → React state → UI 渲染
```

## 目录结构

```
lemma/
├── electron/                  # Electron 主进程 (TypeScript)
│   ├── main.ts               # 入口 + IPC handlers
│   ├── preload.ts            # contextBridge
│   ├── claude-sdk-bridge.ts  # Agent SDK 封装
│   ├── session-manager.ts    # 会话 CRUD
│   ├── claude-md-manager.ts  # CLAUDE.md 读写
│   ├── version-checker.ts    # SDK 兼容检测
│   ├── updater.ts            # 自动更新
│   ├── security.ts           # 安全边界
│   ├── authorized-paths.ts   # 路径授权
│   ├── chat-dispatcher.ts    # 聊天分发
│   ├── domains/              # Domain Registry
│   │   ├── registry.ts       # 领域注册表
│   │   └── schema.ts         # Zod 校验
│   └── presets/index.ts      # 预设模板定义
├── frontend/                  # React SPA
│   ├── src/
│   │   ├── App.tsx           # 根组件 + 路由
│   │   ├── context/AppContext.tsx  # useReducer 全局状态
│   │   ├── components/       # UI 组件
│   │   ├── hooks/            # useClaude, useMessages, etc.
│   │   ├── utils/            # export, helpers
│   │   └── types/            # electron.d.ts (IPC 类型)
│   ├── vite.config.ts
│   └── tailwind.config.js
├── domains/                   # 领域配置
│   ├── math-modeling/
│   ├── paper-writing/
│   ├── lab-report/
│   ├── literature-review/
│   └── data-mining/
└── DEPRECATED/               # 旧架构归档
```
