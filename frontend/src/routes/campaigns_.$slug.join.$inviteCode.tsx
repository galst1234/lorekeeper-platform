import { useMutation } from "@tanstack/react-query";
import { createFileRoute, redirect, useRouter } from "@tanstack/react-router";
import { useState } from "react";
import { meQueryOptions } from "../api/me";
import { fetchJoinPreview, joinCampaign } from "../api/membership";
import { doesSessionExist } from "../lib/auth";

export const Route = createFileRoute("/campaigns_/$slug/join/$inviteCode")({
  beforeLoad: async ({ context, location }) => {
    if (!(await doesSessionExist())) {
      throw redirect({ to: "/login", search: { redirectToPath: location.href } });
    }
    const me = await context.queryClient.fetchQuery(meQueryOptions);
    if (me.display_name === null) {
      throw redirect({ to: "/onboarding" });
    }
  },
  loader: async ({ params }) => {
    return fetchJoinPreview(params.slug, params.inviteCode);
  },
  errorComponent: ({ error }) => {
    const isNotFound = error instanceof Error && error.message === "Invite not found";
    return (
      <main style={{ padding: "2rem" }}>
        <h1>{isNotFound ? "Invite Not Found" : "Something Went Wrong"}</h1>
        <p>
          {isNotFound
            ? "This invite link is invalid or has been revoked."
            : "An unexpected error occurred. Please try again."}
        </p>
      </main>
    );
  },
  component: JoinPage,
});

function JoinPage() {
  const { slug, inviteCode } = Route.useParams();
  const preview = Route.useLoaderData();
  const router = useRouter();
  const [error, setError] = useState("");

  const joinMutation = useMutation({
    mutationFn: () => joinCampaign(slug, inviteCode),
    onSuccess: async (campaign) => {
      await router.navigate({ to: "/campaigns/$slug", params: { slug: campaign.slug } });
    },
    onError: () => setError("Failed to join campaign. The invite link may have been revoked."),
  });

  return (
    <main style={{ padding: "2rem", maxWidth: 480 }}>
      <h1>You've been invited to join {preview.name}</h1>
      <p>Click the button below to join this campaign.</p>
      <button type="button" onClick={() => joinMutation.mutate()} disabled={joinMutation.isPending}>
        {joinMutation.isPending ? "Joining..." : "Join Campaign"}
      </button>
      {error && <p style={{ color: "red" }}>{error}</p>}
    </main>
  );
}
