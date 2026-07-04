import { createFileRoute, redirect } from "@tanstack/react-router";
import { OnboardingForm } from "@/components/onboarding/onboarding-form";
import { doesSessionExist, getCurrentUserOptions } from "@/lib/auth";

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

function OnboardingPage() {
  const { redirectToPath } = Route.useSearch();
  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      <OnboardingForm redirectToPath={redirectToPath} />
    </div>
  );
}
