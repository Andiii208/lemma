import { app, BrowserWindow, ipcMain, dialog, safeStorage, Notification, shell } from 'electron';
import type { IpcMainInvokeEvent } from 'electron';
import * as path from 'path';
import * as fs from 'fs';
import * as http from 'http';
import { URL } from 'url';
import { ClaudeSdkBridge } from './claude-sdk-bridge';
import { createFailedIpcEvent } from './claude-message-adapter';
import { SessionManager } from './session-manager';
import { presets, getPresetById } from './presets';
import { createRegistry } from './domains/registry';
import { getClaudeMdConfig, createClaudeMd, updateClaudeMd, generateTemplate } from './claude-md-manager';
import { checkSdkVersion } from './version-checker';
import { setupAutoUpdater, downloadUpdate, installUpdate } from './updater';
import { getMcpConfig, addMcpServer, removeMcpServer } from './mcp-config-manager';
import { readStoredApiKey, type StoredApiKeyResult } from './api-key-reader';
import { storeApiKey } from './api-key-storage';
import {
  dispatchChat,
  requireRequestId,
  requireSessionId,
  type ChatIpcOptions,
} from './chat-dispatcher';
import * as chokidar from 'chokidar';
import {
  PDF_WINDOW_OPTIONS,
  assertTrustedSender,
  hasDecryptableApiKey,
  isSafeExternalUrl,
  isTrustedAppUrl,
} from './security';
import { authorizedPaths } from './authorized-paths';
import { readFileWithLimits, listDirectoryWithLimits, debounce } from './main-limits';

let mainWindow: BrowserWindow | null = null;
let claudeBridge: ClaudeSdkBridge | null = null;
let sessionManager: SessionManager | null = null;
let fileWatcher: chokidar.FSWatcher | null = null;
let frontendServer: http.Server | null = null;

const MIME_TYPES: Record<string, string> = {
  '.html': 'text/html',
  '.js': 'application/javascript',
  '.css': 'text/css',
  '.json': 'application/json',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.svg': 'image/svg+xml',
  '.woff2': 'font/woff2',
  '.woff': 'font/woff',
};

/**
 * file:// 协议下 ES modules 被 Chromium CORS 策略阻止，
 * 必须通过 HTTP 服务加载前端资源。
 */
function startFrontendServer(): Promise<number> {
  return new Promise((resolve, reject) => {
    const frontendDir = path.join(__dirname, '..', 'frontend', 'dist');
    frontendServer = http.createServer((req, res) => {
      const parsedUrl = new URL(req.url ?? '/', 'http://localhost');
      let filePath = path.join(frontendDir, parsedUrl.pathname);
      if (filePath.endsWith('/') || filePath.endsWith(path.sep)) {
        filePath = path.join(filePath, 'index.html');
      }
      if (!path.extname(filePath)) {
        filePath += '.html';
      }

      fs.readFile(filePath, (err, data) => {
        if (err) {
          fs.readFile(path.join(frontendDir, 'index.html'), (fallbackErr, fallbackData) => {
            if (fallbackErr) {
              res.writeHead(500);
              res.end('Internal Server Error');
              return;
            }
            res.writeHead(200, { 'Content-Type': 'text/html' });
            res.end(fallbackData);
          });
          return;
        }
        const ext = path.extname(filePath);
        res.writeHead(200, { 'Content-Type': MIME_TYPES[ext] ?? 'application/octet-stream' });
        res.end(data);
      });
    });

    frontendServer.listen(0, '127.0.0.1', () => {
      const addr = frontendServer?.address();
      if (addr && typeof addr === 'object') {
        resolve(addr.port);
      } else {
        reject(new Error('Failed to get server port'));
      }
    });
    frontendServer.on('error', reject);
  });
}

function createWindow(port?: number): void {
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

  mainWindow.webContents.on('will-navigate', (event, url) => {
    if (isTrustedAppUrl(url, port)) return;
    event.preventDefault();
    openSafeExternalUrl(url);
  });
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    openSafeExternalUrl(url);
    return { action: 'deny' };
  });

  if (process.env.NODE_ENV === 'development') {
    mainWindow.loadURL('http://localhost:5173');
    mainWindow.webContents.openDevTools();
  } else if (port) {
    mainWindow.loadURL(`http://127.0.0.1:${port}`);
  }
}

app.whenReady().then(async () => {
  const port = process.env.NODE_ENV === 'development' ? undefined : await startFrontendServer();

  createWindow(port);
  sessionManager = new SessionManager(app.getPath('userData'));
  if (mainWindow) {
    claudeBridge = new ClaudeSdkBridge(mainWindow, sessionManager);
  }
  setupIpcHandlers(port);
  if (mainWindow) {
    setupAutoUpdater(mainWindow);
  }

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow(port);
      if (mainWindow) {
        claudeBridge = new ClaudeSdkBridge(mainWindow, sessionManager ?? undefined);
        setupAutoUpdater(mainWindow);
      }
    }
  });
});

app.on('window-all-closed', () => {
  claudeBridge?.dispose();
  fileWatcher?.close();
  if (process.platform !== 'darwin') {
    frontendServer?.close();
    app.quit();
  }
});

