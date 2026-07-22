import {
  useCallback, useEffect, useRef, useState, type Dispatch, type MutableRefObject,
  type SetStateAction,
} from 'react';
import type { PendingOutbound, StoreResult } from './useMessageStore';

type RetryScheduler = (task: () => void, attempt: number) => () => void;

interface SessionMessageQueueOptions {
  sessionId: string | null;
  isBound: boolean;
  createAndSelectSession: (title?: string) => Promise<SessionInfo | null>;
  sendMessage: (text: string) => Promise<void>;
  loadPendingMessages: (sessionId: string) => Promise<StoreResult<PendingOutbound[]>>;
  savePendingMessages: (
    sessionId: string, pending: PendingOutbound[],
  ) => Promise<StoreResult<void>>;
  scheduleRetry?: RetryScheduler;
}

interface QueuedMessage extends PendingOutbound {
  targetSessionId: string | null;
  persisted: boolean;
  complete?: () => void;
}

interface RetryState {
  attempt: number;
  cancel: () => void;
}

export interface OutboxClearToken {
  id: string;
  sessionId: string;
}

interface OutboxClearControls {
  beginClear(sessionId: string): OutboxClearToken;
  commitClear(token: OutboxClearToken): Promise<StoreResult<void>>;
  rollbackClear(token: OutboxClearToken): Promise<StoreResult<void>>;
}

export async function deleteSessionWithOutbox<Result extends { sessionDeleted: boolean }>(
  sessionId: string,
  controls: OutboxClearControls,
  deleteSession: (sessionId: string) => Promise<Result>,
): Promise<Result> {
  const token = controls.beginClear(sessionId);
  try {
    const outcome = await deleteSession(sessionId);
    if (outcome.sessionDeleted) await controls.commitClear(token);
    else await controls.rollbackClear(token);
    return outcome;
  } catch (error: unknown) {
    await controls.rollbackClear(token);
    throw error;
  }
}

interface ClearTransaction {
  token: OutboxClearToken;
  queueSnapshot: QueuedMessage[];
  stalledSnapshot: StalledOutbound[];
}

export interface StalledOutbound extends PendingOutbound {
  sessionId: string;
}

interface QueueRuntime {
  optionsRef: MutableRefObject<SessionMessageQueueOptions>;
  queueRef: MutableRefObject<QueuedMessage[]>;
  generationsRef: MutableRefObject<Map<string, number>>;
  tombstonesRef: MutableRefObject<Set<string>>;
  locksRef: MutableRefObject<Map<string, Promise<StoreResult<void>>>>;
  retriesRef: MutableRefObject<Map<string, RetryState>>;
  pausedRef: MutableRefObject<Set<string>>;
  drainRef: MutableRefObject<Promise<void> | null>;
  transactionsRef: MutableRefObject<Map<string, ClearTransaction>>;
  notify: () => void;
  setError: Dispatch<SetStateAction<string | null>>;
  setStalledItems: Dispatch<SetStateAction<StalledOutbound[]>>;
}

function useLatest<Value>(value: Value): MutableRefObject<Value> {
  const valueRef = useRef(value);
  valueRef.current = value;
  return valueRef;
}

function createQueuedMessage(text: string, targetSessionId: string | null) {
  let complete!: () => void;
  const completion = new Promise<void>((resolve) => { complete = resolve; });
  const item: QueuedMessage = {
    id: crypto.randomUUID(), text, status: 'pending',
    targetSessionId, persisted: false, complete,
  };
  return { item, completion };
}

function generationOf(runtime: QueueRuntime, sessionId: string): number {
  return runtime.generationsRef.current.get(sessionId) ?? 0;
}

function isAlive(runtime: QueueRuntime, sessionId: string, generation: number): boolean {
  return !runtime.tombstonesRef.current.has(sessionId)
    && generationOf(runtime, sessionId) === generation;
}

function pendingForSession(queue: QueuedMessage[], sessionId: string): PendingOutbound[] {
  return queue
    .filter((message) => message.targetSessionId === sessionId)
    .map(({ id, text, status }) => ({ id, text, status }));
}

function serializeSave(
  runtime: QueueRuntime,
  sessionId: string,
  operation: () => Promise<StoreResult<void>>,
): Promise<StoreResult<void>> {
  const previous = runtime.locksRef.current.get(sessionId) ?? Promise.resolve({
    ok: true as const, value: undefined,
  });
  const current = previous.then(operation, operation).finally(() => {
    if (runtime.locksRef.current.get(sessionId) === current) {
      runtime.locksRef.current.delete(sessionId);
    }
  });
  runtime.locksRef.current.set(sessionId, current);
  return current;
}

