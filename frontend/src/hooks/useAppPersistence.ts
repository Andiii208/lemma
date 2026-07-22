import { useEffect, useRef } from 'react';
import { AVAILABLE_MODELS } from '../config';
import { STORAGE_KEYS } from '../constants';
import type { AppAction, AppState } from '../context/AppContext';

type PersistableKeys = 'theme' | 'workDir' | 'sidebarCollapsed' | 'notificationsEnabled' | 'selectedModel' | 'selectedPreset';

type PersistedState = Partial<Pick<AppState, PersistableKeys>>;

const VALID_THEMES = new Set(['light', 'dark', 'system']);

function loadPersistedState(): PersistedState {
  const result: PersistedState = {};
  try {
    const theme = localStorage.getItem(STORAGE_KEYS.THEME);
    if (theme && VALID_THEMES.has(theme)) result.theme = theme as AppState['theme'];

    const workDir = localStorage.getItem(STORAGE_KEYS.WORK_DIR);
    if (workDir) result.workDir = workDir;

    const collapsed = localStorage.getItem(STORAGE_KEYS.SIDEBAR_COLLAPSED);
    if (collapsed !== null) result.sidebarCollapsed = collapsed === 'true';

    const notifications = localStorage.getItem(STORAGE_KEYS.NOTIFICATIONS_ENABLED);
    if (notifications !== null) result.notificationsEnabled = notifications === 'true';

    const model = localStorage.getItem(STORAGE_KEYS.SELECTED_MODEL);
    if (model && AVAILABLE_MODELS.some((m) => m.id === model)) {
      result.selectedModel = model;
    }

    const preset = localStorage.getItem(STORAGE_KEYS.SELECTED_PRESET);
    if (preset) result.selectedPreset = preset;
  } catch {
    /* localStorage may be unavailable */
  }
  return result;
}

function savePersistedState(state: PersistedState): void {
  try {
    if (state.theme !== undefined) {
      localStorage.setItem(STORAGE_KEYS.THEME, state.theme);
    }
    if (state.workDir !== undefined) {
      if (state.workDir) {
        localStorage.setItem(STORAGE_KEYS.WORK_DIR, state.workDir);
      } else {
        localStorage.removeItem(STORAGE_KEYS.WORK_DIR);
      }
    }
    if (state.sidebarCollapsed !== undefined) {
      localStorage.setItem(STORAGE_KEYS.SIDEBAR_COLLAPSED, String(state.sidebarCollapsed));
    }
    if (state.notificationsEnabled !== undefined) {
      localStorage.setItem(STORAGE_KEYS.NOTIFICATIONS_ENABLED, String(state.notificationsEnabled));
    }
    if (state.selectedModel !== undefined) {
      localStorage.setItem(STORAGE_KEYS.SELECTED_MODEL, state.selectedModel);
    }
    if (state.selectedPreset !== undefined) {
      if (state.selectedPreset) {
        localStorage.setItem(STORAGE_KEYS.SELECTED_PRESET, state.selectedPreset);
      } else {
        localStorage.removeItem(STORAGE_KEYS.SELECTED_PRESET);
      }
    }
  } catch {
    /* localStorage may be full */
  }
}

export function useAppPersistence(
  state: PersistedState,
  dispatch: React.Dispatch<AppAction>,
): void {
  const isHydrated = useRef(false);

  // Hydrate state from localStorage on mount
  useEffect(() => {
    const persisted = loadPersistedState();
    if (Object.keys(persisted).length > 0) {
      dispatch({ type: 'HYDRATE_STATE', payload: persisted });
    }
    isHydrated.current = true;
  }, [dispatch]);

  // Save state changes to localStorage — skip until hydration is complete
  useEffect(() => {
    if (!isHydrated.current) return;
    savePersistedState({
      theme: state.theme,
      workDir: state.workDir,
      sidebarCollapsed: state.sidebarCollapsed,
      notificationsEnabled: state.notificationsEnabled,
      selectedModel: state.selectedModel,
      selectedPreset: state.selectedPreset,
    });
  }, [
    state.theme,
    state.workDir,
    state.sidebarCollapsed,
    state.notificationsEnabled,
    state.selectedModel,
    state.selectedPreset,
  ]);
}