function isPathAllowed(targetPath: string, allowedBase: string): boolean {
  const resolved = path.resolve(targetPath);
  const base = path.resolve(allowedBase);
  return resolved.startsWith(base + path.sep) || resolved === base;
}

function isPathAuthorized(targetPath: string): boolean {
  return authorizedPaths.isPathAllowed(targetPath);
}

function openSafeExternalUrl(url: string): void {
  if (!isSafeExternalUrl(url)) return;
  void shell.openExternal(url).catch(() => undefined);
}

function getStoredApiKey(): StoredApiKeyResult {
  const keyPath = path.join(app.getPath('userData'), 'api-key.encrypted');
  return readStoredApiKey({
    isEncryptionAvailable: () => safeStorage.isEncryptionAvailable(),
    keyExists: () => fs.existsSync(keyPath),
    readEncryptedKey: () => fs.readFileSync(keyPath),
    decryptKey: (encryptedKey) => safeStorage.decryptString(encryptedKey),
  });
}

type TrustedHandler<Arguments extends unknown[], Result> =
  (...args: Arguments) => Result | Promise<Result>;

function registerTrustedHandler<Arguments extends unknown[], Result>(
  channel: string,
  expectedPort: number | undefined,
  handler: TrustedHandler<Arguments, Result>,
): void {
  ipcMain.handle(channel, (event: IpcMainInvokeEvent, ...args: unknown[]) => {
    assertTrustedSender(event.senderFrame?.url ?? '', expectedPort);
    return handler(...args as Arguments);
  });
}

