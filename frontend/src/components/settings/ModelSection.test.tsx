import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { AppProvider } from '../../context/AppContext';
import ModelSection from './ModelSection';

describe('ModelSection', () => {
  it('renders model label', () => {
    render(
      <AppProvider>
        <ModelSection />
      </AppProvider>
    );
    expect(screen.getByText('模型')).toBeTruthy();
  });

  it('shows all available models', () => {
    render(
      <AppProvider>
        <ModelSection />
      </AppProvider>
    );
    expect(screen.getByText('Claude Sonnet 4')).toBeTruthy();
    expect(screen.getByText('Claude Opus 4')).toBeTruthy();
    expect(screen.getByText('Claude Haiku 4')).toBeTruthy();
  });
});
