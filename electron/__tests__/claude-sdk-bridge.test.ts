import { describe, expect, it, vi } from 'vitest';
import type { SDKMessage } from '@anthropic-ai/claude-agent-sdk';
import { ClaudeSdkBridge, type ClaudeQueryRunner } from '../claude-sdk-bridge';
import type { SessionManager } from '../session-manager';

function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((complete) => { resolve = complete; });
  return { promise, resolve };
}

function sdkMessage(value: unknown): SDKMessage {
  return value as SDKMessage;
}

function partial(text: string): SDKMessage {
  return sdkMessage({
    type: 'stream_event',
    event: { type: 'content_block_delta', index: 0, delta: { type: 'text_delta', text } },
    parent_tool_use_id: null,
    uuid: `partial-${text}`,
    session_id: 'claude-session',
  });
}

function success(): SDKMessage {
  return sdkMessage({
    type: 'result',
    subtype: 'success',
    total_cost_usd: 0,
    usage: { input_tokens: 1, output_tokens: 1 },
    modelUsage: {},
    session_id: 'claude-session',
  });
}

function createWindow() {
  const send = vi.fn();
  return { window: { isDestroyed: () => false, webContents: { send } }, send };
}

const firstRequestId = '11111111-1111-4111-8111-111111111111';
const secondRequestId = '22222222-2222-4222-8222-222222222222';
const localSessionId = '33333333-3333-4333-8333-333333333333';

function createSessionManager(claudeSessionId?: string) {
  const loadSession = vi.fn(() => ({
    id: localSessionId, title: 'Local', workDir: '',
    createdAt: '2026-01-01T00:00:00.000Z', lastUsedAt: '2026-01-01T00:00:00.000Z',
    ...(claudeSessionId ? { claudeSessionId } : {}),
  }));
  const updateClaudeSessionId = vi.fn();
  return {
    manager: { loadSession, updateClaudeSessionId } as unknown as SessionManager,
    loadSession,
    updateClaudeSessionId,
  };
}

describe('ClaudeSdkBridge', () => {
  it('resumes with the Claude session stored under the local session id', async () => {
    const runner = vi.fn<ClaudeQueryRunner>(async function* () { yield success(); });
    const { window } = createWindow();
    const sessions = createSessionManager('claude-session-existing');
    const bridge = new ClaudeSdkBridge(window, sessions.manager, runner);

    await bridge.sendMessage('message', firstRequestId, localSessionId, { apiKey: 'key' });

    expect(sessions.loadSession).toHaveBeenCalledWith(localSessionId);
    expect(runner.mock.calls[0][0].options?.resume).toBe('claude-session-existing');
  });

  it('persists the Claude session id from a completed result', async () => {
    const runner: ClaudeQueryRunner = async function* () { yield success(); };
    const { window } = createWindow();
    const sessions = createSessionManager();
    const bridge = new ClaudeSdkBridge(window, sessions.manager, runner);

    await bridge.sendMessage('message', firstRequestId, localSessionId, { apiKey: 'key' });

    expect(sessions.updateClaudeSessionId)
      .toHaveBeenCalledWith(localSessionId, 'claude-session');
  });

  it('cancels the old request and drops its late events', async () => {
    const firstGate = deferred<void>();
    const controllers: AbortController[] = [];
    const runner: ClaudeQueryRunner = async function* ({ options }) {
      const runIndex = controllers.length;
      controllers.push(options!.abortController!);
      if (runIndex === 0) await firstGate.promise;
      yield partial(runIndex === 0 ? 'old' : 'new');
      yield success();
    };
    const { window, send } = createWindow();
    const bridge = new ClaudeSdkBridge(window, undefined, runner);

    const firstRun = bridge.sendMessage('first', firstRequestId, 'session-1', { apiKey: 'key' });
    await Promise.resolve();
    const secondRun = bridge.sendMessage('second', secondRequestId, 'session-1', { apiKey: 'key' });
    await secondRun;
    firstGate.resolve();
    await firstRun;

    expect(controllers[0].signal.aborted).toBe(true);
    expect(send.mock.calls.flatMap((call) => call[1]).some((event) => event.delta === 'old')).toBe(false);
    expect(send.mock.calls.flatMap((call) => call[1]).some((event) => event.delta === 'new')).toBe(true);
  });

  it('does not let an old finally clear the active run', async () => {
    const firstGate = deferred<void>();
    const secondGate = deferred<void>();
    let runCount = 0;
    const controllers: AbortController[] = [];
    const runner: ClaudeQueryRunner = async function* ({ options }) {
      controllers.push(options!.abortController!);
      runCount += 1;
      await (runCount === 1 ? firstGate.promise : secondGate.promise);
      yield success();
    };
    const { window } = createWindow();
    const bridge = new ClaudeSdkBridge(window, undefined, runner);

    const firstRun = bridge.sendMessage('first', firstRequestId, 'session', { apiKey: 'key' });
    await Promise.resolve();
    const secondRun = bridge.sendMessage('second', secondRequestId, 'session', { apiKey: 'key' });
    firstGate.resolve();
    await firstRun;
    bridge.cancel();
    secondGate.resolve();
    await secondRun;

    expect(bridge.isRunning()).toBe(false);
    expect(controllers[1].signal.aborted).toBe(true);
  });

  it('does not emit completed or revive after cancellation', async () => {
    const gate = deferred<void>();
    const runner: ClaudeQueryRunner = async function* () {
      await gate.promise;
      yield success();
    };
    const { window, send } = createWindow();
    const bridge = new ClaudeSdkBridge(window, undefined, runner);
    const run = bridge.sendMessage('message', firstRequestId, 'session', { apiKey: 'key' });
    await Promise.resolve();

    bridge.cancel();
    gate.resolve();
    await run;

    expect(send.mock.calls.flatMap((call) => call[1]).some((event) => event.type === 'completed')).toBe(false);
    expect(bridge.isRunning()).toBe(false);
  });

  it('emits one recoverable failure and never retries a network error', async () => {
    const runner = vi.fn<ClaudeQueryRunner>(async function* () {
      yield* [];
      throw new Error('network connection failed');
    });
    const { window, send } = createWindow();
    const bridge = new ClaudeSdkBridge(window, undefined, runner);

    await bridge.sendMessage('message', firstRequestId, 'session', { apiKey: 'key' });

    expect(runner).toHaveBeenCalledOnce();
    expect(send.mock.calls.at(-1)?.[1]).toMatchObject({
      type: 'failed',
      recoverable: true,
      sessionId: 'session',
    });
  });

  it('rejects an invalid renderer request id before starting the query', async () => {
    const runner = vi.fn<ClaudeQueryRunner>(async function* () { yield success(); });
    const { window } = createWindow();
    const bridge = new ClaudeSdkBridge(window, undefined, runner);

    await expect(bridge.sendMessage('message', 'not-valid', 'session', { apiKey: 'key' }))
      .rejects.toThrow('Request ID is invalid');
    expect(runner).not.toHaveBeenCalled();
  });
});
