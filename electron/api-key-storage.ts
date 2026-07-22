export interface ApiKeyStorageDependencies {
  isEncryptionAvailable: () => boolean;
  encryptKey: (apiKey: string) => Buffer;
  writeEncryptedKey: (encryptedKey: Buffer) => void;
}

export type StoreApiKeyResult =
  | { success: true; encrypted: true }
  | { success: false; reason: string };

export function storeApiKey(
  apiKey: string,
  dependencies: ApiKeyStorageDependencies,
): StoreApiKeyResult {
  const trimmedApiKey = apiKey.trim();
  if (!trimmedApiKey) return { success: false, reason: 'API key is required' };
  if (!dependencies.isEncryptionAvailable()) {
    return { success: false, reason: 'Encryption not available' };
  }

  try {
    const encryptedKey = dependencies.encryptKey(trimmedApiKey);
    dependencies.writeEncryptedKey(encryptedKey);
    return { success: true, encrypted: true };
  } catch (error: unknown) {
    const reason = error instanceof Error ? error.message : 'Failed to store API key';
    return { success: false, reason };
  }
}
