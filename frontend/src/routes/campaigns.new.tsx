import { useMutation, useQueryClient } from "@tanstack/react-query";
import { createFileRoute, redirect, useRouter } from "@tanstack/react-router";
import { type SyntheticEvent, useEffect, useState } from "react";
import { createCampaign, toSlugLabel } from "../api/campaigns";
import { meQueryOptions } from "../api/me";
import { doesSessionExist } from "../lib/auth";

export const Route = createFileRoute("/campaigns/new")({
  beforeLoad: async ({ context }) => {
    if (!(await doesSessionExist())) {
      throw redirect({ to: "/login" });
    }
    const me = await context.queryClient.fetchQuery(meQueryOptions);
    if (me.display_name === null) {
      throw redirect({ to: "/onboarding" });
    }
  },
  component: NewCampaignPage,
});

function NewCampaignPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [name, setName] = useState("");
  const [slugLabel, setSlugLabel] = useState("");
  const [description, setDescription] = useState("");
  const [slugEdited, setSlugEdited] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!slugEdited) {
      setSlugLabel(toSlugLabel(name));
    }
  }, [name, slugEdited]);

  const mutation = useMutation({
    mutationFn: createCampaign,
    onSuccess: async (campaign) => {
      await queryClient.invalidateQueries({ queryKey: ["campaigns"], refetchType: "all" });
      await router.navigate({ to: "/campaigns/$slug", params: { slug: campaign.slug } });
    },
    onError: () => setError("Something went wrong. Please try again."),
  });

  function handleSubmit(e: SyntheticEvent<HTMLFormElement>) {
    e.preventDefault();
    const trimmedName = name.trim();
    const trimmedSlug = slugLabel.trim();
    if (!trimmedName) {
      setError("Name is required.");
      return;
    }
    if (!trimmedSlug) {
      setError("URL slug is required.");
      return;
    }
    if (!/^[a-z0-9]+(-[a-z0-9]+)*$/.test(trimmedSlug)) {
      setError(
        "URL slug may only contain lowercase letters, numbers, and hyphens, and cannot start or end with a hyphen."
      );
      return;
    }
    if (trimmedSlug.length > 100) {
      setError("URL slug must be 100 characters or fewer.");
      return;
    }
    setError("");
    mutation.mutate({ name: trimmedName, slug_label: trimmedSlug, description: description.trim() || undefined });
  }

  return (
    <main style={{ padding: "2rem", maxWidth: 480 }}>
      <h1>New Campaign</h1>
      <form onSubmit={handleSubmit}>
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
          <label htmlFor="slug" style={{ display: "block", marginBottom: "0.25rem" }}>
            URL slug *
          </label>
          <input
            id="slug"
            type="text"
            value={slugLabel}
            onChange={(e) => {
              setSlugEdited(true);
              setSlugLabel(e.target.value);
            }}
            style={{ display: "block", width: "100%" }}
          />
          <small style={{ color: "#888" }}>
            A unique suffix will be appended automatically — e.g. <code>{slugLabel || "my-campaign"}-xxxxxxxx</code>
          </small>
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

        <button type="submit" disabled={mutation.isPending}>
          {mutation.isPending ? "Creating…" : "Create Campaign"}
        </button>
      </form>
    </main>
  );
}
