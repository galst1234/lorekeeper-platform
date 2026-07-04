import { createFileRoute, redirect } from "@tanstack/react-router";
import { doesSessionExist } from "@/lib/auth";
import { LoginPage } from "@/pages/login-page";

export const Route = createFileRoute("/login")({
  beforeLoad: async () => {
    if (await doesSessionExist()) {
      throw redirect({ to: "/" });
    }
  },
  component: LoginPage,
});
