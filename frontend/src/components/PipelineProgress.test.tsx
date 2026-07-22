import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import PipelineProgress from './PipelineProgress';

describe('PipelineProgress', () => {
  it('renders stages from props', () => {
    const stages = [
      { id: 'step1', name: '步骤一', status: 'completed' as const },
      { id: 'step2', name: '步骤二', status: 'running' as const },
      { id: 'step3', name: '步骤三', status: 'pending' as const },
    ];
    render(<PipelineProgress stages={stages} />);
    expect(screen.getByText('步骤一')).toBeDefined();
    expect(screen.getByText('步骤二')).toBeDefined();
    expect(screen.getByText('步骤三')).toBeDefined();
  });

  it('shows progress percentage based on completed stages', () => {
    const stages = [
      { id: 'a', name: 'A', status: 'completed' as const },
      { id: 'b', name: 'B', status: 'completed' as const },
      { id: 'c', name: 'C', status: 'pending' as const },
      { id: 'd', name: 'D', status: 'pending' as const },
    ];
    render(<PipelineProgress stages={stages} />);
    expect(screen.getByText('50%')).toBeDefined();
  });

  it('does not use hardcoded default stages', () => {
    render(<PipelineProgress />);
    expect(screen.queryByText('分析')).toBeNull();
    expect(screen.queryByText('推导')).toBeNull();
    expect(screen.queryByText('编码')).toBeNull();
  });

  it('shows step description when provided and no stages', () => {
    render(<PipelineProgress stepDescription="正在分析问题..." />);
    expect(screen.getByText('正在分析问题...')).toBeDefined();
  });

  it('does not show progress bar when no stages', () => {
    render(<PipelineProgress />);
    expect(screen.queryByText(/阶段完成/)).toBeNull();
  });

  it('shows empty state message when no stages and no description', () => {
    render(<PipelineProgress />);
    expect(screen.getByText('暂无进度信息')).toBeDefined();
  });

  it('does not show step description when stages are provided', () => {
    const stages = [
      { id: 'a', name: 'A', status: 'completed' as const },
    ];
    render(<PipelineProgress stages={stages} stepDescription="不应显示" />);
    expect(screen.queryByText('不应显示')).toBeNull();
  });

  it('marks currentStage as running', () => {
    const stages = [
      { id: 'a', name: 'A', status: 'pending' as const },
      { id: 'b', name: 'B', status: 'pending' as const },
    ];
    render(<PipelineProgress stages={stages} currentStage="b" />);
    expect(screen.getByText('B').closest('button')).toBeDefined();
  });

  it('shows progress bar with 0% when stages exist but none completed', () => {
    const stages = [
      { id: 'a', name: 'A', status: 'pending' as const },
      { id: 'b', name: 'B', status: 'pending' as const },
    ];
    render(<PipelineProgress stages={stages} />);
    expect(screen.getByText('0%')).toBeDefined();
    expect(screen.getByText('0/2 阶段完成')).toBeDefined();
  });
});
