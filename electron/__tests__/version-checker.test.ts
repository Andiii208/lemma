import { describe, it, expect } from 'vitest';
import { checkSdkVersion } from '../version-checker';

describe('checkSdkVersion', () => {
  it('returns a version info object', async () => {
    const result = await checkSdkVersion();
    expect(result).toHaveProperty('sdkVersion');
    expect(result).toHaveProperty('supported');
    expect(result).toHaveProperty('warning');
  });

  it('returns a string version', async () => {
    const result = await checkSdkVersion();
    expect(typeof result.sdkVersion).toBe('string');
  });

  it('returns boolean supported', async () => {
    const result = await checkSdkVersion();
    expect(typeof result.supported).toBe('boolean');
  });

  it('returns null warning when supported', async () => {
    const result = await checkSdkVersion();
    if (result.supported) {
      expect(result.warning).toBeNull();
    } else {
      expect(typeof result.warning).toBe('string');
    }
  });
});
