import { describe, expect, it } from 'vitest';
import {
  PDF_WINDOW_OPTIONS,
  assertTrustedSender,
  hasDecryptableApiKey,
  isSafeExternalUrl,
  isTrustedAppUrl,
} from '../security';

describe('isTrustedAppUrl', () => {
  it('accepts only the development origin when no production port is provided', () => {
    expect(isTrustedAppUrl('http://localhost:5173')).toBe(true);
    expect(isTrustedAppUrl('http://localhost:5173/chat?session=1#latest')).toBe(true);
    expect(isTrustedAppUrl('http://127.0.0.1:5173')).toBe(false);
    expect(isTrustedAppUrl('http://localhost:5174')).toBe(false);
  });

  it('accepts only the runtime production origin', () => {
    expect(isTrustedAppUrl('http://127.0.0.1:43127', 43127)).toBe(true);
    expect(isTrustedAppUrl('http://127.0.0.1:43127/settings', 43127)).toBe(true);
    expect(isTrustedAppUrl('http://localhost:43127', 43127)).toBe(false);
    expect(isTrustedAppUrl('http://127.0.0.1:43128', 43127)).toBe(false);
  });

  it('rejects explicit default ports that do not match the trusted origin', () => {
    expect(isTrustedAppUrl('http://localhost:80')).toBe(false);
    expect(isTrustedAppUrl('https://localhost:443')).toBe(false);
    expect(isTrustedAppUrl('http://127.0.0.1:80', 43127)).toBe(false);
  });

  it('rejects credentials, unsupported protocols, and malformed URLs', () => {
    expect(isTrustedAppUrl('http://user:pass@localhost:5173')).toBe(false);
    expect(isTrustedAppUrl('http://user@localhost:5173')).toBe(false);
    expect(isTrustedAppUrl('http://:pass@localhost:5173')).toBe(false);
    expect(isTrustedAppUrl('https://localhost:5173')).toBe(false);
    expect(isTrustedAppUrl('file:///index.html')).toBe(false);
    expect(isTrustedAppUrl('not a url')).toBe(false);
  });
});

describe('isSafeExternalUrl', () => {
  it('allows credential-free HTTP and HTTPS URLs', () => {
    expect(isSafeExternalUrl('https://example.com/docs')).toBe(true);
    expect(isSafeExternalUrl('http://example.com')).toBe(true);
  });

  it('rejects credentials and non-web protocols', () => {
    expect(isSafeExternalUrl('https://user:pass@example.com')).toBe(false);
    expect(isSafeExternalUrl('javascript:alert(1)')).toBe(false);
    expect(isSafeExternalUrl('file:///etc/passwd')).toBe(false);
    expect(isSafeExternalUrl('mailto:user@example.com')).toBe(false);
    expect(isSafeExternalUrl('invalid')).toBe(false);
  });
});

describe('assertTrustedSender', () => {
  it('returns for a trusted sender', () => {
    expect(() => assertTrustedSender('http://localhost:5173/chat')).not.toThrow();
  });

  it('throws for an untrusted sender', () => {
    expect(() => assertTrustedSender('https://attacker.example')).toThrow('Untrusted IPC sender');
    expect(() => assertTrustedSender('')).toThrow('Untrusted IPC sender');
  });

  it('uses the runtime production port for sender validation', () => {
    expect(() => assertTrustedSender('http://127.0.0.1:43127/chat', 43127)).not.toThrow();
    expect(() => assertTrustedSender('http://127.0.0.1:43128/chat', 43127)).toThrow('Untrusted IPC sender');
  });
});

describe('PDF_WINDOW_OPTIONS', () => {
  it('disables script execution and renderer privileges', () => {
    expect(PDF_WINDOW_OPTIONS).toEqual({
      show: false,
      webPreferences: {
        javascript: false,
        contextIsolation: true,
        nodeIntegration: false,
        sandbox: true,
      },
    });
  });
});

describe('hasDecryptableApiKey', () => {
  it('returns true only for a non-empty decrypted key', () => {
    expect(hasDecryptableApiKey(() => 'sk-ant-secret')).toBe(true);
    expect(hasDecryptableApiKey(() => '')).toBe(false);
    expect(hasDecryptableApiKey(() => '   ')).toBe(false);
  });

  it('returns false when reading or decrypting fails', () => {
    expect(hasDecryptableApiKey(() => {
      throw new Error('corrupt key');
    })).toBe(false);
  });
});
