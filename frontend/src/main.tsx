import "./index.css";
import * as Sentry from "@sentry/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { RouterProvider } from "@tanstack/react-router";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { initSuperTokens } from "./lib/auth";
import { createAppRouter } from "./router";

Sentry.init({
  dsn: window.__env__?.SENTRY_DSN,
  sendDefaultPii: true,
  tracesSampleRate: 1.0,
  integrations: [Sentry.browserTracingIntegration(), Sentry.replayIntegration()],
  replaysSessionSampleRate: 0.1,
  replaysOnErrorSampleRate: 1.0,
  enableLogs: true,
});

initSuperTokens();

const queryClient = new QueryClient();
const router = createAppRouter(queryClient);

// biome-ignore lint/style/noNonNullAssertion: root element is guaranteed by index.html
createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <Sentry.ErrorBoundary fallback={<p>Something went wrong.</p>}>
      <QueryClientProvider client={queryClient}>
        <RouterProvider router={router} />
      </QueryClientProvider>
    </Sentry.ErrorBoundary>
  </StrictMode>
);
