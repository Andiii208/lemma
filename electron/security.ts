import type { BrowserWindowConstructorOptions } from 'electron';

const DEVELOPMENT_ORIGIN = 'http://localhost:5173';

export const PDF_WINDOW_OPTIONS: BrowserWindowConstructorOptions = {
  show: false,
  webPreferences: {
    javascript: false,
    contextIsolation: true,
    nodeIntegration: false,
    sandbox: true,
  },
};

function parseCredentialFreeUrl(value: string): URL | null {
  try {
    const parsedUrl = new URL(value);
    return parsedUrl.username || parsedUrl.password ? null : parsedUrl;
  } catch {
    return null;
  }
}

export function isTrustedAppUrl(url: string, expectedPort?: number): boolean {
  const parsedUrl = parseCredentialFreeUrl(url);
  if (!parsedUrl || parsedUrl.protocol !== 'http:') return false;

  const expectedOrigin = expectedPort === undefined
    ? DEVELOPMENT_ORIGIN
    : `http://127.0.0.1:${expectedPort}`;
  return parsedUrl.origin === expectedOrigin;
}

export function isSafeExternalUrl(url: string): boolean {
  const parsedUrl = parseCredentialFreeUrl(url);
  return parsedUrl?.protocol === 'http:' || parsedUrl?.protocol === 'https:';
}

export function hasDecryptableApiKey(readDecryptedKey: () => string): boolean {
  try {
    return readDecryptedKey().trim().length > 0;
  } catch {
    return false;
  }
}

export function assertTrustedSender(url: string, expectedPort?: number): void {
  if (!isTrustedAppUrl(url, expectedPort)) {
    throw new Error('Untrusted IPC sender');
  }
}
