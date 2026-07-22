import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';
import { getMcpConfig, addMcpServer, removeMcpServer } from '../mcp-config-manager';

describe('MCP Config Manager - atomic writes & parse safety', () => {
  let tempDir: string;

  beforeEach(() => {
    tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'lemma-mcp-'));
    fs.mkdirSync(path.join(tempDir, '.claude'));
  });

  afterEach(() => {
    fs.rmSync(tempDir, { recursive: true, force: true });
  });

  it('reads empty config when no file exists', () => {
    const config = getMcpConfig(tempDir);
    expect(config).toEqual([]);
  });

  it('adds and reads an MCP server', () => {
    addMcpServer(tempDir, {
      name: 'test-server',
      command: 'node',
      args: ['server.js'],
    });
    const config = getMcpConfig(tempDir);
    expect(config).toHaveLength(1);
    expect(config[0].name).toBe('test-server');
  });

  it('removes an MCP server', () => {
    addMcpServer(tempDir, { name: 's1', command: 'node', args: [] });
    addMcpServer(tempDir, { name: 's2', command: 'node', args: [] });
    removeMcpServer(tempDir, 's1');
    const config = getMcpConfig(tempDir);
    expect(config).toHaveLength(1);
    expect(config[0].name).toBe('s2');
  });

  it('does not overwrite file when existing JSON is corrupted', () => {
    const settingsPath = path.join(tempDir, '.claude', 'settings.json');
    const corruptContent = '{"mcpServers":{"bad":{';
    fs.writeFileSync(settingsPath, corruptContent);

    addMcpServer(tempDir, { name: 'new', command: 'node', args: [] });

    const afterAdd = fs.readFileSync(settingsPath, 'utf-8');
    const parsed = JSON.parse(afterAdd);
    expect(parsed.mcpServers).toBeDefined();
    expect(parsed.mcpServers['new']).toBeDefined();
  });

  it('getMcpConfig returns empty array for corrupted JSON', () => {
    const settingsPath = path.join(tempDir, '.claude', 'settings.json');
    fs.writeFileSync(settingsPath, 'not json at all');
    const config = getMcpConfig(tempDir);
    expect(config).toEqual([]);
  });

  it('preserves env field when adding server', () => {
    addMcpServer(tempDir, {
      name: 'env-server',
      command: 'node',
      args: [],
      env: { API_KEY: 'secret' },
    });
    const config = getMcpConfig(tempDir);
    expect(config[0].env).toEqual({ API_KEY: 'secret' });
  });
});
