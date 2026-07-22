import { useState, useEffect } from 'react';
import { FolderOpen, Plus, Clock, Search, PanelLeftClose, PanelLeftOpen, Trash2 } from 'lucide-react';
import { useApp } from '../context/AppContext';
import { loadPresets, PRESETS_FALLBACK, type PresetInfo } from '../config';

interface SidebarProps {
  sessions: SessionInfo[];
  selectedPreset: string | null;
  onSelectPreset: (presetId: string) => void;
  onNewSession: () => void;
  onSelectSession: (sessionId: string) => void;
  onDeleteSession?: (sessionId: string) => void;
}

export default function Sidebar({
  sessions, selectedPreset, onSelectPreset, onNewSession, onSelectSession, onDeleteSession,
}: SidebarProps) {
  const { state, dispatch } = useApp();
  const [searchQuery, setSearchQuery] = useState('');
  const [presets, setPresets] = useState<PresetInfo[]>(PRESETS_FALLBACK);
  const isCollapsed = state.sidebarCollapsed;

  useEffect(() => {
    loadPresets().then((p) => {
      if (p.length > 0) setPresets(p);
    });
  }, []);

  const filteredSessions = sessions.filter((session) =>
    session.title.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <aside
      className={`flex flex-col ${isCollapsed ? 'w-12' : 'w-[220px]'} bg-bg-elevated border-r border-border shrink-0 transition-all duration-200`}
      role="navigation"
      aria-label="会话列表"
    >
      {/* 收起/展开按钮 */}
      <div className={`p-2 ${isCollapsed ? '' : 'flex justify-end'}`}>
        <button
          onClick={() => dispatch({ type: 'TOGGLE_SIDEBAR' })}
          className="p-1.5 rounded hover:bg-bg-tertiary text-text-muted hover:text-text-secondary transition-colors"
          aria-label={isCollapsed ? '展开侧栏' : '收起侧栏'}
        >
          {isCollapsed ? <PanelLeftOpen size={16} /> : <PanelLeftClose size={16} />}
        </button>
      </div>

      {isCollapsed ? (
        <div className="flex flex-col items-center gap-3 py-2">
          <button
            onClick={onNewSession}
            className="p-2 rounded hover:bg-bg-tertiary text-text-muted hover:text-text-secondary transition-colors"
            aria-label="新建会话"
          >
            <Plus size={16} />
          </button>
          <button
            onClick={async () => {
              const dir = await window.lemmaAPI?.selectDirectory();
              if (dir) dispatch({ type: 'SET_WORK_DIR', payload: dir });
            }}
            className="p-2 rounded hover:bg-bg-tertiary text-text-muted hover:text-text-secondary transition-colors"
            aria-label="选择工作目录"
          >
            <FolderOpen size={16} />
          </button>
        </div>
      ) : (
        <>
          {/* 新建会话 */}
          <div className="p-3">
            <button
              onClick={onNewSession}
              className="flex items-center gap-2 w-full px-3 py-2 rounded-editorial text-ui font-medium bg-accent hover:bg-accent-hover text-white transition-colors press-scale"
            >
              <Plus size={14} />
              新建会话
            </button>
          </div>

          {/* 预设列表 */}
          <div className="px-3">
            <h3 className="text-caption font-semibold uppercase tracking-wider text-text-muted mb-2">
              预设模板
            </h3>
            <div className="space-y-0.5">
              {presets.map((preset) => (
                <button
                  key={preset.id}
                  onClick={() => onSelectPreset(preset.id)}
                  className={`flex items-center gap-2 w-full px-3 py-1.5 rounded-editorial text-ui transition-colors hover-lift ${
                    selectedPreset === preset.id
                      ? 'bg-accent-soft text-accent font-medium border-l-2 border-accent'
                      : 'text-text-muted hover:bg-bg-tertiary border-l-2 border-transparent'
                  }`}
                  title={preset.description}
                >
                  {preset.name}
                </button>
              ))}
            </div>
          </div>

          {/* 历史会话 */}
          <div className="flex-1 px-3 mt-4 overflow-y-auto">
            <h3 className="text-caption font-semibold uppercase tracking-wider text-text-muted mb-2">
              历史会话
            </h3>
            {sessions.length > 3 && (
              <div className="relative mb-2">
                <Search size={12} className="absolute left-2 top-1/2 -translate-y-1/2 text-text-muted" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(event) => setSearchQuery(event.target.value)}
                  placeholder="搜索会话..."
                  className="w-full pl-7 pr-2 py-1 rounded text-ui bg-bg-secondary border border-border focus:outline-none focus:ring-1 focus:ring-accent"
                />
              </div>
            )}
            <div className="space-y-0.5">
              {filteredSessions.map((session) => (
                <div key={session.id} className="group flex items-center gap-0.5">
                  <button
                    onClick={() => onSelectSession(session.id)}
                    className={`flex items-center gap-2 flex-1 min-w-0 px-3 py-1.5 rounded-editorial text-ui transition-colors ${
                      state.currentSessionId === session.id
                        ? 'bg-bg-tertiary text-text font-medium border-l-2 border-accent'
                        : 'text-text-muted hover:bg-bg-tertiary border-l-2 border-transparent'
                    }`}
                  >
                    <Clock size={11} className="shrink-0" />
                    <span className="truncate">{session.title}</span>
                  </button>
                  <button
                    onClick={(event) => {
                      event.stopPropagation();
                      onDeleteSession?.(session.id);
                    }}
                    className="p-1 rounded opacity-0 group-hover:opacity-100 group-focus-within:opacity-100 hover:bg-bg-tertiary text-text-muted hover:text-error transition-all shrink-0"
                    aria-label="删除会话"
                  >
                    <Trash2 size={11} />
                  </button>
                </div>
              ))}
            </div>
          </div>

          {/* 底部工作目录 */}
          <div className="p-3 border-t border-border">
            <button
              onClick={async () => {
                const dir = await window.lemmaAPI?.selectDirectory();
                if (dir) dispatch({ type: 'SET_WORK_DIR', payload: dir });
              }}
              className="flex items-center gap-2 w-full px-3 py-2 rounded-editorial text-ui text-text-muted hover:bg-bg-tertiary transition-colors"
              aria-label="选择工作目录"
            >
              <FolderOpen size={13} className="shrink-0" />
              <span className="truncate">
                {state.workDir ? state.workDir.split(/[\\/]/).pop() : '选择工作目录'}
              </span>
            </button>
          </div>
        </>
      )}
    </aside>
  );
}
