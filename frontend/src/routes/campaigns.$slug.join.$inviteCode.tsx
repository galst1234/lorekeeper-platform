import { useMutation } from "@tanstack/react-query";
import { createFileRoute, useRouter } from "@tanstack/react-router";
import { useState } from "react";
import { fetchJoinPreview, joinCampaign } from "../api/membership";

export const Route = createFileRoute("/campaigns/$slug/join/$inviteCode")({
  loader: async ({ params }) => {
    return fetchJoinPreview(params.slug, params.inviteCode);
  },
  errorComponent: ({ error }) => (
    <main style={{ padding: "2rem" }}>
      <h1>Invite Not Found</h1>
      <p>{error instanceof Error ? error.message : "This invite link is invalid or has been revoked."}</p>
    </main>
  ),
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
