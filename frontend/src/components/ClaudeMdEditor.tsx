import { useState, useEffect, useCallback } from 'react';
import { FileText, Save, Plus } from 'lucide-react';

interface ClaudeMdEditorProps {
  workDir: string;
}

export default function ClaudeMdEditor({ workDir }: ClaudeMdEditorProps) {
  const [config, setConfig] = useState<ClaudeMdConfig | null>(null);
  const [editContent, setEditContent] = useState('');
  const [isEditing, setIsEditing] = useState(false);
  const [saveStatus, setSaveStatus] = useState<string | null>(null);

  const loadConfig = useCallback(async () => {
    if (!window.lemmaAPI) return;
    const result = await window.lemmaAPI.getClaudeMd(workDir);
    setConfig(result);
    setEditContent(result.content);
  }, [workDir]);

  useEffect(() => {
    if (workDir) void loadConfig();
  }, [workDir, loadConfig]);

  const handleSave = async () => {
    if (!window.lemmaAPI) return;
    await window.lemmaAPI.updateClaudeMd(workDir, editContent);
    setSaveStatus('✓ 已保存');
    setIsEditing(false);
    await loadConfig();
    setTimeout(() => setSaveStatus(null), 2000);
  };

  const handleCreate = async () => {
    if (!window.lemmaAPI) return;
    const template = await window.lemmaAPI.generateClaudeMdTemplate('default', workDir);
    setEditContent(template);
    setIsEditing(true);
  };

  if (!config) return null;

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="flex items-center gap-2 text-sm font-semibold">
          <FileText size={16} />
          CLAUDE.md
        </h3>
        {saveStatus && (
          <span className="text-xs text-green-600">{saveStatus}</span>
        )}
      </div>

      {config.exists && !isEditing ? (
        <div className="space-y-2">
          <pre className="p-3 rounded-lg bg-bg-elevated text-xs overflow-auto max-h-48 whitespace-pre-wrap">
            {config.content}
          </pre>
          <button
            onClick={() => setIsEditing(true)}
            className="text-xs text-accent hover:text-accent"
          >
            编辑
          </button>
        </div>
      ) : isEditing ? (
        <div className="space-y-2">
          <textarea
            value={editContent}
            onChange={(event) => setEditContent(event.target.value)}
            rows={12}
            className="w-full p-3 rounded-lg border border-border-strong bg-bg-secondary text-xs font-mono focus:outline-none focus:ring-2 focus:ring-accent"
          />
          <div className="flex gap-2">
            <button
              onClick={handleSave}
              className="flex items-center gap-1 px-3 py-1.5 rounded text-xs bg-accent text-white hover:bg-accent"
            >
              <Save size={12} />
              保存
            </button>
            <button
              onClick={() => { setIsEditing(false); setEditContent(config.content); }}
              className="px-3 py-1.5 rounded text-xs border border-border-strong hover:bg-bg-tertiary"
            >
              取消
            </button>
          </div>
        </div>
      ) : (
        <div className="space-y-2">
          <p className="text-xs text-text-muted">此目录没有 CLAUDE.md 文件</p>
          <button
            onClick={handleCreate}
            className="flex items-center gap-1 px-3 py-1.5 rounded text-xs bg-accent text-white hover:bg-accent"
          >
            <Plus size={12} />
            创建 CLAUDE.md
          </button>
        </div>
      )}
    </div>
  );
}