async function persistQueue(
  runtime: QueueRuntime,
  sessionId: string,
  generation: number,
): Promise<StoreResult<void>> {
  const pending = pendingForSession(runtime.queueRef.current, sessionId);
  const result = await serializeSave(runtime, sessionId, () => {
    if (!isAlive(runtime, sessionId, generation)) {
      return Promise.resolve({ ok: false, error: 'Outbox was cleared' });
    }
    return runtime.optionsRef.current.savePendingMessages(sessionId, pending);
  });
  if (result.ok && isAlive(runtime, sessionId, generation)) {
    runtime.queueRef.current.forEach((message) => {
      if (message.targetSessionId === sessionId) message.persisted = true;
    });
  }
  return result;
}

function defaultScheduleRetry(task: () => void, attempt: number): () => void {
  const timeoutId = window.setTimeout(task, Math.min(250 * attempt, 750));
  return () => window.clearTimeout(timeoutId);
}

function cancelRetry(runtime: QueueRuntime, sessionId: string): void {
  runtime.retriesRef.current.get(sessionId)?.cancel();
  runtime.retriesRef.current.delete(sessionId);
}

function schedulePersistRetry(runtime: QueueRuntime, sessionId: string): void {
  const previousAttempt = runtime.retriesRef.current.get(sessionId)?.attempt ?? 0;
  if (previousAttempt >= 3 || runtime.tombstonesRef.current.has(sessionId)) return;
  cancelRetry(runtime, sessionId);
  const attempt = previousAttempt + 1;
  const scheduler = runtime.optionsRef.current.scheduleRetry ?? defaultScheduleRetry;
  const cancel = scheduler(() => {
    runtime.retriesRef.current.delete(sessionId);
    void persistPending(runtime, sessionId, attempt);
  }, attempt);
  runtime.retriesRef.current.set(sessionId, { attempt, cancel });
}

async function persistPending(
  runtime: QueueRuntime,
  sessionId: string,
  attempt = 0,
): Promise<void> {
  const generation = generationOf(runtime, sessionId);
  const result = await persistQueue(runtime, sessionId, generation);
  if (!isAlive(runtime, sessionId, generation)) return;
  if (!result.ok) {
    runtime.setError(result.error);
    runtime.retriesRef.current.set(sessionId, { attempt, cancel: () => undefined });
    schedulePersistRetry(runtime, sessionId);
  } else {
    cancelRetry(runtime, sessionId);
    runtime.setError(null);
    runtime.notify();
  }
}

function assignCreatedSession(queue: QueuedMessage[], sessionId: string): void {
  queue.forEach((message) => {
    if (!message.targetSessionId) message.targetSessionId = sessionId;
  });
}

function abandonUntargeted(queue: QueuedMessage[]): void {
  queue.filter((message) => !message.targetSessionId)
    .forEach((message) => message.complete?.());
  const retained = queue.filter((message) => message.targetSessionId);
  queue.splice(0, queue.length, ...retained);
}

function useQueueCreation(runtime: QueueRuntime) {
  const creationRef = useRef<Promise<SessionInfo | null> | null>(null);
  return useCallback((title: string) => {
    if (creationRef.current) return creationRef.current;
    const creation = runtime.optionsRef.current.createAndSelectSession(title)
      .then(async (created) => {
        if (!created) abandonUntargeted(runtime.queueRef.current);
        else {
          assignCreatedSession(runtime.queueRef.current, created.id);
          await persistPending(runtime, created.id);
        }
        runtime.notify();
        return created;
      })
      .finally(() => {
        if (creationRef.current === creation) creationRef.current = null;
      });
    creationRef.current = creation;
    return creation;
  }, [runtime]);
}

function mergeRestored(
  runtime: QueueRuntime,
  restored: PendingOutbound[],
  sessionId: string,
): void {
  const knownIds = new Set(runtime.queueRef.current.map((message) => message.id));
  const stalled = restored.filter((message) => message.status === 'sending');
  runtime.setStalledItems((current) => [
    ...current.filter((item) => !stalled.some((next) => next.id === item.id)),
    ...stalled.map((item) => ({ ...item, sessionId })),
  ]);
  restored.filter((message) => message.status === 'pending').forEach((message) => {
    if (!knownIds.has(message.id)) {
      runtime.queueRef.current.push({
        ...message, targetSessionId: sessionId, persisted: true,
      });
    }
  });
}

function usePendingRestore(options: SessionMessageQueueOptions, runtime: QueueRuntime) {
  const restoredSessionsRef = useRef(new Set<string>());
  const { sessionId, isBound, loadPendingMessages } = options;
  useEffect(() => {
    if (!sessionId || !isBound) return;
    if (restoredSessionsRef.current.has(sessionId)) return;
    restoredSessionsRef.current.add(sessionId);
    void loadPendingMessages(sessionId).then((result) => {
      if (result.ok) mergeRestored(runtime, result.value, sessionId);
      else runtime.setError(result.error);
      runtime.notify();
    });
  }, [isBound, loadPendingMessages, sessionId, runtime]);
}

