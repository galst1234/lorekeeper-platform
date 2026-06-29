import { queryOptions } from "@tanstack/react-query";

export interface Character {
  id: string;
  slug: string;
  name: string;
  character_type: "pc" | "npc";
  description: string | null;
  created_at: string;
  updated_at: string;
}

export interface CreateCharacterData {
  slug: string;
  name: string;
  character_type: "pc" | "npc";
  description?: string;
}

export interface PatchCharacterData {
  name?: string;
  character_type?: "pc" | "npc";
  description?: string | null;
}

async function fetchCharacters(slug: string): Promise<Character[]> {
  const res = await fetch(`/api/v1/campaigns/${slug}/characters`, { credentials: "include" });
  if (!res.ok) throw new Error("Failed to fetch characters");
  return res.json();
}

async function fetchCharacter(slug: string, characterSlug: string): Promise<Character> {
  const res = await fetch(`/api/v1/campaigns/${slug}/characters/${characterSlug}`, { credentials: "include" });
  if (res.status === 404) throw new Error("Character not found");
  if (res.status === 403) throw new Error("Forbidden");
  if (!res.ok) throw new Error("Failed to fetch character");
  return res.json();
}

export const charactersQueryOptions = (slug: string) =>
  queryOptions({
    queryKey: ["characters", slug],
    queryFn: () => fetchCharacters(slug),
    retry: false,
  });

export const characterQueryOptions = (slug: string, characterSlug: string) =>
  queryOptions({
    queryKey: ["characters", slug, characterSlug],
    queryFn: () => fetchCharacter(slug, characterSlug),
    retry: false,
  });

export async function createCharacter(slug: string, data: CreateCharacterData): Promise<Character> {
  const res = await fetch(`/api/v1/campaigns/${slug}/characters`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify(data),
  });
  if (res.status === 409) throw new Error("A character with that slug already exists in this campaign");
  if (!res.ok) throw new Error("Failed to create character");
  return res.json();
}

export async function patchCharacter(
  slug: string,
  characterSlug: string,
  data: PatchCharacterData
): Promise<Character> {
  const res = await fetch(`/api/v1/campaigns/${slug}/characters/${characterSlug}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error("Failed to update character");
  return res.json();
}

export async function deleteCharacter(slug: string, characterSlug: string): Promise<void> {
  const res = await fetch(`/api/v1/campaigns/${slug}/characters/${characterSlug}`, {
    method: "DELETE",
    credentials: "include",
  });
  if (!res.ok) throw new Error("Failed to delete character");
}
