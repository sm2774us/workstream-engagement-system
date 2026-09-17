import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// WES UI dev server: proxies /api to the FastAPI backend so the browser
// never needs CORS-exempt origins beyond localhost during local dev.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": "http://localhost:8000",
    },
  },
});
