import { useState, useRef, useEffect, Suspense, lazy, type KeyboardEvent } from 'react';
import { IPC_CHANNELS } from '../constants';
import { Send, Square, Trash2, ChevronDown, ChevronRight, RefreshCw, Wrench } from 'lucide-react';
import { Virtuoso } from 'react-virtuoso';
import MessageActions from './MessageActions';

const LazyMarkdown = lazy(() => import('./LazyMarkdown'));

interface ChatPanelProps {
  messages: ClaudeMessage[];
  isStreaming: boolean;
  onSend: (text: string, options?: ChatOptions) => void;
  onCancel: () => void;
  onClearMessages: () => void;
  onRetry?: () => void;
}

export default function ChatPanel({
  messages,
  isStreaming,
  onSend,
  onCancel,
  onClearMessages,
  onRetry,
}: ChatPanelProps) {
  const [inputText, setInputText] = useState('');
  const [expandedTools, setExpandedTools] = useState<Set<number>>(new Set());
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // 用 ref 解耦闭包，确保 Ctrl+Enter 始终调用最新的 handleSend
  const handleSendRef = useRef<() => void>(() => {});

  // 监听全局 send-message 事件（Ctrl+Enter 快捷键触发）
  useEffect(() => {
    const handler = () => handleSendRef.current();
    document.addEventListener(IPC_CHANNELS.SEND_MESSAGE, handler);
    return () => document.removeEventListener(IPC_CHANNELS.SEND_MESSAGE, handler);
  }, []);

  const handleKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleSend();
    }
  };

  const handleSend = () => {
    const trimmed = inputText.trim();
    if (!trimmed || isStreaming) return;
    onSend(trimmed);
    setInputText('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  // 每次渲染更新 ref，确保事件监听器调用最新的闭包
  handleSendRef.current = handleSend;

  const toggleToolExpand = (index: number) => {
    setExpandedTools((prev) => {
      const next = new Set(prev);
      if (next.has(index)) next.delete(index);
      else next.add(index);
      return next;
    });
  };

  return (
    <div className="flex flex-col h-full">
      {/* 消息列表 */}
      {messages.length === 0 ? (
        <div className="flex-1 flex items-center justify-center px-4 py-6">
          <div className="flex flex-col items-center justify-center h-full text-text-muted">
            <h2 className="text-2xl font-serif mb-2">Lemma</h2>
            <p className="text-sm">Every Theorem Begins with a Lemma</p>
            <p className="text-xs mt-4">输入问题开始对话，或选择一个预设模板</p>
          </div>
        </div>
      ) : (
        <Virtuoso
          className="flex-1"
          data={messages}
          followOutput="smooth"
          itemContent={(index, message) => (
            <div className="px-4 py-2">
              <MessageBubble
                message={message}
                isExpanded={expandedTools.has(index)}
                onToggleExpand={() => toggleToolExpand(index)}
                onRetry={onRetry}
              />
            </div>
          )}
          components={{
            Footer: () => (
              <div className="px-4 py-2">
                {isStreaming && messages.length > 0 && messages[messages.length - 1]?.metadata?.role === 'user' && (
                  <div className="max-w-4xl mx-auto">
                    <div className="rounded-lg px-4 py-3 bg-bg-tertiary inline-block">
                      <div className="typing-indicator flex items-center gap-1">
                        <span /><span /><span />
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ),
          }}
        />
      )}

      {/* 输入区域 */}
      <div className="border-t border-border p-4">
        <div className="flex items-end gap-2 max-w-4xl mx-auto">
          <textarea
            ref={textareaRef}
            value={inputText}
            onChange={(event) => setInputText(event.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="输入消息... (Shift+Enter 换行)"
            aria-label="输入消息 (Shift+Enter 换行)"
            rows={1}
            className="flex-1 resize-none rounded-lg border border-border-strong bg-bg-secondary px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-accent focus:border-transparent"
            style={{ maxHeight: '200px' }}
          />

          {isStreaming ? (
            <button
              onClick={onCancel}
              className="flex items-center gap-1 px-4 py-3 rounded-lg bg-red-500 hover:bg-red-600 text-white text-sm transition-colors"
            >
              <Square size={16} />
              停止
            </button>
          ) : (
            <button
              onClick={handleSend}
              disabled={!inputText.trim()}
              className="flex items-center gap-1 px-4 py-3 rounded-lg bg-accent hover:bg-accent-hover disabled:opacity-50 disabled:cursor-not-allowed text-white text-sm transition-colors"
            >
              <Send size={16} />
              发送
            </button>
          )}

          {messages.length > 0 && !isStreaming && (
            <button
              onClick={onClearMessages}
              className="p-3 rounded-lg hover:bg-bg-tertiary text-text-muted transition-colors"
              aria-label="清空对话"
            >
              <Trash2 size={16} />
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

function extractToolName(content: string, type: string): string {
  try {
    const parsed = JSON.parse(content);
    if (type === 'tool_use' && parsed.name) return parsed.name;
    if (type === 'tool_result' && parsed.tool_use_id) return '工具';
  } catch {
    // Not JSON
  }
  return type === 'tool_use' ? '工具调用' : '工具结果';
}

function formatToolContent(content: string): string {
  try {
    const parsed = JSON.parse(content);
    return JSON.stringify(parsed, null, 2);
  } catch {
    return content;
  }
}

function MessageBubble({
  message,
  isExpanded,
  onToggleExpand,
  onRetry,
}: {
  message: ClaudeMessage;
  isExpanded: boolean;
  onToggleExpand: () => void;
  onRetry?: () => void;
}) {
  const isUser = message.metadata?.role === 'user';
  const isToolUse = message.type === 'tool_use';
  const isToolResult = message.type === 'tool_result';

  if (isToolUse || isToolResult) {
    const toolName = extractToolName(message.content, message.type);
    return (
      <div className="max-w-4xl mx-auto">
        <button
          onClick={onToggleExpand}
          aria-expanded={isExpanded}
          className="flex items-center gap-2 w-full px-3 py-2 rounded-lg text-xs bg-bg-elevated hover:bg-bg-tertiary transition-colors border border-border"
        >
          {isExpanded ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
          <Wrench size={12} className="text-accent shrink-0" />
          <span className="font-medium text-text-secondary">
            {isToolUse ? toolName : `${toolName} 结果`}
          </span>
          <span className="ml-auto text-text-muted">
            {isExpanded ? '收起' : '展开'}
          </span>
        </button>
        {isExpanded && (
          <pre className="mt-1 p-3 rounded text-xs bg-bg-tertiary overflow-x-auto border-l-2 border-accent max-h-64">
            {formatToolContent(message.content)}
          </pre>
        )}
      </div>
    );
  }

  return (
    <div className={`max-w-4xl mx-auto group ${isUser ? 'flex flex-col items-end' : ''}`}>
      <div
        className={`rounded-lg px-4 py-3 ${
          isUser
            ? 'bg-accent text-white'
            : 'bg-bg-tertiary'
        }`}
      >
        {isUser ? (
          <p className="text-sm whitespace-pre-wrap">{message.content}</p>
        ) : (
          <Suspense fallback={<div className="text-sm text-text-muted animate-pulse">加载中...</div>}>
            <LazyMarkdown content={message.content} />
          </Suspense>
        )}
      </div>
      <MessageActions
        content={message.content}
        isUser={isUser}
        onRegenerate={!isUser ? onRetry : undefined}
      />
      {message.type === 'error' && onRetry && (
        <button
          onClick={onRetry}
          className="mt-2 flex items-center gap-1 text-xs text-accent hover:text-accent"
        >
          <RefreshCw size={12} /> 重试
        </button>
      )}
    </div>
  );
}