function sendableIndex(runtime: QueueRuntime): number {
  const options = runtime.optionsRef.current;
  if (!options.sessionId || !options.isBound) return -1;
  if (runtime.pausedRef.current.has(options.sessionId)) return -1;
  return runtime.queueRef.current.findIndex((message) => (
    message.persisted && message.status === 'pending'
      && message.targetSessionId === options.sessionId
  ));
}

async function sendOne(runtime: QueueRuntime, message: QueuedMessage): Promise<boolean> {
  const sessionId = message.targetSessionId!;
  const generation = generationOf(runtime, sessionId);
  if (!isAlive(runtime, sessionId, generation)) return false;
  message.status = 'sending';
  const marked = await persistQueue(runtime, sessionId, generation);
  if (!marked.ok || !isAlive(runtime, sessionId, generation)) {
    if (isAlive(runtime, sessionId, generation)) {
      message.status = 'pending';
      message.persisted = false;
    }
    if (!marked.ok && marked.error !== 'Outbox was cleared') {
      runtime.setError(marked.error);
      schedulePersistRetry(runtime, sessionId);
    }
    return false;
  }
  if (!isAlive(runtime, sessionId, generation)) return false;
  await runtime.optionsRef.current.sendMessage(message.text);
  if (!isAlive(runtime, sessionId, generation)) return false;
  runtime.queueRef.current.splice(runtime.queueRef.current.indexOf(message), 1);
  if (!isAlive(runtime, sessionId, generation)) return false;
  const cleaned = await persistQueue(runtime, sessionId, generation);
  if (!cleaned.ok) {
    runtime.setError(cleaned.error);
    runtime.setStalledItems((items) => [...items, {
      id: message.id, text: message.text, status: 'sending', sessionId,
    }]);
  } else {
    runtime.setError(null);
  }
  message.complete?.();
  return cleaned.ok;
}

function useQueueDrain(runtime: QueueRuntime) {
  return useCallback(() => {
    if (runtime.drainRef.current) return runtime.drainRef.current;
    const drain = (async () => {
      let index = sendableIndex(runtime);
      while (index >= 0) {
        const continued = await sendOne(runtime, runtime.queueRef.current[index]);
        if (!continued) break;
        index = sendableIndex(runtime);
      }
    })().finally(() => {
      if (runtime.drainRef.current === drain) runtime.drainRef.current = null;
      runtime.notify();
    });
    runtime.drainRef.current = drain;
    return drain;
  }, [runtime]);
}

function snapshotSession(runtime: QueueRuntime, sessionId: string): ClearTransaction {
  return {
    token: { id: crypto.randomUUID(), sessionId },
    queueSnapshot: runtime.queueRef.current
      .filter((item) => item.targetSessionId === sessionId)
      .map((item) => ({ ...item })),
    stalledSnapshot: [],
  };
}

function beginSessionClear(
  runtime: QueueRuntime,
  sessionId: string,
  stalledItems: StalledOutbound[],
): OutboxClearToken {
  const existing = runtime.transactionsRef.current.get(sessionId);
  if (existing) return existing.token;
  const transaction = snapshotSession(runtime, sessionId);
  transaction.stalledSnapshot = stalledItems.filter((item) => item.sessionId === sessionId);
  const nextGeneration = generationOf(runtime, sessionId) + 1;
  runtime.generationsRef.current.set(sessionId, nextGeneration);
  runtime.pausedRef.current.add(sessionId);
  cancelRetry(runtime, sessionId);
  runtime.transactionsRef.current.set(sessionId, transaction);
  return transaction.token;
}

function removeSessionMemory(runtime: QueueRuntime, sessionId: string): void {
  const removed = runtime.queueRef.current.filter((item) => item.targetSessionId === sessionId);
  removed.forEach((item) => item.complete?.());
  runtime.queueRef.current = runtime.queueRef.current.filter(
    (item) => item.targetSessionId !== sessionId,
  );
  runtime.setStalledItems((items) => items.filter((item) => item.sessionId !== sessionId));
}

async function commitSessionClear(runtime: QueueRuntime, token: OutboxClearToken) {
  const transaction = runtime.transactionsRef.current.get(token.sessionId);
  if (!transaction || transaction.token.id !== token.id) {
    return { ok: false as const, error: 'Invalid outbox clear token' };
  }
  runtime.tombstonesRef.current.add(token.sessionId);
  runtime.pausedRef.current.delete(token.sessionId);
  removeSessionMemory(runtime, token.sessionId);
  const result = await serializeSave(runtime, token.sessionId, () => (
    runtime.optionsRef.current.savePendingMessages(token.sessionId, [])
  ));
  if (!result.ok) runtime.setError(result.error);
  runtime.transactionsRef.current.delete(token.sessionId);
  runtime.notify();
  return result;
}

