import { createFileRoute, redirect } from "@tanstack/react-router";
import { getJoinPreview } from "@/api/generated";
import { getMeOptions } from "@/api/generated/@tanstack/react-query.gen";
import { JoinCampaignCard } from "@/components/campaign/join-campaign-card";
import { doesSessionExist } from "@/lib/auth";

export const Route = createFileRoute("/campaigns_/$slug/invites/$inviteCode")({
  beforeLoad: async ({ context, location }) => {
    if (!(await doesSessionExist())) {
      throw redirect({
        to: "/login",
        search: { redirectToPath: location.pathname + location.searchStr + location.hash },
      });
    }
    const me = await context.queryClient.fetchQuery(getMeOptions());
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
