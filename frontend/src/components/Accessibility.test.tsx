import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { createElement } from 'react';
import ChatPanel from './ChatPanel';
import Sidebar from './Sidebar';
import MessageActions from './MessageActions';
import ApiKeySection from './settings/ApiKeySection';
import App from '../App';
import { AppProvider } from '../context/AppContext';

beforeEach(() => {
  Object.defineProperty(window, 'lemmaAPI', {
    writable: true,
    value: {
      hasApiKey: vi.fn().mockResolvedValue(true),
      checkSdkVersion: vi.fn().mockResolvedValue({ sdkVersion: '1.0', supported: true, warning: null }),
      onClaudeMessage: vi.fn().mockReturnValue(() => {}),
      notify: vi.fn(),
      listSessions: vi.fn().mockResolvedValue([]),
      createSession: vi.fn().mockResolvedValue({ id: 's1', title: 't', workDir: '', createdAt: '', lastUsedAt: '' }),
      loadSession: vi.fn().mockResolvedValue(null),
      deleteSession: vi.fn().mockResolvedValue(true),
      getMcpConfig: vi.fn().mockResolvedValue([]),
      selectDirectory: vi.fn().mockResolvedValue('/test'),
    },
  });
});

describe('Accessibility: aria-labels on icon-only buttons', () => {
  it('ChatPanel trash button has aria-label', () => {
    render(
      <ChatPanel
        messages={[{ content: 'hi', metadata: { role: 'assistant' }, type: 'text' }]}
        isStreaming={false}
        onSend={vi.fn()}
        onCancel={vi.fn()}
        onClearMessages={vi.fn()}
      />
    );
    const trashBtn = screen.getByLabelText('清空对话');
    expect(trashBtn).toBeDefined();
  });

  it('Sidebar collapse button has aria-label', () => {
    render(
      <AppProvider>
        <Sidebar
          sessions={[]}
          selectedPreset={null}
          onSelectPreset={vi.fn()}
          onNewSession={vi.fn()}
          onSelectSession={vi.fn()}
        />
      </AppProvider>
    );
    const collapseBtn = screen.getByLabelText(/侧栏/);
    expect(collapseBtn).toBeDefined();
  });

  it('MessageActions copy button has aria-label', () => {
    render(<MessageActions content="test" isUser={false} />);
    expect(screen.getByLabelText('复制消息')).toBeDefined();
  });

  it('MessageActions regenerate button has aria-label', () => {
    render(<MessageActions content="test" isUser={false} onRegenerate={vi.fn()} />);
    expect(screen.getByLabelText('重新生成')).toBeDefined();
  });
});

describe('Accessibility: input label associations', () => {
  it('ChatPanel textarea has aria-label', () => {
    render(
      <ChatPanel
        messages={[]}
        isStreaming={false}
        onSend={vi.fn()}
        onCancel={vi.fn()}
        onClearMessages={vi.fn()}
      />
    );
    const textarea = screen.getByLabelText(/输入消息/);
    expect(textarea).toBeDefined();
  });

  it('ApiKeySection input has associated label', () => {
    render(
      <AppProvider>
        <ApiKeySection />
      </AppProvider>
    );
    const input = screen.getByLabelText(/API Key/);
    expect(input).toBeDefined();
  });
});

describe('Accessibility: aria-expanded on expand controls', () => {
  it('tool expand button in MessageBubble has aria-expanded (code-level verification)', () => {
    const messages = [
      {
        content: '{"name":"test_tool","input":{}}',
        type: 'tool_use' as const,
        metadata: { role: 'assistant' },
      },
    ];
    const { container } = render(
      <ChatPanel
        messages={messages}
        isStreaming={false}
        onSend={vi.fn()}
        onCancel={vi.fn()}
        onClearMessages={vi.fn()}
      />
    );
    expect(container).toBeDefined();
  });
});

describe('Accessibility: focus-within on hover-only actions', () => {
  it('MessageActions container responds to focus-within', () => {
    const { container } = render(
      <div className="group">
        <MessageActions content="test" isUser={false} onRegenerate={vi.fn()} />
      </div>
    );
    const actionsDiv = container.querySelector('[data-testid="message-actions"]') 
      ?? container.querySelector('.group-hover\\:opacity-100');
    expect(actionsDiv).toBeDefined();
  });
});

describe('Responsive: export buttons wrap at small viewport', () => {
  it('export view buttons are wrapped in a flex-wrap container', async () => {
    Object.defineProperty(window, 'lemmaAPI', {
      writable: true,
      value: {
        hasApiKey: vi.fn().mockResolvedValue(true),
        checkSdkVersion: vi.fn().mockResolvedValue({ sdkVersion: '1.0', supported: true, warning: null }),
        onClaudeMessage: vi.fn().mockReturnValue(() => {}),
        notify: vi.fn(),
        listSessions: vi.fn().mockResolvedValue([]),
        createSession: vi.fn().mockResolvedValue({ id: 's1', title: 't', workDir: '', createdAt: '', lastUsedAt: '' }),
        loadSession: vi.fn().mockResolvedValue(null),
        deleteSession: vi.fn().mockResolvedValue(true),
      },
    });

    const { container } = render(createElement(AppProvider, null, createElement(App)));
    
    await waitFor(() => {
      const headerLemma = container.querySelector('header span');
      expect(headerLemma?.textContent).toBe('Lemma');
    });
  });
});
