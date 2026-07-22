import * as fs from 'fs';
import * as path from 'path';
import { randomUUID } from 'crypto';
import { atomicWriteFileSync } from './atomic-file';

const UUID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/;

export interface SessionInfo {
  id: string;
  title: string;
  workDir: string;
  createdAt: string;
  lastUsedAt: string;
  claudeSessionId?: string;
  totalInputTokens?: number;
  totalOutputTokens?: number;
  estimatedCost?: number;
  model?: string;
}

interface SessionFileOperations {
  atomicWrite(filePath: string, data: string): void;
}

const defaultFileOperations: SessionFileOperations = {
  atomicWrite: atomicWriteFileSync,
};

function isSessionInfo(value: unknown): value is SessionInfo {
  if (typeof value !== 'object' || value === null) return false;
  const session = value as Record<string, unknown>;
  return typeof session.id === 'string' && UUID_PATTERN.test(session.id)
    && typeof session.title === 'string' && typeof session.workDir === 'string'
    && typeof session.createdAt === 'string' && typeof session.lastUsedAt === 'string';
}

function sessionIdFromFileName(fileName: string): string | null {
  if (!fileName.endsWith('.json')) return null;
  const sessionId = fileName.slice(0, -'.json'.length);
  return UUID_PATTERN.test(sessionId) ? sessionId : null;
}

export class SessionManager {
  private readonly sessionsDir: string;
  private lastTimestamp = 0;

  constructor(
    userDataDir: string,
    private readonly fileOperations: SessionFileOperations = defaultFileOperations,
  ) {
    this.sessionsDir = path.resolve(userDataDir, 'sessions');
    fs.mkdirSync(this.sessionsDir, { recursive: true });
  }

  createSession(workDir: string, title: string): SessionInfo {
    const timestamp = this.nextTimestamp();
    const info: SessionInfo = {
      id: randomUUID(), title, workDir, createdAt: timestamp, lastUsedAt: timestamp,
    };
    this.saveSession(info);
    return info;
  }

  saveSession(info: SessionInfo): void {
    const filePath = this.sessionPath(info.id);
    info.lastUsedAt = this.nextTimestamp();
    this.fileOperations.atomicWrite(filePath, JSON.stringify(info, null, 2));
  }

  listSessions(): SessionInfo[] {
    return fs.readdirSync(this.sessionsDir)
      .map((fileName) => ({ fileName, sessionId: sessionIdFromFileName(fileName) }))
      .filter((entry): entry is { fileName: string; sessionId: string } => entry.sessionId !== null)
      .map(({ fileName, sessionId }) => this.readSession(
        path.join(this.sessionsDir, fileName), sessionId,
      ))
      .filter((session): session is SessionInfo => session !== null)
      .sort((left, right) => right.lastUsedAt.localeCompare(left.lastUsedAt));
  }

  loadSession(id: string): SessionInfo | null {
    return this.readSession(this.sessionPath(id), id);
  }

  updateClaudeSessionId(id: string, claudeSessionId: string): void {
    const session = this.loadSession(id);
    if (!session) return;
    session.claudeSessionId = claudeSessionId;
    this.saveSession(session);
  }

  updateSessionCost(
    id: string,
    cost: { input: number; output: number; cost: number; model: string },
  ): void {
    const session = this.loadSession(id);
    if (!session) return;
    Object.assign(session, {
      totalInputTokens: cost.input, totalOutputTokens: cost.output,
      estimatedCost: cost.cost, model: cost.model,
    });
    this.saveSession(session);
  }

  deleteSession(id: string): boolean {
    const filePath = this.sessionPath(id);
    if (!fs.existsSync(filePath)) return false;
    fs.unlinkSync(filePath);
    return true;
  }

  private sessionPath(id: string): string {
    if (!UUID_PATTERN.test(id)) throw new Error('Invalid session ID');
    const resolvedPath = path.resolve(this.sessionsDir, `${id}.json`);
    const relativePath = path.relative(this.sessionsDir, resolvedPath);
    if (relativePath.startsWith('..') || path.isAbsolute(relativePath)) {
      throw new Error('Invalid session path');
    }
    return resolvedPath;
  }

  private readSession(filePath: string, expectedId: string): SessionInfo | null {
    if (!fs.existsSync(filePath)) return null;
    try {
      const value: unknown = JSON.parse(fs.readFileSync(filePath, 'utf-8'));
      return isSessionInfo(value) && value.id === expectedId ? value : null;
    } catch {
      return null;
    }
  }

  private nextTimestamp(): string {
    this.lastTimestamp = Math.max(Date.now(), this.lastTimestamp + 1);
    return new Date(this.lastTimestamp).toISOString();
  }
}
