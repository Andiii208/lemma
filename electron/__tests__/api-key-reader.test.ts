import { describe, expect, it, vi } from 'vitest';
import { readStoredApiKey } from '../api-key-reader';

function createDependencies(overrides: Partial<Parameters<typeof readStoredApiKey>[0]> = {}) {
  return {
    isEncryptionAvailable: () => true,
    keyExists: () => true,
    readEncryptedKey: () => Buffer.from('encrypted'),
    decryptKey: () => 'sk-ant-secret',
    ...overrides,
  };
}

describe('readStoredApiKey', () => {
  it('returns the trimmed decrypted key for main-process use', () => {
    expect(readStoredApiKey(createDependencies({
      decryptKey: () => '  sk-ant-secret value  ',
    }))).toEqual({
      ok: true,
      apiKey: 'sk-ant-secret value',
    });
  });

  it('returns a clear error without reading when no key is stored', () => {
    const readEncryptedKey = vi.fn(() => Buffer.from('encrypted'));

    expect(readStoredApiKey(createDependencies({
      keyExists: () => false,
      readEncryptedKey,
    }))).toEqual({
      ok: false,
      error: 'API key 未配置，请先在设置中保存',
    });
    expect(readEncryptedKey).not.toHaveBeenCalled();
  });

  it('returns a clear error when encryption is unavailable or decryption fails', () => {
    expect(readStoredApiKey(createDependencies({
      isEncryptionAvailable: () => false,
    }))).toEqual({
      ok: false,
      error: '系统安全存储不可用，无法读取 API key',
    });

    expect(readStoredApiKey(createDependencies({
      decryptKey: () => {
        throw new Error('corrupt');
      },
    }))).toEqual({
      ok: false,
      error: 'API key 读取或解密失败，请重新保存',
    });
  });

  it('rejects an empty decrypted key', () => {
    expect(readStoredApiKey(createDependencies({ decryptKey: () => '  ' }))).toEqual({
      ok: false,
      error: 'API key 读取或解密失败，请重新保存',
    });
  });
});
