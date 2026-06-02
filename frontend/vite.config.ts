import tanstackRouter from "@tanstack/router-plugin/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [tanstackRouter({ routesDirectory: "./src/routes" }), react()],
  server: {
    port: 5173,
    proxy: {
      "/auth": "http://localhost:8000",
      "/api": "http://localhost:8000",
    },
  },
});
