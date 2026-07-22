import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';
import {
  MAX_FILE_SIZE_BYTES,
  MAX_DIR_ENTRIES,
  readFileWithLimits,
  listDirectoryWithLimits,
  debounce,
} from '../main-limits';

describe('readFileWithLimits', () => {
  let tempDir: string;

  beforeEach(() => {
    tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'lemma-limits-'));
  });

  afterEach(() => {
    fs.rmSync(tempDir, { recursive: true, force: true });
  });

  it('reads a normal file', () => {
    const filePath = path.join(tempDir, 'small.txt');
    fs.writeFileSync(filePath, 'hello world');
    const result = readFileWithLimits(filePath);
    expect(result.content).toBe('hello world');
    expect(result.error).toBeNull();
  });

  it('rejects files exceeding size limit', () => {
    const filePath = path.join(tempDir, 'huge.bin');
    const bigBuffer = Buffer.alloc(MAX_FILE_SIZE_BYTES + 1, 0);
    fs.writeFileSync(filePath, bigBuffer);
    const result = readFileWithLimits(filePath);
    expect(result.content).toBeNull();
    expect(result.error).toContain('exceeds');
  });

  it('reads file exactly at size limit', () => {
    const filePath = path.join(tempDir, 'exact.bin');
    const exactBuffer = Buffer.alloc(MAX_FILE_SIZE_BYTES, 0);
    fs.writeFileSync(filePath, exactBuffer);
    const result = readFileWithLimits(filePath);
    expect(result.error).toBeNull();
  });

  it('returns error for non-existent file', () => {
    const result = readFileWithLimits(path.join(tempDir, 'missing.txt'));
    expect(result.content).toBeNull();
    expect(result.error).toBeTruthy();
  });
});

describe('listDirectoryWithLimits', () => {
  let tempDir: string;

  beforeEach(() => {
    tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'lemma-limits-'));
  });

  afterEach(() => {
    fs.rmSync(tempDir, { recursive: true, force: true });
  });

  it('lists a normal directory', () => {
    fs.writeFileSync(path.join(tempDir, 'a.txt'), '');
    fs.writeFileSync(path.join(tempDir, 'b.txt'), '');
    fs.mkdirSync(path.join(tempDir, 'subdir'));
    const entries = listDirectoryWithLimits(tempDir);
    expect(entries).toHaveLength(3);
    expect(entries.find(e => e.name === 'subdir')?.isDirectory).toBe(true);
  });

  it('limits entries to MAX_DIR_ENTRIES', () => {
    for (let i = 0; i < MAX_DIR_ENTRIES + 10; i++) {
      fs.writeFileSync(path.join(tempDir, `file-${i}.txt`), '');
    }
    const entries = listDirectoryWithLimits(tempDir);
    expect(entries).toHaveLength(MAX_DIR_ENTRIES);
  });

  it('returns empty for non-existent dir', () => {
    const entries = listDirectoryWithLimits(path.join(tempDir, 'missing'));
    expect(entries).toEqual([]);
  });
});

describe('debounce', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('delays execution', () => {
    const fn = vi.fn();
    const debounced = debounce(fn, 100);
    debounced();
    expect(fn).not.toHaveBeenCalled();
    vi.advanceTimersByTime(100);
    expect(fn).toHaveBeenCalledOnce();
  });

  it('resets timer on repeated calls', () => {
    const fn = vi.fn();
    const debounced = debounce(fn, 100);
    debounced();
    vi.advanceTimersByTime(50);
    debounced();
    vi.advanceTimersByTime(50);
    expect(fn).not.toHaveBeenCalled();
    vi.advanceTimersByTime(50);
    expect(fn).toHaveBeenCalledOnce();
  });

  it('passes arguments to the debounced function', () => {
    const fn = vi.fn();
    const debounced = debounce(fn, 100);
    debounced('a', 'b');
    vi.advanceTimersByTime(100);
    expect(fn).toHaveBeenCalledWith('a', 'b');
  });
});
