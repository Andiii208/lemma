import { act, renderHook, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { useSessionLifecycle } from './useSessionLifecycle';
import type { StoreResult } from './useMessageStore';

function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((complete) => { resolve = complete; });
  return { promise, resolve };
}

const localSession: SessionInfo = {
  id: '11111111-1111-4111-8111-111111111111',
  title: 'New Session',
  workDir: '',
  createdAt: '2026-01-01T00:00:00.000Z',
  lastUsedAt: '2026-01-01T00:00:00.000Z',
};

function createDependencies(currentSessionId: string | null = null, isStreaming = false) {
  return {
    currentSessionId,
    workDir: null,
    isStreaming,
    cancelStream: vi.fn(() => Promise.resolve()),
    clearMessages: vi.fn(),
    deleteMessages: vi.fn<(sessionId?: string) => Promise<StoreResult<void>>>(
      () => Promise.resolve({ ok: true, value: undefined }),
    ),
    migrateDefaultMessages: vi.fn(() => Promise.resolve({ ok: true as const, value: [] })),
    dispatch: vi.fn(),
  };
}

beforeEach(() => {
  Object.defineProperty(window, 'lemmaAPI', {
    writable: true,
    value: {
      createSession: vi.fn(() => Promise.resolve(localSession)),
      listSessions: vi.fn(() => Promise.resolve([localSession])),
      deleteSession: vi.fn(() => Promise.resolve(true)),
    },
  });
});

