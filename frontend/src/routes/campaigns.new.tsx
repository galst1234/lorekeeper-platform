import { createFileRoute, redirect } from "@tanstack/react-router";
import { doesSessionExist, getCurrentUserOptions } from "@/lib/auth";
import { NewCampaignPage } from "@/pages/new-campaign-page";

export const Route = createFileRoute("/campaigns/new")({
  beforeLoad: async ({ context }) => {
    if (!(await doesSessionExist())) {
      context.queryClient.clear();
      throw redirect({ to: "/login" });
    }
    const me = await context.queryClient.fetchQuery(getCurrentUserOptions(context.queryClient));
    if (me.display_name === null) {
      throw redirect({ to: "/onboarding" });
    }
  },
  component: NewCampaignPage,
});
