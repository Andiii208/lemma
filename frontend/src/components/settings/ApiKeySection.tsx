import { useState } from 'react';
import { Key } from 'lucide-react';
import { useApp } from '../../context/AppContext';
import { TIMING } from '../../constants';

export default function ApiKeySection() {
  const { dispatch } = useApp();
  const [apiKey, setApiKey] = useState('');
  const [saveStatus, setSaveStatus] = useState<string | null>(null);

  const handleSaveApiKey = async () => {
    if (!apiKey.trim()) return;
    try {
      const result = await window.lemmaAPI?.storeApiKey(apiKey.trim()) ?? { success: false, reason: 'API not available' };
      if (result.success) {
        setSaveStatus('✓ API Key 已安全存储');
        dispatch({ type: 'SET_API_KEY_CONFIGURED', payload: true });
        setApiKey('');
      } else {
        setSaveStatus(`✕ 存储失败: ${result.reason}`);
      }
    } catch {
      setSaveStatus('✕ 存储失败: IPC 不可用');
    }
    setTimeout(() => setSaveStatus(null), TIMING.SAVE_STATUS_DURATION);
  };

  return (
    <section className="space-y-3">
      <h3 className="flex items-center gap-2 text-sm font-semibold text-text">
        <Key size={16} />
        Anthropic API Key
      </h3>
      <div className="flex gap-2">
        <label htmlFor="api-key-input" className="sr-only">Anthropic API Key</label>
        <input
          id="api-key-input"
          type="password"
          value={apiKey}
          onChange={(event) => setApiKey(event.target.value)}
          placeholder="sk-ant-..."
          aria-label="Anthropic API Key"
          className="flex-1 px-3 py-2 rounded-lg border border-border-strong bg-bg-secondary text-sm focus:outline-none focus:ring-2 focus:ring-accent"
        />
        <button
          onClick={handleSaveApiKey}
          disabled={!apiKey.trim()}
          className="px-4 py-2 rounded-lg bg-accent hover:bg-accent-hover disabled:opacity-50 text-white text-sm transition-colors"
        >
          保存
        </button>
      </div>
      {saveStatus && (
        <p className={`text-xs ${saveStatus.startsWith('✓') ? 'text-green-600' : 'text-red-500'}`}>
          {saveStatus}
        </p>
      )}
      <p className="text-xs text-text-muted">
        API Key 通过 Electron safeStorage 加密存储，不会明文保存。
      </p>
    </section>
  );
}
