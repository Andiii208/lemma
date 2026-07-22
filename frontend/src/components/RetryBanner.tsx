import { useState, useEffect } from 'react';
import { RETRY_DELAYS } from '../constants';
import { AlertTriangle, RefreshCw, WifiOff, XCircle } from 'lucide-react';

interface RetryBannerProps {
  error: string | null;
  isRecoverable: boolean;
  onRetry: (text: string, options?: ChatOptions) => Promise<void>;
  onDismiss: () => void;
  lastFailedText?: string;
  lastFailedOptions?: ChatOptions;
}

type BannerState = 'failed' | 'retrying' | 'exhausted';

export default function RetryBanner({
  error,
  isRecoverable,
  onRetry,
  onDismiss,
  lastFailedText,
  lastFailedOptions,
}: RetryBannerProps) {
  const [retryCount, setRetryCount] = useState(0);
  const [bannerState, setBannerState] = useState<BannerState>('failed');
  const [isOnline, setIsOnline] = useState(navigator.onLine);

  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  const isMaxRetries = retryCount >= RETRY_DELAYS.length;

  const handleRetry = async () => {
    if (isMaxRetries || !lastFailedText) return;
    setBannerState('retrying');
    const delay = RETRY_DELAYS[Math.min(retryCount, RETRY_DELAYS.length - 1)];
    await new Promise((resolve) => setTimeout(resolve, delay));
    const nextCount = retryCount + 1;
    try {
      await onRetry(lastFailedText, lastFailedOptions);
    } catch {
      // retry failed
    }
    setRetryCount(nextCount);
    setBannerState(nextCount >= RETRY_DELAYS.length ? 'exhausted' : 'failed');
  };

  if (!error) return null;

  const showRetry = isRecoverable && !isMaxRetries;
  const isRetrying = bannerState === 'retrying';
  const isExhausted = bannerState === 'exhausted';

  return (
    <div className={`flex items-center gap-3 px-4 py-3 rounded-lg ${
      !isOnline || isExhausted
        ? 'bg-red-900/20 border border-red-800'
        : 'bg-amber-900/20 border border-amber-800'
    }`}>
      {!isOnline ? (
        <WifiOff size={18} className="text-red-500 shrink-0" />
      ) : isExhausted ? (
        <XCircle size={18} className="text-red-500 shrink-0" />
      ) : (
        <AlertTriangle size={18} className="text-amber-500 shrink-0" />
      )}

      <div className="flex-1 min-w-0">
        <p className="text-sm text-text">
          {!isOnline ? '网络连接已断开' : isExhausted ? '重试失败' : error}
        </p>
        {retryCount > 0 && !isExhausted && (
          <p className="text-xs text-text-muted mt-0.5">
            已重试 {retryCount} 次
          </p>
        )}
      </div>

      {showRetry && (
        <button
          onClick={handleRetry}
          disabled={isRetrying || !isOnline}
          className="flex items-center gap-1 px-3 py-1.5 rounded text-xs bg-accent text-white hover:bg-accent disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          <RefreshCw size={12} className={isRetrying ? 'animate-spin' : ''} />
          {isRetrying ? '重试中...' : '重试'}
        </button>
      )}

      <button
        onClick={onDismiss}
        className="text-text-muted hover:text-text-secondary text-sm"
        aria-label="关闭"
      >
        ✕
      </button>
    </div>
  );
}
