import { describe, it, expect, vi, beforeEach } from 'vitest';
import { createNotifyHelper } from './notifyHelper';

describe('notifyHelper', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('calls window.lemmaAPI.notify when notifications enabled', () => {
    const notify = vi.fn();
    const helper = createNotifyHelper(() => true, notify);
    helper('Test Title', 'Test Body');
    expect(notify).toHaveBeenCalledWith('Test Title', 'Test Body');
  });

  it('does not call notify when notifications disabled', () => {
    const notify = vi.fn();
    const helper = createNotifyHelper(() => false, notify);
    helper('Test Title', 'Test Body');
    expect(notify).not.toHaveBeenCalled();
  });

  it('does not throw when notify is undefined', () => {
    const helper = createNotifyHelper(() => true, undefined);
    expect(() => helper('Test', 'Body')).not.toThrow();
  });
});
