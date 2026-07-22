import { createContext, useContext, useReducer, useEffect, type ReactNode } from 'react';
import { AUTO_MODEL } from '../config';
import { useAppPersistence } from '../hooks/useAppPersistence';
import type { PipelineStage } from '../components/PipelineProgress';

export type ViewType = 'chat' | 'settings' | 'files' | 'cost' | 'export';
type ThemeType = 'light' | 'dark' | 'system';

export interface AppState {
  currentView: ViewType;
  theme: ThemeType;
  workDir: string | null;
  currentSessionId: string | null;
  apiKeyConfigured: boolean;
  sidebarCollapsed: boolean;
  notificationsEnabled: boolean;
  selectedModel: string;
  selectedPreset: string | null;
  pipelineStages: PipelineStage[] | null;
  currentStage: string | null;
}

export type AppAction =
  | { type: 'SET_VIEW'; payload: ViewType }
  | { type: 'SET_THEME'; payload: ThemeType }
  | { type: 'SET_WORK_DIR'; payload: string | null }
  | { type: 'SET_SESSION'; payload: string | null }
  | { type: 'SET_API_KEY_CONFIGURED'; payload: boolean }
  | { type: 'TOGGLE_SIDEBAR' }
  | { type: 'SET_NOTIFICATIONS'; payload: boolean }
  | { type: 'SET_MODEL'; payload: string }
  | { type: 'SET_PRESET'; payload: string | null }
  | { type: 'SET_PIPELINE'; payload: { stages: PipelineStage[]; currentStage: string } }
  | { type: 'CLEAR_PIPELINE' }
  | { type: 'HYDRATE_STATE'; payload: Partial<AppState> };

const initialState: AppState = {
  currentView: 'chat',
  theme: 'system',
  workDir: null,
  currentSessionId: null,
  apiKeyConfigured: false,
  sidebarCollapsed: false,
  notificationsEnabled: true,
  selectedModel: AUTO_MODEL,
  selectedPreset: null,
  pipelineStages: null,
  currentStage: null,
};

function appReducer(state: AppState, action: AppAction): AppState {
  switch (action.type) {
    case 'SET_VIEW':
      return { ...state, currentView: action.payload };
    case 'SET_THEME':
      return { ...state, theme: action.payload };
    case 'SET_WORK_DIR':
      return { ...state, workDir: action.payload };
    case 'SET_SESSION':
      return { ...state, currentSessionId: action.payload };
    case 'SET_API_KEY_CONFIGURED':
      return { ...state, apiKeyConfigured: action.payload };
    case 'TOGGLE_SIDEBAR':
      return { ...state, sidebarCollapsed: !state.sidebarCollapsed };
    case 'SET_NOTIFICATIONS':
      return { ...state, notificationsEnabled: action.payload };
    case 'SET_MODEL':
      return { ...state, selectedModel: action.payload };
    case 'SET_PRESET':
      return { ...state, selectedPreset: action.payload };
    case 'SET_PIPELINE':
      return { ...state, pipelineStages: action.payload.stages, currentStage: action.payload.currentStage };
    case 'CLEAR_PIPELINE':
      return { ...state, pipelineStages: null, currentStage: null };
    case 'HYDRATE_STATE':
      return { ...state, ...action.payload };
    default:
      return state;
  }
}

interface AppContextType {
  state: AppState;
  dispatch: React.Dispatch<AppAction>;
}

const AppContext = createContext<AppContextType | null>(null);

export function AppProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(appReducer, initialState);

  // localStorage 持久化
  useAppPersistence(state, dispatch);

  // 初始化：检查 API Key 是否已配置
  useEffect(() => {
    checkApiKeyConfig(dispatch);
  }, []);

  // 主题同步
  useEffect(() => {
    applyTheme(state.theme);
  }, [state.theme]);

  return (
    <AppContext.Provider value={{ state, dispatch }}>
      {children}
    </AppContext.Provider>
  );
}

async function checkApiKeyConfig(dispatch: React.Dispatch<AppAction>): Promise<void> {
  try {
    const configured = await window.lemmaAPI?.hasApiKey() ?? false;
    dispatch({ type: 'SET_API_KEY_CONFIGURED', payload: configured });
  } catch {
    // API 不可用时忽略
  }
}

function applyTheme(theme: ThemeType): void {
  const root = document.documentElement;
  if (theme === 'system') {
    const prefersLight = window.matchMedia('(prefers-color-scheme: light)').matches;
    root.classList.toggle('light', prefersLight);
  } else {
    root.classList.toggle('light', theme === 'light');
  }
}

// eslint-disable-next-line react-refresh/only-export-components
export function useApp(): AppContextType {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within AppProvider');
  }
  return context;
}
