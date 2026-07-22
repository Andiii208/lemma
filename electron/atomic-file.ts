import * as fs from 'fs';
import * as path from 'path';
import { randomUUID } from 'crypto';

export interface AtomicWriteResult {
  success: boolean;
  error?: string;
}

export function atomicWriteFileSync(filePath: string, data: string): void {
  const dir = path.dirname(filePath);
  fs.mkdirSync(dir, { recursive: true });
  const tmpPath = path.join(dir, `.${randomUUID()}.tmp`);
  try {
    const fd = fs.openSync(tmpPath, 'w');
    try {
      fs.writeSync(fd, data, null, 'utf-8');
      fs.fsyncSync(fd);
    } finally {
      fs.closeSync(fd);
    }
    fs.renameSync(tmpPath, filePath);
  } catch (error: unknown) {
    try {
      if (fs.existsSync(tmpPath)) fs.unlinkSync(tmpPath);
    } catch {
      // cleanup failure is non-fatal
    }
    throw error;
  }
}

export function atomicWriteFileSyncSafe(filePath: string, data: string): AtomicWriteResult {
  try {
    atomicWriteFileSync(filePath, data);
    return { success: true };
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : 'Unknown write error';
    return { success: false, error: message };
  }
}
