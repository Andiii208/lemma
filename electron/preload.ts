import { contextBridge, ipcRenderer } from 'electron';
import type { ClaudeIpcEvent } from './claude-message-adapter';
import type { ChatIpcOptions } from './chat-dispatcher';

contextBridge.exposeInMainWorld('lemmaAPI', {
  // Claude 操作
  chat: (message: string, options?: ChatIpcOptions) =>
    ipcRenderer.invoke('chat', message, options),
  cancel: () => ipcRenderer.invoke('cancel'),

  // 安全存储
  storeApiKey: (key: string) => ipcRenderer.invoke('store-api-key', key),
  hasApiKey: () => ipcRenderer.invoke('has-api-key'),
  deleteApiKey: () => ipcRenderer.invoke('delete-api-key'),
  openExternal: (url: string) => ipcRenderer.invoke('open-external', url),

  // 文件系统
  selectDirectory: () => ipcRenderer.invoke('select-directory'),
  readFile: (filePath: string, workDir?: string) => ipcRenderer.invoke('read-file', filePath, workDir),
  listDirectory: (dirPath: string, workDir?: string) => ipcRenderer.invoke('list-directory', dirPath, workDir),

  // 会话
  createSession: (workDir: string, title: string) =>
    ipcRenderer.invoke('create-session', workDir, title),
  listSessions: () => ipcRenderer.invoke('list-sessions'),
  loadSession: (id: string) => ipcRenderer.invoke('load-session', id),
  deleteSession: (id: string) => ipcRenderer.invoke('delete-session', id),

  // 通知
  notify: (title: string, body: string) =>
    ipcRenderer.invoke('notify', title, body),

  // 预设
  listPresets: () => ipcRenderer.invoke('list-presets'),
  getPreset: (presetId: string) => ipcRenderer.invoke('get-preset', presetId),

  // CLAUDE.md
  getClaudeMd: (workDir: string) => ipcRenderer.invoke('get-claude-md', workDir),
  createClaudeMd: (workDir: string, template: string) =>
    ipcRenderer.invoke('create-claude-md', workDir, template),
  updateClaudeMd: (workDir: string, content: string) =>
    ipcRenderer.invoke('update-claude-md', workDir, content),
  generateClaudeMdTemplate: (presetId: string, workDir: string) =>
    ipcRenderer.invoke('generate-claude-md-template', presetId, workDir),

  // SDK 版本
  checkSdkVersion: () => ipcRenderer.invoke('check-sdk-version'),

  // 监听
  onClaudeMessage: (callback: (message: ClaudeIpcEvent) => void) => {
    const handler = (_event: unknown, message: ClaudeIpcEvent) => callback(message);
    ipcRenderer.on('claude-message', handler);
    return () => ipcRenderer.removeListener('claude-message', handler);
  },

  // MCP Server 管理
  getMcpConfig: (workDir: string) => ipcRenderer.invoke('get-mcp-config', workDir),
  addMcpServer: (workDir: string, config: unknown) => ipcRenderer.invoke('add-mcp-server', workDir, config),
  removeMcpServer: (workDir: string, name: string) => ipcRenderer.invoke('remove-mcp-server', workDir, name),

  // 文件变更监听
  watchDirectory: (dirPath: string) => ipcRenderer.invoke('watch-directory', dirPath),
  unwatchDirectory: () => ipcRenderer.invoke('unwatch-directory'),
  onFileChanged: (callback: (info: unknown) => void) => {
    const handler = (_event: unknown, info: unknown) => callback(info);
    ipcRenderer.on('file-changed', handler);
    return () => ipcRenderer.removeListener('file-changed', handler);
  },

  // PDF 导出
  exportPdf: (htmlContent: string) => ipcRenderer.invoke('export-pdf', htmlContent),

  // 自动更新
  onUpdateStateChanged: (callback: (data: { state: string; info?: unknown; progress?: unknown; error?: string }) => void) => {
    const handler = (_event: unknown, data: { state: string; info?: unknown; progress?: unknown; error?: string }) => callback(data);
    ipcRenderer.on('update-state-changed', handler);
    return () => ipcRenderer.removeListener('update-state-changed', handler);
  },
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
});
