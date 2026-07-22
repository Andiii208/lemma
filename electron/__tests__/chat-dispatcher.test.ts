import { describe, expect, it, vi } from 'vitest';
import { readStoredApiKey } from '../api-key-reader';
import { dispatchChat, requireRequestId, requireSessionId } from '../chat-dispatcher';

const message = 'Review this project';
const options = { workDir: 'C:\\workspace', model: 'claude-sonnet-4-5' };

function createKeyReader(overrides: Partial<Parameters<typeof readStoredApiKey>[0]> = {}) {
  return () => readStoredApiKey({
    isEncryptionAvailable: () => true,
    keyExists: () => true,
    readEncryptedKey: () => Buffer.from('encrypted'),
    decryptKey: () => 'sk-ant-secret',
    ...overrides,
  });
}

describe('dispatchChat', () => {
  it('requires a non-empty session id at the IPC boundary', () => {
    expect(() => requireSessionId('  ')).toThrow('Session ID is required');
    expect(requireSessionId(' session-1 ')).toBe('session-1');
  });

  it('accepts only bounded canonical request ids', () => {
    const requestId = '11111111-1111-4111-8111-111111111111';
    expect(requireRequestId(requestId)).toBe(requestId);
    expect(() => requireRequestId('request-1')).toThrow('Request ID is invalid');
    expect(() => requireRequestId('x'.repeat(10_000))).toThrow('Request ID is invalid');
  });

  it('does not call the bridge when the key is missing', async () => {
    const sendMessage = vi.fn();

    const result = await dispatchChat(message, options, {
      readApiKey: createKeyReader({ keyExists: () => false }),
      sendMessage,
    });

    expect(result).toEqual({ ok: false, error: 'API key 未配置，请先在设置中保存' });
    expect(sendMessage).not.toHaveBeenCalled();
  });

  it('does not call the bridge when the key cannot be decrypted', async () => {
    const sendMessage = vi.fn();

    const result = await dispatchChat(message, options, {
      readApiKey: createKeyReader({
        decryptKey: () => {
          throw new Error('corrupt');
        },
      }),
      sendMessage,
    });

    expect(result).toEqual({ ok: false, error: 'API key 读取或解密失败，请重新保存' });
    expect(sendMessage).not.toHaveBeenCalled();
  });

  it('does not call the bridge when the decrypted key is empty', async () => {
    const sendMessage = vi.fn();

    const result = await dispatchChat(message, options, {
      readApiKey: createKeyReader({ decryptKey: () => '  ' }),
      sendMessage,
    });

    expect(result).toEqual({ ok: false, error: 'API key 读取或解密失败，请重新保存' });
    expect(sendMessage).not.toHaveBeenCalled();
  });

  it('passes a valid key to the bridge', async () => {
    const sendMessage = vi.fn();

    const result = await dispatchChat(message, options, {
      readApiKey: createKeyReader(),
      sendMessage,
    });

    expect(result).toEqual({ ok: true });
    expect(sendMessage).toHaveBeenCalledWith(message, {
      ...options,
      apiKey: 'sk-ant-secret',
    });
  });
});
