import { describe, it, expect, beforeEach } from 'vitest';
import { STORAGE_KEYS } from '../constants';

describe('useAppPersistence', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  describe('localStorage keys', () => {
    it('STORAGE_KEYS has all required keys', () => {
      expect(STORAGE_KEYS.THEME).toBe('lemma-theme');
      expect(STORAGE_KEYS.WORK_DIR).toBe('lemma-work-dir');
      expect(STORAGE_KEYS.SIDEBAR_COLLAPSED).toBe('lemma-sidebar-collapsed');
      expect(STORAGE_KEYS.NOTIFICATIONS_ENABLED).toBe('lemma-notifications-enabled');
      expect(STORAGE_KEYS.SELECTED_MODEL).toBe('lemma-selected-model');
      expect(STORAGE_KEYS.SELECTED_PRESET).toBe('lemma-selected-preset');
    });
  });

  describe('load and save cycle', () => {
    it('persists and restores theme', () => {
      localStorage.setItem(STORAGE_KEYS.THEME, 'dark');
      const stored = localStorage.getItem(STORAGE_KEYS.THEME);
      expect(stored).toBe('dark');
    });

    it('persists and restores workDir', () => {
      localStorage.setItem(STORAGE_KEYS.WORK_DIR, '/test/path');
      const stored = localStorage.getItem(STORAGE_KEYS.WORK_DIR);
      expect(stored).toBe('/test/path');
    });

    it('persists and restores sidebarCollapsed as string', () => {
      localStorage.setItem(STORAGE_KEYS.SIDEBAR_COLLAPSED, 'true');
      const stored = localStorage.getItem(STORAGE_KEYS.SIDEBAR_COLLAPSED);
      expect(stored).toBe('true');
      expect(stored === 'true').toBe(true);
    });

    it('persists and restores notificationsEnabled as string', () => {
      localStorage.setItem(STORAGE_KEYS.NOTIFICATIONS_ENABLED, 'false');
      const stored = localStorage.getItem(STORAGE_KEYS.NOTIFICATIONS_ENABLED);
      expect(stored).toBe('false');
      expect(stored === 'true').toBe(false);
    });

    it('persists and restores selectedModel', () => {
      localStorage.setItem(STORAGE_KEYS.SELECTED_MODEL, 'claude-sonnet-4-20250514');
      const stored = localStorage.getItem(STORAGE_KEYS.SELECTED_MODEL);
      expect(stored).toBe('claude-sonnet-4-20250514');
    });

    it('persists and restores selectedPreset', () => {
      localStorage.setItem(STORAGE_KEYS.SELECTED_PRESET, 'math-modeling');
      const stored = localStorage.getItem(STORAGE_KEYS.SELECTED_PRESET);
      expect(stored).toBe('math-modeling');
    });

    it('handles missing keys gracefully', () => {
      expect(localStorage.getItem(STORAGE_KEYS.THEME)).toBeNull();
      expect(localStorage.getItem(STORAGE_KEYS.WORK_DIR)).toBeNull();
      expect(localStorage.getItem(STORAGE_KEYS.SELECTED_PRESET)).toBeNull();
    });

    it('removes workDir when set to null', () => {
      localStorage.setItem(STORAGE_KEYS.WORK_DIR, '/test');
      expect(localStorage.getItem(STORAGE_KEYS.WORK_DIR)).toBe('/test');
      localStorage.removeItem(STORAGE_KEYS.WORK_DIR);
      expect(localStorage.getItem(STORAGE_KEYS.WORK_DIR)).toBeNull();
    });

    it('removes selectedPreset when set to null', () => {
      localStorage.setItem(STORAGE_KEYS.SELECTED_PRESET, 'test');
      expect(localStorage.getItem(STORAGE_KEYS.SELECTED_PRESET)).toBe('test');
      localStorage.removeItem(STORAGE_KEYS.SELECTED_PRESET);
      expect(localStorage.getItem(STORAGE_KEYS.SELECTED_PRESET)).toBeNull();
    });
  });
});
