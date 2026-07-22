import { describe, expect, it } from 'vitest';
import type { SDKMessage } from '@anthropic-ai/claude-agent-sdk';
import { ClaudeMessageAdapter, createFailedIpcEvent } from '../claude-message-adapter';

const context = { requestId: 'request-1', sessionId: 'session-1' };

function sdkMessage(value: unknown): SDKMessage {
  return value as SDKMessage;
}

function assistant(content: unknown[]): SDKMessage {
  return sdkMessage({
    type: 'assistant',
    message: { content, id: 'message-1', model: 'claude-sonnet', role: 'assistant' },
    parent_tool_use_id: null,
    uuid: 'assistant-1',
    session_id: 'claude-session-1',
  });
}

function result(subtype: 'success' | 'error_during_execution'): SDKMessage {
  return sdkMessage({
    type: 'result',
    subtype,
    duration_ms: 10,
    duration_api_ms: 8,
    is_error: subtype !== 'success',
    num_turns: 1,
    stop_reason: null,
    total_cost_usd: 0.012,
    usage: { input_tokens: 12, output_tokens: 7 },
    modelUsage: {
      'claude-sonnet': {
        inputTokens: 12,
        outputTokens: 7,
        cacheReadInputTokens: 0,
        cacheCreationInputTokens: 0,
        webSearchRequests: 0,
        costUSD: 0.012,
        contextWindow: 200000,
        maxOutputTokens: 8192,
      },
    },
    permission_denials: [],
    errors: subtype === 'success' ? undefined : ['network connection lost'],
    result: subtype === 'success' ? 'ok' : undefined,
    uuid: 'result-1',
    session_id: 'claude-session-1',
  });
}

describe('ClaudeMessageAdapter', () => {
  it('creates a valid failure event for errors outside an SDK query', () => {
    expect(createFailedIpcEvent(context, 'API key is unavailable', false)).toEqual({
      ...context,
      type: 'failed',
      message: 'API key is unavailable',
      errors: ['API key is unavailable'],
      recoverable: false,
    });
  });

  it('emits text deltas from partial stream events', () => {
    const adapter = new ClaudeMessageAdapter(context);
    const events = adapter.adapt(sdkMessage({
      type: 'stream_event',
      event: {
        type: 'content_block_delta',
        index: 0,
        delta: { type: 'text_delta', text: 'Hello' },
      },
      parent_tool_use_id: null,
      uuid: 'partial-1',
      session_id: 'claude-session-1',
    }));

    expect(events).toEqual([{ ...context, type: 'text_delta', delta: 'Hello' }]);
  });

  it('falls back to assistant text when no partial text was received', () => {
    const adapter = new ClaudeMessageAdapter(context);
    expect(adapter.adapt(assistant([{ type: 'text', text: 'Complete answer', citations: [] }]))).toEqual([{
      ...context,
      type: 'text_delta',
      delta: 'Complete answer',
    }]);
  });

  it('does not duplicate assistant text after partial deltas', () => {
    const adapter = new ClaudeMessageAdapter(context);
    adapter.adapt(sdkMessage({
      type: 'stream_event',
      event: {
        type: 'content_block_delta',
        index: 0,
        delta: { type: 'text_delta', text: 'Complete answer' },
      },
      parent_tool_use_id: null,
      uuid: 'partial-1',
      session_id: 'claude-session-1',
    }));
    const completeEvents = adapter.adapt(assistant([{
      type: 'text', text: 'Complete answer', citations: [],
    }]));

    expect(completeEvents).toEqual([]);
  });

  it('falls back in a later assistant turn after an earlier turn used partial text', () => {
    const adapter = new ClaudeMessageAdapter(context);
    adapter.adapt(sdkMessage({
      type: 'stream_event',
      event: {
        type: 'content_block_delta', index: 0,
        delta: { type: 'text_delta', text: 'First turn' },
      },
      parent_tool_use_id: null,
      uuid: 'partial-turn-1',
      session_id: 'claude-session-1',
    }));
    const firstComplete = adapter.adapt(assistant([
      { type: 'text', text: 'First turn', citations: [] },
      { type: 'tool_use', id: 'tool-1', name: 'Read', input: { file_path: 'README.md' } },
    ]));
    adapter.adapt(sdkMessage({
      type: 'user',
      message: { role: 'user', content: [{
        type: 'tool_result', tool_use_id: 'tool-1', content: 'contents', is_error: false,
      }] },
      parent_tool_use_id: null,
      uuid: 'tool-result-1',
      session_id: 'claude-session-1',
    }));

    expect(firstComplete.filter((event) => event.type === 'text_delta')).toEqual([]);
    expect(adapter.adapt(assistant([{
      type: 'text', text: 'Second turn fallback', citations: [],
    }]))).toEqual([{
      ...context, type: 'text_delta', delta: 'Second turn fallback',
    }]);
  });

  it('maps tool use and matching tool result with their real content blocks', () => {
    const adapter = new ClaudeMessageAdapter(context);
    const started = adapter.adapt(assistant([{
      type: 'tool_use',
      id: 'tool-1',
      name: 'Read',
      input: { file_path: 'README.md' },
    }]));
    const finished = adapter.adapt(sdkMessage({
      type: 'user',
      message: {
        role: 'user',
        content: [{
          type: 'tool_result',
          tool_use_id: 'tool-1',
          content: 'file contents',
          is_error: false,
        }],
      },
      parent_tool_use_id: null,
      uuid: 'user-1',
      session_id: 'claude-session-1',
    }));

    expect(started).toEqual([{
      ...context,
      type: 'tool_started',
      toolUseId: 'tool-1',
      name: 'Read',
      input: { file_path: 'README.md' },
      output: null,
      isError: false,
    }]);
    expect(finished).toEqual([{
      ...context,
      type: 'tool_finished',
      toolUseId: 'tool-1',
      name: 'Read',
      input: { file_path: 'README.md' },
      output: 'file contents',
      isError: false,
    }]);
  });

  it('maps success result usage, cost, model, and Claude session id', () => {
    const events = new ClaudeMessageAdapter(context).adapt(result('success'));

    expect(events).toEqual([
      {
        ...context,
        type: 'usage',
        inputTokens: 12,
        outputTokens: 7,
        totalCostUsd: 0.012,
        model: 'claude-sonnet',
      },
      { ...context, type: 'completed', claudeSessionId: 'claude-session-1' },
    ]);
  });

  it('maps result errors without completing the request', () => {
    const events = new ClaudeMessageAdapter(context).adapt(result('error_during_execution'));

    expect(events.at(-1)).toEqual({
      ...context,
      type: 'failed',
      message: 'network connection lost',
      errors: ['network connection lost'],
      recoverable: true,
    });
    expect(events.some((event) => event.type === 'completed')).toBe(false);
  });

  it('ignores system and unknown SDK messages without emitting empty text', () => {
    const adapter = new ClaudeMessageAdapter(context);
    const system = sdkMessage({
      type: 'system',
      subtype: 'init',
      uuid: 'system-1',
      session_id: 'claude-session-1',
    });

    expect(adapter.adapt(system)).toEqual([]);
    expect(adapter.adapt(sdkMessage({ type: 'future_event' }))).toEqual([]);
  });
});
