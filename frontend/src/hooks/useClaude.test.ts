import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { createRequestId, useClaude } from './useClaude';

// Mock lemmaAPI functions
const mockUnsubscribe = vi.fn();
const mockOnClaudeMessage = vi.fn<(callback: (message: unknown) => void) => () => void>(
  () => mockUnsubscribe
);
const mockChat = vi.fn<(message: string, options?: ChatOptions) => Promise<void>>(
  () => Promise.resolve(),
);
const mockCancel = vi.fn(() => Promise.resolve());
const mockNotify = vi.fn(() => Promise.resolve());
const activeSessionId = 'session-1';

function renderClaude(sessionId = activeSessionId) {
  return renderHook(() => useClaude(sessionId));
}

async function beginRequest(result: ReturnType<typeof renderClaude>['result']): Promise<string> {
  await act(async () => result.current.sendMessage('Prompt'));
  const requestId = mockChat.mock.calls[mockChat.mock.calls.length - 1][1]?.requestId;
  if (!requestId) throw new Error('Expected requestId');
  act(() => result.current.clearMessages());
  return requestId;
}

// Mock requestAnimationFrame / cancelAnimationFrame for jsdom
let rafCallbacks: Array<() => void> = [];
let rafIdCounter = 0;

beforeEach(() => {
  rafCallbacks = [];
  rafIdCounter = 0;

  vi.stubGlobal('requestAnimationFrame', (callback: FrameRequestCallback) => {
    const id = ++rafIdCounter;
    rafCallbacks.push(() => callback(performance.now()));
    return id;
  });

  vi.stubGlobal('cancelAnimationFrame', (_id: number) => {
    // Simple mock — just clear the queue
    rafCallbacks = [];
  });

  // Set up window.lemmaAPI mock
  Object.defineProperty(window, 'lemmaAPI', {
    writable: true,
    value: {
      onClaudeMessage: mockOnClaudeMessage,
      chat: mockChat,
      cancel: mockCancel,
      notify: mockNotify,
    },
  });
});

afterEach(() => {
  vi.clearAllMocks();
});

