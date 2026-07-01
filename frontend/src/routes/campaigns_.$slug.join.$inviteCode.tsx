import { createFileRoute, redirect } from "@tanstack/react-router";
import { meQueryOptions } from "@/api/me";
import { fetchJoinPreview } from "@/api/membership";
import { JoinCampaignCard } from "@/components/campaign/join-campaign-card";
import { doesSessionExist } from "@/lib/auth";

export const Route = createFileRoute("/campaigns_/$slug/join/$inviteCode")({
  beforeLoad: async ({ context, location }) => {
    if (!(await doesSessionExist())) {
      throw redirect({
        to: "/login",
        search: { redirectToPath: location.pathname + location.searchStr + location.hash },
      });
    }
    const me = await context.queryClient.fetchQuery(meQueryOptions);
    if (me.display_name === null) {
      throw redirect({
        to: "/onboarding",
        search: { redirectToPath: location.pathname + location.searchStr + location.hash },
      });
    }
  },
  loader: async ({ params }) => {
    return fetchJoinPreview(params.slug, params.inviteCode);
  },
  errorComponent: ({ error }) => {
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
  },
  component: JoinPage,
});

function JoinPage() {
  const { slug, inviteCode } = Route.useParams();
  const preview = Route.useLoaderData();

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      <JoinCampaignCard campaignName={preview.name} campaignSlug={slug} inviteCode={inviteCode} />
    </div>
  );
}
