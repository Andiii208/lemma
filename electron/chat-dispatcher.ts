import type { StoredApiKeyResult } from './api-key-reader';

export interface ChatDispatchOptions {
  workDir?: string;
  model?: string;
  systemPrompt?: string;
  presetId?: string;
}

export interface ChatIpcOptions extends ChatDispatchOptions {
  requestId: string;
  sessionId: string;
}

export interface ChatBridgeOptions extends ChatDispatchOptions {
  apiKey: string;
}

interface ChatDispatcherDependencies {
  readApiKey: () => StoredApiKeyResult;
  sendMessage: (message: string, options: ChatBridgeOptions) => void | Promise<void>;
}

export type ChatDispatchResult = { ok: true } | { ok: false; error: string };

export function requireSessionId(value: unknown): string {
  if (typeof value !== 'string' || !value.trim()) {
    throw new Error('Session ID is required');
  }
  return value.trim();
}

const UUID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

export function requireRequestId(value: unknown): string {
  if (typeof value !== 'string' || !UUID_PATTERN.test(value)) {
    throw new Error('Request ID is invalid');
  }
  return value;
}

export async function dispatchChat(
  message: string,
  options: ChatDispatchOptions,
  dependencies: ChatDispatcherDependencies,
): Promise<ChatDispatchResult> {
  const storedApiKey = dependencies.readApiKey();
  if (!storedApiKey.ok) return storedApiKey;

  await dependencies.sendMessage(message, { ...options, apiKey: storedApiKey.apiKey });
  return { ok: true };
}
