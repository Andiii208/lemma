import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useMessageStore } from './useMessageStore';

function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((complete) => { resolve = complete; });
  return { promise, resolve };
}

vi.mock('idb-keyval', () => ({
  get: vi.fn(() => Promise.resolve(undefined)),
  set: vi.fn(() => Promise.resolve()),
  del: vi.fn(() => Promise.resolve()),
}));

describe('useMessageStore', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should load empty array when no stored messages', async () => {
    const { result } = renderHook(() => useMessageStore('test-session'));
    await act(async () => {
      await result.current.loadMessages();
    });
    expect(result.current.messages).toEqual([]);
  });

  it('should save and expose messages', async () => {
    const { result } = renderHook(() => useMessageStore('test-session'));
    const testMessages: ClaudeMessage[] = [
      { type: 'text', content: 'hello', metadata: { role: 'user' } },
    ];
    await act(async () => {
      await result.current.saveMessages(testMessages);
    });
    expect(result.current.messages).toEqual(testMessages);
  });

  it('should provide deleteMessages function', () => {
    const { result } = renderHook(() => useMessageStore('test-session'));
    expect(typeof result.current.deleteMessages).toBe('function');
  });

  it('should call idb-keyval set when saving', async () => {
    const { set } = await import('idb-keyval');
    const { result } = renderHook(() => useMessageStore('test-session'));
    const testMessages: ClaudeMessage[] = [
      { type: 'text', content: 'hello', metadata: { role: 'user' } },
    ];
    await act(async () => {
      await result.current.saveMessages(testMessages);
    });
    expect(set).toHaveBeenCalledWith('lemma-messages:test-session', testMessages);
  });

  it('should call idb-keyval del when deleting', async () => {
    const { del } = await import('idb-keyval');
    const { result } = renderHook(() => useMessageStore('test-session'));
    await act(async () => {
      await result.current.deleteMessages();
    });
    expect(del).toHaveBeenCalledWith('lemma-messages:test-session');
    expect(del).toHaveBeenCalledWith('lemma-pending:test-session');
    expect(result.current.messages).toEqual([]);
  });

  it('should restore stored messages on load', async () => {
    const { get } = await import('idb-keyval');
    const storedMessages: ClaudeMessage[] = [
      { type: 'text', content: 'persisted', metadata: { role: 'assistant' } },
    ];
    vi.mocked(get).mockResolvedValueOnce(storedMessages);

    const { result } = renderHook(() => useMessageStore('test-session'));
    await act(async () => {
      await result.current.loadMessages();
    });
    expect(result.current.messages).toEqual(storedMessages);
  });

  it('does not let an old session load overwrite a newer session', async () => {
    const { get } = await import('idb-keyval');
    const oldLoad = deferred<ClaudeMessage[] | undefined>();
    const newMessages: ClaudeMessage[] = [
      { type: 'text', content: 'new session', metadata: { role: 'assistant' } },
    ];
    vi.mocked(get).mockReturnValueOnce(oldLoad.promise).mockResolvedValueOnce(newMessages);
    const { result, rerender } = renderHook(
      ({ sessionId }) => useMessageStore(sessionId),
      { initialProps: { sessionId: 'session-a' as string | null } },
    );

    let oldPromise: Promise<ClaudeMessage[] | null>;
    await act(async () => { oldPromise = result.current.loadMessages(); });
    rerender({ sessionId: 'session-b' });
    await act(async () => { await result.current.loadMessages(); });
    oldLoad.resolve([{ type: 'text', content: 'old session', metadata: {} }]);
    await act(async () => { await oldPromise; });

    expect(result.current.messages).toEqual(newMessages);
    expect(result.current.loadState).toBe('loaded');
  });

  it('migrates legacy default messages into an empty real session once', async () => {
    const { get, set, del } = await import('idb-keyval');
    const legacyMessages: ClaudeMessage[] = [
      { type: 'text', content: 'legacy', metadata: { role: 'user' } },
    ];
    vi.mocked(get).mockResolvedValueOnce([]).mockResolvedValueOnce(legacyMessages);
    const { result } = renderHook(() => useMessageStore(null));

    await act(async () => {
      await result.current.migrateDefaultMessages('real-session');
    });

    expect(set).toHaveBeenCalledWith('lemma-messages:real-session', legacyMessages);
    expect(del).toHaveBeenCalledWith('lemma-messages:default');
  });

  it('returns a failed result and exposes storage errors', async () => {
    const { set } = await import('idb-keyval');
    vi.mocked(set).mockRejectedValueOnce(new Error('quota exceeded'));
    const { result } = renderHook(() => useMessageStore('test-session'));

    const saveResults: Array<Awaited<ReturnType<typeof result.current.saveMessages>>> = [];
    await act(async () => {
      saveResults.push(await result.current.saveMessages([
        { type: 'text', content: 'will fail', metadata: {} },
      ]));
    });

    expect(saveResults[0]?.ok).toBe(false);
    expect(result.current.error).toBe('quota exceeded');
  });

  it('completes a failed current load with empty messages and a non-blocking error', async () => {
    const { get } = await import('idb-keyval');
    vi.mocked(get).mockRejectedValueOnce(new Error('database unavailable'));
    const { result } = renderHook(() => useMessageStore('test-session'));

    let loaded: ClaudeMessage[] | null = null;
    await act(async () => { loaded = await result.current.loadMessages(); });

    expect(loaded).toEqual([]);
    expect(result.current.messages).toEqual([]);
    expect(result.current.loadState).toBe('error');
    expect(result.current.error).toBe('database unavailable');
  });

  it('should skip operations when sessionId is null', async () => {
    const { get, set, del } = await import('idb-keyval');
    const { result } = renderHook(() => useMessageStore(null));

    await act(async () => {
      await result.current.loadMessages();
    });
    expect(get).not.toHaveBeenCalled();

    await act(async () => {
      await result.current.saveMessages([{ type: 'text', content: 'test', metadata: {} }]);
    });
    expect(set).not.toHaveBeenCalled();

    await act(async () => {
      await result.current.deleteMessages();
    });
    expect(del).not.toHaveBeenCalled();
  });

  it('persists and reloads outbound messages under a dedicated session key', async () => {
    const { get, set } = await import('idb-keyval');
    const pending = [{ id: 'pending-1', text: 'queued', status: 'pending' as const }];
    vi.mocked(get).mockResolvedValueOnce(pending);
    const { result } = renderHook(() => useMessageStore('session-a'));

    await act(async () => {
      await result.current.savePendingMessages('session-a', pending);
    });
    const loaded = await result.current.loadPendingMessages('session-a');

    expect(set).toHaveBeenCalledWith('lemma-pending:session-a', pending);
    expect(loaded).toEqual({ ok: true, value: pending });
  });

  it('deletes the pending outbound key after the queue is empty', async () => {
    const { del } = await import('idb-keyval');
    const { result } = renderHook(() => useMessageStore('session-a'));

    await act(async () => {
      await result.current.savePendingMessages('session-a', []);
    });

    expect(del).toHaveBeenCalledWith('lemma-pending:session-a');
  });
});
