import * as fs from 'fs';
import * as path from 'path';
import * as yaml from 'js-yaml';
import { DomainConfigSchema, type DomainConfig } from './schema';

export interface PresetSummary {
  id: string;
  name: string;
  description: string;
  systemPrompt: string;
}

export interface DomainRegistry {
  listDomains(): DomainConfig[];
  getDomain(id: string): DomainConfig | null;
  getPresetFromDomain(id: string): PresetSummary | null;
}

function loadDomainFromFile(filePath: string): DomainConfig | null {
  if (!fs.existsSync(filePath)) return null;
  try {
    const raw = yaml.load(fs.readFileSync(filePath, 'utf-8'));
    const result = DomainConfigSchema.safeParse(raw);
    if (!result.success) {
      console.warn(`[registry] Invalid domain config at ${filePath}:`, result.error.issues);
      return null;
    }
    return result.data;
  } catch (err: unknown) {
    console.warn(`[registry] Failed to load ${filePath}:`, err);
    return null;
  }
}

function loadSystemPrompt(domainDir: string): string {
  const coordinatorPath = path.join(domainDir, 'prompts', 'coordinator.md');
  if (fs.existsSync(coordinatorPath)) {
    return fs.readFileSync(coordinatorPath, 'utf-8');
  }
  const leadPath = path.join(domainDir, 'prompts', 'agent_lead.md');
  if (fs.existsSync(leadPath)) {
    return fs.readFileSync(leadPath, 'utf-8');
  }
  return '';
}

export function createRegistry(domainsDir: string): DomainRegistry {
  const domains = new Map<string, DomainConfig>();

  if (fs.existsSync(domainsDir)) {
    const entries = fs.readdirSync(domainsDir, { withFileTypes: true });
    for (const entry of entries) {
      if (!entry.isDirectory()) continue;
      const domainDir = path.join(domainsDir, entry.name);
      const yamlPath = path.join(domainDir, 'domain.yaml');
      const config = loadDomainFromFile(yamlPath);
      if (config) {
        domains.set(config.id, config);
      }
    }
  }

  return {
    listDomains(): DomainConfig[] {
      return Array.from(domains.values());
    },

    getDomain(id: string): DomainConfig | null {
      return domains.get(id) ?? null;
    },

    getPresetFromDomain(id: string): PresetSummary | null {
      const config = domains.get(id);
      if (!config) return null;
      const domainDir = path.join(domainsDir, config.id);
      return {
        id: config.id,
        name: config.name,
        description: config.description,
        systemPrompt: loadSystemPrompt(domainDir),
      };
    },
  };
}
