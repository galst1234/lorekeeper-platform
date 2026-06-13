import { useMutation, useQueryClient, useSuspenseQuery } from "@tanstack/react-query";
import { createFileRoute, useRouter } from "@tanstack/react-router";
import { type SyntheticEvent, useEffect, useState } from "react";
import { campaignQueryOptions, deleteCampaign, patchCampaign } from "../api/campaigns";
import { meQueryOptions } from "../api/me";
import { generateInvite, revokeInvite } from "../api/membership";

export const Route = createFileRoute("/campaigns/$slug/")({
  component: CampaignDetailPage,
});

function CampaignDetailPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const { slug } = Route.useParams();
  const { data: me } = useSuspenseQuery(meQueryOptions);
  const { data: campaign } = useSuspenseQuery(campaignQueryOptions(me.id, slug));
  const [editing, setEditing] = useState(false);
  const [name, setName] = useState(campaign.name);
  const [description, setDescription] = useState(campaign.description ?? "");
  const [error, setError] = useState("");
  const [inviteUrl, setInviteUrl] = useState<string | null>(null);
  const [inviteError, setInviteError] = useState("");

  const isOwner = campaign.role === "gm";

  useEffect(() => {
    if (!editing) {
      setName(campaign.name);
      setDescription(campaign.description ?? "");
    }
  }, [campaign.name, campaign.description, editing]);

  const patchMutation = useMutation({
    mutationFn: (data: { name: string; description: string | null }) =>
      patchCampaign(campaign.slug, { name: data.name, description: data.description }),
    onSuccess: async (updated) => {
      await queryClient.invalidateQueries({ queryKey: ["campaigns"], refetchType: "all" });
      setEditing(false);
      if (updated.slug !== slug) {
        await router.navigate({ to: "/campaigns/$slug", params: { slug: updated.slug } });
      }
    },
    onError: () => setError("Failed to save. Please try again."),
  });

  const deleteMutation = useMutation({
    mutationFn: () => deleteCampaign(campaign.slug),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["campaigns"], refetchType: "all" });
      await router.navigate({ to: "/", replace: true });
    },
    onError: () => setError("Failed to delete. Please try again."),
  });

  const generateInviteMutation = useMutation({
    mutationFn: () => generateInvite(campaign.slug),
    onSuccess: (data) => {
      setInviteUrl(`${window.location.origin}${data.invite_url}`);
      setInviteError("");
    },
    onError: () => setInviteError("Failed to generate invite link."),
  });

  const revokeInviteMutation = useMutation({
    mutationFn: () => revokeInvite(campaign.slug),
    onSuccess: () => {
      setInviteUrl(null);
      setInviteError("");
    },
    onError: () => setInviteError("Failed to revoke invite link."),
  });

  function handleSave(e: SyntheticEvent<HTMLFormElement>) {
    e.preventDefault();
    const trimmedName = name.trim();
    if (!trimmedName) {
      setError("Name is required.");
      return;
    }
    setError("");
    patchMutation.mutate({ name: trimmedName, description: description.trim() || null });
  }

  function handleDelete() {
    if (window.confirm(`Delete "${campaign.name}"? This cannot be undone.`)) {
      deleteMutation.mutate();
    }
  }

  if (editing) {
    return (
      <main style={{ padding: "2rem", maxWidth: 480 }}>
        <h1>Edit Campaign</h1>
        <form onSubmit={handleSave}>
          <div style={{ marginBottom: "1rem" }}>
            <label htmlFor="name" style={{ display: "block", marginBottom: "0.25rem" }}>
              Name *
            </label>
            <input
              id="name"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              style={{ display: "block", width: "100%" }}
            />
          </div>

          <div style={{ marginBottom: "1rem" }}>
            <label htmlFor="description" style={{ display: "block", marginBottom: "0.25rem" }}>
              Description
            </label>
            <textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
              style={{ display: "block", width: "100%" }}
            />
          </div>

          {error && <p style={{ color: "red" }}>{error}</p>}

          <div style={{ display: "flex", gap: "0.5rem" }}>
            <button type="submit" disabled={patchMutation.isPending}>
              {patchMutation.isPending ? "Saving..." : "Save"}
            </button>
            <button
              type="button"
              onClick={() => {
                setName(campaign.name);
                setDescription(campaign.description ?? "");
                setEditing(false);
              }}
              disabled={patchMutation.isPending}
            >
              Cancel
            </button>
          </div>
        </form>
      </main>
    );
  }

  return (
    <main style={{ padding: "2rem" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <h1 style={{ margin: 0 }}>{campaign.name}</h1>
        {isOwner && (
          <div style={{ display: "flex", gap: "0.5rem" }}>
            <button type="button" onClick={() => setEditing(true)} disabled={deleteMutation.isPending}>
              Edit
            </button>
            <button type="button" onClick={handleDelete} disabled={deleteMutation.isPending} style={{ color: "red" }}>
              {deleteMutation.isPending ? "Deleting..." : "Delete"}
            </button>
          </div>
        )}
      </div>

      {campaign.description && <p style={{ marginTop: "1rem", color: "#555" }}>{campaign.description}</p>}

      {error && <p style={{ color: "red" }}>{error}</p>}

      <div
        style={{
          marginTop: "2rem",
          padding: "2rem",
          background: "#f9f9f9",
          borderRadius: "8px",
          color: "#999",
          textAlign: "center",
        }}
      >
        Campaign content coming soon
      </div>

      {isOwner && (
        <div style={{ marginTop: "2rem" }}>
          <h2>Invite Players</h2>
          {inviteUrl ? (
            <div>
              <p>Share this link with players:</p>
              <code
                style={{
                  display: "block",
                  padding: "0.5rem",
                  background: "#f0f0f0",
                  borderRadius: "4px",
                  wordBreak: "break-all",
                }}
              >
                {inviteUrl}
              </code>
              <button
                type="button"
                onClick={() => revokeInviteMutation.mutate()}
                disabled={revokeInviteMutation.isPending}
                style={{ marginTop: "0.5rem", color: "red" }}
              >
                {revokeInviteMutation.isPending ? "Revoking..." : "Revoke Invite Link"}
              </button>
            </div>
          ) : (
            <button
              type="button"
              onClick={() => generateInviteMutation.mutate()}
              disabled={generateInviteMutation.isPending}
            >
              {generateInviteMutation.isPending ? "Generating..." : "Generate Invite Link"}
            </button>
          )}
          {inviteError && <p style={{ color: "red" }}>{inviteError}</p>}
        </div>
      )}
    </main>
  );
}
