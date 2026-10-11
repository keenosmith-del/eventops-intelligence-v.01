import { defineConfig } from "@playwright/test";
const preview = process.env.TEST_PREVIEW === "true";
const previewPort = Number(process.env.TEST_PREVIEW_PORT || 4174);
const localURL = preview ? `http://127.0.0.1:${previewPort}` : "http://127.0.0.1:5174";
export default defineConfig({
  testDir: "./tests/browser",
  timeout: 120000,
  expect: { timeout: 10000 },
  workers: 1,
  use: {
    baseURL: process.env.TEST_BASE_URL || localURL,
    reducedMotion: "reduce",
    channel: process.env.PLAYWRIGHT_CHANNEL || undefined,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  webServer: process.env.TEST_BASE_URL
    ? undefined
    : {
        command: preview ? `npm run preview -- --port ${previewPort}` : "npm run dev",
        url: localURL,
        reuseExistingServer: !preview,
      },
});
