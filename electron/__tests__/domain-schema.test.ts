import { describe, expect, it } from 'vitest';
import { DomainConfigSchema, type DomainConfig } from '../domains/schema';

const VALID_CONFIG: DomainConfig = {
  id: 'test-domain',
  name: 'Test Domain',
  description: 'A test domain',
  version: '1.0',
  phases: [
    { id: 'idle', name: 'Idle', order: -1, progress: 0, transition: { pass: 'start' } },
    { id: 'start', name: 'Start', order: 0, progress: 10, transition: { pass: 'end', fail: 'start' } },
    { id: 'end', name: 'End', order: 1, progress: 100 },
  ],
  roles: [
    { id: 'lead', name: 'Lead', emoji: '🎯', temperature: 0.5, tools: ['file_manager'] },
  ],
  directories: { output: 'output', paper: 'paper' },
};

describe('DomainConfigSchema', () => {
  it('accepts a valid config', () => {
    const result = DomainConfigSchema.safeParse(VALID_CONFIG);
    expect(result.success).toBe(true);
  });

  it('rejects missing id', () => {
    const noId = { ...VALID_CONFIG };
    delete (noId as Record<string, unknown>).id;
    const result = DomainConfigSchema.safeParse(noId);
    expect(result.success).toBe(false);
  });

  it('rejects empty phases array', () => {
    const result = DomainConfigSchema.safeParse({ ...VALID_CONFIG, phases: [] });
    expect(result.success).toBe(false);
  });

  it('rejects empty roles array', () => {
    const result = DomainConfigSchema.safeParse({ ...VALID_CONFIG, roles: [] });
    expect(result.success).toBe(false);
  });

  it('rejects phase with invalid transition target', () => {
    const badConfig = {
      ...VALID_CONFIG,
      phases: [
        { id: 'a', name: 'A', order: 0, progress: 0, transition: { pass: 'nonexistent' } },
      ],
    };
    const result = DomainConfigSchema.safeParse(badConfig);
    expect(result.success).toBe(false);
  });

  it('rejects progress out of range', () => {
    const badConfig = {
      ...VALID_CONFIG,
      phases: [
        { id: 'a', name: 'A', order: 0, progress: 150 },
      ],
    };
    const result = DomainConfigSchema.safeParse(badConfig);
    expect(result.success).toBe(false);
  });

  it('rejects temperature out of range', () => {
    const badConfig = {
      ...VALID_CONFIG,
      roles: [
        { id: 'lead', name: 'Lead', emoji: '🎯', temperature: 1.5, tools: ['file_manager'] },
      ],
    };
    const result = DomainConfigSchema.safeParse(badConfig);
    expect(result.success).toBe(false);
  });

  it('rejects path traversal in prompt paths', () => {
    const badConfig = {
      ...VALID_CONFIG,
      agents: [
        { id: 'hacker', role: 'lead', promptPath: '../../../etc/passwd' },
      ],
    };
    const result = DomainConfigSchema.safeParse(badConfig);
    expect(result.success).toBe(false);
  });

  it('rejects path traversal in knowledge path', () => {
    const badConfig = {
      ...VALID_CONFIG,
      knowledge: { path: '../../secret' },
    };
    const result = DomainConfigSchema.safeParse(badConfig);
    expect(result.success).toBe(false);
  });

  it('accepts valid agent with safe prompt path', () => {
    const config = {
      ...VALID_CONFIG,
      agents: [
        { id: 'lead', role: 'lead', promptPath: 'prompts/agent_lead.md' },
      ],
    };
    const result = DomainConfigSchema.safeParse(config);
    expect(result.success).toBe(true);
  });

  it('accepts valid knowledge path', () => {
    const config = {
      ...VALID_CONFIG,
      knowledge: { path: 'knowledge/guide.md' },
    };
    const result = DomainConfigSchema.safeParse(config);
    expect(result.success).toBe(true);
  });
});