describe('useSessionLifecycle', () => {
  it('selects the newest session after initial load when current is null', async () => {
    const dependencies = createDependencies();
    renderHook(() => useSessionLifecycle(dependencies));

    await waitFor(() => expect(dependencies.dispatch).toHaveBeenCalledWith({
      type: 'SET_SESSION', payload: localSession.id,
    }));
  });

  it('replaces a missing current session after initial load', async () => {
    const dependencies = createDependencies('missing-session');
    renderHook(() => useSessionLifecycle(dependencies));

    await waitFor(() => expect(dependencies.dispatch).toHaveBeenCalledWith({
      type: 'SET_SESSION', payload: localSession.id,
    }));
  });

  it('keeps null when the initial session list is empty', async () => {
    vi.mocked(window.lemmaAPI!.listSessions).mockResolvedValueOnce([]);
    const dependencies = createDependencies();
    renderHook(() => useSessionLifecycle(dependencies));

    await waitFor(() => expect(window.lemmaAPI?.listSessions).toHaveBeenCalled());
    expect(dependencies.dispatch).not.toHaveBeenCalledWith({
      type: 'SET_SESSION', payload: expect.anything(),
    });
  });

  it('does not overwrite a manual selection made during initial loading', async () => {
    const loading = deferred<SessionInfo[]>();
    vi.mocked(window.lemmaAPI!.listSessions).mockReturnValueOnce(loading.promise);
    const initial = createDependencies();
    const { rerender } = renderHook(
      ({ dependencies }) => useSessionLifecycle(dependencies),
      { initialProps: { dependencies: initial } },
    );
    rerender({ dependencies: createDependencies('manual-session') });

    loading.resolve([localSession]);
    await waitFor(() => expect(window.lemmaAPI?.listSessions).toHaveBeenCalled());

    expect(initial.dispatch).not.toHaveBeenCalledWith({
      type: 'SET_SESSION', payload: localSession.id,
    });
  });

  it('creates a real session, refreshes, selects it, and clears its view', async () => {
    const dependencies = createDependencies();
    const { result } = renderHook(() => useSessionLifecycle(dependencies));
    await waitFor(() => expect(window.lemmaAPI?.listSessions).toHaveBeenCalled());
    dependencies.dispatch.mockClear();

    await act(async () => { await result.current.createAndSelectSession('New Session'); });

    expect(window.lemmaAPI?.createSession).toHaveBeenCalledWith('', 'New Session');
    expect(window.lemmaAPI?.listSessions).toHaveBeenCalled();
    expect(dependencies.migrateDefaultMessages).toHaveBeenCalledWith(localSession.id);
    expect(dependencies.dispatch).toHaveBeenCalledWith({
      type: 'SET_SESSION', payload: localSession.id,
    });
    expect(dependencies.clearMessages).toHaveBeenCalled();
  });

  it('shares one in-flight session creation across concurrent callers', async () => {
    const creation = deferred<SessionInfo>();
    vi.mocked(window.lemmaAPI!.createSession).mockReturnValue(creation.promise);
    const dependencies = createDependencies();
    const { result } = renderHook(() => useSessionLifecycle(dependencies));
    await waitFor(() => expect(window.lemmaAPI?.listSessions).toHaveBeenCalled());

    let first: ReturnType<typeof result.current.createAndSelectSession>;
    let second: ReturnType<typeof result.current.createAndSelectSession>;
    act(() => {
      first = result.current.createAndSelectSession('First');
      second = result.current.createAndSelectSession('Second');
    });

    expect(window.lemmaAPI?.createSession).toHaveBeenCalledTimes(1);
    creation.resolve(localSession);
    await act(async () => { await Promise.all([first, second]); });
  });

  it('cancels an active stream before selecting another session', async () => {
    const dependencies = createDependencies('current-session', true);
    const { result } = renderHook(() => useSessionLifecycle(dependencies));

    await act(async () => { await result.current.selectSession(localSession.id); });

    expect(dependencies.cancelStream).toHaveBeenCalledOnce();
    expect(dependencies.cancelStream.mock.invocationCallOrder[0])
      .toBeLessThan(dependencies.dispatch.mock.invocationCallOrder[0]);
    expect(dependencies.clearMessages).toHaveBeenCalled();
  });

  it('deletes IndexedDB messages and selects the newest remaining session', async () => {
    const remaining = { ...localSession, id: '22222222-2222-4222-8222-222222222222' };
    vi.mocked(window.lemmaAPI!.listSessions).mockResolvedValueOnce([localSession])
      .mockResolvedValueOnce([remaining]);
    const dependencies = createDependencies(localSession.id);
    const { result } = renderHook(() => useSessionLifecycle(dependencies));
    await waitFor(() => expect(window.lemmaAPI?.listSessions).toHaveBeenCalledTimes(1));
    dependencies.dispatch.mockClear();

    await act(async () => { await result.current.deleteSession(localSession.id); });

    expect(window.lemmaAPI?.deleteSession).toHaveBeenCalledWith(localSession.id);
    expect(dependencies.deleteMessages).toHaveBeenCalledWith(localSession.id);
    expect(dependencies.dispatch).toHaveBeenCalledWith({
      type: 'SET_SESSION', payload: remaining.id,
    });
    expect(dependencies.clearMessages).toHaveBeenCalled();
  });

  it('does not fallback or cancel a new stream after the user switches during deletion', async () => {
    const deletion = deferred<boolean>();
    vi.mocked(window.lemmaAPI!.deleteSession).mockReturnValueOnce(deletion.promise);
    const initial = createDependencies(localSession.id);
    const { result, rerender } = renderHook(
      ({ dependencies }) => useSessionLifecycle(dependencies),
      { initialProps: { dependencies: initial } },
    );
    await waitFor(() => expect(window.lemmaAPI?.listSessions).toHaveBeenCalled());
    initial.dispatch.mockClear();

    let deletionPromise: ReturnType<typeof result.current.deleteSession>;
    act(() => { deletionPromise = result.current.deleteSession(localSession.id); });
    const newStreamCancel = vi.fn(() => Promise.resolve());
    const switched = {
      ...initial, currentSessionId: 'manual-session', isStreaming: true,
      cancelStream: newStreamCancel,
    };
    rerender({ dependencies: switched });
    deletion.resolve(true);
    await act(async () => { await deletionPromise; });

    expect(newStreamCancel).not.toHaveBeenCalled();
    expect(initial.dispatch).not.toHaveBeenCalledWith(expect.objectContaining({
      type: 'SET_SESSION',
    }));
  });

  it('lets slow deletion of current A fallback after fast deletion of non-current B', async () => {
    const sessionB = { ...localSession, id: '22222222-2222-4222-8222-222222222222' };
    const sessionC = { ...localSession, id: '33333333-3333-4333-8333-333333333333' };
    const slowDeletion = deferred<boolean>();
    vi.mocked(window.lemmaAPI!.listSessions)
      .mockResolvedValueOnce([localSession, sessionB, sessionC])
      .mockResolvedValueOnce([localSession, sessionC])
      .mockResolvedValueOnce([sessionC]);
    vi.mocked(window.lemmaAPI!.deleteSession).mockImplementation((sessionId) => {
      return sessionId === localSession.id ? slowDeletion.promise : Promise.resolve(true);
    });
    const dependencies = createDependencies(localSession.id);
    const { result } = renderHook(() => useSessionLifecycle(dependencies));
    await waitFor(() => expect(result.current.sessions).toHaveLength(3));
    dependencies.dispatch.mockClear();

    let deleteA: ReturnType<typeof result.current.deleteSession>;
    act(() => { deleteA = result.current.deleteSession(localSession.id); });
    await act(async () => { await result.current.deleteSession(sessionB.id); });
    slowDeletion.resolve(true);
    await act(async () => { await deleteA; });

    expect(dependencies.dispatch).toHaveBeenCalledWith({
      type: 'SET_SESSION', payload: sessionC.id,
    });
  });

  it('does not select a created session after the user manually selects B', async () => {
    const creation = deferred<SessionInfo>();
    vi.mocked(window.lemmaAPI!.createSession).mockReturnValue(creation.promise);
    const dependencies = createDependencies();
    const { result } = renderHook(() => useSessionLifecycle(dependencies));
    await waitFor(() => expect(window.lemmaAPI?.listSessions).toHaveBeenCalled());
    dependencies.dispatch.mockClear();

    let creating: ReturnType<typeof result.current.createAndSelectSession>;
    act(() => { creating = result.current.createAndSelectSession('Delayed'); });
    await act(async () => { await result.current.selectSession('manual-session'); });
    dependencies.dispatch.mockClear();
    dependencies.isStreaming = true;
    creation.resolve(localSession);
    await act(async () => { await creating; });

    expect(dependencies.dispatch).not.toHaveBeenCalledWith({
      type: 'SET_SESSION', payload: localSession.id,
    });
    expect(dependencies.cancelStream).not.toHaveBeenCalled();
  });

  it('keeps the session when the main process reports deletion failure', async () => {
    vi.mocked(window.lemmaAPI!.deleteSession).mockResolvedValueOnce(false);
    const dependencies = createDependencies(localSession.id);
    const { result } = renderHook(() => useSessionLifecycle(dependencies));
    await waitFor(() => expect(result.current.sessions).toEqual([localSession]));

    const outcomes: Array<Awaited<ReturnType<typeof result.current.deleteSession>>> = [];
    await act(async () => { outcomes.push(await result.current.deleteSession(localSession.id)); });

    expect(outcomes[0]?.ok).toBe(false);
    expect(dependencies.deleteMessages).not.toHaveBeenCalled();
    expect(result.current.sessions).toEqual([localSession]);
  });

  it('records retryable cleanup when IndexedDB deletion fails', async () => {
    const remaining = { ...localSession, id: '22222222-2222-4222-8222-222222222222' };
    vi.mocked(window.lemmaAPI!.listSessions).mockResolvedValueOnce([localSession])
      .mockResolvedValueOnce([remaining]);
    const dependencies = createDependencies(localSession.id);
    dependencies.deleteMessages.mockResolvedValueOnce({
      ok: false, error: 'IndexedDB unavailable',
    });
    const { result } = renderHook(() => useSessionLifecycle(dependencies));
    await waitFor(() => expect(result.current.sessions).toEqual([localSession]));

    const outcomes: Array<Awaited<ReturnType<typeof result.current.deleteSession>>> = [];
    await act(async () => { outcomes.push(await result.current.deleteSession(localSession.id)); });

    expect(outcomes[0]).toMatchObject({ ok: false, sessionDeleted: true });
    expect(result.current.pendingStorageCleanup).toEqual({
      sessionId: localSession.id, error: 'IndexedDB unavailable',
    });
    expect(result.current.sessions).toEqual([remaining]);
  });

  it('keeps a filtered known list when refresh fails after deletion', async () => {
    vi.mocked(window.lemmaAPI!.listSessions).mockResolvedValueOnce([localSession])
      .mockRejectedValueOnce(new Error('refresh unavailable'));
    const dependencies = createDependencies(localSession.id);
    const { result } = renderHook(() => useSessionLifecycle(dependencies));
    await waitFor(() => expect(result.current.sessions).toEqual([localSession]));

    const outcomes: Array<Awaited<ReturnType<typeof result.current.deleteSession>>> = [];
    await act(async () => { outcomes.push(await result.current.deleteSession(localSession.id)); });

    expect(outcomes[0]).toMatchObject({ ok: false, sessionDeleted: true });
    expect(result.current.sessions).toEqual([]);
    expect(result.current.error).toContain('refresh unavailable');
  });
});
