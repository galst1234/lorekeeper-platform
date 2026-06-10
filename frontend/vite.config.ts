import { sentryVitePlugin } from "@sentry/vite-plugin";
import tanstackRouter from "@tanstack/router-plugin/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [
    tanstackRouter({ routesDirectory: "./src/routes" }),
    react(),
    sentryVitePlugin({
      url: process.env.SENTRY_URL,
      org: process.env.SENTRY_ORG,
      project: process.env.SENTRY_PROJECT,
      authToken: process.env.SENTRY_AUTH_TOKEN,
    }),
  ],
  build: {
    sourcemap: true,
  },
  server: {
    port: 5173,
    proxy: {
      "/auth": "http://localhost:8000",
      "/api": "http://localhost:8000",
    },
  },
});
