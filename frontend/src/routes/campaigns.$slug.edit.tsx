import { createFileRoute, redirect } from "@tanstack/react-router";
import { getCampaignOptions } from "@/api/generated/@tanstack/react-query.gen";
import { CampaignEditPage } from "@/pages/campaign-edit-page";

export const Route = createFileRoute("/campaigns/$slug/edit")({
  beforeLoad: async ({ context, params }) => {
    const campaign = await context.queryClient.ensureQueryData(getCampaignOptions({ path: { slug: params.slug } }));
    if (campaign.role !== "gm") {
      throw redirect({ to: "/campaigns/$slug", params: { slug: params.slug } });
    }
  },
  component: CampaignEditPage,
});
