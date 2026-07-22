import * as fs from 'fs';
import * as path from 'path';
import { atomicWriteFileSync } from './atomic-file';

interface McpServerConfig {
  name: string;
  command: string;
  args: string[];
  env?: Record<string, string>;
}

interface ClaudeSettings {
  mcpServers?: Record<string, {
    command: string;
    args: string[];
    env?: Record<string, string>;
  }>;
}

function getSettingsPath(workDir: string): string {
  return path.join(workDir, '.claude', 'settings.json');
}

function readSettings(workDir: string): ClaudeSettings {
  const settingsPath = getSettingsPath(workDir);
  if (!fs.existsSync(settingsPath)) return {};
  try {
    return JSON.parse(fs.readFileSync(settingsPath, 'utf-8')) as ClaudeSettings;
  } catch {
    return {};
  }
}

function writeSettings(workDir: string, settings: ClaudeSettings): void {
  const settingsPath = getSettingsPath(workDir);
  atomicWriteFileSync(settingsPath, JSON.stringify(settings, null, 2));
}

export function getMcpConfig(workDir: string): McpServerConfig[] {
  const settings = readSettings(workDir);
  if (!settings.mcpServers) return [];

  return Object.entries(settings.mcpServers).map(([name, config]) => ({
    name,
    command: config.command,
    args: config.args,
    env: config.env,
  }));
}

export function addMcpServer(workDir: string, config: McpServerConfig): void {
  const settings = readSettings(workDir);
  if (!settings.mcpServers) settings.mcpServers = {};

  settings.mcpServers[config.name] = {
    command: config.command,
    args: config.args,
    env: config.env,
  };

  writeSettings(workDir, settings);
}

export function removeMcpServer(workDir: string, name: string): void {
  const settings = readSettings(workDir);
  if (settings.mcpServers) {
    delete settings.mcpServers[name];
    writeSettings(workDir, settings);
  }
}
