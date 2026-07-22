import { act, renderHook, waitFor } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import {
  deleteSessionWithOutbox, useSessionMessageQueue,
} from './useSessionMessageQueue';
import type { PendingOutbound, StoreResult } from './useMessageStore';

const createdSession: SessionInfo = {
  id: '11111111-1111-4111-8111-111111111111',
  title: 'First',
  workDir: '',
  createdAt: '2026-01-01T00:00:00.000Z',
  lastUsedAt: '2026-01-01T00:00:00.000Z',
};
const sessionB = '22222222-2222-4222-8222-222222222222';

function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((complete) => { resolve = complete; });
  return { promise, resolve };
}

function createPersistence(initial: PendingOutbound[] = []) {
  let persisted = [...initial];
  const history: PendingOutbound[][] = [];
  const loadPendingMessages = vi.fn(() => Promise.resolve<StoreResult<PendingOutbound[]>>({
    ok: true, value: [...persisted],
  }));
  const savePendingMessages = vi.fn((
    _sessionId: string, pending: PendingOutbound[],
  ) => {
    persisted = [...pending];
    history.push([...pending]);
    return Promise.resolve<StoreResult<void>>({ ok: true, value: undefined });
  });
  return {
    loadPendingMessages, savePendingMessages,
    persisted: () => persisted, history: () => history,
  };
}

