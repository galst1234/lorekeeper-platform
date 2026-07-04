import { useSuspenseQuery } from "@tanstack/react-query";
import { createFileRoute, redirect } from "@tanstack/react-router";
import { getCampaignOptions } from "@/api/generated/@tanstack/react-query.gen";
import { InvitePlayersCard } from "@/components/campaign/invite-players-card";

export const Route = createFileRoute("/campaigns/$slug/settings")({
  beforeLoad: async ({ context, params }) => {
    const campaign = await context.queryClient.ensureQueryData(getCampaignOptions({ path: { slug: params.slug } }));
    if (campaign.role !== "gm") {
      throw redirect({ to: "/campaigns/$slug", params: { slug: params.slug } });
    }
  },
  component: CampaignSettingsPage,
});

function CampaignSettingsPage() {
  const { slug } = Route.useParams();
  const { data: campaign } = useSuspenseQuery(getCampaignOptions({ path: { slug } }));

  return (
    <div className="max-w-2xl mx-auto px-6 py-8 space-y-6">
      <h1 className="text-2xl font-bold">Settings</h1>
      <InvitePlayersCard campaignSlug={slug} existingInviteCode={campaign.invite_code} />
    </div>
  );
}
