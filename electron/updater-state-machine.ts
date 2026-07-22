export type UpdateState = 'idle' | 'checking' | 'available' | 'downloading' | 'downloaded' | 'error';

export interface UpdateInfo {
  version: string;
  releaseDate: string;
  releaseNotes?: string;
}

export interface DownloadProgress {
  percent: number;
  bytesPerSecond?: number;
}

type StateChangeListener = (state: UpdateState) => void;

const VALID_TRANSITIONS: Record<UpdateState, UpdateState[]> = {
  idle: ['checking'],
  checking: ['available', 'idle', 'error'],
  available: ['downloading', 'error'],
  downloading: ['downloaded', 'error'],
  downloaded: [],
  error: ['idle'],
};

export class UpdaterStateMachine {
  private state: UpdateState = 'idle';
  private updateInfo: UpdateInfo | null = null;
  private errorReason: string | null = null;
  private progress: DownloadProgress | null = null;
  private readonly listeners: StateChangeListener[] = [];

  getState(): UpdateState {
    return this.state;
  }

  getUpdateInfo(): UpdateInfo | null {
    return this.updateInfo;
  }

  getError(): string | null {
    return this.errorReason;
  }

  getProgress(): DownloadProgress | null {
    return this.progress;
  }

  onStateChange(listener: StateChangeListener): void {
    this.listeners.push(listener);
  }

  checkForUpdates(): void {
    this.transition('checking');
    this.updateInfo = null;
    this.errorReason = null;
    this.progress = null;
  }

  updateAvailable(info: UpdateInfo): void {
    this.updateInfo = info;
    this.transition('available');
  }

  noUpdateAvailable(): void {
    this.transition('idle');
  }

  download(): void {
    this.progress = null;
    this.transition('downloading');
  }

  downloadProgress(progress: DownloadProgress): void {
    this.progress = progress;
  }

  downloadComplete(): void {
    this.transition('downloaded');
  }

  error(reason: string): void {
    this.errorReason = reason;
    this.transition('error');
  }

  retry(): void {
    this.transition('idle');
    this.errorReason = null;
  }

  private transition(newState: UpdateState): void {
    const allowed = VALID_TRANSITIONS[this.state];
    if (!allowed.includes(newState)) return;
    this.state = newState;
    for (const listener of this.listeners) {
      listener(this.state);
    }
  }
}
