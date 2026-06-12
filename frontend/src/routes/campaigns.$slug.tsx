import { useMutation, useQueryClient, useSuspenseQuery } from "@tanstack/react-query";
import { createFileRoute, redirect, useRouter } from "@tanstack/react-router";
import { type SyntheticEvent, useState } from "react";
import { campaignQueryOptions, deleteCampaign, patchCampaign } from "../api/campaigns";
import { meQueryOptions } from "../api/me";
import { doesSessionExist } from "../lib/auth";

export const Route = createFileRoute("/campaigns/$slug")({
  beforeLoad: async ({ context, params }) => {
    if (!(await doesSessionExist())) {
      throw redirect({ to: "/login" });
    }
    const me = await context.queryClient.ensureQueryData(meQueryOptions);
    if (me.display_name === null) {
      throw redirect({ to: "/onboarding" });
    }
    const campaign = await context.queryClient.ensureQueryData(campaignQueryOptions(params.slug));
    if (campaign.slug !== params.slug) {
      throw redirect({ to: "/campaigns/$slug", params: { slug: campaign.slug } });
    }
  },
  component: CampaignDetailPage,
});

function CampaignDetailPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const { slug } = Route.useParams();
  const { data: campaign } = useSuspenseQuery(campaignQueryOptions(slug));
  const [editing, setEditing] = useState(false);
  const [name, setName] = useState(campaign.name);
  const [description, setDescription] = useState(campaign.description ?? "");
  const [error, setError] = useState("");

  const patchMutation = useMutation({
    mutationFn: (data: { name: string; description: string | null }) =>
      patchCampaign(campaign.slug, { name: data.name, description: data.description }),
    onSuccess: async (updated) => {
      await queryClient.invalidateQueries({ queryKey: ["campaigns"] });
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
      await queryClient.invalidateQueries({ queryKey: ["campaigns"] });
      await router.navigate({ to: "/" });
    },
    onError: () => setError("Failed to delete. Please try again."),
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
        <div style={{ display: "flex", gap: "0.5rem" }}>
          <button type="button" onClick={() => setEditing(true)} disabled={deleteMutation.isPending}>
            Edit
          </button>
          <button type="button" onClick={handleDelete} disabled={deleteMutation.isPending} style={{ color: "red" }}>
            {deleteMutation.isPending ? "Deleting..." : "Delete"}
          </button>
        </div>
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
    </main>
  );
}
