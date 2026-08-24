/// <reference types="vitest" />
import { defineConfig } from "vite";
import { configDefaults } from "vitest/config";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import { fileURLToPath } from "node:url";
import { resolve, dirname } from "node:path";

const __dirname = dirname(fileURLToPath(import.meta.url));

export default defineConfig(({ mode }) => {
  const isMock = mode === "mock";
  return {
    base: "/",
    plugins: [react(), tailwindcss()],
    resolve: {
      alias: {
        "@": resolve(__dirname, "src"),
      },
    },
    define: {
      __VITE_MOCK_API__: JSON.stringify(isMock),
    },
    server: {
      port: 4173,
      host: "127.0.0.1",
      strictPort: false,
    },
    build: {
      outDir: "dist",
      sourcemap: true,
    },
    test: {
      environment: "jsdom",
      setupFiles: ["./tests/setup.ts"],
      globals: true,
      testTimeout: 15000,
      // Ordinary Vitest runs own only unit/component suites. Playwright E2E
      // specs under e2e/ are executed exclusively by the dedicated
      // `npm run e2e*` commands and the Frontend Playwright workflow.
      exclude: [...configDefaults.exclude, "**/e2e/**"],
    },
  };
});
