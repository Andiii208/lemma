import { useState, useEffect, Suspense, lazy, useCallback, useMemo } from 'react';
import { IPC_CHANNELS } from './constants';
import { selectAutoModel } from './config';
import { useApp } from './context/AppContext';
import { useClaude } from './hooks/useClaude';
import { useMessageStore } from './hooks/useMessageStore';
import { useSessionLifecycle } from './hooks/useSessionLifecycle';
import { useSessionMessageBinding } from './hooks/useSessionMessageBinding';
import {
  deleteSessionWithOutbox, useSessionMessageQueue,
} from './hooks/useSessionMessageQueue';
import { useKeyboardShortcuts, DEFAULT_SHORTCUTS } from './hooks/useKeyboardShortcuts';
import { useNetworkStatus } from './hooks/useNetworkStatus';
import { createNotifyHelper } from './utils/notifyHelper';
import Sidebar from './components/Sidebar';
import TitleBar from './components/TitleBar';
import ChatPanel from './components/ChatPanel';
import StatusBar from './components/StatusBar';
import RetryBanner from './components/RetryBanner';
import FileBrowser from './components/FileBrowser';
import CostTracker from './components/CostTracker';
import OnboardingWizard from './components/OnboardingWizard';
import { exportMessages, exportMessagesJson, copyToClipboard, downloadFile } from './utils/export';

const SettingsPanel = lazy(() => import('./components/SettingsPanel'));
const PipelineProgress = lazy(() => import('./components/PipelineProgress'));

