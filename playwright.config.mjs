import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  testMatch: 'e2e.spec.mjs',
  fullyParallel: false,
  workers: 1,
  timeout: 45_000,
  expect: { timeout: 12_000 },
  reporter: 'list',
  use: {
    baseURL: 'http://localhost:18765',
    headless: true,
    launchOptions: {
      ...(process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE ? { executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE } : {}),
      args: ['--autoplay-policy=no-user-gesture-required', '--allow-loopback-in-peer-connection', '--disable-features=WebRtcHideLocalIpsWithMdns'],
    },
  },
  webServer: {
    command: `${process.platform === 'win32' ? 'python' : 'python3'} server.py`,
    url: 'http://127.0.0.1:18765/health',
    reuseExistingServer: false,
    env: { TABTELLY_PORT: '18765', TABTELLY_BIND: '127.0.0.1', TABTELLY_LAN_IP: '127.0.0.1', TABTELLY_RUNTIME_DIR: '.run/e2e' },
  },
});
