import { MessageCircle, FolderTree, DollarSign, Download, Settings } from 'lucide-react';
import { useApp, type ViewType } from '../context/AppContext';

type LucideIcon = React.ComponentType<{ size?: number | string }>;

const NAV_ITEMS: { id: ViewType; label: string; icon: LucideIcon }[] = [
  { id: 'chat', label: '对话', icon: MessageCircle },
  { id: 'files', label: '文件', icon: FolderTree },
  { id: 'cost', label: '成本', icon: DollarSign },
  { id: 'export', label: '导出', icon: Download },
  { id: 'settings', label: '设置', icon: Settings },
];

export default function TitleBar() {
  const { state, dispatch } = useApp();

  return (
    <header className="drag-region flex items-center h-12 px-4 border-b border-border bg-bg-elevated shrink-0">
      {/* Logo */}
      <div className="flex items-center gap-2 mr-8 no-drag">
        <span className="text-base font-display font-semibold tracking-tight text-accent">
          Lemma
        </span>
      </div>

      {/* Navigation Tabs */}
      <nav className="flex items-center gap-1 no-drag" role="navigation" aria-label="主导航">
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          const isActive = state.currentView === item.id;
          return (
            <button
              key={item.id}
              onClick={() => dispatch({ type: 'SET_VIEW', payload: item.id })}
              className={`flex items-center gap-1.5 px-3 py-1.5 text-ui font-medium rounded-editorial transition-colors ${
                isActive
                  ? 'text-accent bg-accent-soft'
                  : 'text-text-muted hover:text-text-secondary hover:bg-bg-tertiary'
              }`}
              aria-current={isActive ? 'page' : undefined}
            >
              <Icon size={14} />
              {item.label}
            </button>
          );
        })}
      </nav>

      {/* Spacer for Electron window controls */}
      <div className="flex-1" />
    </header>
  );
}