export default function App() {
  const { state, dispatch } = useApp();
  const sessionId = state.currentSessionId;
  const notify = useMemo(
    () => createNotifyHelper(() => state.notificationsEnabled, window.lemmaAPI?.notify),
    [state.notificationsEnabled],
  );
  const claude = useClaude(sessionId, notify);
  const messageStore = useMessageStore(sessionId);
  const network = useNetworkStatus(undefined, notify);
  const [apiKeyStatus, setApiKeyStatus] = useState<'checking' | 'missing' | 'configured'>('checking');
  const [sdkWarning, setSdkWarning] = useState<string | null>(null);
  const [lastFailedText, setLastFailedText] = useState<string | undefined>();
  const [lastFailedOptions, setLastFailedOptions] = useState<ChatOptions | undefined>();
  const sessionLifecycle = useSessionLifecycle({
    currentSessionId: sessionId,
    workDir: state.workDir,
    isStreaming: claude.isStreaming,
    cancelStream: claude.cancelStream,
    clearMessages: claude.clearMessages,
    deleteMessages: messageStore.deleteMessages,
    migrateDefaultMessages: messageStore.migrateDefaultMessages,
    dispatch,
  });
  const sessionMessagesLoaded = useSessionMessageBinding({
    sessionId,
    messages: claude.messages,
    setMessages: claude.setMessages,
    loadMessages: messageStore.loadMessages,
    saveMessages: messageStore.saveMessages,
  });

  useEffect(() => {
    const checkApiKey = async () => {
      if (!window.lemmaAPI) {
        setApiKeyStatus('missing');
        return;
      }
      try {
        const configured = await window.lemmaAPI.hasApiKey();
        setApiKeyStatus(configured ? 'configured' : 'missing');
        dispatch({ type: 'SET_API_KEY_CONFIGURED', payload: configured });
      } catch {
        setApiKeyStatus('missing');
      }
    };
    checkSdk();
    checkApiKey();
  }, [dispatch, setApiKeyStatus]);

  // 发送成功后清错误和失败记录
  useEffect(() => {
    if (!claude.error && !claude.isStreaming) {
      setLastFailedText(undefined);
      setLastFailedOptions(undefined);
    }
  }, [claude.messages, claude.error, claude.isStreaming, setLastFailedText, setLastFailedOptions]);

  useEffect(() => {
    const handler = (event: Event) => {
      const configured = (event as CustomEvent).detail as boolean;
      dispatch({ type: 'SET_API_KEY_CONFIGURED', payload: configured });
      setApiKeyStatus(configured ? 'configured' : 'missing');
    };
    document.addEventListener(IPC_CHANNELS.API_KEY_STATUS, handler);
    return () => document.removeEventListener(IPC_CHANNELS.API_KEY_STATUS, handler);
  }, [dispatch, setApiKeyStatus]);

  const checkSdk = async () => {
    if (!window.lemmaAPI) return;
    try {
      const versionInfo = await window.lemmaAPI.checkSdkVersion();
      if (versionInfo.warning) setSdkWarning(versionInfo.warning);
    } catch { /* 忽略 */ }
  };

  const sendToClaude = useCallback(async (text: string) => {
    const options: ChatOptions = {};
    if (state.workDir) options.workDir = state.workDir;
    if (state.selectedPreset) options.presetId = state.selectedPreset;
    const effectiveModel = state.selectedModel === 'auto'
      ? selectAutoModel(text.length)
      : state.selectedModel;
    options.model = effectiveModel;
    try {
      await claude.sendMessage(text, options);
    } catch {
      // 保存失败请求供 RetryBanner 使用
      setLastFailedText(text);
      setLastFailedOptions(options);
    }
  }, [state.workDir, state.selectedPreset, state.selectedModel, claude, setLastFailedText, setLastFailedOptions]);
  const messageQueue = useSessionMessageQueue({
    sessionId,
    isBound: sessionMessagesLoaded,
    createAndSelectSession: sessionLifecycle.createAndSelectSession,
    sendMessage: sendToClaude,
    loadPendingMessages: messageStore.loadPendingMessages,
    savePendingMessages: messageStore.savePendingMessages,
  });
  const { enqueueMessage } = messageQueue;
  const handleSend = useCallback((text: string) => {
    void enqueueMessage(text);
  }, [enqueueMessage]);

  const handleClearWithPersist = useCallback(() => {
    claude.clearMessages();
    void messageStore.deleteMessages();
  }, [claude, messageStore]);

  const handleExport = useCallback(() => {
    const content = exportMessages(claude.messages, {
      format: 'markdown',
      includeTimestamps: true,
      includeMetadata: false,
    });
    downloadFile(content, `lemma-export-${Date.now()}.md`, 'text/markdown');
  }, [claude.messages]);

  const handleExportJson = useCallback(() => {
    const content = exportMessagesJson(claude.messages);
    downloadFile(content, `lemma-export-${Date.now()}.json`, 'application/json');
  }, [claude.messages]);

  const handleCopyChat = useCallback(async () => {
    const content = exportMessages(claude.messages, {
      format: 'text',
      includeTimestamps: false,
      includeMetadata: false,
    });
    const success = await copyToClipboard(content);
    if (success) {
      notify('Lemma', '对话已复制到剪贴板');
    }
  }, [claude.messages, notify]);

  const handleExportPdf = useCallback(async () => {
    const html = `<!DOCTYPE html><html><head><meta charset="utf-8"><style>
    body { font-family: serif; max-width: 800px; margin: 40px auto; padding: 20px; line-height: 1.6; }
    h3 { color: #333; margin-top: 1.5em; }
    pre { background: #f5f5f5; padding: 12px; overflow-x: auto; border-radius: 4px; }
  </style></head><body>
  <h1>Lemma 对话导出</h1>
  <p>导出时间: ${new Date().toLocaleString()}</p>
  ${claude.messages.map((message) => {
    const isUser = message.metadata?.role === 'user';
    return `<h3>${isUser ? '用户' : 'Claude'}</h3><div>${message.content.replace(/</g, '&lt;').replace(/>/g, '&gt;')}</div>`;
  }).join('\n')}
  </body></html>`;
    await window.lemmaAPI?.exportPdf(html);
  }, [claude.messages]);

  // 键盘快捷键
  useKeyboardShortcuts([
    { ...DEFAULT_SHORTCUTS.newSession, action: () => { void sessionLifecycle.createAndSelectSession(); } },
    { ...DEFAULT_SHORTCUTS.openDirectory, action: async () => { const dir = await window.lemmaAPI?.selectDirectory(); if (dir) dispatch({ type: 'SET_WORK_DIR', payload: dir }); } },
    { ...DEFAULT_SHORTCUTS.send, action: () => document.dispatchEvent(new CustomEvent(IPC_CHANNELS.SEND_MESSAGE)) },
    { ...DEFAULT_SHORTCUTS.stopGeneration, action: claude.cancelStream },
    { ...DEFAULT_SHORTCUTS.clearChat, action: handleClearWithPersist },
    { ...DEFAULT_SHORTCUTS.settings, action: () => dispatch({ type: 'SET_VIEW', payload: 'settings' }) },
    { ...DEFAULT_SHORTCUTS.exportChat, action: handleExport },
  ]);

  const isRecoverable = (claude.error?.includes('连接中断') ||
    claude.error?.includes('timeout') ||
    claude.error?.includes('connection')) ?? false;

  const handleOnboardingComplete = (settings: { workDir: string | null; preset: string | null }) => {
    if (settings.workDir) {
      dispatch({ type: 'SET_WORK_DIR', payload: settings.workDir });
    }
    if (settings.preset) {
      dispatch({ type: 'SET_PRESET', payload: settings.preset });
    }
    setApiKeyStatus('configured');
  };

  if (apiKeyStatus === 'checking') {
    return (
      <div className="flex items-center justify-center h-screen bg-bg-secondary">
        <div className="text-center space-y-3">
          <div className="animate-spin h-8 w-8 border-2 border-accent border-t-transparent rounded-full mx-auto" />
          <p className="text-sm text-text-muted">正在检查配置...</p>
        </div>
      </div>
    );
  }

  if (apiKeyStatus === 'missing') {
    return <OnboardingWizard onComplete={handleOnboardingComplete} />;
  }

  return (
    <div className="flex flex-col h-screen bg-bg-secondary text-text">
      {/* 顶部标题栏 + 导航 */}
      <TitleBar />

      {/* 主体：Sidebar + Content */}
      <div className="flex flex-1 min-h-0">
        <Sidebar sessions={sessionLifecycle.sessions} selectedPreset={state.selectedPreset} onNewSession={() => {
          void sessionLifecycle.createAndSelectSession();
        }} onSelectSession={(id) => {
          void sessionLifecycle.selectSession(id);
        }} onSelectPreset={(id) => {
          dispatch({ type: 'SET_PRESET', payload: id });
          if (id !== 'math-modeling') {
            dispatch({ type: 'CLEAR_PIPELINE' });
          }
        }} onDeleteSession={(id) => {
          void deleteSessionWithOutbox(id, messageQueue, sessionLifecycle.deleteSession);
        }} />

        <main className="flex-1 flex flex-col min-w-0">
          {sdkWarning && (
            <div className="px-4 py-2 bg-amber-900/20 text-amber-300 text-xs text-center">
              ⚠️ {sdkWarning}
            </div>
          )}

          <div className="flex-1 overflow-hidden view-enter">
            {state.currentView === 'chat' && state.pipelineStages && (
              <Suspense fallback={null}>
                <PipelineProgress
                  stages={state.pipelineStages}
                  currentStage={state.currentStage ?? undefined}
                />
              </Suspense>
            )}

            {state.currentView === 'chat' && (
              <ChatPanel
                messages={claude.messages}
                isStreaming={claude.isStreaming}
                onSend={handleSend}
                onCancel={claude.cancelStream}
                onClearMessages={handleClearWithPersist}
                onRetry={() => {
                  const lastUserMsg = [...claude.messages].reverse().find((message) => message.metadata?.role === 'user');
                  if (lastUserMsg) handleSend(lastUserMsg.content);
                }}
              />
            )}

            {state.currentView === 'settings' && (
              <Suspense fallback={<div className="p-8 text-center text-text-muted">加载中...</div>}>
                <SettingsPanel />
              </Suspense>
            )}

            {state.currentView === 'files' && (
              <FileBrowser workDir={state.workDir} />
            )}

            {state.currentView === 'cost' && (
              <CostTracker usage={claude.usageData} sessionId={sessionId ?? undefined} />
            )}

            {state.currentView === 'export' && (
              <div className="p-8 max-w-2xl mx-auto space-y-6 view-enter">
                <h2 className="text-h1 font-display">导出对话</h2>
                <p className="text-body text-text-muted">当前会话共 {claude.messages.length} 条消息</p>
                <div className="flex flex-wrap gap-3">
                  <button
                    onClick={handleExport}
                    disabled={claude.messages.length === 0}
                    className="px-5 py-2.5 rounded-editorial bg-accent text-white hover:bg-accent-hover disabled:opacity-50 text-ui font-medium press-scale"
                  >
                    导出为 Markdown
                  </button>
                  <button
                    onClick={handleCopyChat}
                    disabled={claude.messages.length === 0}
                    className="px-5 py-2.5 rounded-editorial border border-border-strong hover:bg-bg-tertiary disabled:opacity-50 text-ui font-medium press-scale"
                  >
                    复制到剪贴板
                  </button>
                  <button
                    onClick={handleExportPdf}
                    disabled={claude.messages.length === 0}
                    className="px-5 py-2.5 rounded-editorial border border-border-strong hover:bg-bg-tertiary disabled:opacity-50 text-ui font-medium press-scale"
                  >
                    导出为 PDF
                  </button>
                  <button
                    onClick={handleExportJson}
                    disabled={claude.messages.length === 0}
                    className="px-5 py-2.5 rounded-editorial border border-border-strong hover:bg-bg-tertiary disabled:opacity-50 text-ui font-medium press-scale"
                  >
                    导出为 JSON
                  </button>
                </div>
              </div>
            )}
          </div>

          {claude.error && (
            <div className="px-4 py-2 border-t border-border">
              <RetryBanner
                error={claude.error}
                isRecoverable={isRecoverable}
                onRetry={async (text, options) => {
                  claude.clearError();
                  await claude.sendMessage(text, options);
                }}
                onDismiss={claude.clearError}
                lastFailedText={lastFailedText}
                lastFailedOptions={lastFailedOptions}
              />
            </div>
          )}

          <StatusBar
            isStreaming={claude.isStreaming}
            workDir={state.workDir}
            sessionId={state.currentSessionId}
            isOnline={network.isOnline}
            tokenCounts={claude.tokenCounts}
          />
        </main>
      </div>
    </div>
  );
}
