import { useState } from 'react';
import { CheckCircle2, XCircle, Loader2, Clock, ChevronDown, ChevronRight, Info } from 'lucide-react';

export interface PipelineStage {
  id: string;
  name: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  output?: string;
  startedAt?: string;
  completedAt?: string;
}

interface PipelineProgressProps {
  stages?: PipelineStage[];
  currentStage?: string;
  stepDescription?: string;
}

const STATUS_ICONS: Record<PipelineStage['status'], React.ReactNode> = {
  pending: <Clock size={14} className="text-text-muted" />,
  running: <Loader2 size={14} className="text-accent animate-spin" />,
  completed: <CheckCircle2 size={14} className="text-green-500" />,
  failed: <XCircle size={14} className="text-red-500" />,
};

export default function PipelineProgress({ stages = [], currentStage, stepDescription }: PipelineProgressProps) {
  const [expandedStage, setExpandedStage] = useState<string | null>(null);

  const hasStages = stages.length > 0;

  const completedCount = stages.filter((stage) => stage.status === 'completed').length;
  const progressPercent = hasStages ? Math.round((completedCount / stages.length) * 100) : 0;

  const getEffectiveStatus = (stage: PipelineStage): PipelineStage['status'] => {
    if (stage.status === 'pending' && stage.id === currentStage) return 'running';
    return stage.status;
  };

  const toggleExpand = (stageId: string) => {
    setExpandedStage((prev) => (prev === stageId ? null : stageId));
  };

  return (
    <div className="p-4 space-y-4">
      <h3 className="text-sm font-semibold text-text">
        Pipeline 进度
      </h3>

      {/* 步骤说明模式：无真实阶段时显示 */}
      {!hasStages && stepDescription && (
        <div className="flex items-start gap-2 p-3 rounded-lg bg-bg-elevated border border-border">
          <Info size={16} className="text-accent shrink-0 mt-0.5" />
          <div className="text-sm text-text-secondary">
            {stepDescription}
          </div>
        </div>
      )}

      {/* 进度条：仅在有真实阶段时显示 */}
      {hasStages && (
        <div className="space-y-1">
          <div className="flex justify-between text-xs text-text-muted">
            <span>{completedCount}/{stages.length} 阶段完成</span>
            <span>{progressPercent}%</span>
          </div>
          <div className="h-2 rounded-full bg-bg-tertiary overflow-hidden">
            <div
              className="h-full rounded-full bg-accent transition-all duration-500"
              style={{ width: `${progressPercent}%` }}
            />
          </div>
        </div>
      )}

      {/* 阶段列表：仅在有真实阶段时显示 */}
      {hasStages && (
        <div className="space-y-1">
          {stages.map((stage) => {
            const status = getEffectiveStatus(stage);
            const isExpanded = expandedStage === stage.id;

            return (
              <div key={stage.id} className="rounded-lg border border-border">
                <button
                  onClick={() => stage.output && toggleExpand(stage.id)}
                  className="flex items-center gap-2 w-full px-3 py-2 text-sm transition-colors hover:bg-bg-secondary"
                >
                  {STATUS_ICONS[status]}
                  <span className="flex-1 text-left">{stage.name}</span>
                  {stage.output && (
                    isExpanded ? <ChevronDown size={12} /> : <ChevronRight size={12} />
                  )}
                  {stage.completedAt && (
                    <span className="text-xs text-text-muted">
                      {new Date(stage.completedAt).toLocaleTimeString()}
                    </span>
                  )}
                </button>
                {isExpanded && stage.output && (
                  <pre className="px-3 py-2 text-xs font-mono bg-bg-secondary border-t border-border overflow-x-auto">
                    {stage.output}
                  </pre>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* 空状态：既无阶段也无说明 */}
      {!hasStages && !stepDescription && (
        <p className="text-sm text-text-muted">暂无进度信息</p>
      )}
    </div>
  );
}
