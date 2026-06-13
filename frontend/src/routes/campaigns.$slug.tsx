import { createFileRoute, Outlet, redirect } from "@tanstack/react-router";
import { campaignQueryOptions } from "../api/campaigns";
import { meQueryOptions } from "../api/me";
import { doesSessionExist } from "../lib/auth";

export const Route = createFileRoute("/campaigns/$slug")({
  beforeLoad: async ({ context, params }) => {
    if (!(await doesSessionExist())) {
      throw redirect({ to: "/login" });
    }
    const me = await context.queryClient.fetchQuery(meQueryOptions);
    if (me.display_name === null) {
      throw redirect({ to: "/onboarding" });
    }
    const campaign = await context.queryClient.ensureQueryData(campaignQueryOptions(me.id, params.slug));
    if (campaign.slug !== params.slug) {
      throw redirect({ to: "/campaigns/$slug", params: { slug: campaign.slug } });
    }
  },
  component: () => <Outlet />,
});
