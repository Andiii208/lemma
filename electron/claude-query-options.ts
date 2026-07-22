import type { CanUseTool, Options } from '@anthropic-ai/claude-agent-sdk';

const READ_ONLY_TOOLS = ['Read', 'Glob', 'Grep'];
const SAFE_WRITE_TOOLS = ['Write', 'Edit', 'MultiEdit'];
const ALL_ALLOWED_TOOLS = [...READ_ONLY_TOOLS, ...SAFE_WRITE_TOOLS];

export interface ClaudeQueryOptionsInput {
  workDir?: string;
  model?: string;
  systemPrompt?: string;
  apiKey: string;
  abortController: AbortController;
  canUseTool?: CanUseTool;
  resume?: string;
}

function createToolPermissionHandler(delegate?: CanUseTool): CanUseTool {
  return async (toolName, input, options) => {
    if (!ALL_ALLOWED_TOOLS.includes(toolName)) {
      return {
        behavior: 'deny',
        message: `Tool ${toolName} is not permitted`,
      };
    }
    return delegate ? delegate(toolName, input, options) : { behavior: 'allow' };
  };
}

export function createClaudeQueryOptions(input: ClaudeQueryOptionsInput): Options {
  if (!input.apiKey.trim()) throw new Error('API key is required');

  return {
    cwd: input.workDir,
    model: input.model,
    resume: input.resume,
    systemPrompt: input.systemPrompt,
    abortController: input.abortController,
    includePartialMessages: true,
    settingSources: [],
    strictMcpConfig: true,
    permissionMode: 'dontAsk',
    tools: [...ALL_ALLOWED_TOOLS],
    canUseTool: createToolPermissionHandler(input.canUseTool),
    maxTurns: 20,
    maxBudgetUsd: 2,
    env: { ...process.env, ANTHROPIC_API_KEY: input.apiKey },
  };
}
