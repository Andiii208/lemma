import { describe, it, expect } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { createElement } from 'react';
import { AppProvider, useApp } from '../context/AppContext';

function createWrapper() {
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return createElement(AppProvider, null, children);
  };
}

describe('AppContext', () => {
  it('provides initial state', () => {
    const { result } = renderHook(() => useApp(), { wrapper: createWrapper() });
    expect(result.current.state.currentView).toBe('chat');
    expect(result.current.state.theme).toBe('system');
    expect(result.current.state.workDir).toBeNull();
    expect(result.current.state.notificationsEnabled).toBe(true);
  });

  it('dispatches SET_VIEW', () => {
    const { result } = renderHook(() => useApp(), { wrapper: createWrapper() });
    act(() => {
      result.current.dispatch({ type: 'SET_VIEW', payload: 'settings' });
    });
    expect(result.current.state.currentView).toBe('settings');
  });

  it('dispatches SET_THEME', () => {
    const { result } = renderHook(() => useApp(), { wrapper: createWrapper() });
    act(() => {
      result.current.dispatch({ type: 'SET_THEME', payload: 'dark' });
    });
    expect(result.current.state.theme).toBe('dark');
  });

  it('dispatches SET_WORK_DIR', () => {
    const { result } = renderHook(() => useApp(), { wrapper: createWrapper() });
    act(() => {
      result.current.dispatch({ type: 'SET_WORK_DIR', payload: '/test/dir' });
    });
    expect(result.current.state.workDir).toBe('/test/dir');
  });

  it('dispatches SET_NOTIFICATIONS', () => {
    const { result } = renderHook(() => useApp(), { wrapper: createWrapper() });
    act(() => {
      result.current.dispatch({ type: 'SET_NOTIFICATIONS', payload: false });
    });
    expect(result.current.state.notificationsEnabled).toBe(false);
  });

  it('dispatches TOGGLE_SIDEBAR', () => {
    const { result } = renderHook(() => useApp(), { wrapper: createWrapper() });
    expect(result.current.state.sidebarCollapsed).toBe(false);
    act(() => {
      result.current.dispatch({ type: 'TOGGLE_SIDEBAR' });
    });
    expect(result.current.state.sidebarCollapsed).toBe(true);
  });

  it('dispatches SET_PIPELINE with stages', () => {
    const { result } = renderHook(() => useApp(), { wrapper: createWrapper() });
    const stages = [
      { id: 'step1', name: '步骤一', status: 'pending' as const },
      { id: 'step2', name: '步骤二', status: 'pending' as const },
    ];
    act(() => {
      result.current.dispatch({
        type: 'SET_PIPELINE',
        payload: { stages, currentStage: 'step1' },
      });
    });
    expect(result.current.state.pipelineStages).toEqual(stages);
    expect(result.current.state.currentStage).toBe('step1');
  });

  it('dispatches CLEAR_PIPELINE', () => {
    const { result } = renderHook(() => useApp(), { wrapper: createWrapper() });
    act(() => {
      result.current.dispatch({
        type: 'SET_PIPELINE',
        payload: {
          stages: [{ id: 'a', name: 'A', status: 'pending' as const }],
          currentStage: 'a',
        },
      });
    });
    expect(result.current.state.pipelineStages).toHaveLength(1);

    act(() => {
      result.current.dispatch({ type: 'CLEAR_PIPELINE' });
    });
    expect(result.current.state.pipelineStages).toBeNull();
    expect(result.current.state.currentStage).toBeNull();
  });

  it('initializes with null pipeline', () => {
    const { result } = renderHook(() => useApp(), { wrapper: createWrapper() });
    expect(result.current.state.pipelineStages).toBeNull();
    expect(result.current.state.currentStage).toBeNull();
  });
});
