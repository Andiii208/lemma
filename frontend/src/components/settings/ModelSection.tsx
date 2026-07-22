import { Info } from 'lucide-react';
import { useApp } from '../../context/AppContext';
import { AVAILABLE_MODELS } from '../../config';

export default function ModelSection() {
  const { state, dispatch } = useApp();

  return (
    <section className="space-y-3">
      <h3 className="flex items-center gap-2 text-sm font-semibold text-text">
        <Info size={16} />
        模型
      </h3>
      <select
        value={state.selectedModel}
        onChange={(event) => dispatch({ type: 'SET_MODEL', payload: event.target.value })}
        className="w-full px-3 py-2 rounded-lg border border-border-strong bg-bg-secondary text-sm focus:outline-none focus:ring-2 focus:ring-accent"
      >
        <option value="auto">🤖 自动选择 (推荐)</option>
        {AVAILABLE_MODELS.map((model) => (
          <option key={model.id} value={model.id}>
            {model.name}
          </option>
        ))}
      </select>
    </section>
  );
}
