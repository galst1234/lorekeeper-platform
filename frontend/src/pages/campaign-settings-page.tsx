import { useSuspenseQuery } from "@tanstack/react-query";
import { getRouteApi } from "@tanstack/react-router";
import { getCampaignOptions } from "@/api/generated/@tanstack/react-query.gen";
import { InvitePlayersCard } from "@/components/campaign/invite-players-card";

const Route = getRouteApi("/campaigns/$slug/settings");

export function CampaignSettingsPage() {
  const { slug } = Route.useParams();
  const { data: campaign } = useSuspenseQuery(getCampaignOptions({ path: { slug } }));

  return (
    <div className="max-w-2xl mx-auto px-6 py-8 space-y-6">
      <h1 className="text-2xl font-bold">Settings</h1>
      <InvitePlayersCard campaignSlug={slug} existingInviteCode={campaign.invite_code} />
    </div>
  );
}
