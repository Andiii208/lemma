import { useEffect } from 'react';

interface ShortcutAction {
  key: string;
  ctrl?: boolean;
  shift?: boolean;
  action: () => void;
  description: string;
}

export function useKeyboardShortcuts(shortcuts: ShortcutAction[]) {
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      for (const shortcut of shortcuts) {
        const ctrlMatch = shortcut.ctrl
          ? event.ctrlKey || event.metaKey
          : !event.ctrlKey && !event.metaKey;
        const shiftMatch = shortcut.shift ? event.shiftKey : !event.shiftKey;

        if (event.key === shortcut.key && ctrlMatch && shiftMatch) {
          event.preventDefault();
          shortcut.action();
          return;
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [shortcuts]);
}

export const DEFAULT_SHORTCUTS = {
  newSession: { key: 'n', ctrl: true, description: '新建会话' },
  openDirectory: { key: 'o', ctrl: true, description: '选择工作目录' },
  send: { key: 'Enter', ctrl: true, description: '发送消息' },
  stopGeneration: { key: '.', ctrl: true, description: '停止生成' },
  clearChat: { key: 'k', ctrl: true, description: '清空对话' },
  settings: { key: ',', ctrl: true, description: '设置' },
  exportChat: { key: 'e', ctrl: true, shift: true, description: '导出对话' },
};
