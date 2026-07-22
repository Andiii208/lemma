import {
  useCallback, useEffect, useRef, useState, type Dispatch, type MutableRefObject,
  type SetStateAction,
} from 'react';
import type { AppAction } from '../context/AppContext';
import type { StoreResult } from './useMessageStore';

interface SessionLifecycleDependencies {
  currentSessionId: string | null;
  workDir: string | null;
  isStreaming: boolean;
  cancelStream: () => Promise<void>;
  clearMessages: () => void;
  deleteMessages: (sessionId?: string) => Promise<StoreResult<void>>;
  migrateDefaultMessages: (sessionId: string) => Promise<StoreResult<ClaudeMessage[]>>;
  dispatch: React.Dispatch<AppAction>;
}

interface StorageCleanup {
  sessionId: string;
  error: string;
}

export type SessionOperationResult =
  | { ok: true; sessionDeleted: boolean }
  | { ok: false; sessionDeleted: boolean; error: string };

type ErrorSetter = Dispatch<SetStateAction<string | null>>;
type DependenciesRef = MutableRefObject<SessionLifecycleDependencies>;
type SessionIdRef = MutableRefObject<string | null>;
type SelectionGenerationRef = MutableRefObject<number>;
type KnownSessions = ReturnType<typeof useKnownSessions>;
type RefreshSessions = (reconcile?: boolean) => Promise<StoreResult<SessionInfo[]>>;
type SelectSession = (sessionId: string | null) => Promise<void>;

function failureMessage(error: unknown): string {
  return error instanceof Error ? error.message : 'Session operation failed';
}

function useLatest<Value>(value: Value): MutableRefObject<Value> {
  const valueRef = useRef(value);
  valueRef.current = value;
  return valueRef;
}

function useKnownSessions() {
  const [sessions, setSessions] = useState<SessionInfo[]>([]);
  const sessionsRef = useRef<SessionInfo[]>([]);
  const replaceSessions = useCallback((next: SessionInfo[]) => {
    sessionsRef.current = next;
    setSessions(next);
    return next;
  }, []);
  const removeSession = useCallback((sessionId: string) => {
    return replaceSessions(sessionsRef.current.filter((session) => session.id !== sessionId));
  }, [replaceSessions]);
  return { sessions, sessionsRef, replaceSessions, removeSession };
}

function reconcileCurrentSession(
  loaded: SessionInfo[],
  currentAtStart: string | null,
  currentRef: SessionIdRef,
  dependenciesRef: DependenciesRef,
): void {
  if (currentRef.current !== currentAtStart) return;
  if (currentAtStart && loaded.some((session) => session.id === currentAtStart)) return;
  const fallbackId = loaded[0]?.id ?? null;
  if (fallbackId === currentAtStart) return;
  currentRef.current = fallbackId;
  dependenciesRef.current.dispatch({ type: 'SET_SESSION', payload: fallbackId });
}

function useSessionRefresher(
  known: ReturnType<typeof useKnownSessions>,
  currentRef: SessionIdRef,
  dependenciesRef: DependenciesRef,
  setError: ErrorSetter,
) {
  const generationRef = useRef(0);
  const { replaceSessions } = known;
  return useCallback(async (reconcile = true): Promise<StoreResult<SessionInfo[]>> => {
    const generation = ++generationRef.current;
    const currentAtStart = currentRef.current;
    try {
      const loaded = await window.lemmaAPI?.listSessions() ?? [];
      if (generation !== generationRef.current) return { ok: true, value: loaded };
      replaceSessions(loaded);
      setError(null);
      if (reconcile) {
        reconcileCurrentSession(loaded, currentAtStart, currentRef, dependenciesRef);
      }
      return { ok: true, value: loaded };
    } catch (refreshError: unknown) {
      const error = failureMessage(refreshError);
      setError(error);
      return { ok: false, error };
    }
  }, [currentRef, dependenciesRef, replaceSessions, setError]);
}

