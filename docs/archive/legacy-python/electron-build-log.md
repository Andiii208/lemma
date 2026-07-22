# Electron 打包验证记录

## 构建信息

- **日期**: 2026-06-27
- **electron-builder 版本**: 24.13.3
- **Electron 目标版本**: 31.7.7
- **前端构建**: ✅ 成功 (vite build 3.71s)
- **后端打包**: ✅ PyInstaller onfile (123MB)
- **Electron 打包**: ✅ 成功

## 构建产物

```
frontend/release/
├── Lemma Setup 5.1.0.exe          # 322MB NSIS 安装包（含完整 Python 运行时 + 后端）
├── Lemma Setup 5.1.0.exe.blockmap # 增量更新 map
├── builder-debug.yml
└── win-unpacked/                  # 解包目录
```

## 安装包内容

- **前端**: React 18 + Electron 31 前端界面
- **后端**: PyInstaller 打包的 FastAPI 后端（lemma-server.exe, 123MB）
- **领域**: 5 个领域配置（math-modeling / paper-writing / lab-report / literature-review / data-mining）
- **Python 运行时**: CPython 3.11 + 所有依赖（numpy, scipy, matplotlib, chromadb, tiktoken 等）

## 工作流

1. 用户双击安装 `Lemma Setup 5.1.0.exe`
2. 启动 Lemma 应用 → Electron 自动启动内嵌的 lemma-server.exe（端口 8765）
3. 后端就绪后窗口显示，左下角显示"后端已连接"
4. 用户配置 API Key 即可使用

## 构建配置

```json
// frontend/package.json "build" 字段
{
  "productName": "Lemma",
  "win": { "target": "nsis", "signAndEditExecutable": false },
  "forceCodeSigning": false,
  "extraResources": [
    { "from": "electron/backend/lemma-server.exe", "to": "backend/lemma-server.exe" },
    { "from": "../domains", "to": "domains" }
  ]
}
```

## 遇到的问题及解决

| 问题 | 解决 |
|------|------|
| GitHub 连接超时 | VPN/代理 |
| winCodeSign 符号链接权限 | `signAndEditExecutable: false` |
| 后端依赖用户安装 Python | PyInstaller 打包为独立 exe |
| 旧模块名 `ultramath` | 修正为 `lemma` |
| PyInstaller 中文路径 | PyInstaller spec 文件 + SPECPATH |

## 验证清单

| 检查项 | 状态 |
|--------|------|
| 前端构建 (vite build) | ✅ |
| 后端打包 (PyInstaller) | ✅ 123MB |
| Electron 打包 (electron-builder) | ✅ 322MB |
| 安装 | 待 GUI 验证 |
| 启动 + 后端自启动 | 待 GUI 验证 |
| WebSocket 连接 | 待 GUI 验证 |
