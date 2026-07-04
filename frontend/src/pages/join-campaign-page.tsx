import { getRouteApi } from "@tanstack/react-router";
import { JoinCampaignCard } from "@/components/campaign/join-campaign-card";

const Route = getRouteApi("/campaigns_/$slug/invites/$inviteCode");

export function JoinCampaignPage() {
  const { slug, inviteCode } = Route.useParams();
  const preview = Route.useLoaderData();

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      <JoinCampaignCard campaignName={preview.name} campaignSlug={slug} inviteCode={inviteCode} />
    </div>
  );
}

export function JoinCampaignErrorPage({ error }: { error: unknown }) {
  const isNotFound = error instanceof Error && error.message === "Invite not found";
  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      <div className="text-center space-y-2">
        <h1 className="text-xl font-semibold">{isNotFound ? "Invite Not Found" : "Something Went Wrong"}</h1>
        <p className="text-sm text-muted-foreground">
          {isNotFound
            ? "This invite link is invalid or has been revoked."
            : "An unexpected error occurred. Please try again."}
        </p>
      </div>
    </div>
  );
}
