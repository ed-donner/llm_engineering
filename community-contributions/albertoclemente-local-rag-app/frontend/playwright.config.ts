import { defineConfig, devices } from '@playwright/test'

const enableWebServers = process.env.PW_WEB_SERVERS !== '0'

export default defineConfig({
  testDir: './tests',
  fullyParallel: true,
  use: {
    baseURL: 'http://127.0.0.1:3000',
    headless: true,
  },
  // Start and reuse local dev servers for E2E tests unless disabled via PW_WEB_SERVERS=0
  webServer: enableWebServers
    ? [
        {
          command:
            '/Users/alberto/projects/RAG_APP/backend/venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000',
          url: 'http://127.0.0.1:8000/health',
          reuseExistingServer: true,
          timeout: 120_000,
          cwd: '/Users/alberto/projects/RAG_APP/backend',
        },
        {
          command: 'npm run dev',
          url: 'http://localhost:3000',
          reuseExistingServer: true,
          timeout: 120_000,
          cwd: '/Users/alberto/projects/RAG_APP/frontend',
        },
      ]
    : undefined,
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
})
