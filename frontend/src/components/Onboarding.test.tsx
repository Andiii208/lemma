import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { createElement } from 'react';
import App from '../App';
import { AppProvider } from '../context/AppContext';

beforeEach(() => {
  Object.defineProperty(window, 'lemmaAPI', {
    writable: true,
    value: {
      hasApiKey: vi.fn(),
      checkSdkVersion: vi.fn().mockResolvedValue({ sdkVersion: '1.0', supported: true, warning: null }),
      onClaudeMessage: vi.fn().mockReturnValue(() => {}),
      notify: vi.fn(),
      listSessions: vi.fn().mockResolvedValue([]),
      createSession: vi.fn().mockResolvedValue({ id: 's1', title: 't', workDir: '', createdAt: '', lastUsedAt: '' }),
      loadSession: vi.fn().mockResolvedValue(null),
      deleteSession: vi.fn().mockResolvedValue(true),
    },
  });
});

function renderApp() {
  return render(createElement(AppProvider, null, createElement(App)));
}

describe('Onboarding state machine', () => {
  it('shows loading while checking API key', () => {
    (window.lemmaAPI!.hasApiKey as ReturnType<typeof vi.fn>).mockReturnValue(new Promise(() => {})); // never resolves
    renderApp();
    expect(screen.getByText('正在检查配置...')).toBeDefined();
  });

  it('shows onboarding when API key is missing', async () => {
    (window.lemmaAPI!.hasApiKey as ReturnType<typeof vi.fn>).mockResolvedValue(false);
    renderApp();
    await waitFor(() => {
      expect(screen.getByText('欢迎使用 Lemma')).toBeDefined();
    });
  });

  it('skips onboarding when API key is configured', async () => {
    (window.lemmaAPI!.hasApiKey as ReturnType<typeof vi.fn>).mockResolvedValue(true);
    renderApp();
    await waitFor(() => {
      expect(screen.queryByText('正在检查配置...')).toBeNull();
      expect(screen.queryByText('欢迎使用 Lemma')).toBeNull();
    });
  });

  it('shows onboarding when API check fails', async () => {
    (window.lemmaAPI!.hasApiKey as ReturnType<typeof vi.fn>).mockRejectedValue(new Error('IPC error'));
    renderApp();
    await waitFor(() => {
      expect(screen.getByText('欢迎使用 Lemma')).toBeDefined();
    });
  });
});
