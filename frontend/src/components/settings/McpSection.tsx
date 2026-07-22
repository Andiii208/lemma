import { useState, useEffect } from 'react';
import { Server, Plus, Trash2 } from 'lucide-react';
import { useApp } from '../../context/AppContext';

interface McpServer {
  name: string;
  command: string;
  args: string[];
}

export default function McpSection() {
  const { state } = useApp();
  const [mcpServers, setMcpServers] = useState<McpServer[]>([]);
  const [newMcpName, setNewMcpName] = useState('');
  const [newMcpCommand, setNewMcpCommand] = useState('');

  useEffect(() => {
    if (state.workDir) {
      window.lemmaAPI?.getMcpConfig(state.workDir).then(setMcpServers);
    }
  }, [state.workDir]);

  const handleAddMcpServer = async () => {
    if (!state.workDir || !newMcpName.trim() || !newMcpCommand.trim()) return;
    const args = newMcpCommand.split(' ').filter(Boolean);
    const command = args.shift() || '';
    await window.lemmaAPI?.addMcpServer(state.workDir, { name: newMcpName.trim(), command, args });
    const updated = await window.lemmaAPI?.getMcpConfig(state.workDir);
    if (updated) setMcpServers(updated);
    setNewMcpName('');
    setNewMcpCommand('');
  };

  const handleRemoveMcpServer = async (name: string) => {
    if (!state.workDir) return;
    await window.lemmaAPI?.removeMcpServer(state.workDir, name);
    const updated = await window.lemmaAPI?.getMcpConfig(state.workDir);
    if (updated) setMcpServers(updated);
  };

  if (!state.workDir) return null;

  return (
    <section className="space-y-3">
      <h3 className="flex items-center gap-2 text-sm font-semibold text-text">
        <Server size={16} />
        MCP Server
      </h3>
      {mcpServers.length > 0 && (
        <div className="space-y-1">
          {mcpServers.map((server) => (
            <div key={server.name} className="flex items-center justify-between px-3 py-2 rounded bg-bg-elevated">
              <div>
                <p className="text-sm font-medium">{server.name}</p>
                <p className="text-xs text-text-muted">{server.command} {server.args.join(' ')}</p>
              </div>
              <button onClick={() => handleRemoveMcpServer(server.name)} aria-label={`删除 ${server.name}`} className="text-red-400 hover:text-red-600">
                <Trash2 size={14} />
              </button>
            </div>
          ))}
        </div>
      )}
      <div className="flex gap-2">
        <input
          type="text"
          value={newMcpName}
          onChange={(event) => setNewMcpName(event.target.value)}
          placeholder="名称"
          aria-label="MCP 服务器名称"
          className="w-24 px-3 py-2 rounded-lg border border-border-strong bg-bg-secondary text-sm"
        />
        <input
          type="text"
          value={newMcpCommand}
          onChange={(event) => setNewMcpCommand(event.target.value)}
          placeholder="命令 (如: npx @playwright/mcp)"
          aria-label="MCP 服务器命令"
          className="flex-1 px-3 py-2 rounded-lg border border-border-strong bg-bg-secondary text-sm"
        />
        <button
          onClick={handleAddMcpServer}
          disabled={!newMcpName.trim() || !newMcpCommand.trim()}
          aria-label="添加 MCP 服务器"
          className="px-3 py-2 rounded-lg bg-accent hover:bg-accent-hover disabled:opacity-50 text-white text-sm"
        >
          <Plus size={14} />
        </button>
      </div>
    </section>
  );
}
