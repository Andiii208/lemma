/**
 * Lemma 前端配置
 * 新架构：通过 Electron IPC 与 Claude Agent SDK 通信
 */

// 自动选择标识
export const AUTO_MODEL = 'auto' as const;

// 可用模型列表（含层级信息）
export const AVAILABLE_MODELS = [
  { id: 'claude-sonnet-4-20250514', name: 'Claude Sonnet 4', tier: 'standard' },
  { id: 'claude-opus-4-20250514', name: 'Claude Opus 4', tier: 'premium' },
  { id: 'claude-haiku-4-20250514', name: 'Claude Haiku 4', tier: 'fast' },
] as const;

/** 根据消息长度估算查询复杂度，自动选择合适模型 */
export function selectAutoModel(messageLength: number): string {
  if (messageLength < 100) return 'claude-haiku-4-20250514';
  return 'claude-sonnet-4-20250514';
}

export interface PresetInfo {
  id: string;
  name: string;
  description: string;
}

let cachedPresets: PresetInfo[] | null = null;

export async function loadPresets(): Promise<PresetInfo[]> {
  if (cachedPresets && cachedPresets.length > 0) return cachedPresets;
  try {
    const presets = await window.lemmaAPI?.listPresets();
    if (presets && presets.length > 0) {
      cachedPresets = presets as PresetInfo[];
      return cachedPresets;
    }
    return PRESETS_FALLBACK;
  } catch {
    return PRESETS_FALLBACK;
  }
}

export const PRESETS_FALLBACK: PresetInfo[] = [
  { id: 'math-modeling', name: '数学建模', description: '数学建模竞赛全自动求解' },
  { id: 'paper-writing', name: '论文写作', description: '学术论文撰写助手' },
  { id: 'lab-report', name: '实验报告', description: '实验报告撰写与分析' },
  { id: 'literature-review', name: '文献综述', description: '系统性文献检索与综述' },
  { id: 'data-mining', name: '数据挖掘', description: '数据探索与模型构建' },
];
