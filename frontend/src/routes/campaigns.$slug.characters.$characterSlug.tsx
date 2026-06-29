import { useMutation, useQueryClient, useSuspenseQuery } from "@tanstack/react-query";
import { createFileRoute, useRouter } from "@tanstack/react-router";
import { type SyntheticEvent, useEffect, useState } from "react";
import { characterQueryOptions, deleteCharacter, patchCharacter } from "../api/characters";

export const Route = createFileRoute("/campaigns/$slug/characters/$characterSlug")({
  component: CharacterDetailPage,
});

function CharacterDetailPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const { slug, characterSlug } = Route.useParams();
  const { data: character } = useSuspenseQuery(characterQueryOptions(slug, characterSlug));
  const [editing, setEditing] = useState(false);
  const [name, setName] = useState(character.name);
  const [characterType, setCharacterType] = useState<"pc" | "npc">(character.character_type);
  const [description, setDescription] = useState(character.description ?? "");
  const [error, setError] = useState("");

  useEffect(() => {
    if (!editing) {
      setName(character.name);
      setCharacterType(character.character_type);
      setDescription(character.description ?? "");
    }
  }, [character.name, character.character_type, character.description, editing]);

  const patchMutation = useMutation({
    mutationFn: (data: { name: string; character_type: "pc" | "npc"; description: string | null }) =>
      patchCharacter(slug, characterSlug, data),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["characters", slug] });
      setEditing(false);
    },
    onError: () => setError("Failed to save. Please try again."),
  });

  const deleteMutation = useMutation({
    mutationFn: () => deleteCharacter(slug, characterSlug),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["characters", slug] });
      await router.navigate({ to: "/campaigns/$slug", params: { slug } });
    },
    onError: () => setError("Failed to delete. Please try again."),
  });

  function handleSave(event: SyntheticEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmedName = name.trim();
    if (!trimmedName) {
      setError("Name is required.");
      return;
    }
    setError("");
    patchMutation.mutate({
      name: trimmedName,
      character_type: characterType,
      description: description.trim() || null,
    });
  }

  function handleDelete() {
    if (window.confirm(`Delete "${character.name}"? This cannot be undone.`)) {
      deleteMutation.mutate();
    }
  }

  if (editing) {
    return (
      <main style={{ padding: "2rem", maxWidth: 480 }}>
        <h1>Edit Character</h1>
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
            <label htmlFor="character-type" style={{ display: "block", marginBottom: "0.25rem" }}>
              Type
            </label>
            <select
              id="character-type"
              value={characterType}
              onChange={(event) => setCharacterType(event.target.value as "pc" | "npc")}
              style={{ display: "block" }}
            >
              <option value="pc">PC</option>
              <option value="npc">NPC</option>
            </select>
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
                setName(character.name);
                setCharacterType(character.character_type);
                setDescription(character.description ?? "");
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
        <h1 style={{ margin: 0 }}>{character.name}</h1>
        <div style={{ display: "flex", gap: "0.5rem" }}>
          <button type="button" onClick={() => setEditing(true)} disabled={deleteMutation.isPending}>
            Edit
          </button>
          <button type="button" onClick={handleDelete} disabled={deleteMutation.isPending} style={{ color: "red" }}>
            {deleteMutation.isPending ? "Deleting..." : "Delete"}
          </button>
        </div>
      </div>

      <div style={{ marginTop: "0.5rem" }}>
        <span
          style={{
            display: "inline-block",
            padding: "0.2rem 0.5rem",
            background: character.character_type === "pc" ? "#e0f0ff" : "#f0ffe0",
            borderRadius: "4px",
            fontSize: "0.875rem",
            fontWeight: 500,
          }}
        >
          {character.character_type === "pc" ? "PC" : "NPC"}
        </span>
      </div>

      {character.description && <p style={{ marginTop: "1rem", color: "#555" }}>{character.description}</p>}

      {error && <p style={{ color: "red" }}>{error}</p>}
    </main>
  );
}
