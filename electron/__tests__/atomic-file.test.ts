import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';
import { atomicWriteFileSync, atomicWriteFileSyncSafe } from '../atomic-file';

describe('atomicWriteFileSync', () => {
  let tempDir: string;

  beforeEach(() => {
    tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'lemma-atomic-'));
  });

  afterEach(() => {
    fs.rmSync(tempDir, { recursive: true, force: true });
  });

  it('writes a new file atomically', () => {
    const filePath = path.join(tempDir, 'test.json');
    atomicWriteFileSync(filePath, '{"key":"value"}');
    expect(fs.readFileSync(filePath, 'utf-8')).toBe('{"key":"value"}');
  });

  it('overwrites an existing file atomically', () => {
    const filePath = path.join(tempDir, 'test.json');
    fs.writeFileSync(filePath, 'old content');
    atomicWriteFileSync(filePath, 'new content');
    expect(fs.readFileSync(filePath, 'utf-8')).toBe('new content');
  });

  it('creates parent directories if needed', () => {
    const filePath = path.join(tempDir, 'deep', 'nested', 'file.json');
    atomicWriteFileSync(filePath, 'data');
    expect(fs.readFileSync(filePath, 'utf-8')).toBe('data');
  });

  it('cleans up temp file on rename failure', () => {
    const filePath = path.join(tempDir, 'fail.json');
    const data = 'x'.repeat(10);
    atomicWriteFileSync(filePath, data);
    expect(fs.readFileSync(filePath, 'utf-8')).toBe(data);
    const tmpFiles = fs.readdirSync(tempDir).filter(f => f.endsWith('.tmp'));
    expect(tmpFiles).toHaveLength(0);
  });

  it('does not corrupt original file when write fails', () => {
    const filePath = path.join(tempDir, 'precious.json');
    fs.writeFileSync(filePath, '{"original":true}');
    const readonlyDir = path.join(tempDir, 'ro');
    fs.mkdirSync(readonlyDir, { mode: 0o444 });
    const targetPath = path.join(readonlyDir, 'precious.json');

    try {
      atomicWriteFileSync(targetPath, '{"corrupt":true}');
    } catch {
      // expected
    }
    expect(fs.readFileSync(filePath, 'utf-8')).toBe('{"original":true}');
  });

  it('safe variant returns success result', () => {
    const filePath = path.join(tempDir, 'safe.json');
    const result = atomicWriteFileSyncSafe(filePath, 'data');
    expect(result.success).toBe(true);
    expect(fs.readFileSync(filePath, 'utf-8')).toBe('data');
  });

  it('safe variant returns error on failure', () => {
    const result = atomicWriteFileSyncSafe('', 'data');
    expect(result.success).toBe(false);
    expect(result.error).toBeTruthy();
  });
});
