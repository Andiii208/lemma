import { describe, expect, it, beforeEach } from 'vitest';
import { createRegistry, type DomainRegistry } from '../domains/registry';
import * as path from 'path';

const DOMAINS_DIR = path.resolve(__dirname, '..', '..', 'domains');

describe('DomainRegistry', () => {
  let registry: DomainRegistry;

  beforeEach(() => {
    registry = createRegistry(DOMAINS_DIR);
  });

  describe('listDomains', () => {
    it('returns all domains from the domains/ directory', () => {
      const domains = registry.listDomains();
      expect(domains.length).toBeGreaterThanOrEqual(5);
      const ids = domains.map((d) => d.id);
      expect(ids).toContain('math-modeling');
      expect(ids).toContain('data-mining');
      expect(ids).toContain('literature-review');
      expect(ids).toContain('paper-writing');
      expect(ids).toContain('lab-report');
    });

    it('each domain has id, name, description', () => {
      for (const domain of registry.listDomains()) {
        expect(domain.id).toBeTruthy();
        expect(domain.name).toBeTruthy();
        expect(typeof domain.description).toBe('string');
      }
    });
  });

  describe('getDomain', () => {
    it('returns domain config for a valid id', () => {
      const domain = registry.getDomain('math-modeling');
      expect(domain).not.toBeNull();
      expect(domain!.id).toBe('math-modeling');
      expect(domain!.phases.length).toBeGreaterThan(0);
      expect(domain!.roles.length).toBeGreaterThan(0);
    });

    it('returns null for unknown id', () => {
      expect(registry.getDomain('nonexistent')).toBeNull();
    });

    it('literature-review has no dangling phase references', () => {
      const domain = registry.getDomain('literature-review');
      expect(domain).not.toBeNull();
      const phaseIds = new Set(domain!.phases.map((p) => p.id));
      for (const phase of domain!.phases) {
        if (phase.transition?.pass) {
          expect(phaseIds.has(phase.transition.pass)).toBe(true);
        }
        if (phase.transition?.fail) {
          expect(phaseIds.has(phase.transition.fail)).toBe(true);
        }
      }
    });
  });

  describe('getPresetFromDomain', () => {
    it('returns a preset object with id, name, description', () => {
      const preset = registry.getPresetFromDomain('math-modeling');
      expect(preset).not.toBeNull();
      expect(preset!.id).toBe('math-modeling');
      expect(preset!.name).toBeTruthy();
      expect(preset!.description).toBeTruthy();
    });

    it('returns null for unknown id', () => {
      expect(registry.getPresetFromDomain('nonexistent')).toBeNull();
    });

    it('generates presets for all domains', () => {
      const presets = registry.listDomains().map((d) => registry.getPresetFromDomain(d.id));
      for (const preset of presets) {
        expect(preset).not.toBeNull();
        expect(preset!.id).toBeTruthy();
        expect(preset!.name).toBeTruthy();
      }
    });
  });
});
