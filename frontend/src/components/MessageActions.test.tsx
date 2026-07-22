import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import MessageActions from './MessageActions';

describe('MessageActions', () => {
  it('renders copy button', () => {
    render(<MessageActions content="test content" isUser={false} />);
    expect(screen.getByLabelText('复制消息')).toBeTruthy();
  });

  it('renders regenerate button for assistant messages', () => {
    const onRegenerate = vi.fn();
    render(<MessageActions content="test" isUser={false} onRegenerate={onRegenerate} />);
    expect(screen.getByLabelText('重新生成')).toBeTruthy();
  });

  it('does not render regenerate for user messages', () => {
    render(<MessageActions content="test" isUser={true} />);
    expect(screen.queryByLabelText('重新生成')).toBeNull();
  });
});
