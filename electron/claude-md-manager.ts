import * as fs from 'fs';
import * as path from 'path';

interface ClaudeMdConfig {
  exists: boolean;
  content: string;
  path: string;
}

export function getClaudeMdConfig(workDir: string): ClaudeMdConfig {
  const claudeMdPath = path.join(workDir, 'CLAUDE.md');
  const exists = fs.existsSync(claudeMdPath);
  const content = exists ? fs.readFileSync(claudeMdPath, 'utf-8') : '';
  return { exists, content, path: claudeMdPath };
}

export function createClaudeMd(workDir: string, template: string): void {
  const claudeMdPath = path.join(workDir, 'CLAUDE.md');
  fs.writeFileSync(claudeMdPath, template, 'utf-8');
}

export function updateClaudeMd(workDir: string, content: string): void {
  const claudeMdPath = path.join(workDir, 'CLAUDE.md');
  fs.writeFileSync(claudeMdPath, content, 'utf-8');
}

export function generateTemplate(presetId: string, workDir: string): string {
  const dirName = path.basename(workDir);
  const presetSection = buildPresetSection(presetId);

  return `# ${dirName}

## 项目描述
<!-- 描述这个项目的目标和范围 -->

## 技术栈
<!-- 列出使用的技术和工具 -->

${presetSection}

## 约束条件
<!-- 列出任何约束条件或规则 -->
`;
}

function buildPresetSection(presetId: string): string {
  try {
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    const presetsModule = require('./presets') as { getPresetById: (id: string) => Preset | undefined };
    const preset = presetsModule.getPresetById(presetId);
    if (preset) {
      const promptPreview = preset.systemPrompt?.slice(0, 200) ?? '';
      return `## 当前预设: ${preset.name}\n${preset.description}\n\n## 行为规范\n${promptPreview}...`;
    }
  } catch {
    // presets 模块不可用时降级
  }
  return `## 预设: ${presetId}`;
}

interface Preset {
  name: string;
  description: string;
  systemPrompt?: string;
}
