import '@testing-library/jest-dom';

// jsdom 缺少 matchMedia，需要 mock
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: (query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: () => {},
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => false,
  }),
});

// mock lemmaAPI（Electron IPC）
Object.defineProperty(window, 'lemmaAPI', {
  writable: true,
  value: undefined,
});
