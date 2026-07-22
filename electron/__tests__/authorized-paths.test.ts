import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';
import { AuthorizedPaths } from '../authorized-paths';

describe('AuthorizedPaths', () => {
  let tempDir: string;
  let authPaths: AuthorizedPaths;

  beforeEach(() => {
    tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'lemma-auth-'));
    authPaths = new AuthorizedPaths();
  });

  afterEach(() => {
    fs.rmSync(tempDir, { recursive: true, force: true });
  });

  it('allows access to an authorized root', () => {
    authPaths.authorize(tempDir);
    const subFile = path.join(tempDir, 'file.txt');
    expect(authPaths.isPathAllowed(subFile)).toBe(true);
  });

  it('rejects access to unauthorized paths', () => {
    const outside = path.join(os.tmpdir(), 'outside');
    expect(authPaths.isPathAllowed(outside)).toBe(false);
  });

  it('rejects symlink that escapes authorized root', () => {
    const outsideDir = fs.mkdtempSync(path.join(os.tmpdir(), 'lemma-outside-'));
    const symlinkPath = path.join(tempDir, 'escape-link');
    try {
      fs.symlinkSync(outsideDir, symlinkPath);
      authPaths.authorize(tempDir);
      const target = path.join(symlinkPath, 'secret.txt');
      expect(authPaths.isPathAllowed(target)).toBe(false);
    } finally {
      fs.rmSync(outsideDir, { recursive: true, force: true });
    }
  });

  it('allows symlink that stays within authorized root', () => {
    const subDir = path.join(tempDir, 'sub');
    fs.mkdirSync(subDir);
    const symlinkPath = path.join(tempDir, 'internal-link');
    fs.symlinkSync(subDir, symlinkPath);
    authPaths.authorize(tempDir);
    const target = path.join(symlinkPath, 'file.txt');
    expect(authPaths.isPathAllowed(target)).toBe(true);
  });

  it('handles multiple authorized roots', () => {
    const dir2 = fs.mkdtempSync(path.join(os.tmpdir(), 'lemma-auth2-'));
    try {
      authPaths.authorize(tempDir);
      authPaths.authorize(dir2);
      expect(authPaths.isPathAllowed(path.join(tempDir, 'a.txt'))).toBe(true);
      expect(authPaths.isPathAllowed(path.join(dir2, 'b.txt'))).toBe(true);
      expect(authPaths.isPathAllowed(path.join(os.tmpdir(), 'c.txt'))).toBe(false);
    } finally {
      fs.rmSync(dir2, { recursive: true, force: true });
    }
  });

  it('can deauthorize a root', () => {
    authPaths.authorize(tempDir);
    expect(authPaths.isPathAllowed(path.join(tempDir, 'a.txt'))).toBe(true);
    authPaths.deauthorize(tempDir);
    expect(authPaths.isPathAllowed(path.join(tempDir, 'a.txt'))).toBe(false);
  });

  it('lists authorized roots', () => {
    authPaths.authorize(tempDir);
    const roots = authPaths.getAuthorizedRoots();
    expect(roots).toContain(path.resolve(tempDir));
  });

  it('authorizing the same root twice is idempotent', () => {
    authPaths.authorize(tempDir);
    authPaths.authorize(tempDir);
    expect(authPaths.getAuthorizedRoots()).toHaveLength(1);
  });
});
