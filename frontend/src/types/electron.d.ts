export {};

declare global {
  interface ClaudeMessage {
    type: 'text' | 'tool_use' | 'tool_result' | 'error' | 'recoverable_error' | 'done';
    content: string;
    metadata?: Record<string, unknown>;
  }

  interface ClaudeIpcBase {
    requestId: string;
    sessionId: string;
  }

  interface ClaudeIpcToolEvent extends ClaudeIpcBase {
    toolUseId: string;
    name: string;
    input: unknown;
    output: unknown;
    isError: boolean;
  }

  type ClaudeIpcEvent =
    | (ClaudeIpcBase & { type: 'text_delta'; delta: string })
    | (ClaudeIpcToolEvent & { type: 'tool_started' })
    | (ClaudeIpcToolEvent & { type: 'tool_finished' })
    | (ClaudeIpcBase & {
        type: 'usage'; inputTokens: number; outputTokens: number;
        totalCostUsd: number; model?: string;
      })
    | (ClaudeIpcBase & { type: 'completed'; claudeSessionId: string })
    | (ClaudeIpcBase & {
        type: 'failed'; message: string; errors: string[]; recoverable: boolean;
      });

  interface ChatOptions {
    requestId?: string;
    sessionId?: string;
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
    claudeSessionId?: string;
    totalInputTokens?: number;
    totalOutputTokens?: number;
    estimatedCost?: number;
    model?: string;
  }

  interface FileEntry {
    name: string;
    isDirectory: boolean;
    path: string;
  }

  interface PresetInfo {
    id: string;
    name: string;
    description: string;
    systemPrompt: string;
    icon: string;
  }

  interface ClaudeMdConfig {
    exists: boolean;
    content: string;
    path: string;
  }

  interface SdkVersionInfo {
    sdkVersion: string;
    supported: boolean;
    warning: string | null;
  }

  interface LemmaAPI {
    chat(message: string, options?: ChatOptions): Promise<void>;
    cancel(): Promise<void>;

    storeApiKey(key: string): Promise<{ success: boolean; encrypted?: boolean; reason?: string }>;
    hasApiKey(): Promise<boolean>;
    deleteApiKey(): Promise<{ success: boolean; deleted: boolean; reason?: string }>;
    openExternal(url: string): Promise<{ success: boolean; reason?: string }>;

    selectDirectory(): Promise<string | null>;
    readFile(filePath: string, workDir?: string): Promise<{ content: string | null; error: string | null }>;
    listDirectory(dirPath: string, workDir?: string): Promise<FileEntry[]>;

    createSession(workDir: string, title: string): Promise<SessionInfo>;
    listSessions(): Promise<SessionInfo[]>;
    loadSession(id: string): Promise<SessionInfo | null>;
    deleteSession(id: string): Promise<boolean>;

    notify(title: string, body: string): Promise<void>;

    listPresets(): Promise<PresetInfo[]>;
    getPreset(presetId: string): Promise<PresetInfo | undefined>;

    getClaudeMd(workDir: string): Promise<ClaudeMdConfig>;
    createClaudeMd(workDir: string, template: string): Promise<{ success: boolean }>;
    updateClaudeMd(workDir: string, content: string): Promise<{ success: boolean }>;
    generateClaudeMdTemplate(presetId: string, workDir: string): Promise<string>;

    checkSdkVersion(): Promise<SdkVersionInfo>;

    onClaudeMessage(callback: (message: ClaudeIpcEvent) => void): () => void;

    getMcpConfig(workDir: string): Promise<Array<{ name: string; command: string; args: string[]; env?: Record<string, string> }>>;
    addMcpServer(workDir: string, config: { name: string; command: string; args: string[]; env?: Record<string, string> }): Promise<{ success: boolean }>;
    removeMcpServer(workDir: string, name: string): Promise<{ success: boolean }>;

    watchDirectory(dirPath: string): Promise<{ success: boolean }>;
    unwatchDirectory(): Promise<{ success: boolean }>;
    onFileChanged(callback: (info: { eventName: string; filePath: string }) => void): () => void;

    exportPdf(htmlContent: string): Promise<{ success: boolean; path?: string }>;

    onUpdateAvailable(callback: (info: unknown) => void): () => void;
    onUpdateDownloaded(callback: (info: unknown) => void): () => void;
    onUpdateStateChanged(callback: (data: { state: string; info?: unknown; progress?: unknown; error?: string }) => void): () => void;
    downloadUpdate(): Promise<void>;
    installUpdate(): Promise<void>;
  }

  interface Window {
    lemmaAPI?: LemmaAPI;
  }
}
