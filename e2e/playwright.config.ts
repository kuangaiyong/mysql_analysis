import { defineConfig, devices } from '@playwright/test';

export default defineConfig({

  testDir: './src/tests',

  timeout: 30 * 1000,
  expect: {
    timeout: 5 * 1000
  },

  fullyParallel: true,
  workers: process.env.CI ? 4 : 2,

  retries: process.env.CI ? 2 : 0,

  reporter: [
    ['html', { outputFolder: 'playwright-report' }],
    ['json', { outputFile: 'test-results/results.json' }],
    ['junit', { outputFile: 'test-results/junit.xml' }]
  ],

  use: {
    baseURL: process.env.BASE_URL || 'http://localhost:5173',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',

    viewport: { width: 1280, height: 720 },
    ignoreHTTPSErrors: true,
    locale: 'zh-CN',
    timezoneId: 'Asia/Shanghai'
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    }
  ],

  webServer: [
    {
      command: 'cd ../backend && python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000',
      port: 8000,
      timeout: 120 * 1000,
      reuseExistingServer: !process.env.CI
    },
    {
      command: 'cd ../frontend && npm run dev',
      port: 5173,
      timeout: 60 * 1000,
      reuseExistingServer: !process.env.CI
    }
  ]
});