describe('useClaude', () => {
  it('should initialize with empty messages', () => {
    const { result } = renderClaude();
    expect(result.current.messages).toEqual([]);
    expect(result.current.isStreaming).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it('should add user message optimistically when sending', async () => {
    const { result } = renderClaude();
    await act(async () => {
      result.current.sendMessage('Hello');
    });
    expect(result.current.messages).toHaveLength(1);
    expect(result.current.messages[0]).toEqual({
      type: 'text',
      content: 'Hello',
      metadata: { role: 'user' },
    });
    expect(mockChat).toHaveBeenCalledWith('Hello', expect.objectContaining({
      sessionId: activeSessionId,
      requestId: expect.stringMatching(/^[0-9a-f-]{36}$/i),
    }));
  });

  it('should set isStreaming to true when sending', async () => {
    const { result } = renderClaude();
    await act(async () => {
      result.current.sendMessage('Hello');
    });
    expect(result.current.isStreaming).toBe(true);
  });

  it('should clear messages and error', () => {
    const { result } = renderClaude();
    act(() => {
      result.current.clearMessages();
    });
    expect(result.current.messages).toEqual([]);
    expect(result.current.error).toBeNull();
  });

  it('should register IPC listener on mount', () => {
    renderClaude();
    expect(mockOnClaudeMessage).toHaveBeenCalledTimes(1);
  });

  it('merges text chunks from the same request into one assistant message', async () => {
    const { result } = renderClaude();
    const requestId = await beginRequest(result);

    // Get the callback registered with onClaudeMessage
    const messageHandler = mockOnClaudeMessage.mock.calls[0][0];

    // Simulate incoming streaming tokens
    act(() => {
      messageHandler({ type: 'text_delta', requestId, sessionId: 'session-1', delta: 'Hello' });
      messageHandler({ type: 'text_delta', requestId, sessionId: 'session-1', delta: ' World' });
    });

    // Messages should NOT be in state yet (buffered)
    expect(result.current.messages).toHaveLength(0);

    // Flush rAF callbacks
    act(() => {
      rafCallbacks.forEach((cb) => cb());
      rafCallbacks = [];
    });

    // Now messages should appear in state
    expect(result.current.messages).toHaveLength(1);
    expect(result.current.messages[0].content).toBe('Hello World');
  });

  it('preserves text, tool, text order instead of merging across the tool', async () => {
    const { result } = renderClaude();
    const requestId = await beginRequest(result);
    const messageHandler = mockOnClaudeMessage.mock.calls[0][0];

    act(() => {
      messageHandler({ type: 'text_delta', requestId, sessionId: 'session-1', delta: 'Before' });
      messageHandler({
        type: 'tool_started', requestId, sessionId: 'session-1',
        toolUseId: 'tool-1', name: 'Read', input: {}, output: null, isError: false,
      });
      messageHandler({ type: 'text_delta', requestId, sessionId: 'session-1', delta: ' after' });
      rafCallbacks.forEach((callback) => callback());
      rafCallbacks = [];
    });

    expect(result.current.messages.map((message) => [message.type, message.content])).toEqual([
      ['text', 'Before'],
      ['tool_use', JSON.stringify({ id: 'tool-1', name: 'Read', input: {} })],
      ['text', ' after'],
    ]);
  });

  it('should flush remaining buffer on done message', async () => {
    const { result } = renderClaude();
    const requestId = await beginRequest(result);

    const messageHandler = mockOnClaudeMessage.mock.calls[0][0];

    act(() => {
      messageHandler({ type: 'text_delta', requestId, sessionId: 'session-1', delta: 'token' });
      messageHandler({
        type: 'completed',
        requestId,
        sessionId: 'session-1',
        claudeSessionId: 'claude-session-1',
      });
    });

    expect(result.current.messages).toHaveLength(1);
    expect(result.current.messages[0].content).toBe('token');
    expect(result.current.isStreaming).toBe(false);
  });

  it('should unsubscribe listener on unmount', () => {
    const { unmount } = renderClaude();
    expect(mockOnClaudeMessage).toHaveBeenCalled();
    unmount();
    // Verify cleanup was called
    expect(mockUnsubscribe).toHaveBeenCalled();
  });

  it('should set error state on error message', async () => {
    const { result } = renderClaude();
    const requestId = await beginRequest(result);
    const messageHandler = mockOnClaudeMessage.mock.calls[0][0];

    act(() => {
      messageHandler({
        type: 'failed', requestId, sessionId: 'session-1',
        message: 'Something went wrong', errors: ['Something went wrong'], recoverable: false,
      });
    });

    expect(result.current.error).toBe('Something went wrong');
    expect(result.current.isStreaming).toBe(false);
  });

  it('tracks usage without adding it to chat messages', async () => {
    const { result } = renderClaude();
    const requestId = await beginRequest(result);
    const messageHandler = mockOnClaudeMessage.mock.calls[0][0];

    act(() => {
      messageHandler({
        type: 'usage', requestId, sessionId: 'session-1',
        inputTokens: 10, outputTokens: 4, totalCostUsd: 0.01, model: 'claude-sonnet',
      });
    });

    expect(result.current.tokenCounts).toEqual({ input: 10, output: 4 });
    expect(result.current.usageData).toEqual({
      inputTokens: 10, outputTokens: 4, totalCostUsd: 0.01, model: 'claude-sonnet',
    });
    expect(result.current.messages).toEqual([]);
  });

  it('maps tool lifecycle events into display messages', async () => {
    const { result } = renderClaude();
    const requestId = await beginRequest(result);
    const messageHandler = mockOnClaudeMessage.mock.calls[0][0];

    act(() => {
      messageHandler({
        type: 'tool_started', requestId, sessionId: 'session-1',
        toolUseId: 'tool-1', name: 'Read', input: { file_path: 'README.md' },
        output: null, isError: false,
      });
      messageHandler({
        type: 'tool_finished', requestId, sessionId: 'session-1',
        toolUseId: 'tool-1', name: 'Read', input: { file_path: 'README.md' },
        output: 'contents', isError: false,
      });
      rafCallbacks.forEach((callback) => callback());
      rafCallbacks = [];
    });

    expect(result.current.messages.map((message) => message.type)).toEqual(['tool_use', 'tool_result']);
    expect(result.current.messages[1].content).toContain('contents');
  });

  it('ignores incomplete tool events and usage with an invalid model', async () => {
    const { result } = renderClaude();
    const requestId = await beginRequest(result);
    const messageHandler = mockOnClaudeMessage.mock.calls[0][0];

    act(() => {
      messageHandler({
        type: 'tool_started', requestId, sessionId: activeSessionId,
        toolUseId: 'tool-1', name: 'Read', output: null, isError: false,
      });
      messageHandler({
        type: 'tool_started', requestId, sessionId: activeSessionId,
        toolUseId: 'tool-2', name: 'Read', input: {}, isError: false,
      });
      messageHandler({
        type: 'tool_finished', requestId, sessionId: activeSessionId,
        toolUseId: 'tool-1', name: 'Read', input: {}, isError: false,
      });
      messageHandler({
        type: 'usage', requestId, sessionId: activeSessionId,
        inputTokens: 10, outputTokens: 4, totalCostUsd: 0.01, model: 42,
      });
      rafCallbacks.forEach((callback) => callback());
      rafCallbacks = [];
    });

    expect(result.current.messages).toEqual([]);
    expect(result.current.tokenCounts).toEqual({ input: 0, output: 0 });
    expect(result.current.error).toBeNull();
  });

  it('ignores all events belonging to another session', async () => {
    const { result } = renderClaude();
    await act(async () => result.current.sendMessage('Hello'));
    const messageHandler = mockOnClaudeMessage.mock.calls[0][0];

    act(() => {
      messageHandler({ type: 'text_delta', requestId: 'foreign', sessionId: 'session-2', delta: 'wrong' });
      messageHandler({
        type: 'usage', requestId: 'foreign', sessionId: 'session-2',
        inputTokens: 10, outputTokens: 4, totalCostUsd: 0.01,
      });
      messageHandler({
        type: 'failed', requestId: 'foreign', sessionId: 'session-2',
        message: 'wrong', errors: ['wrong'], recoverable: false,
      });
      messageHandler({
        type: 'completed', requestId: 'foreign', sessionId: 'session-2',
        claudeSessionId: 'claude-session-2',
      });
    });

    expect(result.current.messages).toHaveLength(1);
    expect(result.current.error).toBeNull();
    expect(result.current.tokenCounts).toEqual({ input: 0, output: 0 });
    expect(result.current.isStreaming).toBe(true);
    expect(mockNotify).not.toHaveBeenCalled();
  });

  it('drops queued events from a superseded request in the same session', async () => {
    const { result } = renderClaude();
    await act(async () => result.current.sendMessage('First'));
    const firstId = mockChat.mock.calls[0][1]?.requestId;
    const messageHandler = mockOnClaudeMessage.mock.calls[0][0];
    act(() => messageHandler({
      type: 'text_delta', requestId: firstId, sessionId: activeSessionId, delta: 'old queued',
    }));

    await act(async () => result.current.sendMessage('Second'));
    const secondId = mockChat.mock.calls[1][1]?.requestId;
    act(() => {
      messageHandler({
        type: 'usage', requestId: firstId, sessionId: activeSessionId,
        inputTokens: 99, outputTokens: 99, totalCostUsd: 1,
      });
      messageHandler({
        type: 'completed', requestId: firstId, sessionId: activeSessionId,
        claudeSessionId: 'old-claude-session',
      });
      messageHandler({
        type: 'text_delta', requestId: secondId, sessionId: activeSessionId, delta: 'new',
      });
      rafCallbacks.forEach((callback) => callback());
      rafCallbacks = [];
    });

    expect(firstId).not.toBe(secondId);
    expect(result.current.messages.map((message) => message.content)).toEqual(['First', 'Second', 'new']);
    expect(result.current.tokenCounts).toEqual({ input: 0, output: 0 });
    expect(result.current.isStreaming).toBe(true);
    expect(mockNotify).not.toHaveBeenCalled();
  });

  it('uses crypto.getRandomValues when randomUUID is unavailable', () => {
    const secureCrypto = {
      getRandomValues: (bytes: Uint8Array) => {
        bytes.set([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]);
        return bytes;
      },
    };

    expect(createRequestId(secureCrypto)).toMatch(
      /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/,
    );
  });

  it('should clear error with clearError', async () => {
    const { result } = renderClaude();
    const requestId = await beginRequest(result);
    const messageHandler = mockOnClaudeMessage.mock.calls[0][0];

    act(() => {
      messageHandler({
        type: 'failed', requestId, sessionId: 'session-1',
        message: 'test error', errors: ['test error'], recoverable: false,
      });
    });
    expect(result.current.error).toBe('test error');

    act(() => {
      result.current.clearError();
    });
    expect(result.current.error).toBeNull();
  });

  it('should flush buffer and set isStreaming false on cancelStream', async () => {
    const { result } = renderClaude();

    await act(async () => {
      result.current.sendMessage('Hello');
    });
    expect(result.current.isStreaming).toBe(true);

    const messageHandler = mockOnClaudeMessage.mock.calls[0][0];
    const requestId = mockChat.mock.calls[mockChat.mock.calls.length - 1][1]?.requestId;

    // Buffer a message during streaming
    act(() => {
      messageHandler({ type: 'text_delta', requestId, sessionId: 'session-1', delta: 'partial' });
    });

    await act(async () => {
      result.current.cancelStream();
    });

    expect(mockCancel).toHaveBeenCalled();
    expect(result.current.isStreaming).toBe(false);
    // Buffered message should have been flushed
    expect(result.current.messages.some((m: ClaudeMessage) => m.content === 'partial')).toBe(true);
  });

  it('should handle sendMessage IPC failure', async () => {
    mockChat.mockRejectedValueOnce(new Error('IPC failed'));
    const { result } = renderClaude();

    await act(async () => {
      result.current.sendMessage('test');
    });

    expect(result.current.error).toBe('IPC failed');
    expect(result.current.isStreaming).toBe(false);
  });

  it('resets request, stream state, usage, messages, and buffered events on session change', async () => {
    const { result, rerender } = renderHook(
      ({ sessionId }) => useClaude(sessionId),
      { initialProps: { sessionId: 'session-1' as string | null } },
    );
    await act(async () => result.current.sendMessage('Prompt'));
    const requestId = mockChat.mock.calls[mockChat.mock.calls.length - 1]?.[1]?.requestId;
    const messageHandler = mockOnClaudeMessage.mock.calls[0][0];
    act(() => {
      messageHandler({
        type: 'usage', requestId, sessionId: 'session-1',
        inputTokens: 12, outputTokens: 5, totalCostUsd: 0.1, model: 'claude-sonnet',
      });
      messageHandler({ type: 'text_delta', requestId, sessionId: 'session-1', delta: 'old' });
    });

    rerender({ sessionId: 'session-2' });
    act(() => {
      rafCallbacks.forEach((callback) => callback());
      rafCallbacks = [];
    });

    expect(result.current.messages).toEqual([]);
    expect(result.current.isStreaming).toBe(false);
    expect(result.current.error).toBeNull();
    expect(result.current.tokenCounts).toEqual({ input: 0, output: 0 });
    expect(result.current.usageData).toEqual({ inputTokens: 0, outputTokens: 0, totalCostUsd: 0 });
  });

  it('resets an existing error when the session changes', async () => {
    mockChat.mockRejectedValueOnce(new Error('failed'));
    const { result, rerender } = renderHook(
      ({ sessionId }) => useClaude(sessionId),
      { initialProps: { sessionId: 'session-1' as string | null } },
    );
    await act(async () => result.current.sendMessage('Prompt'));
    expect(result.current.error).toBe('failed');

    rerender({ sessionId: 'session-2' });

    expect(result.current.error).toBeNull();
  });

});
