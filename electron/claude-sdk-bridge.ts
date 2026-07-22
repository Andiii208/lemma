import type { CanUseTool, Options, SDKMessage } from '@anthropic-ai/claude-agent-sdk';
import type { SessionManager } from './session-manager';
import type { ChatBridgeOptions } from './chat-dispatcher';
import {
  ClaudeMessageAdapter,
  createFailedIpcEvent,
  type ClaudeIpcEvent,
} from './claude-message-adapter';
import { createClaudeQueryOptions } from './claude-query-options';
import { requireRequestId } from './chat-dispatcher';

interface ChatOptions extends ChatBridgeOptions {
  canUseTool?: CanUseTool;
}

interface RendererWindow {
  isDestroyed(): boolean;
  webContents: { send(channel: string, event: ClaudeIpcEvent): void };
}

interface QueryParameters {
  prompt: string;
  options?: Options;
}

export type ClaudeQueryRunner = (
  parameters: QueryParameters,
) => AsyncIterable<SDKMessage> | Promise<AsyncIterable<SDKMessage>>;

interface RunContext {
  requestId: string;
  sessionId: string;
  controller: AbortController;
}

function isRecoverable(error: unknown): boolean {
  const message = error instanceof Error ? error.message : '';
  return /timeout|network|connection|ECONNREFUSED|fetch failed/i.test(message);
}

export class ClaudeSdkBridge {
  private currentRun: RunContext | null = null;

  constructor(
    private readonly mainWindow: RendererWindow,
    private readonly sessionManager?: SessionManager,
    private readonly queryRunner: ClaudeQueryRunner = ClaudeSdkBridge.runSdkQuery,
  ) {}

  async sendMessage(
    message: string,
    requestId: string,
    sessionId: string,
    options: ChatOptions,
  ): Promise<void> {
    const validatedRequestId = requireRequestId(requestId);
    this.cancel();
    const context = {
      requestId: validatedRequestId, sessionId, controller: new AbortController(),
    };
    this.currentRun = context;
    await this.run(message, options, context);
  }

  cancel(): void {
    const run = this.currentRun;
    this.currentRun = null;
    run?.controller.abort();
  }

  dispose(): void {
    this.cancel();
  }

  isRunning(): boolean {
    return this.currentRun !== null;
  }

  private async run(message: string, options: ChatOptions, context: RunContext): Promise<void> {
    const adapter = new ClaudeMessageAdapter(context);
    try {
      const resume = this.sessionManager?.loadSession(context.sessionId)?.claudeSessionId;
      const response = await this.queryRunner({
        prompt: message,
        options: createClaudeQueryOptions({
          ...options, resume, abortController: context.controller,
        }),
      });
      await this.forward(response, adapter, context);
    } catch (error: unknown) {
      this.handleError(error, context);
    } finally {
      if (this.currentRun?.requestId === context.requestId) this.currentRun = null;
    }
  }

  private async forward(
    response: AsyncIterable<SDKMessage>,
    adapter: ClaudeMessageAdapter,
    context: RunContext,
  ): Promise<void> {
    for await (const message of response) {
      if (!this.isCurrent(context)) break;
      for (const event of adapter.adapt(message)) {
        if (!this.isCurrent(context)) break;
        if (event.type === 'completed') {
          this.sessionManager?.updateClaudeSessionId(context.sessionId, event.claudeSessionId);
        }
        this.sendToRenderer(event);
      }
    }
  }

  private handleError(error: unknown, context: RunContext): void {
    if (!this.isCurrent(context) || context.controller.signal.aborted) return;
    const message = error instanceof Error ? error.message : 'Unknown error';
    this.sendToRenderer(createFailedIpcEvent(
      context, `Claude 调用失败: ${message}`, isRecoverable(error), [message],
    ));
  }

  private isCurrent(context: RunContext): boolean {
    return !context.controller.signal.aborted
      && this.currentRun?.requestId === context.requestId;
  }

  private sendToRenderer(event: ClaudeIpcEvent): void {
    if (!this.mainWindow.isDestroyed()) {
      this.mainWindow.webContents.send('claude-message', event);
    }
  }

  private static async runSdkQuery(parameters: QueryParameters): Promise<AsyncIterable<SDKMessage>> {
    const sdk = await ClaudeSdkBridge.loadSdk();
    return sdk.query(parameters);
  }

  private static async loadSdk(): Promise<typeof import('@anthropic-ai/claude-agent-sdk')> {
    return import('@anthropic-ai/claude-agent-sdk');
  }
}
