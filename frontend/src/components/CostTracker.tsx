import { useState, useEffect, useRef } from 'react';
import { DollarSign, TrendingUp, BarChart3 } from 'lucide-react';

export interface UsageData {
  inputTokens: number;
  outputTokens: number;
  totalCostUsd: number;
  model?: string;
}

interface CostTrackerProps {
  usage?: UsageData;
  sessionId?: string;
}

interface SessionUsage {
  inputTokens: number;
  outputTokens: number;
  totalCostUsd: number;
  model?: string;
}

export default function CostTracker({ usage, sessionId }: CostTrackerProps) {
  const [sessionUsage, setSessionUsage] = useState<SessionUsage>({
    inputTokens: 0,
    outputTokens: 0,
    totalCostUsd: 0,
  });
  const prevSessionRef = useRef(sessionId);

  useEffect(() => {
    if (sessionId !== prevSessionRef.current) {
      prevSessionRef.current = sessionId;
      setSessionUsage({ inputTokens: 0, outputTokens: 0, totalCostUsd: 0 });
    }
  }, [sessionId]);

  useEffect(() => {
    if (usage) {
      setSessionUsage((prev) => ({
        inputTokens: prev.inputTokens + usage.inputTokens,
        outputTokens: prev.outputTokens + usage.outputTokens,
        totalCostUsd: prev.totalCostUsd + usage.totalCostUsd,
        model: usage.model ?? prev.model,
      }));
    }
  }, [usage]);

  const formatTokens = (count: number): string => {
    if (count >= 1_000_000) return `${(count / 1_000_000).toFixed(1)}M`;
    if (count >= 1_000) return `${(count / 1_000).toFixed(1)}K`;
    return count.toString();
  };

  const formatCost = (cost: number): string => {
    if (cost < 0.01) return `$${cost.toFixed(4)}`;
    return `$${cost.toFixed(2)}`;
  };

  const displayModel = sessionUsage.model ?? 'unknown';

  return (
    <div className="p-4 space-y-4">
      <h3 className="flex items-center gap-2 text-sm font-semibold">
        <DollarSign size={16} />
        成本追踪
      </h3>

      <p className="text-xs text-text-muted">
        * 数据来自 SDK 实际返回的 usage
      </p>

      {/* 当前会话统计 */}
      <div className="grid grid-cols-2 gap-3">
        <div className="p-3 rounded-lg bg-bg-elevated">
          <div className="flex items-center gap-1 text-xs text-text-muted mb-1">
            <TrendingUp size={12} />
            输入 Token
          </div>
          <p className="text-lg font-semibold">{formatTokens(sessionUsage.inputTokens)}</p>
        </div>
        <div className="p-3 rounded-lg bg-bg-elevated">
          <div className="flex items-center gap-1 text-xs text-text-muted mb-1">
            <TrendingUp size={12} />
            输出 Token
          </div>
          <p className="text-lg font-semibold">{formatTokens(sessionUsage.outputTokens)}</p>
        </div>
      </div>

      {/* 实际成本 */}
      <div className="p-3 rounded-lg bg-accent-soft border border-accent">
        <div className="flex items-center gap-1 text-xs text-accent mb-1">
          <BarChart3 size={12} />
          当前会话成本
        </div>
        <p className="text-2xl font-bold text-accent">
          {formatCost(sessionUsage.totalCostUsd)}
        </p>
        <p className="text-xs text-text-muted mt-1">
          模型: {displayModel}
        </p>
      </div>
    </div>
  );
}
