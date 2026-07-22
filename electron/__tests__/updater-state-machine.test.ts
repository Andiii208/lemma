import { describe, it, expect, beforeEach } from 'vitest';
import { UpdaterStateMachine, type UpdateState } from '../updater-state-machine';

describe('UpdaterStateMachine', () => {
  let machine: UpdaterStateMachine;
  let stateChanges: UpdateState[];

  beforeEach(() => {
    machine = new UpdaterStateMachine();
    stateChanges = [];
    machine.onStateChange((state) => stateChanges.push(state));
  });

  it('starts in idle state', () => {
    expect(machine.getState()).toBe('idle');
  });

  it('transitions idle -> checking on checkForUpdates', () => {
    machine.checkForUpdates();
    expect(machine.getState()).toBe('checking');
  });

  it('transitions checking -> available when update found', () => {
    machine.checkForUpdates();
    machine.updateAvailable({ version: '1.2.0', releaseDate: '2026-01-01' });
    expect(machine.getState()).toBe('available');
    expect(machine.getUpdateInfo()?.version).toBe('1.2.0');
  });

  it('transitions checking -> idle when no update', () => {
    machine.checkForUpdates();
    machine.noUpdateAvailable();
    expect(machine.getState()).toBe('idle');
  });

  it('transitions available -> downloading on download', () => {
    machine.checkForUpdates();
    machine.updateAvailable({ version: '1.2.0', releaseDate: '2026-01-01' });
    machine.download();
    expect(machine.getState()).toBe('downloading');
  });

  it('transitions downloading -> downloaded when complete', () => {
    machine.checkForUpdates();
    machine.updateAvailable({ version: '1.2.0', releaseDate: '2026-01-01' });
    machine.download();
    machine.downloadComplete();
    expect(machine.getState()).toBe('downloaded');
  });

  it('transitions to error from checking', () => {
    machine.checkForUpdates();
    machine.error('Network failure');
    expect(machine.getState()).toBe('error');
    expect(machine.getError()).toBe('Network failure');
  });

  it('transitions to error from downloading', () => {
    machine.checkForUpdates();
    machine.updateAvailable({ version: '1.2.0', releaseDate: '2026-01-01' });
    machine.download();
    machine.error('Download failed');
    expect(machine.getState()).toBe('error');
  });

  it('can retry from error state', () => {
    machine.checkForUpdates();
    machine.error('fail');
    machine.retry();
    expect(machine.getState()).toBe('idle');
  });

  it('emits state changes', () => {
    machine.checkForUpdates();
    machine.updateAvailable({ version: '1.2.0', releaseDate: '2026-01-01' });
    expect(stateChanges).toEqual(['checking', 'available']);
  });

  it('ignores invalid transitions', () => {
    machine.updateAvailable({ version: '1.0.0', releaseDate: '2026-01-01' });
    expect(machine.getState()).toBe('idle');
  });

  it('ignores download when not in available state', () => {
    machine.download();
    expect(machine.getState()).toBe('idle');
  });

  it('tracks download progress', () => {
    machine.checkForUpdates();
    machine.updateAvailable({ version: '1.2.0', releaseDate: '2026-01-01' });
    machine.download();
    machine.downloadProgress({ percent: 50, bytesPerSecond: 1024 });
    expect(machine.getProgress()?.percent).toBe(50);
  });
});
