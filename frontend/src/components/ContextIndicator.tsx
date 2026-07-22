interface ContextIndicatorProps {
  inputTokens: number;
  outputTokens: number;
  maxTokens?: number;
}

const DEFAULT_MAX = 200_000;

export default function ContextIndicator({ inputTokens, outputTokens, maxTokens = DEFAULT_MAX }: ContextIndicatorProps) {
  const totalTokens = inputTokens + outputTokens;
  const percent = Math.min(100, Math.round((totalTokens / maxTokens) * 100));
  const barColor = percent > 80 ? 'bg-error' : percent > 50 ? 'bg-warning' : 'bg-success';

  const formatCount = (count: number): string => {
    if (count >= 1_000_000) return `${(count / 1_000_000).toFixed(1)}M`;
    if (count >= 1_000) return `${(count / 1_000).toFixed(1)}K`;
    return count.toString();
  };

  return (
    <div
      className="flex items-center gap-2 text-caption text-text-muted"
      title={`上下文: ${formatCount(totalTokens)} / ${formatCount(maxTokens)} tokens`}
    >
      <div className="w-16 h-1.5 rounded-full bg-bg-tertiary overflow-hidden">
        <div
          className={`h-full rounded-full ${barColor} transition-all duration-300`}
          style={{ width: `${percent}%` }}
        />
      </div>
      <span>{percent}%</span>
    </div>
  );
}
