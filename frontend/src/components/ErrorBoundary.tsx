import { ErrorBoundary as ReactErrorBoundary, type FallbackProps } from 'react-error-boundary';
import { AlertTriangle, RefreshCw } from 'lucide-react';

function getErrorMessage(error: unknown): string {
  if (error instanceof Error) return error.message;
  return String(error);
}

function ErrorFallback({ error, resetErrorBoundary }: FallbackProps) {
  return (
    <div className="flex flex-col items-center justify-center h-screen bg-bg-secondary text-text p-8">
      <AlertTriangle size={48} className="text-error mb-4" />
      <h1 className="text-h2 font-display mb-2">出错了</h1>
      <p className="text-body text-text-secondary mb-4 text-center max-w-md">
        Lemma 遇到了意外错误。你可以尝试重新加载，或重启应用。
      </p>
      <pre className="text-caption text-text-muted bg-bg-tertiary p-4 rounded-lg max-w-lg w-full overflow-auto mb-6">
        {getErrorMessage(error)}
      </pre>
      <button
        onClick={resetErrorBoundary}
        className="flex items-center gap-2 px-5 py-2.5 rounded-lg bg-accent text-white hover:bg-accent-hover text-ui font-medium transition-colors"
      >
        <RefreshCw size={14} />
        重新加载
      </button>
    </div>
  );
}

export function ErrorBoundary({ children }: { children: React.ReactNode }) {
  return (
    <ReactErrorBoundary
      FallbackComponent={ErrorFallback}
      onReset={() => window.location.reload()}
    >
      {children}
    </ReactErrorBoundary>
  );
}
