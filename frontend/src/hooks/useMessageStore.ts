import { useCallback, useRef, useState, type Dispatch, type SetStateAction } from 'react';
import { del, get, set } from 'idb-keyval';

const MESSAGE_KEY_PREFIX = 'lemma-messages:';
const PENDING_KEY_PREFIX = 'lemma-pending:';
const LEGACY_SESSION_ID = 'default';

export type StoreResult<Value> =
  | { ok: true; value: Value }
  | { ok: false; error: string };

export interface PendingOutbound {
  id: string;
  text: string;
  status: 'pending' | 'sending';
}

type LoadState = 'idle' | 'loading' | 'loaded' | 'error';
type StateSetter<Value> = Dispatch<SetStateAction<Value>>;

function storageKey(sessionId: string): string {
  return `${MESSAGE_KEY_PREFIX}${sessionId}`;
}

function pendingKey(sessionId: string): string {
  return `${PENDING_KEY_PREFIX}${sessionId}`;
}

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : 'Message storage failed';
}

function useSessionGeneration(sessionId: string | null) {
  const sessionRef = useRef(sessionId);
  const generationRef = useRef(0);
  if (sessionRef.current !== sessionId) {
    sessionRef.current = sessionId;
    generationRef.current += 1;
  }
  return { sessionRef, generationRef };
}

function useMessageLoader(
  sessionId: string | null,
  generationRef: React.MutableRefObject<number>,
  setMessages: StateSetter<ClaudeMessage[]>,
  setLoadState: StateSetter<LoadState>,
  setError: StateSetter<string | null>,
) {
  return useCallback(async (): Promise<ClaudeMessage[] | null> => {
    if (!sessionId) return [];
    const generation = generationRef.current;
    setLoadState('loading');
    setError(null);
    try {
      const loaded = await get<ClaudeMessage[]>(storageKey(sessionId)) ?? [];
      if (generation !== generationRef.current) return null;
      setMessages(loaded);
      setLoadState('loaded');
      return loaded;
    } catch (loadError: unknown) {
      if (generation !== generationRef.current) return null;
      setMessages([]);
      setError(errorMessage(loadError));
      setLoadState('error');
      return [];
    }
  }, [generationRef, sessionId, setError, setLoadState, setMessages]);
}

function useMessageSaver(
  sessionId: string | null,
  setMessages: StateSetter<ClaudeMessage[]>,
  setError: StateSetter<string | null>,
) {
  return useCallback(async (messages: ClaudeMessage[]): Promise<StoreResult<void>> => {
    if (!sessionId) return { ok: true, value: undefined };
    setMessages(messages);
    try {
      if (messages.length) await set(storageKey(sessionId), messages);
      else await del(storageKey(sessionId));
      setError(null);
      return { ok: true, value: undefined };
    } catch (saveError: unknown) {
      const message = errorMessage(saveError);
      setError(message);
      return { ok: false, error: message };
    }
  }, [sessionId, setError, setMessages]);
}

function useMessageDeleter(
  sessionId: string | null,
  sessionRef: React.MutableRefObject<string | null>,
  setMessages: StateSetter<ClaudeMessage[]>,
  setError: StateSetter<string | null>,
) {
  return useCallback(async (target = sessionId): Promise<StoreResult<void>> => {
    if (!target) return { ok: true, value: undefined };
    try {
      await Promise.all([del(storageKey(target)), del(pendingKey(target))]);
      if (target === sessionRef.current) setMessages([]);
      setError(null);
      return { ok: true, value: undefined };
    } catch (deleteError: unknown) {
      const message = errorMessage(deleteError);
      setError(message);
      return { ok: false, error: message };
    }
  }, [sessionId, sessionRef, setError, setMessages]);
}

function useDefaultMigration(setError: StateSetter<string | null>) {
  return useCallback(async (targetId: string): Promise<StoreResult<ClaudeMessage[]>> => {
    try {
      const target = await get<ClaudeMessage[]>(storageKey(targetId));
      if (target?.length) return { ok: true, value: target };
      const legacy = await get<ClaudeMessage[]>(storageKey(LEGACY_SESSION_ID));
      if (!legacy?.length) return { ok: true, value: target ?? [] };
      await set(storageKey(targetId), legacy);
      await del(storageKey(LEGACY_SESSION_ID));
      return { ok: true, value: legacy };
    } catch (migrationError: unknown) {
      const message = errorMessage(migrationError);
      setError(message);
      return { ok: false, error: message };
    }
  }, [setError]);
}

function usePendingLoader(setError: StateSetter<string | null>) {
  return useCallback(async (
    sessionId: string,
  ): Promise<StoreResult<PendingOutbound[]>> => {
    try {
      const pending = await get<PendingOutbound[]>(pendingKey(sessionId)) ?? [];
      return { ok: true, value: pending };
    } catch (loadError: unknown) {
      const message = errorMessage(loadError);
      setError(message);
      return { ok: false, error: message };
    }
  }, [setError]);
}

function usePendingSaver(setError: StateSetter<string | null>) {
  return useCallback(async (
    sessionId: string,
    pending: PendingOutbound[],
  ): Promise<StoreResult<void>> => {
    try {
      if (pending.length) await set(pendingKey(sessionId), pending);
      else await del(pendingKey(sessionId));
      return { ok: true, value: undefined };
    } catch (saveError: unknown) {
      const message = errorMessage(saveError);
      setError(message);
      return { ok: false, error: message };
    }
  }, [setError]);
}

export function useMessageStore(sessionId: string | null) {
  const [messages, setMessages] = useState<ClaudeMessage[]>([]);
  const [loadState, setLoadState] = useState<LoadState>('idle');
  const [error, setError] = useState<string | null>(null);
  const { sessionRef, generationRef } = useSessionGeneration(sessionId);
  const loadMessages = useMessageLoader(
    sessionId, generationRef, setMessages, setLoadState, setError,
  );
  const saveMessages = useMessageSaver(sessionId, setMessages, setError);
  const deleteMessages = useMessageDeleter(
    sessionId, sessionRef, setMessages, setError,
  );
  const migrateDefaultMessages = useDefaultMigration(setError);
  const loadPendingMessages = usePendingLoader(setError);
  const savePendingMessages = usePendingSaver(setError);
  return {
    messages, loadState, error, loadMessages, saveMessages,
    deleteMessages, migrateDefaultMessages,
    loadPendingMessages, savePendingMessages,
  };
}
