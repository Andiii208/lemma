import type {
  SDKAssistantMessage,
  SDKMessage,
  SDKPartialAssistantMessage,
  SDKResultMessage,
  SDKUserMessage,
} from '@anthropic-ai/claude-agent-sdk';

type AssistantContentBlock = SDKAssistantMessage['message']['content'][number];
type UserContent = SDKUserMessage['message']['content'];
type UserContentBlock = Exclude<UserContent, string>[number];

interface ClaudeIpcBase {
  requestId: string;
  sessionId: string;
}

interface ClaudeToolEvent extends ClaudeIpcBase {
  toolUseId: string;
  name: string;
  input: unknown;
  output: unknown;
  isError: boolean;
}

export type ClaudeIpcEvent =
  | (ClaudeIpcBase & { type: 'text_delta'; delta: string })
  | (ClaudeToolEvent & { type: 'tool_started' })
  | (ClaudeToolEvent & { type: 'tool_finished' })
  | (ClaudeIpcBase & {
      type: 'usage'; inputTokens: number; outputTokens: number;
      totalCostUsd: number; model?: string;
    })
  | (ClaudeIpcBase & { type: 'completed'; claudeSessionId: string })
  | (ClaudeIpcBase & {
      type: 'failed'; message: string; errors: string[]; recoverable: boolean;
    });

type AdapterContext = ClaudeIpcBase;

interface ToolDetails {
  name: string;
  input: unknown;
}

function isRecoverableMessage(message: string): boolean {
  return /timeout|network|connection|ECONNREFUSED|fetch failed/i.test(message);
}

export function createFailedIpcEvent(
  context: ClaudeIpcBase,
  message: string,
  recoverable: boolean,
  errors: string[] = [message],
): Extract<ClaudeIpcEvent, { type: 'failed' }> {
  return { ...context, type: 'failed', message, errors, recoverable };
}

export class ClaudeMessageAdapter {
  private readonly tools = new Map<string, ToolDetails>();
  private sawTextDelta = false;

  constructor(private readonly context: AdapterContext) {}

  adapt(message: SDKMessage): ClaudeIpcEvent[] {
    switch (message.type) {
      case 'assistant': return this.adaptAssistant(message.message.content);
      case 'stream_event': return this.adaptStreamEvent(message.event);
      case 'user': return this.adaptUser(message.message.content);
      case 'result': return this.adaptResult(message);
      default: return [];
    }
  }

  private adaptAssistant(content: SDKAssistantMessage['message']['content']): ClaudeIpcEvent[] {
    const suppressCompleteText = this.sawTextDelta;
    this.sawTextDelta = false;
    return content.flatMap((block: AssistantContentBlock) => {
      if (block.type === 'text') {
        return suppressCompleteText || !block.text
          ? []
          : [{ ...this.context, type: 'text_delta' as const, delta: block.text }];
      }
      if (block.type !== 'tool_use') return [];
      this.tools.set(block.id, { name: block.name, input: block.input });
      return [this.toolEvent('tool_started', block.id, null, false)];
    });
  }

  private adaptStreamEvent(
    event: SDKPartialAssistantMessage['event'],
  ): ClaudeIpcEvent[] {
    if (event.type !== 'content_block_delta' || event.delta.type !== 'text_delta') return [];
    if (!event.delta.text) return [];
    this.sawTextDelta = true;
    return [{ ...this.context, type: 'text_delta', delta: event.delta.text }];
  }

  private adaptUser(
    content: UserContent,
  ): ClaudeIpcEvent[] {
    if (typeof content === 'string') return [];
    return content.flatMap((block: UserContentBlock) => {
      if (block.type !== 'tool_result') return [];
      return [this.toolEvent(
        'tool_finished', block.tool_use_id, block.content ?? null, block.is_error ?? false,
      )];
    });
  }

  private adaptResult(result: SDKResultMessage): ClaudeIpcEvent[] {
    const events = [this.usageEvent(result)];
    if (result.subtype === 'success') {
      return [...events, {
        ...this.context, type: 'completed', claudeSessionId: result.session_id,
      }];
    }
    const errors = result.errors.length ? result.errors : [result.subtype];
    const message = errors.join('\n');
    return [...events, createFailedIpcEvent(
      this.context, message, isRecoverableMessage(message), errors,
    )];
  }

  private usageEvent(result: SDKResultMessage): ClaudeIpcEvent {
    const model = Object.keys(result.modelUsage)[0];
    return {
      ...this.context,
      type: 'usage',
      inputTokens: result.usage.input_tokens,
      outputTokens: result.usage.output_tokens,
      totalCostUsd: result.total_cost_usd,
      ...(model ? { model } : {}),
    };
  }

  private toolEvent(
    type: 'tool_started' | 'tool_finished',
    toolUseId: string,
    output: unknown,
    isError: boolean,
  ): ClaudeIpcEvent {
    const details = this.tools.get(toolUseId) ?? { name: 'Unknown tool', input: null };
    return { ...this.context, type, toolUseId, ...details, output, isError };
  }
}
