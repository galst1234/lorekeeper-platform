import { useSuspenseQuery } from "@tanstack/react-query";
import { createFileRoute, redirect } from "@tanstack/react-router";
import { campaignQueryOptions } from "@/api/campaigns";
import { meQueryOptions } from "@/api/me";
import { InvitePlayersCard } from "@/components/campaign/invite-players-card";

export const Route = createFileRoute("/campaigns/$slug/settings")({
  beforeLoad: async ({ context, params }) => {
    const me = await context.queryClient.ensureQueryData(meQueryOptions);
    const campaign = await context.queryClient.ensureQueryData(campaignQueryOptions(me.id, params.slug));
    if (campaign.role !== "gm") {
      throw redirect({ to: "/campaigns/$slug", params: { slug: params.slug } });
    }
  },
  component: CampaignSettingsPage,
});

function CampaignSettingsPage() {
  const { slug } = Route.useParams();
  const { data: me } = useSuspenseQuery(meQueryOptions);
  const { data: campaign } = useSuspenseQuery(campaignQueryOptions(me.id, slug));

  return (
    <div className="max-w-2xl mx-auto px-6 py-8 space-y-6">
      <h1 className="text-2xl font-bold">Settings</h1>
      <InvitePlayersCard campaignSlug={slug} existingInviteCode={campaign.invite_code} />
    </div>
  );
}
