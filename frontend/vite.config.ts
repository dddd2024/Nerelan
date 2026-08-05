/// <reference types="vitest" />
import { defineConfig } from "vite";
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
    },
  };
});
