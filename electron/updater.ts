import { BrowserWindow } from 'electron';
import { UpdaterStateMachine } from './updater-state-machine';
import type { UpdateInfo } from './updater-state-machine';

const stateMachine = new UpdaterStateMachine();

export function getStateMachine(): UpdaterStateMachine {
  return stateMachine;
}

export function setupAutoUpdater(mainWindow: BrowserWindow): void {
  if (process.env.NODE_ENV === 'development') return;

  try {
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    const { autoUpdater } = require('electron-updater');

    autoUpdater.autoDownload = false;

    autoUpdater.on('update-available', (info: UpdateInfo) => {
      stateMachine.updateAvailable(info);
      mainWindow.webContents.send('update-state-changed', {
        state: stateMachine.getState(),
        info: stateMachine.getUpdateInfo(),
      });
    });

    autoUpdater.on('update-not-available', () => {
      stateMachine.noUpdateAvailable();
      mainWindow.webContents.send('update-state-changed', {
        state: stateMachine.getState(),
      });
    });

    autoUpdater.on('download-progress', (progress: { percent: number; bytesPerSecond: number }) => {
      stateMachine.downloadProgress(progress);
      mainWindow.webContents.send('update-state-changed', {
        state: stateMachine.getState(),
        progress: stateMachine.getProgress(),
      });
    });

    autoUpdater.on('update-downloaded', (info: UpdateInfo) => {
      stateMachine.downloadComplete();
      mainWindow.webContents.send('update-state-changed', {
        state: stateMachine.getState(),
        info,
      });
    });

    autoUpdater.on('error', (error: Error) => {
      stateMachine.error(error.message);
      mainWindow.webContents.send('update-state-changed', {
        state: stateMachine.getState(),
        error: stateMachine.getError(),
      });
    });

    stateMachine.onStateChange((state) => {
      if (state === 'downloading') {
        autoUpdater.downloadUpdate().catch((err: unknown) => {
          const msg = err instanceof Error ? err.message : 'Download failed';
          stateMachine.error(msg);
          mainWindow.webContents.send('update-state-changed', {
            state: stateMachine.getState(),
            error: stateMachine.getError(),
          });
        });
      }
    });

    setTimeout(() => {
      stateMachine.checkForUpdates();
      mainWindow.webContents.send('update-state-changed', {
        state: stateMachine.getState(),
      });
      autoUpdater.checkForUpdates().catch((err: unknown) => {
        const msg = err instanceof Error ? err.message : 'Check failed';
        stateMachine.error(msg);
        mainWindow.webContents.send('update-state-changed', {
          state: stateMachine.getState(),
          error: stateMachine.getError(),
        });
      });
    }, 5000);
  } catch {
    // electron-updater 未安装时忽略
  }
}

export function downloadUpdate(): void {
  stateMachine.download();
}

export function installUpdate(): void {
  try {
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    const { autoUpdater } = require('electron-updater');
    autoUpdater.quitAndInstall();
  } catch {
    // 忽略
  }
}
