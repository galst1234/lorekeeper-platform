import { useMutation, useQueryClient, useSuspenseQuery } from "@tanstack/react-query";
import { createFileRoute, Link, useRouter } from "@tanstack/react-router";
import { type SyntheticEvent, useEffect, useState } from "react";
import { campaignQueryOptions, deleteCampaign, patchCampaign } from "../api/campaigns";
import { type Character, charactersQueryOptions, createCharacter } from "../api/characters";
import { meQueryOptions } from "../api/me";
import { generateInvite, revokeInvite } from "../api/membership";

export const Route = createFileRoute("/campaigns/$slug/")({
  component: CampaignDetailPage,
});

type AddingFor = "pc" | "npc" | null;

function CharacterSection({
  title,
  characters,
  slug,
  characterType,
}: {
  title: string;
  characters: Character[];
  slug: string;
  characterType: "pc" | "npc";
}) {
  const queryClient = useQueryClient();
  const [addingFor, setAddingFor] = useState<AddingFor>(null);
  const [newName, setNewName] = useState("");
  const [newType, setNewType] = useState<"pc" | "npc">(characterType);
  const [newDescription, setNewDescription] = useState("");
  const [addError, setAddError] = useState("");

  const createMutation = useMutation({
    mutationFn: (data: { name: string; character_type: "pc" | "npc"; description?: string }) =>
      createCharacter(slug, data),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["characters", slug] });
      setAddingFor(null);
      setNewName("");
      setNewDescription("");
      setAddError("");
    },
    onError: () => setAddError("Failed to create character. Please try again."),
  });

  function handleAdd(event: SyntheticEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmedName = newName.trim();
    if (!trimmedName) {
      setAddError("Name is required.");
      return;
    }
    setAddError("");
    createMutation.mutate({
      name: trimmedName,
      character_type: newType,
      description: newDescription.trim() || undefined,
    });
  }

  function openAddForm() {
    setNewType(characterType);
    setNewName("");
    setNewDescription("");
    setAddError("");
    setAddingFor(characterType);
  }

  return (
    <div style={{ marginBottom: "2rem" }}>
      <h2>{title}</h2>
      {characters.length === 0 ? (
        <p style={{ color: "#999" }}>No {characterType === "pc" ? "player characters" : "NPCs"} yet.</p>
      ) : (
        <ul style={{ paddingLeft: "1.25rem" }}>
          {characters.map((character) => (
            <li key={character.id}>
              <Link to="/campaigns/$slug/characters/$characterId" params={{ slug, characterId: character.id }}>
                {character.name}
              </Link>
            </li>
          ))}
        </ul>
      )}

      {addingFor === characterType ? (
        <form onSubmit={handleAdd} style={{ marginTop: "1rem" }}>
          <div style={{ marginBottom: "0.5rem" }}>
            <label htmlFor={`name-${characterType}`} style={{ display: "block", marginBottom: "0.25rem" }}>
              Name *
            </label>
            <input
              id={`name-${characterType}`}
              type="text"
              value={newName}
              onChange={(event) => setNewName(event.target.value)}
              style={{ display: "block", width: "100%" }}
            />
          </div>
          <div style={{ marginBottom: "0.5rem" }}>
            <label htmlFor={`type-${characterType}`} style={{ display: "block", marginBottom: "0.25rem" }}>
              Type
            </label>
            <select
              id={`type-${characterType}`}
              value={newType}
              onChange={(event) => setNewType(event.target.value as "pc" | "npc")}
              style={{ display: "block" }}
            >
              <option value="pc">PC</option>
              <option value="npc">NPC</option>
            </select>
          </div>
          <div style={{ marginBottom: "0.5rem" }}>
            <label htmlFor={`desc-${characterType}`} style={{ display: "block", marginBottom: "0.25rem" }}>
              Description
            </label>
            <textarea
              id={`desc-${characterType}`}
              value={newDescription}
              onChange={(event) => setNewDescription(event.target.value)}
              rows={2}
              style={{ display: "block", width: "100%" }}
            />
          </div>
          {addError && <p style={{ color: "red" }}>{addError}</p>}
          <div style={{ display: "flex", gap: "0.5rem" }}>
            <button type="submit" disabled={createMutation.isPending}>
              {createMutation.isPending ? "Adding..." : "Add"}
            </button>
            <button type="button" onClick={() => setAddingFor(null)} disabled={createMutation.isPending}>
              Cancel
            </button>
          </div>
        </form>
      ) : (
        <button type="button" onClick={openAddForm} style={{ marginTop: "0.5rem" }}>
          + Add {characterType === "pc" ? "Player Character" : "NPC"}
        </button>
      )}
    </div>
  );
}

function CampaignDetailPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const { slug } = Route.useParams();
  const { data: me } = useSuspenseQuery(meQueryOptions);
  const { data: campaign } = useSuspenseQuery(campaignQueryOptions(me.id, slug));
  const { data: characters } = useSuspenseQuery(charactersQueryOptions(slug));
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

  function handleSave(event: SyntheticEvent<HTMLFormElement>) {
    event.preventDefault();
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

  const playerCharacters = characters.filter((character) => character.character_type === "pc");
  const npcs = characters.filter((character) => character.character_type === "npc");

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
              onChange={(event) => setName(event.target.value)}
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
              onChange={(event) => setDescription(event.target.value)}
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

      <div style={{ marginTop: "2rem" }}>
        <CharacterSection title="Player Characters" characters={playerCharacters} slug={slug} characterType="pc" />
        <CharacterSection title="NPCs" characters={npcs} slug={slug} characterType="npc" />
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
