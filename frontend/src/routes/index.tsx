import { createFileRoute, redirect } from "@tanstack/react-router";
import { listCampaignsOptions } from "@/api/generated/@tanstack/react-query.gen";
import { doesSessionExist, getCurrentUserOptions } from "@/lib/auth";
import { HomePage, HomePendingPage } from "@/pages/home-page";

export const Route = createFileRoute("/")({
  beforeLoad: async ({ context }) => {
    if (!(await doesSessionExist())) {
      context.queryClient.clear();
      throw redirect({ to: "/login" });
    }
    const me = await context.queryClient.fetchQuery(getCurrentUserOptions(context.queryClient));
    if (me.display_name === null) {
      throw redirect({ to: "/onboarding" });
    }
    await context.queryClient.ensureQueryData(listCampaignsOptions());
  },
  pendingComponent: HomePendingPage,
  pendingMs: 0,
  component: HomePage,
});
