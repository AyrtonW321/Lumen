import tailwindcss from "@tailwindcss/vite";
import { defineConfig } from "vitest/config";

// `npm run dev` serves the UI on :5173 and forwards /api to the Python server (python -m lumen).
export default defineConfig({
  plugins: [tailwindcss()],
  server: { proxy: { "/api": "http://127.0.0.1:8765" } },
  build: { outDir: "dist", emptyOutDir: true },
  test: { include: ["src/**/*.test.ts"] },
});
