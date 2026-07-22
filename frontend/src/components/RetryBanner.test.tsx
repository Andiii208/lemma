import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, act } from '@testing-library/react';
import RetryBanner from './RetryBanner';

describe('RetryBanner', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    Object.defineProperty(navigator, 'onLine', { value: true, writable: true });
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('renders nothing when error is null', () => {
    const { container } = render(
      <RetryBanner error={null} isRecoverable onRetry={vi.fn()} onDismiss={vi.fn()} />
    );
    expect(container.firstChild).toBeNull();
  });

  it('displays error message', () => {
    render(
      <RetryBanner error="连接中断" isRecoverable onRetry={vi.fn()} onDismiss={vi.fn()} />
    );
    expect(screen.getByText('连接中断')).toBeDefined();
  });

  it('shows retry button when recoverable', () => {
    render(
      <RetryBanner error="timeout" isRecoverable onRetry={vi.fn()} onDismiss={vi.fn()} />
    );
    expect(screen.getByText('重试')).toBeDefined();
  });

  it('hides retry button when not recoverable', () => {
    render(
      <RetryBanner error="认证失败" isRecoverable={false} onRetry={vi.fn()} onDismiss={vi.fn()} />
    );
    expect(screen.queryByText('重试')).toBeNull();
  });

  it('calls onRetry with saved text and options', async () => {
    const onRetry = vi.fn().mockResolvedValue(undefined);
    render(
      <RetryBanner
        error="timeout"
        isRecoverable
        onRetry={onRetry}
        onDismiss={vi.fn()}
        lastFailedText="hello"
        lastFailedOptions={{ model: 'claude-sonnet-4-20250514' }}
      />
    );

    await act(async () => {
      fireEvent.click(screen.getByText('重试'));
      await vi.advanceTimersByTimeAsync(2000);
    });

    expect(onRetry).toHaveBeenCalledWith('hello', { model: 'claude-sonnet-4-20250514' });
  });

  it('shows retrying state during retry', async () => {
    const onRetry = vi.fn().mockImplementation(() => new Promise(() => {})); // never resolves
    render(
      <RetryBanner
        error="timeout"
        isRecoverable
        onRetry={onRetry}
        onDismiss={vi.fn()}
        lastFailedText="hello"
      />
    );

    await act(async () => {
      fireEvent.click(screen.getByText('重试'));
    });

    expect(screen.getByText('重试中...')).toBeDefined();
    expect(screen.getByText('重试中...').closest('button')).toHaveProperty('disabled', true);
  });

  it('transitions to failed state after max retries', async () => {
    const onRetry = vi.fn().mockResolvedValue(undefined);
    render(
      <RetryBanner
        error="timeout"
        isRecoverable
        onRetry={onRetry}
        onDismiss={vi.fn()}
        lastFailedText="hello"
      />
    );

    // Retry 5 times (RETRY_DELAYS has 5 entries)
    for (let i = 0; i < 5; i++) {
      await act(async () => {
        fireEvent.click(screen.getByText('重试'));
        await vi.advanceTimersByTimeAsync(30000);
      });
    }

    expect(screen.getByText('重试失败')).toBeDefined();
  });

  it('calls onDismiss', () => {
    const onDismiss = vi.fn();
    render(
      <RetryBanner error="timeout" isRecoverable onRetry={vi.fn()} onDismiss={onDismiss} />
    );
    fireEvent.click(screen.getByText('✕'));
    expect(onDismiss).toHaveBeenCalled();
  });
});
