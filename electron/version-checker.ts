interface VersionInfo {
  sdkVersion: string;
  supported: boolean;
  warning: string | null;
}

const SUPPORTED_RANGE = { min: '0.2.0', max: '1.0.0' };

export async function checkSdkVersion(): Promise<VersionInfo> {
  try {
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    const sdkPackageJson = require('@anthropic-ai/claude-agent-sdk/package.json');
    const sdkVersion = (sdkPackageJson as Record<string, unknown>).version as string ?? 'unknown';
    const supported = isVersionInRange(sdkVersion, SUPPORTED_RANGE.min, SUPPORTED_RANGE.max);

    return {
      sdkVersion,
      supported,
      warning: supported
        ? null
        : `Agent SDK 版本 ${sdkVersion} 不在支持范围 >=${SUPPORTED_RANGE.min} <${SUPPORTED_RANGE.max}，请更新 Lemma`,
    };
  } catch {
    return {
      sdkVersion: 'not-installed',
      supported: false,
      warning: 'Claude Agent SDK 未安装',
    };
  }
}

function isVersionInRange(version: string, minVersion: string, maxVersion: string): boolean {
  if (version === 'unknown' || version === 'not-installed') return false;

  const parseVersion = (versionStr: string) =>
    versionStr.replace(/^v/, '').split('.').map(Number);

  const [major, minor, patch] = parseVersion(version);
  const [minMajor, minMinor, minPatch] = parseVersion(minVersion);
  const [maxMajor] = parseVersion(maxVersion);

  if (major < minMajor) return false;
  if (major >= maxMajor) return false;
  if (major === minMajor && minor < minMinor) return false;
  if (major === minMajor && minor === minMinor && patch < minPatch) return false;

  return true;
}