function useSessionSelector(
  dependenciesRef: DependenciesRef,
  currentRef: SessionIdRef,
  selectionGenerationRef: SelectionGenerationRef,
) {
  const generationRef = useRef(0);
  return useCallback(async (sessionId: string | null) => {
    const generation = ++generationRef.current;
    selectionGenerationRef.current += 1;
    currentRef.current = sessionId;
    const dependencies = dependenciesRef.current;
    if (dependencies.isStreaming) await dependencies.cancelStream();
    if (generation !== generationRef.current) return;
    dependenciesRef.current.dispatch({ type: 'SET_SESSION', payload: sessionId });
    dependenciesRef.current.clearMessages();
    dependenciesRef.current.dispatch({ type: 'SET_VIEW', payload: 'chat' });
  }, [currentRef, dependenciesRef, selectionGenerationRef]);
}

async function createLocalSession(
  title: string,
  dependenciesRef: DependenciesRef,
  currentRef: SessionIdRef,
  selectionGenerationRef: SelectionGenerationRef,
  refreshSessions: RefreshSessions,
  selectSession: SelectSession,
  setError: ErrorSetter,
): Promise<SessionInfo | null> {
  const currentAtStart = currentRef.current;
  const selectionAtStart = selectionGenerationRef.current;
  try {
    const dependencies = dependenciesRef.current;
    const created = await window.lemmaAPI?.createSession(dependencies.workDir ?? '', title);
    if (!created) return null;
    await dependencies.migrateDefaultMessages(created.id);
    await refreshSessions(false);
    if (currentRef.current === currentAtStart
      && selectionGenerationRef.current === selectionAtStart) {
      await selectSession(created.id);
    }
    return created;
  } catch (createError: unknown) {
    setError(failureMessage(createError));
    return null;
  }
}

function useSessionCreator(
  dependenciesRef: DependenciesRef,
  currentRef: SessionIdRef,
  selectionGenerationRef: SelectionGenerationRef,
  refreshSessions: RefreshSessions,
  selectSession: SelectSession,
  setError: ErrorSetter,
) {
  const creationRef = useRef<Promise<SessionInfo | null> | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const createAndSelectSession = useCallback((title = '新会话') => {
    if (creationRef.current) return creationRef.current;
    setIsCreating(true);
    const creation = createLocalSession(
      title, dependenciesRef, currentRef, selectionGenerationRef,
      refreshSessions, selectSession, setError,
    ).finally(() => {
      if (creationRef.current === creation) creationRef.current = null;
      setIsCreating(false);
    });
    creationRef.current = creation;
    return creation;
  }, [currentRef, dependenciesRef, refreshSessions, selectSession, selectionGenerationRef, setError]);

  return { createAndSelectSession, isCreating };
}

async function deleteStoredMessages(
  dependenciesRef: DependenciesRef,
  sessionId: string,
): Promise<StoreResult<void>> {
  try {
    return await dependenciesRef.current.deleteMessages(sessionId);
  } catch (deleteError: unknown) {
    return { ok: false, error: failureMessage(deleteError) };
  }
}

async function deleteMainSession(sessionId: string): Promise<StoreResult<void>> {
  try {
    const deleted = await window.lemmaAPI?.deleteSession(sessionId);
    return deleted
      ? { ok: true, value: undefined }
      : { ok: false, error: 'Session deletion failed' };
  } catch (mainError: unknown) {
    return { ok: false, error: failureMessage(mainError) };
  }
}

function failedDeletion(error: string, sessionDeleted: boolean): SessionOperationResult {
  return { ok: false, sessionDeleted, error };
}

