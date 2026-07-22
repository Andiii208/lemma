# Lemma

> **Every Theorem Begins with a Lemma**

基于 Claude 的学术写作桌面软件。无需安装 Claude Code，开箱即用。

[![CI](https://github.com/Andiii208/lemma/actions/workflows/ci.yml/badge.svg)](https://github.com/Andiii208/lemma/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

## 特性

### 已验证

- 🤖 **Claude Agent SDK** — 直接使用 Anthropic 最新的 Agent SDK，无需预装 Claude Code
- 📐 **学科预设** — 数学建模、论文写作、实验报告、文献综述、数据挖掘
- 💬 **流式对话** — Markdown 渲染 + 代码高亮 + 工具调用可视化
- 📁 **文件浏览器** — 工作目录浏览 + 文件内容预览
- 📊 **成本追踪** — 实时 Token 消耗和成本估算
- 🔄 **错误恢复** — 崩溃自动重连 + 指数退避重试
- 🎨 **双主题** — 亮色/暗色主题 + 跟随系统
- ⌨️ **快捷键** — 完整的键盘快捷键系统
- 📤 **对话导出** — Markdown 导出 + 剪贴板复制
- 🔐 **安全存储** — API Key 通过 Electron safeStorage 加密
- 📡 **离线模式** — 断网时可浏览历史会话

### 实验性

- 🧪 **Domain Registry** — 通过 YAML 配置扩展领域（5 个领域已验证）
- 🔌 **MCP Server** — 支持 Model Context Protocol 扩展

## 架构

```
Electron 39 → React 18 → IPC → Node.js 主进程 → Claude Agent SDK → Claude
```

## 快速开始

### 开发

```bash
# 安装依赖
npm ci

# 启动开发模式（Vite + Electron）
npm run electron:dev

# 仅前端开发
npm run dev
```

### 构建

```bash
# 类型检查
npm run typecheck

# 构建前端
npm run build

# 打包桌面应用
npm run electron:build
```

## 项目结构

```
lemma/
├── package.json              # 项目配置
├── tsconfig.electron.json    # Electron TypeScript 配置
├── electron/
│   ├── main.ts               # Electron 主进程
│   ├── preload.ts            # 预加载脚本
│   ├── claude-sdk-bridge.ts  # Agent SDK 桥接
│   ├── session-manager.ts    # 会话管理
│   ├── claude-md-manager.ts  # CLAUDE.md 管理
│   ├── version-checker.ts    # SDK 版本检测
│   ├── updater.ts            # 自动更新
│   ├── security.ts           # 安全边界
│   ├── authorized-paths.ts   # 路径授权
│   ├── domains/              # Domain Registry
│   │   ├── registry.ts       # 领域注册表
│   │   └── schema.ts         # Zod 校验
│   └── presets/              # 预设模板
├── frontend/
│   ├── src/
│   │   ├── App.tsx           # 根组件
│   │   ├── context/          # 全局状态
│   │   ├── components/       # UI 组件
│   │   ├── hooks/            # 自定义 Hooks
│   │   ├── utils/            # 工具函数
│   │   └── types/            # 类型定义
│   ├── index.html
│   ├── vite.config.ts
│   └── tailwind.config.js
├── domains/                  # 领域配置（YAML + prompts）
├── DEPRECATED/               # 旧架构代码归档
└── docs/
```

## 技术栈

- **桌面**: Electron 39
- **前端**: React 18 + TypeScript + Vite 5 + Tailwind CSS
- **AI 引擎**: @anthropic-ai/claude-agent-sdk
- **通信**: Electron IPC
- **构建**: electron-builder

## 键盘快捷键

| 快捷键 | 功能 |
|--------|------|
| `Ctrl/Cmd + N` | 新建会话 |
| `Ctrl/Cmd + O` | 选择工作目录 |
| `Ctrl/Cmd + .` | 停止生成 |
| `Ctrl/Cmd + K` | 清空对话 |
| `Ctrl/Cmd + ,` | 设置 |
| `Ctrl/Cmd + Shift + E` | 导出对话 |

## 许可证

[MIT](LICENSE)
