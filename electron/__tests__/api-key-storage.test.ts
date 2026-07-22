import { describe, expect, it, vi } from 'vitest';
import { storeApiKey } from '../api-key-storage';

function createDependencies() {
  return {
    isEncryptionAvailable: () => true,
    encryptKey: vi.fn((apiKey: string) => Buffer.from(apiKey)),
    writeEncryptedKey: vi.fn(),
  };
}

describe('storeApiKey', () => {
  it('rejects a whitespace-only key without encrypting or writing', () => {
    const dependencies = createDependencies();

    expect(storeApiKey('   ', dependencies)).toEqual({
      success: false,
      reason: 'API key is required',
    });
    expect(dependencies.encryptKey).not.toHaveBeenCalled();
    expect(dependencies.writeEncryptedKey).not.toHaveBeenCalled();
  });

  it('trims only surrounding whitespace before encrypting and writing', () => {
    const dependencies = createDependencies();

    expect(storeApiKey('  sk-ant-secret value  ', dependencies)).toEqual({
      success: true,
      encrypted: true,
    });
    expect(dependencies.encryptKey).toHaveBeenCalledWith('sk-ant-secret value');
    expect(dependencies.writeEncryptedKey).toHaveBeenCalledWith(
      Buffer.from('sk-ant-secret value'),
    );
  });
});
