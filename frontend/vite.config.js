import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const target = process.env.API_PROXY_TARGET || "http://127.0.0.1:5051";
const proxy = {
  "/api": {
    target,
    changeOrigin: true,
    timeout: 90000,
  },
  "/health": { target, changeOrigin: true },
};
export default defineConfig({
  plugins: [react()],
  server: { port: 5174, strictPort: true, proxy },
  preview: { port: 4174, strictPort: true, proxy },
  test: { include: ["tests/**/*.test.js"] },
});