describe('useSessionMessageQueue', () => {
  it.each([
    { deleted: false, expected: 'rollbackClear' },
    { deleted: true, expected: 'commitClear' },
  ])('finalizes App deletion with $expected when deleted=$deleted', async ({ deleted, expected }) => {
    const token = { id: 'clear-token', sessionId: createdSession.id };
    const controls = {
      beginClear: vi.fn(() => token),
      commitClear: vi.fn(() => Promise.resolve({ ok: true as const, value: undefined })),
      rollbackClear: vi.fn(() => Promise.resolve({ ok: true as const, value: undefined })),
    };
    const deleteSession = vi.fn(() => Promise.resolve({
      ok: deleted, sessionDeleted: deleted, ...(deleted ? {} : { error: 'failed' }),
    }));

    await deleteSessionWithOutbox(createdSession.id, controls, deleteSession);

    expect(controls.beginClear).toHaveBeenCalledWith(createdSession.id);
    expect(controls[expected as 'commitClear' | 'rollbackClear']).toHaveBeenCalledWith(token);
  });

  it('persists concurrent first messages and sends them once in order after A binds', async () => {
    const creation = deferred<SessionInfo | null>();
    const createAndSelectSession = vi.fn(() => creation.promise);
    const sendMessage = vi.fn<(message: string) => Promise<void>>(() => Promise.resolve());
    const persistence = createPersistence();
    const { result, rerender } = renderHook(
      ({ sessionId, isBound }) => useSessionMessageQueue({
        sessionId, isBound, createAndSelectSession, sendMessage, ...persistence,
      }),
      { initialProps: { sessionId: null as string | null, isBound: false } },
    );

    let first: Promise<void>;
    let second: Promise<void>;
    act(() => {
      first = result.current.enqueueMessage('first');
      second = result.current.enqueueMessage('second');
    });
    expect(createAndSelectSession).toHaveBeenCalledTimes(1);
    creation.resolve(createdSession);
    await waitFor(() => expect(persistence.persisted()).toHaveLength(2));

    rerender({ sessionId: createdSession.id, isBound: true });
    await act(async () => { await Promise.all([first, second]); });

    expect(sendMessage.mock.calls).toEqual([['first'], ['second']]);
    expect(persistence.persisted()).toEqual([]);
    expect(persistence.history().flat().some((item) => item.status === 'sending')).toBe(true);
  });

  it('does not call chat while B is active and sends only after A becomes active', async () => {
    const creation = deferred<SessionInfo | null>();
    const sendMessage = vi.fn<(message: string) => Promise<void>>(() => Promise.resolve());
    const persistence = createPersistence();
    const { result, rerender } = renderHook(
      ({ sessionId, isBound }) => useSessionMessageQueue({
        sessionId, isBound, sendMessage, ...persistence,
        createAndSelectSession: () => creation.promise,
      }),
      { initialProps: { sessionId: null as string | null, isBound: false } },
    );

    act(() => { void result.current.enqueueMessage('for A'); });
    rerender({ sessionId: sessionB, isBound: true });
    creation.resolve(createdSession);
    await waitFor(() => expect(persistence.persisted()).toHaveLength(1));
    expect(sendMessage).not.toHaveBeenCalled();

    rerender({ sessionId: createdSession.id, isBound: true });
    await waitFor(() => expect(sendMessage).toHaveBeenCalledWith('for A'));
    expect(sendMessage).toHaveBeenCalledTimes(1);
  });

  it('restores persisted outbound after reload and removes it without duplicate sends', async () => {
    const pending = [{ id: 'persisted-1', text: 'restored', status: 'pending' as const }];
    const persistence = createPersistence(pending);
    const sendMessage = vi.fn<(message: string) => Promise<void>>(() => Promise.resolve());
    const options = {
      sessionId: createdSession.id,
      isBound: true,
      createAndSelectSession: vi.fn(() => Promise.resolve(createdSession)),
      sendMessage,
      ...persistence,
    };
    const { rerender } = renderHook(() => useSessionMessageQueue(options));

    await waitFor(() => expect(sendMessage).toHaveBeenCalledWith('restored'));
    rerender();

    expect(sendMessage).toHaveBeenCalledTimes(1);
    expect(persistence.persisted()).toEqual([]);
  });

  it('does not send restored sending items and exposes them as stalled', async () => {
    const sending = [{ id: 'sending-1', text: 'uncertain', status: 'sending' as const }];
    const persistence = createPersistence(sending);
    const sendMessage = vi.fn<(message: string) => Promise<void>>(() => Promise.resolve());
    const { result } = renderHook(() => useSessionMessageQueue({
      sessionId: createdSession.id,
      isBound: true,
      createAndSelectSession: vi.fn(() => Promise.resolve(createdSession)),
      sendMessage,
      ...persistence,
    }));

    await waitFor(() => expect(result.current.stalledItems).toEqual([
      { ...sending[0], sessionId: createdSession.id },
    ]));
    expect(sendMessage).not.toHaveBeenCalled();
  });

  it('removes stalled items when their session is cleared', async () => {
    const sending = [{ id: 'sending-clear', text: 'uncertain', status: 'sending' as const }];
    const persistence = createPersistence(sending);
    const { result } = renderHook(() => useSessionMessageQueue({
      sessionId: createdSession.id,
      isBound: true,
      createAndSelectSession: vi.fn(() => Promise.resolve(createdSession)),
      sendMessage: vi.fn(() => Promise.resolve()),
      ...persistence,
    }));
    await waitFor(() => expect(result.current.stalledItems).toHaveLength(1));

    let token: Awaited<ReturnType<typeof result.current.beginClear>>;
    await act(async () => { token = await result.current.beginClear(createdSession.id); });
    await act(async () => { await result.current.commitClear(token); });

    expect(result.current.stalledItems).toEqual([]);
    expect(persistence.persisted()).toEqual([]);
  });

  it('retries a failed initial persist once scheduled, then sends', async () => {
    const scheduled: Array<() => void> = [];
    let saveAttempt = 0;
    const persistence = createPersistence();
    persistence.savePendingMessages.mockImplementation((_, _pending) => {
      saveAttempt += 1;
      if (saveAttempt === 1) {
        return Promise.resolve({ ok: false, error: 'write failed' });
      }
      return Promise.resolve({ ok: true, value: undefined });
    });
    const sendMessage = vi.fn<(message: string) => Promise<void>>(() => Promise.resolve());
    const { result } = renderHook(() => useSessionMessageQueue({
      sessionId: createdSession.id,
      isBound: true,
      createAndSelectSession: vi.fn(() => Promise.resolve(createdSession)),
      sendMessage,
      loadPendingMessages: persistence.loadPendingMessages,
      savePendingMessages: persistence.savePendingMessages,
      scheduleRetry: (task) => {
        scheduled.push(task);
        return () => undefined;
      },
    }));

    act(() => { void result.current.enqueueMessage('retry me'); });
    await waitFor(() => expect(scheduled).toHaveLength(1));
    expect(sendMessage).not.toHaveBeenCalled();
    act(() => scheduled[0]());

    await waitFor(() => expect(sendMessage).toHaveBeenCalledWith('retry me'));
    expect(scheduled).toHaveLength(1);
  });

  it('schedules a bounded retry instead of spinning when sending-state persist fails', async () => {
    const scheduled: Array<() => void> = [];
    let saveAttempt = 0;
    const persistence = createPersistence();
    persistence.savePendingMessages.mockImplementation(() => {
      saveAttempt += 1;
      return saveAttempt === 1
        ? Promise.resolve({ ok: true, value: undefined })
        : Promise.resolve({ ok: false, error: 'sending write failed' });
    });
    const sendMessage = vi.fn<(message: string) => Promise<void>>(() => Promise.resolve());
    const { result } = renderHook(() => useSessionMessageQueue({
      sessionId: createdSession.id,
      isBound: true,
      createAndSelectSession: vi.fn(() => Promise.resolve(createdSession)),
      sendMessage,
      loadPendingMessages: persistence.loadPendingMessages,
      savePendingMessages: persistence.savePendingMessages,
      scheduleRetry: (task) => {
        scheduled.push(task);
        return () => undefined;
      },
    }));

    act(() => { void result.current.enqueueMessage('wait for persist'); });
    await waitFor(() => expect(saveAttempt).toBeGreaterThan(1));

    expect(scheduled).toHaveLength(1);
    expect(sendMessage).not.toHaveBeenCalled();
  });

  it('keeps sending on disk after cleanup failure and does not resend after reload', async () => {
    let disk: PendingOutbound[] = [
      { id: 'cleanup-1', text: 'once', status: 'pending' },
    ];
    const loadPendingMessages = vi.fn(() => Promise.resolve({ ok: true as const, value: [...disk] }));
    const savePendingMessages = vi.fn((_id: string, pending: PendingOutbound[]) => {
      if (pending.length === 0) return Promise.resolve({ ok: false as const, error: 'cleanup failed' });
      disk = [...pending];
      return Promise.resolve({ ok: true as const, value: undefined });
    });
    const firstSend = vi.fn<(message: string) => Promise<void>>(() => Promise.resolve());
    const options = {
      sessionId: createdSession.id, isBound: true,
      createAndSelectSession: vi.fn(() => Promise.resolve(createdSession)),
      loadPendingMessages, savePendingMessages,
    };
    const first = renderHook(() => useSessionMessageQueue({ ...options, sendMessage: firstSend }));
    await waitFor(() => expect(firstSend).toHaveBeenCalledOnce());
    await waitFor(() => expect(first.result.current.error).toBe('cleanup failed'));
    first.unmount();

    const secondSend = vi.fn<(message: string) => Promise<void>>(() => Promise.resolve());
    const second = renderHook(() => useSessionMessageQueue({ ...options, sendMessage: secondSend }));
    await waitFor(() => expect(second.result.current.stalledItems).toHaveLength(1));
    expect(secondSend).not.toHaveBeenCalled();
  });

  it('begins clear immediately so a never-resolving send cannot block cancel or delete', async () => {
    const sending = new Promise<void>(() => undefined);
    const persistence = createPersistence();
    const sendMessage = vi.fn(() => sending);
    const { result } = renderHook(() => useSessionMessageQueue({
      sessionId: createdSession.id,
      isBound: true,
      createAndSelectSession: vi.fn(() => Promise.resolve(createdSession)),
      sendMessage,
      ...persistence,
    }));

    void result.current.enqueueMessage('delete during send');
    await waitFor(() => expect(sendMessage).toHaveBeenCalled());
    const cancelStream = vi.fn(() => Promise.resolve());
    const mainDelete = vi.fn(() => Promise.resolve());
    const deleteSession = vi.fn(async () => {
      await cancelStream();
      await mainDelete();
      return { ok: true as const, sessionDeleted: true };
    });

    await deleteSessionWithOutbox(createdSession.id, result.current, deleteSession);

    expect(cancelStream).toHaveBeenCalledOnce();
    expect(mainDelete).toHaveBeenCalledOnce();
    expect(persistence.persisted()).toEqual([]);
  });

  it('rolls back a failed deletion without losing pending or future sends', async () => {
    const persistence = createPersistence();
    const sendMessage = vi.fn<(message: string) => Promise<void>>(() => Promise.resolve());
    const { result, rerender } = renderHook(
      ({ isBound }) => useSessionMessageQueue({
        sessionId: createdSession.id,
        isBound,
        createAndSelectSession: vi.fn(() => Promise.resolve(createdSession)),
        sendMessage,
        ...persistence,
      }),
      { initialProps: { isBound: false } },
    );
    const original = result.current.enqueueMessage('original pending');
    await waitFor(() => expect(persistence.persisted()).toHaveLength(1));

    let token: Awaited<ReturnType<typeof result.current.beginClear>>;
    await act(async () => { token = await result.current.beginClear(createdSession.id); });
    expect(persistence.persisted()).toHaveLength(1);
    await act(async () => { await result.current.rollbackClear(token); });
    rerender({ isBound: true });
    await waitFor(() => expect(sendMessage).toHaveBeenCalledWith('original pending'));
    await act(async () => { await original; });

    const next = result.current.enqueueMessage('after rollback');
    await waitFor(() => expect(sendMessage).toHaveBeenCalledWith('after rollback'));
    await act(async () => { await next; });
    expect(sendMessage.mock.calls).toEqual([['original pending'], ['after rollback']]);
  });

  it('restarts persistence retry after rollback and survives reload', async () => {
    let disk: PendingOutbound[] = [];
    let saveAttempt = 0;
    const scheduled: Array<() => void> = [];
    const loadPendingMessages = vi.fn(() => Promise.resolve({
      ok: true as const, value: [...disk],
    }));
    const savePendingMessages = vi.fn((_id: string, pending: PendingOutbound[]) => {
      saveAttempt += 1;
      if (saveAttempt === 1) return Promise.resolve({ ok: false as const, error: 'offline' });
      disk = [...pending];
      return Promise.resolve({ ok: true as const, value: undefined });
    });
    const scheduleRetry = (task: () => void) => {
      scheduled.push(task);
      return () => undefined;
    };
    const options = {
      sessionId: createdSession.id,
      isBound: false,
      createAndSelectSession: vi.fn(() => Promise.resolve(createdSession)),
      sendMessage: vi.fn<(message: string) => Promise<void>>(() => Promise.resolve()),
      loadPendingMessages,
      savePendingMessages,
      scheduleRetry,
    };
    const first = renderHook(() => useSessionMessageQueue(options));
    void first.result.current.enqueueMessage('survives rollback');
    await waitFor(() => expect(scheduled).toHaveLength(1));

    const token = first.result.current.beginClear(createdSession.id);
    await first.result.current.rollbackClear(token);
    await waitFor(() => expect(scheduled).toHaveLength(2));
    act(() => scheduled[1]());
    await waitFor(() => expect(disk).toHaveLength(1));
    first.unmount();

    const sendAfterReload = vi.fn<(message: string) => Promise<void>>(() => Promise.resolve());
    renderHook(() => useSessionMessageQueue({
      ...options, isBound: true, sendMessage: sendAfterReload,
    }));
    await waitFor(() => expect(sendAfterReload).toHaveBeenCalledWith('survives rollback'));
  });
});