function restoreQueueSnapshot(
  runtime: QueueRuntime,
  transaction: ClearTransaction,
): StalledOutbound[] {
  const known = new Map(runtime.queueRef.current.map((item) => [item.id, item]));
  const uncertain: StalledOutbound[] = [];
  transaction.queueSnapshot.forEach((snapshot) => {
    if (snapshot.status === 'sending') {
      runtime.queueRef.current = runtime.queueRef.current.filter((item) => item.id !== snapshot.id);
      uncertain.push({
        id: snapshot.id, text: snapshot.text, status: 'sending',
        sessionId: transaction.token.sessionId,
      });
    } else if (known.has(snapshot.id)) {
      Object.assign(known.get(snapshot.id)!, snapshot);
    } else {
      runtime.queueRef.current.push({ ...snapshot });
    }
  });
  return uncertain;
}

async function rollbackSessionClear(runtime: QueueRuntime, token: OutboxClearToken) {
  const transaction = runtime.transactionsRef.current.get(token.sessionId);
  if (!transaction || transaction.token.id !== token.id) {
    return { ok: false as const, error: 'Invalid outbox clear token' };
  }
  runtime.generationsRef.current.set(token.sessionId, generationOf(runtime, token.sessionId) + 1);
  runtime.pausedRef.current.delete(token.sessionId);
  runtime.tombstonesRef.current.delete(token.sessionId);
  const uncertain = restoreQueueSnapshot(runtime, transaction);
  runtime.setStalledItems((items) => [
    ...items.filter((item) => item.sessionId !== token.sessionId),
    ...transaction.stalledSnapshot, ...uncertain,
  ]);
  runtime.transactionsRef.current.delete(token.sessionId);
  if (runtime.queueRef.current.some((item) => (
    item.targetSessionId === token.sessionId
      && item.status === 'pending' && !item.persisted
  ))) {
    schedulePersistRetry(runtime, token.sessionId);
  }
  runtime.notify();
  return { ok: true as const, value: undefined };
}

function useQueueRuntime(options: SessionMessageQueueOptions) {
  const optionsRef = useLatest(options);
  const queueRef = useRef<QueuedMessage[]>([]);
  const generationsRef = useRef(new Map<string, number>());
  const tombstonesRef = useRef(new Set<string>());
  const locksRef = useRef(new Map<string, Promise<StoreResult<void>>>());
  const retriesRef = useRef(new Map<string, RetryState>());
  const pausedRef = useRef(new Set<string>());
  const drainRef = useRef<Promise<void> | null>(null);
  const transactionsRef = useRef(new Map<string, ClearTransaction>());
  const [, setQueueVersion] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [stalledItems, setStalledItems] = useState<StalledOutbound[]>([]);
  const notify = useCallback(() => setQueueVersion((version) => version + 1), []);
  return {
    runtime: {
      optionsRef, queueRef, generationsRef, tombstonesRef,
      locksRef, retriesRef, pausedRef, drainRef, transactionsRef,
      notify, setError, setStalledItems,
    },
    error,
    stalledItems,
  };
}

export function useSessionMessageQueue(options: SessionMessageQueueOptions) {
  const { runtime, error, stalledItems } = useQueueRuntime(options);
  const ensureCreation = useQueueCreation(runtime);
  const drainQueue = useQueueDrain(runtime);
  usePendingRestore(options, runtime);

  const enqueueMessage = useCallback((text: string): Promise<void> => {
    const queued = createQueuedMessage(text, runtime.optionsRef.current.sessionId);
    runtime.queueRef.current.push(queued.item);
    if (!runtime.optionsRef.current.sessionId) {
      void ensureCreation(text.trim().slice(0, 30) || '新会话');
    } else {
      void persistPending(runtime, runtime.optionsRef.current.sessionId);
    }
    return queued.completion;
  }, [ensureCreation, runtime]);

  useEffect(() => {
    if (sendableIndex(runtime) >= 0) void drainQueue();
  });

  const beginClear = useCallback((sessionId: string) => (
    beginSessionClear(runtime, sessionId, stalledItems)
  ), [runtime, stalledItems]);
  const commitClear = useCallback((token: OutboxClearToken) => (
    commitSessionClear(runtime, token)
  ), [runtime]);
  const rollbackClear = useCallback((token: OutboxClearToken) => (
    rollbackSessionClear(runtime, token)
  ), [runtime]);
  return {
    enqueueMessage, beginClear, commitClear, rollbackClear, error, stalledItems,
    queuedMessageCount: runtime.queueRef.current.length,
  };
}
