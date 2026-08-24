import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  workers: 1,
  retries: 0,
  timeout: 30_000,
  expect: { timeout: 8_000 },
  forbidOnly: !!process.env.CI,
  snapshotPathTemplate: "{testDir}/snapshots/{projectName}/{arg}{ext}",
  use: {
    baseURL: "http://127.0.0.1:4173",
    channel: "chromium",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    video: "off",
    locale: "zh-CN",
    timezoneId: "UTC",
    colorScheme: "light",
  },
  projects: [
    {
      name: "desktop-chromium",
      use: { ...devices["Desktop Chrome"], viewport: { width: 1440, height: 900 } },
    },
    {
      name: "mobile-chromium",
      use: { ...devices["Pixel 5"], viewport: { width: 390, height: 844 }, deviceScaleFactor: 1, isMobile: true },
    },
  ],
  webServer: {
    command: "npm run dev:mock -- --host 127.0.0.1 --port 4173 --strictPort",
    url: "http://127.0.0.1:4173",
    reuseExistingServer: false,
    timeout: 120_000,
  },
});
