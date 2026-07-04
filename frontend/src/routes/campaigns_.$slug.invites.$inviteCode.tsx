import { createFileRoute, redirect } from "@tanstack/react-router";
import { getJoinPreview } from "@/api/generated";
import { doesSessionExist, getCurrentUserOptions } from "@/lib/auth";
import { JoinCampaignErrorPage, JoinCampaignPage } from "@/pages/join-campaign-page";

export const Route = createFileRoute("/campaigns_/$slug/invites/$inviteCode")({
  beforeLoad: async ({ context, location }) => {
    if (!(await doesSessionExist())) {
      context.queryClient.clear();
      throw redirect({
        to: "/login",
        search: { redirectToPath: location.pathname + location.searchStr + location.hash },
      });
    }
    const me = await context.queryClient.fetchQuery(getCurrentUserOptions(context.queryClient));
    if (me.display_name === null) {
      throw redirect({
        to: "/onboarding",
        search: { redirectToPath: location.pathname + location.searchStr + location.hash },
      });
    }
  },
  loader: async ({ params }) => {
    const { data, response } = await getJoinPreview({
      path: { slug: params.slug, invite_code: params.inviteCode },
    });
    if (!data) {
      if (response?.status === 404) throw new Error("Invite not found");
      throw new Error("Failed to fetch join preview");
    }
    return data;
  },
  errorComponent: JoinCampaignErrorPage,
  component: JoinCampaignPage,
});
