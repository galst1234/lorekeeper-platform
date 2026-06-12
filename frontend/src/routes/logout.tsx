import { createFileRoute, redirect } from "@tanstack/react-router";
import { signOut } from "../lib/auth";

export const Route = createFileRoute("/logout")({
  beforeLoad: async ({ context }) => {
    await signOut();
    context.queryClient.clear();
    throw redirect({ to: "/login" });
  },
});
