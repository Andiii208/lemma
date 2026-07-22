import { Bell } from 'lucide-react';
import { useApp } from '../context/AppContext';
import ApiKeySection from './settings/ApiKeySection';
import ModelSection from './settings/ModelSection';
import WorkDirSection from './settings/WorkDirSection';
import ThemeSection from './settings/ThemeSection';
import McpSection from './settings/McpSection';
import ClaudeMdEditor from './ClaudeMdEditor';

export default function SettingsPanel() {
  const { state, dispatch } = useApp();

  return (
    <div className="h-full overflow-y-auto">
      <div className="max-w-2xl mx-auto p-8 space-y-8">
        <h2 className="text-xl font-serif">设置</h2>

        <ApiKeySection />
        <ModelSection />
        <WorkDirSection />

        {state.workDir && (
          <section className="space-y-3">
            <ClaudeMdEditor workDir={state.workDir} />
          </section>
        )}

        <section className="space-y-3">
          <h3 className="flex items-center gap-2 text-sm font-semibold text-text">
            <Bell size={16} />
            通知
          </h3>
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={state.notificationsEnabled}
              onChange={(event) => dispatch({ type: 'SET_NOTIFICATIONS', payload: event.target.checked })}
              className="rounded border-border"
            />
            启用系统通知
          </label>
        </section>

        <ThemeSection />
        <McpSection />

        <section className="space-y-3 pt-4 border-t border-border">
          <h3 className="text-sm font-semibold text-text">关于</h3>
          <div className="text-xs text-text-muted space-y-1">
            <p>Lemma v0.1.0</p>
            <p>基于 Claude Agent SDK 的学术写作桌面软件</p>
            <p>Electron 39 + React 18 + TypeScript</p>
          </div>
        </section>
      </div>
    </div>
  );
}
