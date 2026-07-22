import { Palette } from 'lucide-react';
import { useApp } from '../../context/AppContext';

const THEME_OPTIONS = [
  { value: 'light', label: '亮色' },
  { value: 'dark', label: '暗色' },
  { value: 'system', label: '跟随系统' },
] as const;

export default function ThemeSection() {
  const { state, dispatch } = useApp();

  return (
    <section className="space-y-3">
      <h3 className="flex items-center gap-2 text-sm font-semibold text-text">
        <Palette size={16} />
        主题
      </h3>
      <div className="flex gap-2">
        {THEME_OPTIONS.map((option) => (
          <button
            key={option.value}
            onClick={() => dispatch({ type: 'SET_THEME', payload: option.value })}
            className={`px-4 py-2 rounded-lg text-sm transition-colors ${
              state.theme === option.value
                ? 'bg-accent text-white'
                : 'border border-border-strong hover:bg-bg-tertiary'
            }`}
          >
            {option.label}
          </button>
        ))}
      </div>
    </section>
  );
}
