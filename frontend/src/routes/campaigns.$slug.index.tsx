import { useSuspenseQuery } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";
import { campaignQueryOptions } from "@/api/campaigns";
import { meQueryOptions } from "@/api/me";
import { CampaignHeader } from "@/components/campaign/campaign-header";
import { CharactersSection } from "@/components/campaign/characters-section";
import { InvitePlayersCard } from "@/components/campaign/invite-players-card";

export const Route = createFileRoute("/campaigns/$slug/")({
  component: CampaignDetailPage,
});

function CampaignDetailPage() {
  const { slug } = Route.useParams();
  const { data: me } = useSuspenseQuery(meQueryOptions);
  const { data: campaign } = useSuspenseQuery(campaignQueryOptions(me.id, slug));

  return (
    <div className="max-w-4xl mx-auto px-6 py-8 space-y-8">
      <CampaignHeader campaign={campaign} />

      <div id="characters" className="space-y-8">
        <CharactersSection slug={slug} characterType="pc" />
        <CharactersSection slug={slug} characterType="npc" />
      </div>

      {campaign.role === "gm" && <InvitePlayersCard campaignSlug={slug} />}
    </div>
  );
}
