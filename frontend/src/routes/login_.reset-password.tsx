import { createFileRoute } from "@tanstack/react-router";
import { ResetPasswordPage } from "@/pages/reset-password-page";

export const Route = createFileRoute("/login_/reset-password")({
  component: ResetPasswordPage,
});
