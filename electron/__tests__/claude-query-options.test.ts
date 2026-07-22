import { describe, expect, it, vi } from 'vitest';
import type { CanUseTool } from '@anthropic-ai/claude-agent-sdk';
import { createClaudeQueryOptions } from '../claude-query-options';

const permissionContext = {
  signal: new AbortController().signal,
  toolUseID: 'tool-use-id',
  requestId: 'request-id',
};

describe('createClaudeQueryOptions', () => {
  it('isolates project configuration and exposes only read-only tools', () => {
    const abortController = new AbortController();
    const options = createClaudeQueryOptions({
      workDir: 'C:\\workspace',
      model: 'claude-sonnet-4-5',
      systemPrompt: 'Review the project',
      apiKey: 'sk-ant-test',
      abortController,
    });

    expect(options).toMatchObject({
      cwd: 'C:\\workspace',
      model: 'claude-sonnet-4-5',
      systemPrompt: 'Review the project',
      abortController,
      settingSources: [],
      strictMcpConfig: true,
      tools: ['Read', 'Glob', 'Grep'],
      maxTurns: 20,
      maxBudgetUsd: 2,
      includePartialMessages: true,
    });
    expect(options).not.toHaveProperty('allowedTools');
    expect(options.canUseTool).toBeTypeOf('function');
  });

  it('injects the API key into a copied environment without mutating process.env', () => {
    const originalEnvironment = { ...process.env };

    const options = createClaudeQueryOptions({
      apiKey: 'sk-ant-injected',
      abortController: new AbortController(),
    });

    expect(options.env).not.toBe(process.env);
    expect(options.env).toEqual({
      ...originalEnvironment,
      ANTHROPIC_API_KEY: 'sk-ant-injected',
    });
    expect(process.env).toEqual(originalEnvironment);
  });

  it('passes the Claude SDK session id through resume', () => {
    const options = createClaudeQueryOptions({
      apiKey: 'sk-ant-test',
      abortController: new AbortController(),
      resume: 'claude-session-id',
    });

    expect(options.resume).toBe('claude-session-id');
  });

  it('rejects an empty API key instead of placing it in the environment', () => {
    expect(() => createClaudeQueryOptions({
      apiKey: '   ',
      abortController: new AbortController(),
    })).toThrow('API key is required');
  });

  it('denies dangerous tools by default', async () => {
    const options = createClaudeQueryOptions({
      apiKey: 'sk-ant-test',
      abortController: new AbortController(),
    });

    await expect(options.canUseTool?.('Bash', { command: 'rm -rf .' }, permissionContext))
      .resolves.toEqual({
        behavior: 'deny',
        message: 'Tool Bash is not permitted',
      });
    await expect(options.canUseTool?.('Read', { file_path: 'README.md' }, permissionContext))
      .resolves.toMatchObject({ behavior: 'allow' });
  });

  it('does not let an injected permission handler allow dangerous tools', async () => {
    const canUseTool = vi.fn<CanUseTool>(async () => ({ behavior: 'allow' }));

    const options = createClaudeQueryOptions({
      apiKey: 'sk-ant-test',
      abortController: new AbortController(),
      canUseTool,
    });

    await expect(options.canUseTool?.('Bash', { command: 'echo unsafe' }, permissionContext))
      .resolves.toEqual({
        behavior: 'deny',
        message: 'Tool Bash is not permitted',
      });
    expect(canUseTool).not.toHaveBeenCalled();
  });

  it('delegates read-only tools to an injected permission handler', async () => {
    const canUseTool = vi.fn<CanUseTool>(async () => ({
      behavior: 'deny',
      message: 'User denied access',
    }));
    const options = createClaudeQueryOptions({
      apiKey: 'sk-ant-test',
      abortController: new AbortController(),
      canUseTool,
    });

    await expect(options.canUseTool?.('Read', { file_path: 'README.md' }, permissionContext))
      .resolves.toEqual({
        behavior: 'deny',
        message: 'User denied access',
      });
    expect(canUseTool).toHaveBeenCalledOnce();
  });
});
