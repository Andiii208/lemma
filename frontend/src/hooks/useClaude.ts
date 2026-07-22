import { useState, useEffect, useCallback, useRef } from 'react';

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null;
}

function hasEventBase(value: Record<string, unknown>): boolean {
  return typeof value.requestId === 'string' && typeof value.sessionId === 'string';
}

function isToolEvent(value: Record<string, unknown>): boolean {
  return typeof value.toolUseId === 'string'
    && typeof value.name === 'string'
    && typeof value.isError === 'boolean';
}

function hasOwn(value: Record<string, unknown>, key: string): boolean {
  return Object.prototype.hasOwnProperty.call(value, key);
}

function isClaudeIpcEvent(value: unknown): value is ClaudeIpcEvent {
  if (!isRecord(value) || !hasEventBase(value)) return false;
  switch (value.type) {
    case 'text_delta': return typeof value.delta === 'string';
    case 'tool_started': return isToolEvent(value)
      && hasOwn(value, 'input') && hasOwn(value, 'output');
    case 'tool_finished': return isToolEvent(value)
      && hasOwn(value, 'input') && hasOwn(value, 'output');
    case 'usage': return typeof value.inputTokens === 'number'
      && typeof value.outputTokens === 'number' && typeof value.totalCostUsd === 'number'
      && (value.model === undefined || typeof value.model === 'string');
    case 'completed': return typeof value.claudeSessionId === 'string';
    case 'failed': return typeof value.message === 'string'
      && Array.isArray(value.errors) && value.errors.every((error) => typeof error === 'string')
      && typeof value.recoverable === 'boolean';
    default: return false;
  }
}

function requestIdOf(message: ClaudeMessage): unknown {
  return message.metadata?.requestId;
}

interface RequestIdCrypto {
  randomUUID?: () => string;
  getRandomValues(bytes: Uint8Array): Uint8Array;
}

export function createRequestId(source: RequestIdCrypto = globalThis.crypto): string {
  if (source.randomUUID) return source.randomUUID();
  const bytes = source.getRandomValues(new Uint8Array(16));
  bytes[6] = (bytes[6] & 0x0f) | 0x40;
  bytes[8] = (bytes[8] & 0x3f) | 0x80;
  const hex = Array.from(bytes, (byte) => byte.toString(16).padStart(2, '0'));
  return `${hex.slice(0, 4).join('')}-${hex.slice(4, 6).join('')}`
    + `-${hex.slice(6, 8).join('')}-${hex.slice(8, 10).join('')}`
    + `-${hex.slice(10).join('')}`;
}

function mergeMessages(previous: ClaudeMessage[], incoming: ClaudeMessage[]): ClaudeMessage[] {
  const merged = [...previous];
  for (const message of incoming) {
    const previousMessage = merged[merged.length - 1];
    const isContinuousText = message.type === 'text' && previousMessage?.type === 'text'
      && message.metadata?.role === 'assistant'
      && requestIdOf(message) === requestIdOf(previousMessage);
    if (isContinuousText && previousMessage) {
      merged[merged.length - 1] = {
        ...previousMessage, content: previousMessage.content + message.content,
      };
    } else {
      merged.push(message);
    }
  }
  return merged;
}

function displayMessage(event: ClaudeIpcEvent): ClaudeMessage | null {
  const metadata = { role: 'assistant', requestId: event.requestId, sessionId: event.sessionId };
  if (event.type === 'text_delta') return { type: 'text', content: event.delta, metadata };
  if (event.type === 'tool_started') {
    return { type: 'tool_use', content: JSON.stringify({
      id: event.toolUseId, name: event.name, input: event.input,
    }), metadata };
  }
  if (event.type === 'tool_finished') {
    return { type: 'tool_result', content: JSON.stringify({
      tool_use_id: event.toolUseId, name: event.name, input: event.input,
      output: event.output, is_error: event.isError,
    }), metadata };
  }
  return null;
}

