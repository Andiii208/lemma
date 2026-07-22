export interface ApiKeyReaderDependencies {
  isEncryptionAvailable: () => boolean;
  keyExists: () => boolean;
  readEncryptedKey: () => Buffer;
  decryptKey: (encryptedKey: Buffer) => string;
}

export type StoredApiKeyResult =
  | { ok: true; apiKey: string }
  | { ok: false; error: string };

export function readStoredApiKey(dependencies: ApiKeyReaderDependencies): StoredApiKeyResult {
  if (!dependencies.isEncryptionAvailable()) {
    return { ok: false, error: '系统安全存储不可用，无法读取 API key' };
  }
  if (!dependencies.keyExists()) {
    return { ok: false, error: 'API key 未配置，请先在设置中保存' };
  }

  try {
    const apiKey = dependencies.decryptKey(dependencies.readEncryptedKey()).trim();
    return apiKey
      ? { ok: true, apiKey }
      : { ok: false, error: 'API key 读取或解密失败，请重新保存' };
  } catch {
    return { ok: false, error: 'API key 读取或解密失败，请重新保存' };
  }
}
