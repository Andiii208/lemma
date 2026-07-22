import { defineConfig } from '@playwright/test'

export default defineConfig({
  testDir: './e2e',
  timeout: 120000,  // 2 分钟，给 LLM 响应留时间
  retries: 0,
  use: {
    baseURL: 'http://localhost:5173',
    headless: true,
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
  webServer: [
    {
      command: 'cd ../backend && PYTHONPATH=src python -m uvicorn lemma.api.server:app --port 8765',
      port: 8765,
      timeout: 30000,
      reuseExistingServer: true,
    },
    {
      command: 'npx vite --port 5173',
      port: 5173,
      timeout: 30000,
      reuseExistingServer: true,
    },
  ],
})
