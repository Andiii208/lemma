import { defineWorkspace } from 'vitest/config'
import react from '@vitejs/plugin-react'

export default defineWorkspace([
  {
    plugins: [react()],
    test: {
      name: 'frontend',
      include: ['frontend/src/**/*.test.{ts,tsx}'],
      environment: 'jsdom',
      globals: true,
      setupFiles: './frontend/src/__tests__/setup.ts',
      css: true,
      exclude: ['dist', 'dist-electron', 'DEPRECATED', 'electron/**'],
    },
  },
  {
    test: {
      name: 'electron',
      include: ['electron/__tests__/**/*.test.ts'],
      environment: 'node',
      globals: true,
      exclude: ['dist', 'dist-electron', 'DEPRECATED', 'frontend/**'],
    },
  },
])
