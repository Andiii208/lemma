import * as fs from 'fs';
import * as path from 'path';

export const MAX_FILE_SIZE_BYTES = 1 * 1024 * 1024;
export const MAX_DIR_ENTRIES = 10000;

interface FileReadResult {
  content: string | null;
  error: string | null;
}

interface DirEntry {
  name: string;
  isDirectory: boolean;
  path: string;
}

export function readFileWithLimits(filePath: string): FileReadResult {
  try {
    const stat = fs.statSync(filePath);
    if (stat.size > MAX_FILE_SIZE_BYTES) {
      return { content: null, error: `File size ${stat.size} exceeds limit of ${MAX_FILE_SIZE_BYTES} bytes` };
    }
    return { content: fs.readFileSync(filePath, 'utf-8'), error: null };
  } catch (error: unknown) {
    const msg = error instanceof Error ? error.message : 'Read failed';
    return { content: null, error: msg };
  }
}

export function listDirectoryWithLimits(dirPath: string): DirEntry[] {
  try {
    const entries = fs.readdirSync(dirPath, { withFileTypes: true });
    const limited = entries.slice(0, MAX_DIR_ENTRIES);
    return limited.map((entry) => ({
      name: entry.name,
      isDirectory: entry.isDirectory(),
      path: path.join(dirPath, entry.name),
    }));
  } catch {
    return [];
  }
}

export function debounce<T extends (...args: unknown[]) => void>(
  fn: T,
  delayMs: number,
): (...args: Parameters<T>) => void {
  let timer: ReturnType<typeof setTimeout> | null = null;
  return (...args: Parameters<T>) => {
    if (timer !== null) clearTimeout(timer);
    timer = setTimeout(() => {
      timer = null;
      fn(...args);
    }, delayMs);
  };
}
