import { useState, useEffect } from 'react';
import { Check } from 'lucide-react';
import { loadPresets, PRESETS_FALLBACK, type PresetInfo } from '../config';

interface PresetSelectorProps {
  selectedPreset: string | null;
  onSelect: (presetId: string) => void;
}

const presetIcons: Record<string, string> = {
  'math-modeling': '📐',
  'paper-writing': '📝',
  'lab-report': '🔬',
  'literature-review': '📚',
  'data-mining': '📊',
};

export default function PresetSelector({ selectedPreset, onSelect }: PresetSelectorProps) {
  const [presets, setPresets] = useState<PresetInfo[]>(PRESETS_FALLBACK);

  useEffect(() => {
    loadPresets().then((p) => {
      if (p.length > 0) setPresets(p);
    });
  }, []);

  return (
    <div className="grid grid-cols-2 gap-2">
      {presets.map((preset) => (
        <button
          key={preset.id}
          onClick={() => onSelect(preset.id)}
          className={`flex items-start gap-2 p-3 rounded-lg text-left transition-all ${
            selectedPreset === preset.id
              ? 'bg-accent-soft border-2 border-accent'
              : 'bg-bg-elevated border-2 border-transparent hover:border-border-strong'
          }`}
        >
          <span className="text-lg mt-0.5">{presetIcons[preset.id] || '📄'}</span>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-1">
              <span className="text-sm font-medium">{preset.name}</span>
              {selectedPreset === preset.id && (
                <Check size={14} className="text-accent" />
              )}
            </div>
            <p className="text-xs text-text-muted mt-0.5 truncate">{preset.description}</p>
          </div>
        </button>
      ))}
    </div>
  );
}