export function useClaude(activeSessionId: string | null, onNotify?: (title: string, body: string) => void) {
  const [messages, setMessages] = useState<ClaudeMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [tokenCounts, setTokenCounts] = useState({ input: 0, output: 0 });
  const [usageData, setUsageData] = useState<{
    inputTokens: number;
    outputTokens: number;
    totalCostUsd: number;
    model?: string;
  }>({ inputTokens: 0, outputTokens: 0, totalCostUsd: 0 });
  const messageBufferRef = useRef<ClaudeMessage[]>([]);
  const rafIdRef = useRef<number | null>(null);
  const completedRequestsRef = useRef(new Set<string>());
  const activeRequestIdRef = useRef<string | null>(null);

  const flushMessages = useCallback(() => {
    rafIdRef.current = null;
    if (messageBufferRef.current.length === 0) return;
    const buffered = messageBufferRef.current;
    messageBufferRef.current = [];
    setMessages((previous) => mergeMessages(previous, buffered));
  }, []);

  const scheduleFlush = useCallback(() => {
    if (rafIdRef.current !== null) return;
    rafIdRef.current = requestAnimationFrame(flushMessages);
  }, [flushMessages]);

  const bufferMessage = useCallback((message: ClaudeMessage) => {
    messageBufferRef.current.push(message);
    scheduleFlush();
  }, [scheduleFlush]);

  const cancelPendingRaf = useCallback(() => {
    if (rafIdRef.current === null) return;
    cancelAnimationFrame(rafIdRef.current);
    rafIdRef.current = null;
  }, []);

  useEffect(() => {
    activeRequestIdRef.current = null;
    cancelPendingRaf();
    messageBufferRef.current = [];
    completedRequestsRef.current.clear();
    setMessages([]);
    setIsStreaming(false);
    setError(null);
    setTokenCounts({ input: 0, output: 0 });
    setUsageData({ inputTokens: 0, outputTokens: 0, totalCostUsd: 0 });
  }, [activeSessionId, cancelPendingRaf]);

  useEffect(() => {
    if (!window.lemmaAPI) return;
    const unsubscribe = window.lemmaAPI.onClaudeMessage((runtimeEvent: unknown) => {
      if (!isClaudeIpcEvent(runtimeEvent)) return;
      if (runtimeEvent.sessionId !== activeSessionId) return;
      if (runtimeEvent.requestId !== activeRequestIdRef.current) return;
      const message = displayMessage(runtimeEvent);
      if (message) bufferMessage(message);
      if (runtimeEvent.type === 'usage') {
        setTokenCounts((previous) => ({
          input: previous.input + runtimeEvent.inputTokens,
          output: previous.output + runtimeEvent.outputTokens,
        }));
        setUsageData((previous) => ({
          inputTokens: previous.inputTokens + runtimeEvent.inputTokens,
          outputTokens: previous.outputTokens + runtimeEvent.outputTokens,
          totalCostUsd: previous.totalCostUsd + runtimeEvent.totalCostUsd,
          model: runtimeEvent.model ?? previous.model,
        }));
      }
      if (runtimeEvent.type === 'failed') {
        cancelPendingRaf();
        flushMessages();
        setError(runtimeEvent.message);
        setIsStreaming(false);
        activeRequestIdRef.current = null;
      }
      if (runtimeEvent.type === 'completed') {
        cancelPendingRaf();
        flushMessages();
        setIsStreaming(false);
        activeRequestIdRef.current = null;
        if (!completedRequestsRef.current.has(runtimeEvent.requestId)) {
          completedRequestsRef.current.add(runtimeEvent.requestId);
          onNotify?.('Lemma', 'Claude 已完成回复');
        }
      }
    });
    return () => {
      unsubscribe();
      cancelPendingRaf();
      messageBufferRef.current = [];
    };
  }, [activeSessionId, bufferMessage, cancelPendingRaf, flushMessages, onNotify]);

  const sendMessage = useCallback(async (
    text: string,
    options?: ChatOptions,
  ) => {
    if (!window.lemmaAPI) {
      setError('Electron IPC 不可用');
      return;
    }
    if (!activeSessionId) {
      setError('Session is required');
      return;
    }
    const requestId = createRequestId();
    activeRequestIdRef.current = requestId;
    cancelPendingRaf();
    messageBufferRef.current = [];
    setIsStreaming(true);
    setError(null);
    setMessages((previous) => [...previous, {
      type: 'text', content: text, metadata: { role: 'user' },
    }]);
    try {
      await window.lemmaAPI.chat(text, { ...options, requestId, sessionId: activeSessionId });
    } catch (sendError: unknown) {
      if (activeRequestIdRef.current !== requestId) return;
      activeRequestIdRef.current = null;
      setError(sendError instanceof Error ? sendError.message : '发送失败');
      setIsStreaming(false);
    }
  }, [activeSessionId, cancelPendingRaf]);

  const cancelStream = useCallback(async () => {
    if (!window.lemmaAPI) return;
    await window.lemmaAPI.cancel();
    activeRequestIdRef.current = null;
    cancelPendingRaf();
    flushMessages();
    setIsStreaming(false);
  }, [cancelPendingRaf, flushMessages]);

  const clearMessages = useCallback(() => {
    messageBufferRef.current = [];
    completedRequestsRef.current.clear();
    setMessages([]);
    setError(null);
    setTokenCounts({ input: 0, output: 0 });
    setUsageData({ inputTokens: 0, outputTokens: 0, totalCostUsd: 0 });
  }, []);

  const clearError = useCallback(() => setError(null), []);
  const setMessagesExternal = useCallback((newMessages: ClaudeMessage[]) => {
    setMessages(newMessages);
  }, []);

  return {
    messages, isStreaming, error, tokenCounts, usageData, sendMessage, cancelStream,
    clearMessages, clearError, setMessages: setMessagesExternal,
  };
}
