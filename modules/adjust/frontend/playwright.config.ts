import { defineConfig, devices } from '@playwright/test';
export default defineConfig({ testDir: './tests/e2e', fullyParallel: false, workers: 1, timeout: 45000,
  reporter: 'list', use: { baseURL: process.env.ADJUST_TEST_URL || 'http://127.0.0.1:3001', trace: 'retain-on-failure' },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'], channel: process.env.ADJUST_BROWSER_CHANNEL } }] });
