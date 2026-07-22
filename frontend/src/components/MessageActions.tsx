import { useState } from 'react';
import { Copy, Check, RefreshCw } from 'lucide-react';
import { TIMING } from '../constants';

interface MessageActionsProps {
  content: string;
  isUser: boolean;
  onRegenerate?: () => void;
}

export default function MessageActions({ content, isUser, onRegenerate }: MessageActionsProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(content);
      setCopied(true);
      setTimeout(() => setCopied(false), TIMING.COPY_FEEDBACK_DURATION);
    } catch {
      // Clipboard may fail
    }
  };

  return (
    <div className="flex items-center gap-1 mt-1 opacity-0 group-hover:opacity-100 group-focus-within:opacity-100 transition-opacity" data-testid="message-actions">
      <button
        onClick={handleCopy}
        className="p-1 rounded hover:bg-bg-tertiary text-text-muted hover:text-text-secondary transition-colors"
        aria-label="复制消息"
      >
        {copied ? <Check size={12} className="text-success" /> : <Copy size={12} />}
      </button>
      {!isUser && onRegenerate && (
        <button
          onClick={onRegenerate}
          className="p-1 rounded hover:bg-bg-tertiary text-text-muted hover:text-text-secondary transition-colors"
          aria-label="重新生成"
        >
          <RefreshCw size={12} />
        </button>
      )}
    </div>
  );
}
