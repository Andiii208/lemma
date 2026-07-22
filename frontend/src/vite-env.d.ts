/// <reference types="vite/client" />

declare module 'prism-react-renderer' {
  export const Highlight: React.ComponentType<{
    theme?: unknown;
    code: string;
    language: string;
    children: (props: {
      style: React.CSSProperties;
      tokens: unknown[][];
      getLineProps: (props: { line: unknown[] }) => Record<string, unknown>;
      getTokenProps: (props: { token: unknown }) => Record<string, unknown>;
    }) => React.ReactNode;
  }>;
  export const themes: {
    oneDark: unknown;
  };
}
