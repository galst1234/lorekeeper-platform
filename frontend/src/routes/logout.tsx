import { createFileRoute, redirect } from "@tanstack/react-router";
import { signOut } from "../lib/auth";

export const Route = createFileRoute("/logout")({
  beforeLoad: async () => {
    await signOut();
    throw redirect({ to: "/login" });
  },
});
