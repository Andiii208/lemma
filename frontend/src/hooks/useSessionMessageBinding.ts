import { useEffect, useRef } from 'react';
import type { StoreResult } from './useMessageStore';

interface SessionMessageBindingOptions {
  sessionId: string | null;
  messages: ClaudeMessage[];
  setMessages: (messages: ClaudeMessage[]) => void;
  loadMessages: () => Promise<ClaudeMessage[] | null>;
  saveMessages: (messages: ClaudeMessage[]) => Promise<StoreResult<void>>;
}

export function useSessionMessageBinding(options: SessionMessageBindingOptions): boolean {
  const loadedSessionRef = useRef<string | null>(null);
  const { sessionId, messages, setMessages, loadMessages, saveMessages } = options;

  useEffect(() => {
    loadedSessionRef.current = null;
    if (!sessionId) {
      setMessages([]);
      return;
    }
    let cancelled = false;
    void loadMessages().then((loaded) => {
      if (cancelled || !loaded) return;
      setMessages(loaded);
      loadedSessionRef.current = sessionId;
    });
    return () => { cancelled = true; };
  }, [sessionId, loadMessages, setMessages]);

  useEffect(() => {
    if (!sessionId || loadedSessionRef.current !== sessionId) return;
    void saveMessages(messages);
  }, [messages, sessionId, saveMessages]);

  return loadedSessionRef.current === sessionId && sessionId !== null;
}
