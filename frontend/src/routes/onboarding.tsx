import { createFileRoute, redirect } from "@tanstack/react-router";
import { doesSessionExist, getCurrentUserOptions } from "@/lib/auth";
import { OnboardingPage } from "@/pages/onboarding-page";

export const Route = createFileRoute("/onboarding")({
  validateSearch: (search: Record<string, unknown>): { redirectToPath?: string } => ({
    ...(typeof search.redirectToPath === "string" ? { redirectToPath: search.redirectToPath } : {}),
  }),
  beforeLoad: async ({ context }) => {
    if (!(await doesSessionExist())) {
      context.queryClient.clear();
      throw redirect({ to: "/login" });
    }
    const me = await context.queryClient.fetchQuery(getCurrentUserOptions(context.queryClient));
    if (me.display_name !== null) {
      throw redirect({ to: "/" });
    }
  },
  component: OnboardingPage,
});
