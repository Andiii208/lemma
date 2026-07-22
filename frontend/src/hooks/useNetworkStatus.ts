import { useState, useEffect, useCallback, useRef } from 'react';

export function useNetworkStatus(
  onReconnect?: () => void,
  onNotify?: (title: string, body: string) => void,
) {
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [wasOffline, setWasOffline] = useState(false);
  const onReconnectRef = useRef(onReconnect);
  const onNotifyRef = useRef(onNotify);
  onReconnectRef.current = onReconnect;
  onNotifyRef.current = onNotify;

  useEffect(() => {
    const handleOnline = () => {
      setIsOnline(true);
      if (wasOffline) {
        onReconnectRef.current?.();
        onNotifyRef.current?.('Lemma', '网络连接已恢复');
      }
    };

    const handleOffline = () => {
      setIsOnline(false);
      setWasOffline(true);
      onNotifyRef.current?.('Lemma', '网络连接已断开，进入离线模式');
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, [wasOffline]);

  const resetOfflineFlag = useCallback(() => {
    setWasOffline(false);
  }, []);

  return { isOnline, wasOffline, resetOfflineFlag };
}
