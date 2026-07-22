import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import CostTracker from './CostTracker';

describe('CostTracker', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('displays data source disclaimer', () => {
    render(<CostTracker />);
    expect(screen.getByText(/数据来自 SDK 实际返回的 usage/)).toBeDefined();
  });

  it('accumulates usage data from SDK', () => {
    const { rerender } = render(
      <CostTracker usage={{ inputTokens: 100, outputTokens: 50, totalCostUsd: 0.05 }} />
    );
    expect(screen.getByText('100')).toBeDefined();
    expect(screen.getByText('50')).toBeDefined();
    expect(screen.getByText('$0.05')).toBeDefined();

    rerender(
      <CostTracker usage={{ inputTokens: 200, outputTokens: 100, totalCostUsd: 0.10 }} />
    );
    expect(screen.getByText('300')).toBeDefined();
    expect(screen.getByText('150')).toBeDefined();
    expect(screen.getByText('$0.15')).toBeDefined();
  });

  it('resets when sessionId changes', () => {
    const { rerender } = render(
      <CostTracker
        sessionId="session1"
        usage={{ inputTokens: 100, outputTokens: 50, totalCostUsd: 0.05 }}
      />
    );
    expect(screen.getByText('100')).toBeDefined();

    rerender(
      <CostTracker
        sessionId="session2"
        usage={{ inputTokens: 200, outputTokens: 100, totalCostUsd: 0.10 }}
      />
    );
    expect(screen.getByText('200')).toBeDefined();
    expect(screen.getByText('100')).toBeDefined();
    expect(screen.getByText('$0.10')).toBeDefined();
  });

  it('displays model name from usage', () => {
    render(<CostTracker usage={{ inputTokens: 10, outputTokens: 5, totalCostUsd: 0.01, model: 'claude-sonnet-4-20250514' }} />);
    expect(screen.getByText(/claude-sonnet-4-20250514/)).toBeDefined();
  });

  it('shows zero when no usage data', () => {
    render(<CostTracker />);
    const zeros = screen.getAllByText('0');
    expect(zeros.length).toBeGreaterThanOrEqual(2);
  });

  it('formats large token counts', () => {
    render(<CostTracker usage={{ inputTokens: 1500000, outputTokens: 500000, totalCostUsd: 10.5 }} />);
    expect(screen.getByText('1.5M')).toBeDefined();
    expect(screen.getByText('500.0K')).toBeDefined();
    expect(screen.getByText('$10.50')).toBeDefined();
  });

  it('displays unknown model when no model provided', () => {
    render(<CostTracker usage={{ inputTokens: 10, outputTokens: 5, totalCostUsd: 0.01 }} />);
    expect(screen.getByText(/模型: unknown/)).toBeDefined();
  });

  it('does not crash with unknown model', () => {
    expect(() => {
      render(<CostTracker usage={{ inputTokens: 10, outputTokens: 5, totalCostUsd: 0.01, model: 'some-unknown-model' }} />);
    }).not.toThrow();
    expect(screen.getByText(/some-unknown-model/)).toBeDefined();
  });

  it('uses real cost from SDK, not client-side estimation', () => {
    render(
      <CostTracker usage={{ inputTokens: 1000000, outputTokens: 1000000, totalCostUsd: 42.5 }} />
    );
    expect(screen.getByText('$42.50')).toBeDefined();
  });
});
