import { Wifi, WifiOff, Loader2, FolderOpen, Hash } from 'lucide-react';
import ContextIndicator from './ContextIndicator';

interface StatusBarProps {
  isStreaming: boolean;
  workDir: string | null;
  sessionId: string | null;
  isOnline?: boolean;
  tokenCounts?: { input: number; output: number };
}

export default function StatusBar({ isStreaming, workDir, sessionId, isOnline = true, tokenCounts }: StatusBarProps) {
  const dirName = workDir ? workDir.split(/[\\/]/).pop() : null;

  return (
    <div
      className="flex items-center justify-between px-4 h-7 bg-bg-elevated border-t border-border shrink-0"
      role="status"
      aria-live="polite"
    >
      <div className="flex items-center gap-3 text-caption text-text-muted">
        {!isOnline ? (
          <span className="flex items-center gap-1 text-warning">
            <WifiOff size={10} />
            离线
          </span>
        ) : isStreaming ? (
          <span className="flex items-center gap-1 text-accent">
            <Loader2 size={10} className="animate-spin" />
            生成中
          </span>
        ) : (
          <span className="flex items-center gap-1">
            <Wifi size={10} />
            就绪
          </span>
        )}
      </div>

      <div className="flex items-center gap-4 text-caption text-text-muted">
        {dirName && (
          <span className="flex items-center gap-1" title={workDir || ''}>
            <FolderOpen size={10} />
            {dirName}
          </span>
        )}
        {sessionId && (
          <span className="flex items-center gap-1">
            <Hash size={10} />
            {sessionId.slice(0, 12)}
          </span>
        )}
        {tokenCounts && (
          <ContextIndicator inputTokens={tokenCounts.input} outputTokens={tokenCounts.output} />
        )}
      </div>
    </div>
  );
}