async function completeDeletedSession(
  sessionId: string,
  dependenciesRef: DependenciesRef,
  currentRef: SessionIdRef,
  known: KnownSessions,
  refreshSessions: RefreshSessions,
  selectSession: SelectSession,
  setPendingCleanup: Dispatch<SetStateAction<StorageCleanup | null>>,
): Promise<{ result: SessionOperationResult; error: string | null }> {
  const storage = await deleteStoredMessages(dependenciesRef, sessionId);
  const knownRemaining = known.removeSession(sessionId);
  const refreshed = await refreshSessions(false);
  const remaining = refreshed.ok ? refreshed.value : knownRemaining;
  if (currentRef.current === sessionId) {
    await selectSession(remaining[0]?.id ?? null);
  }
  if (!storage.ok) setPendingCleanup({ sessionId, error: storage.error });
  const errors = [storage, refreshed]
    .filter((outcome): outcome is { ok: false; error: string } => !outcome.ok)
    .map((outcome) => outcome.error);
  if (errors.length) {
    const error = errors.join('; ');
    return { result: failedDeletion(error, true), error };
  }
  setPendingCleanup((pending) => pending?.sessionId === sessionId ? null : pending);
  return { result: { ok: true, sessionDeleted: true }, error: null };
}

async function runSessionDeletion(
  sessionId: string,
  dependenciesRef: DependenciesRef,
  currentRef: SessionIdRef,
  known: KnownSessions,
  refreshSessions: RefreshSessions,
  selectSession: SelectSession,
  setError: ErrorSetter,
  setPendingCleanup: Dispatch<SetStateAction<StorageCleanup | null>>,
): Promise<SessionOperationResult> {
  const dependencies = dependenciesRef.current;
  if (currentRef.current === sessionId && dependencies.isStreaming) {
    await dependencies.cancelStream();
  }
  const mainResult = await deleteMainSession(sessionId);
  if (!mainResult.ok) {
    setError(mainResult.error);
    return failedDeletion(mainResult.error, false);
  }
  const completed = await completeDeletedSession(
    sessionId, dependenciesRef, currentRef, known,
    refreshSessions, selectSession, setPendingCleanup,
  );
  setError(completed.error);
  return completed.result;
}

function useSessionDeleter(
  dependenciesRef: DependenciesRef,
  currentRef: SessionIdRef,
  known: KnownSessions,
  refreshSessions: RefreshSessions,
  selectSession: SelectSession,
  setError: ErrorSetter,
  setPendingCleanup: Dispatch<SetStateAction<StorageCleanup | null>>,
) {
  const deletionsRef = useRef(new Map<string, Promise<SessionOperationResult>>());
  return useCallback((sessionId: string): Promise<SessionOperationResult> => {
    const existing = deletionsRef.current.get(sessionId);
    if (existing) return existing;
    const deletion = runSessionDeletion(
      sessionId, dependenciesRef, currentRef, known,
      refreshSessions, selectSession, setError, setPendingCleanup,
    ).finally(() => deletionsRef.current.delete(sessionId));
    deletionsRef.current.set(sessionId, deletion);
    return deletion;
  }, [currentRef, dependenciesRef, known, refreshSessions, selectSession, setError, setPendingCleanup]);
}

export function useSessionLifecycle(dependencies: SessionLifecycleDependencies) {
  const [error, setError] = useState<string | null>(null);
  const [pendingStorageCleanup, setPendingCleanup] = useState<StorageCleanup | null>(null);
  const dependenciesRef = useLatest(dependencies);
  const currentRef = useLatest(dependencies.currentSessionId);
  const selectionGenerationRef = useRef(0);
  const known = useKnownSessions();
  const refreshSessions = useSessionRefresher(
    known, currentRef, dependenciesRef, setError,
  );
  useEffect(() => { void refreshSessions(); }, [refreshSessions]);
  const selectSession = useSessionSelector(
    dependenciesRef, currentRef, selectionGenerationRef,
  );
  const creator = useSessionCreator(
    dependenciesRef, currentRef, selectionGenerationRef,
    refreshSessions, selectSession, setError,
  );
  const deleteSession = useSessionDeleter(
    dependenciesRef, currentRef, known, refreshSessions,
    selectSession, setError, setPendingCleanup,
  );
  return {
    sessions: known.sessions, error, pendingStorageCleanup,
    isCreating: creator.isCreating, refreshSessions, selectSession,
    createAndSelectSession: creator.createAndSelectSession, deleteSession,
  };
}