function setupIpcHandlers(expectedPort?: number): void {
  // API Key 安全存储（使用 Electron safeStorage）
  registerTrustedHandler('store-api-key', expectedPort, async (key: string) => {
    return storeApiKey(key, {
      isEncryptionAvailable: () => safeStorage.isEncryptionAvailable(),
      encryptKey: (apiKey) => safeStorage.encryptString(apiKey),
      writeEncryptedKey: (encryptedKey) => {
        const keyPath = path.join(app.getPath('userData'), 'api-key.encrypted');
        fs.writeFileSync(keyPath, encryptedKey);
      },
    });
  });

  registerTrustedHandler('has-api-key', expectedPort, async () => {
    if (!safeStorage.isEncryptionAvailable()) return false;
    const keyPath = path.join(app.getPath('userData'), 'api-key.encrypted');
    if (!fs.existsSync(keyPath)) return false;
    return hasDecryptableApiKey(() => safeStorage.decryptString(fs.readFileSync(keyPath)));
  });

  registerTrustedHandler('delete-api-key', expectedPort, async () => {
    const keyPath = path.join(app.getPath('userData'), 'api-key.encrypted');
    try {
      if (!fs.existsSync(keyPath)) return { success: true, deleted: false };
      fs.unlinkSync(keyPath);
      return { success: true, deleted: true };
    } catch (error: unknown) {
      const reason = error instanceof Error ? error.message : 'Failed to delete API key';
      return { success: false, deleted: false, reason };
    }
  });

  registerTrustedHandler('open-external', expectedPort, async (url: string) => {
    if (!isSafeExternalUrl(url)) {
      return { success: false, reason: 'Only HTTP(S) URLs are allowed' };
    }
    try {
      await shell.openExternal(url);
      return { success: true };
    } catch (error: unknown) {
      const reason = error instanceof Error ? error.message : 'Failed to open external URL';
      return { success: false, reason };
    }
  });

  registerTrustedHandler('chat', expectedPort, async (message: string, options?: ChatIpcOptions) => {
    const requestId = requireRequestId(options?.requestId);
    const sessionId = requireSessionId(options?.sessionId);
    let systemPrompt = options?.systemPrompt;

    if (options?.presetId) {
      const preset = getPresetById(options.presetId);
      if (preset?.systemPrompt) {
        systemPrompt = preset.systemPrompt;
      }
    }

    const result = await dispatchChat(message, { ...options, systemPrompt }, {
      readApiKey: getStoredApiKey,
      sendMessage: async (chatMessage, bridgeOptions) => {
        if (!claudeBridge) throw new Error('Claude bridge not initialized');
        await claudeBridge.sendMessage(chatMessage, requestId, sessionId, bridgeOptions);
      },
    });
    if (!result.ok) {
      mainWindow?.webContents.send('claude-message', createFailedIpcEvent(
        { requestId, sessionId }, result.error, false,
      ));
    }
  });

  registerTrustedHandler('cancel', expectedPort, async () => claudeBridge?.cancel());

  registerTrustedHandler('select-directory', expectedPort, async () => {
    const result = await dialog.showOpenDialog({ properties: ['openDirectory'] });
    const selectedPath = result.filePaths[0] || null;
    if (selectedPath) {
      authorizedPaths.authorize(selectedPath);
    }
    return selectedPath;
  });

  // 会话管理
  registerTrustedHandler('create-session', expectedPort, async (workDir: string, title: string) => {
    return sessionManager?.createSession(workDir, title);
  });
  registerTrustedHandler('list-sessions', expectedPort, async () => sessionManager?.listSessions());
  registerTrustedHandler('load-session', expectedPort, async (id: string) => sessionManager?.loadSession(id));
  registerTrustedHandler('delete-session', expectedPort, async (id: string) => sessionManager?.deleteSession(id));

  // 系统通知
  registerTrustedHandler('notify', expectedPort, async (title: string, body: string) => {
    if (Notification.isSupported()) {
      new Notification({ title, body }).show();
    }
  });

  // 文件操作
  registerTrustedHandler('read-file', expectedPort, async (filePath: string, workDir?: string) => {
    if (!workDir || !isPathAllowed(filePath, workDir)) {
      return { content: null, error: '路径不在工作目录范围内' };
    }
    if (!isPathAuthorized(workDir)) authorizedPaths.authorize(workDir);
    if (!isPathAuthorized(filePath)) {
      return { content: null, error: '路径未授权' };
    }
    return readFileWithLimits(filePath);
  });

  registerTrustedHandler('list-directory', expectedPort, async (dirPath: string, workDir?: string) => {
    if (!workDir || !isPathAllowed(dirPath, workDir)) {
      return [];
    }
    if (!isPathAuthorized(workDir)) authorizedPaths.authorize(workDir);
    if (!isPathAuthorized(dirPath)) {
      return [];
    }
    return listDirectoryWithLimits(dirPath);
  });

  // 预设管理
  registerTrustedHandler('list-presets', expectedPort, async () => presets);
  registerTrustedHandler('get-preset', expectedPort, async (presetId: string) => getPresetById(presetId));

  // Domain 管理
  registerTrustedHandler('list-domains', expectedPort, async () => {
    const baseDir = path.resolve(__dirname, '..', 'domains');
    const registry = createRegistry(baseDir);
    return registry.listDomains();
  });

  // CLAUDE.md 管理
  registerTrustedHandler('get-claude-md', expectedPort, async (workDir: string) => getClaudeMdConfig(workDir));
  registerTrustedHandler('create-claude-md', expectedPort, async (workDir: string, template: string) => {
    createClaudeMd(workDir, template);
    return { success: true };
  });
  registerTrustedHandler('update-claude-md', expectedPort, async (workDir: string, content: string) => {
    updateClaudeMd(workDir, content);
    return { success: true };
  });
  registerTrustedHandler('generate-claude-md-template', expectedPort, async (presetId: string, workDir: string) => {
    return generateTemplate(presetId, workDir);
  });

  // SDK 版本检测
  registerTrustedHandler('check-sdk-version', expectedPort, async () => checkSdkVersion());

  // MCP Server 管理
  registerTrustedHandler('get-mcp-config', expectedPort, async (workDir: string) => getMcpConfig(workDir));
  registerTrustedHandler('add-mcp-server', expectedPort, async (workDir: string, config: unknown) => {
    addMcpServer(workDir, config as { name: string; command: string; args: string[]; env?: Record<string, string> });
    return { success: true };
  });
  registerTrustedHandler('remove-mcp-server', expectedPort, async (workDir: string, name: string) => {
    removeMcpServer(workDir, name);
    return { success: true };
  });

  // 文件变更监听
  registerTrustedHandler('watch-directory', expectedPort, async (dirPath: string) => {
    fileWatcher?.close();
    fileWatcher = chokidar.watch(dirPath, {
      ignored: /(^|[/\\])\.|node_modules/,
      persistent: true,
      ignoreInitial: true,
    });

    const debouncedNotify = debounce((eventName: unknown, filePath: unknown) => {
      mainWindow?.webContents.send('file-changed', { eventName, filePath });
    }, 300);

    fileWatcher.on('all', (eventName, filePath) => {
      debouncedNotify(eventName, filePath);
    });

    return { success: true };
  });

  registerTrustedHandler('unwatch-directory', expectedPort, async () => {
    fileWatcher?.close();
    fileWatcher = null;
    return { success: true };
  });

  // PDF 导出
  registerTrustedHandler('export-pdf', expectedPort, async (htmlContent: string) => {
    const result = await dialog.showSaveDialog({
      filters: [{ name: 'PDF', extensions: ['pdf'] }],
    });
    if (result.canceled || !result.filePath) return { success: false };

    const pdfWindow = new BrowserWindow(PDF_WINDOW_OPTIONS);
    pdfWindow.webContents.on('will-navigate', (event) => event.preventDefault());
    pdfWindow.webContents.setWindowOpenHandler(() => ({ action: 'deny' }));

    try {
      await pdfWindow.loadURL(`data:text/html;charset=utf-8,${encodeURIComponent(htmlContent)}`);
      const pdfData = await pdfWindow.webContents.printToPDF({ printBackground: true });
      fs.writeFileSync(result.filePath, pdfData);
      return { success: true, path: result.filePath };
    } finally {
      if (!pdfWindow.isDestroyed()) pdfWindow.destroy();
    }
  });

  // 自动更新
  registerTrustedHandler('download-update', expectedPort, async () => {
    downloadUpdate();
  });
  registerTrustedHandler('install-update', expectedPort, async () => {
    installUpdate();
  });
}
