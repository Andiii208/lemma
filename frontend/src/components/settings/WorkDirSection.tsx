import { FolderOpen } from 'lucide-react';
import { useApp } from '../../context/AppContext';

export default function WorkDirSection() {
  const { state, dispatch } = useApp();

  const handleSelectWorkDir = async () => {
    const dir = await window.lemmaAPI?.selectDirectory();
    if (dir) dispatch({ type: 'SET_WORK_DIR', payload: dir });
  };

  return (
    <section className="space-y-3">
      <h3 className="flex items-center gap-2 text-sm font-semibold text-text">
        <FolderOpen size={16} />
        工作目录
      </h3>
      <div className="flex gap-2">
        <input
          type="text"
          value={state.workDir || ''}
          readOnly
          placeholder="未选择"
          className="flex-1 px-3 py-2 rounded-lg border border-border-strong bg-bg-elevated text-sm"
        />
        <button
          onClick={handleSelectWorkDir}
          className="px-4 py-2 rounded-lg border border-border-strong hover:bg-bg-tertiary text-sm transition-colors"
        >
          浏览
        </button>
      </div>
    </section>
  );
}
