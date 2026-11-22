import { defineConfig } from '@playwright/test'
import { fileURLToPath } from 'node:url'

const baseURL = 'http://127.0.0.1:8765'

export default defineConfig({
  testDir: './e2e',
  workers: 1,
  timeout: 60_000,
  expect: { timeout: 15_000 },
  use: {
    baseURL,
    browserName: 'chromium',
    viewport: { width: 1280, height: 900 },
    locale: 'hr-HR',
  },
  webServer: {
    command: 'uv run uprent serve --port 8765',
    cwd: fileURLToPath(new URL('../', import.meta.url)),
    url: baseURL + '/api/health',
    reuseExistingServer: false,
    timeout: 45_000,
  },
})
