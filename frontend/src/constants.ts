/** IPC event channel names */
export const IPC_CHANNELS = {
  CLAUDE_MESSAGE: 'claude-message',
  FILE_CHANGED: 'file-changed',
  SEND_MESSAGE: 'send-message',
  API_KEY_STATUS: 'api-key-status',
} as const;

/** IndexedDB / localStorage keys */
export const STORAGE_KEYS = {
  MESSAGE_PREFIX: 'lemma-messages:',
  THEME: 'lemma-theme',
  WORK_DIR: 'lemma-work-dir',
  SELECTED_PRESET: 'lemma-selected-preset',
  SELECTED_MODEL: 'lemma-selected-model',
  SIDEBAR_COLLAPSED: 'lemma-sidebar-collapsed',
  NOTIFICATIONS_ENABLED: 'lemma-notifications-enabled',
} as const;

/** Timing constants (milliseconds) */
export const TIMING = {
  SAVE_STATUS_DURATION: 2000,
  COPY_FEEDBACK_DURATION: 2000,
  NOTIFICATION_TIMEOUT: 3000,
} as const;

/** Retry backoff delays */
export const RETRY_DELAYS = [2000, 4000, 8000, 16000, 30000] as const;
