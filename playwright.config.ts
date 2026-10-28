import { defineConfig } from "@playwright/test";

/**
 * E2E smoke test against a running app + worker in mock-LLM mode:
 *   LLM_PROVIDER=mock pnpm build && pnpm start & pnpm worker &
 *   E2E_EMAIL=… E2E_PASSWORD=… pnpm test:e2e
 */
export default defineConfig({
  testDir: "tests/e2e",
  timeout: 180_000,
  use: { baseURL: process.env.E2E_BASE_URL ?? "http://localhost:3000", screenshot: "only-on-failure" },
  reporter: [["list"]],
});
