import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';
import { SessionManager } from '../session-manager';

describe('SessionManager', () => {
  let tempDir: string;
  let manager: SessionManager;

  beforeEach(() => {
    tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'lemma-test-'));
    manager = new SessionManager(tempDir);
  });

  afterEach(() => {
    vi.restoreAllMocks();
    fs.rmSync(tempDir, { recursive: true, force: true });
  });

  it('creates a session with correct fields', () => {
    const session = manager.createSession('/work', 'Test Session');
    expect(session.id).toMatch(/^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/);
    expect(session.title).toBe('Test Session');
    expect(session.workDir).toBe('/work');
    expect(session.createdAt).toBeTruthy();
    expect(session.lastUsedAt).toBeTruthy();
  });

  it('creates distinct UUID sessions in the same millisecond', () => {
    vi.spyOn(Date, 'now').mockReturnValue(123456789);

    const first = manager.createSession('/work', 'First');
    const second = manager.createSession('/work', 'Second');

    expect(first.id).not.toBe(second.id);
    expect(manager.listSessions()).toHaveLength(2);
  });

  it('lists sessions sorted by lastUsedAt', () => {
    manager.createSession('/work', 'First');
    manager.createSession('/work', 'Second');
    const sessions = manager.listSessions();
    expect(sessions).toHaveLength(2);
    expect(sessions[0].title).toBe('Second');
  });

  it('loads a saved session', () => {
    const created = manager.createSession('/work', 'Load Test');
    const loaded = manager.loadSession(created.id);
    expect(loaded).not.toBeNull();
    expect(loaded!.title).toBe('Load Test');
  });

  it('returns null for non-existent session', () => {
    const loaded = manager.loadSession('11111111-1111-4111-8111-111111111111');
    expect(loaded).toBeNull();
  });

  it('deletes a session', () => {
    const session = manager.createSession('/work', 'Delete Me');
    expect(manager.deleteSession(session.id)).toBe(true);
    expect(manager.loadSession(session.id)).toBeNull();
  });

  it('returns false when deleting non-existent session', () => {
    expect(manager.deleteSession('11111111-1111-4111-8111-111111111111')).toBe(false);
  });

  it.each(['../outside', '..\\outside', 'C:\\outside', '/outside', 'not-a-uuid'])(
    'rejects non-canonical session id %s',
    (invalidId) => {
      expect(() => manager.loadSession(invalidId)).toThrow('Invalid session ID');
      expect(() => manager.deleteSession(invalidId)).toThrow('Invalid session ID');
    },
  );

  it('handles corrupted JSON gracefully', () => {
    const sessionsDir = path.join(tempDir, 'sessions');
    fs.writeFileSync(path.join(sessionsDir, 'corrupted.json'), 'not valid json{');
    manager.createSession('/work', 'Valid');

    const sessions = manager.listSessions();
    expect(sessions).toHaveLength(1);
    expect(sessions[0].title).toBe('Valid');
  });

  it('ignores JSON files without a canonical UUID filename', () => {
    const valid = manager.createSession('/work', 'Valid');
    const sessionsDir = path.join(tempDir, 'sessions');
    fs.copyFileSync(
      path.join(sessionsDir, `${valid.id}.json`),
      path.join(sessionsDir, 'copied-session.json'),
    );

    expect(manager.listSessions()).toEqual([expect.objectContaining({ id: valid.id })]);
  });

  it('ignores session content whose id differs from its UUID filename', () => {
    const valid = manager.createSession('/work', 'Valid');
    const mismatchedId = '11111111-1111-4111-8111-111111111111';
    const sessionsDir = path.join(tempDir, 'sessions');
    fs.writeFileSync(
      path.join(sessionsDir, `${mismatchedId}.json`),
      JSON.stringify(valid),
    );

    expect(manager.listSessions()).toEqual([expect.objectContaining({ id: valid.id })]);
  });

  it('returns null when loading corrupted session JSON', () => {
    const sessionId = '11111111-1111-4111-8111-111111111111';
    fs.writeFileSync(path.join(tempDir, 'sessions', `${sessionId}.json`), 'not json');

    expect(manager.loadSession(sessionId)).toBeNull();
  });

  it('atomically writes session through file operations', () => {
    const atomicWrite = vi.fn();
    const atomicManager = new SessionManager(tempDir, { atomicWrite });
    const session = atomicManager.createSession('/work', 'Atomic');

    expect(atomicWrite).toHaveBeenCalledOnce();
    const [filePath, data] = atomicWrite.mock.calls[0];
    expect(String(filePath)).toBe(path.join(tempDir, 'sessions', `${session.id}.json`));
    expect(JSON.parse(String(data)).title).toBe('Atomic');
  });

  it('propagates error when atomic write fails', () => {
    const failingManager = new SessionManager(tempDir, {
      atomicWrite: () => { throw new Error('write failed'); },
    });

    expect(() => failingManager.createSession('/work', 'Failure')).toThrow('write failed');
    expect(fs.readdirSync(path.join(tempDir, 'sessions'))).toEqual([]);
  });

  it('updates session cost data', () => {
    const session = manager.createSession('/work', 'Cost Test');
    manager.updateSessionCost(session.id, {
      input: 1000,
      output: 500,
      cost: 0.05,
      model: 'claude-sonnet-4-20250514',
    });

    const loaded = manager.loadSession(session.id);
    expect(loaded!.totalInputTokens).toBe(1000);
    expect(loaded!.totalOutputTokens).toBe(500);
    expect(loaded!.estimatedCost).toBe(0.05);
    expect(loaded!.model).toBe('claude-sonnet-4-20250514');
  });
});
