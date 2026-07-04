import { createFileRoute } from "@tanstack/react-router";
import { LoginCallbackPage } from "@/pages/login-callback-page";

export const Route = createFileRoute("/login_/callback/$provider")({
  component: LoginCallbackPage,
});
