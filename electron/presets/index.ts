import * as path from 'path';
import { createRegistry, type DomainRegistry } from '../domains/registry';

export interface Preset {
  id: string;
  name: string;
  description: string;
  systemPrompt: string;
  icon: string;
}

const ICONS: Record<string, string> = {
  'math-modeling': '📐',
  'paper-writing': '📝',
  'lab-report': '🔬',
  'literature-review': '📚',
  'data-mining': '📊',
};

function buildRegistry(): DomainRegistry {
  const baseDir = path.resolve(__dirname, '..', '..', 'domains');
  return createRegistry(baseDir);
}

let cachedRegistry: DomainRegistry | null = null;

function getRegistry(): DomainRegistry {
  if (!cachedRegistry) {
    cachedRegistry = buildRegistry();
  }
  return cachedRegistry;
}

export function getPresets(): Preset[] {
  const registry = getRegistry();
  return registry.listDomains().map((domain) => {
    const preset = registry.getPresetFromDomain(domain.id);
    return {
      id: domain.id,
      name: domain.name,
      description: domain.description,
      systemPrompt: preset?.systemPrompt ?? '',
      icon: ICONS[domain.id] ?? '📄',
    };
  });
}

export const presets: Preset[] = getPresets();

export function getPresetById(presetId: string): Preset | undefined {
  return presets.find((preset) => preset.id === presetId);
}
