import { defineConfig } from '@playwright/test'
import { existsSync } from 'node:fs'

const baseURL = process.env.TEST_BASE_URL ?? 'https://localhost:8447'
const localTls =
  new URL(baseURL).protocol === 'https:' &&
  ['localhost', '127.0.0.1'].includes(new URL(baseURL).hostname)

export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: false,
  workers: 1,
  timeout: 45000,
  expect: { timeout: 15000 },
  use: {
    baseURL,
    ignoreHTTPSErrors: localTls,
    viewport: { width: 1440, height: 1050 },
    screenshot: 'only-on-failure',
    trace: 'retain-on-failure',
    launchOptions: {
      // SharedWorker TLS requests need the browser-level flag in isolated test Chromium.
      args: localTls ? ['--ignore-certificate-errors'] : [],
      executablePath:
        process.env.CHROMIUM_PATH ??
        (existsSync('/usr/bin/chromium') ? '/usr/bin/chromium' : undefined),
    },
  },
})
