import { queryOptions } from "@tanstack/react-query";

export interface ChronicleAuthor {
  id: string;
  display_name: string;
}

export interface ChronicleEntry {
  id: string;
  slug: string;
  title: string;
  occurred_at: string;
  body: string | null;
  created_at: string;
  updated_at: string;
}

export interface ChronicleEntryDetail extends ChronicleEntry {
  author: ChronicleAuthor | null;
}

export interface CreateChronicleEntryData {
  slug: string;
  title: string;
  occurred_at: string;
  body?: string;
}

export interface PatchChronicleEntryData {
  title?: string;
  occurred_at?: string;
  body?: string | null;
}

async function fetchChronicleEntries(slug: string): Promise<ChronicleEntry[]> {
  const res = await fetch(`/api/v1/campaigns/${slug}/chronicle/entries`, { credentials: "include" });
  if (!res.ok) throw new Error("Failed to fetch chronicle entries");
  return res.json();
}

async function fetchChronicleEntry(slug: string, entrySlug: string): Promise<ChronicleEntryDetail> {
  const res = await fetch(`/api/v1/campaigns/${slug}/chronicle/entries/${entrySlug}`, { credentials: "include" });
  if (res.status === 404) throw new Error("Chronicle entry not found");
  if (res.status === 403) throw new Error("Forbidden");
  if (!res.ok) throw new Error("Failed to fetch chronicle entry");
  return res.json();
}

export const chronicleEntriesQueryOptions = (slug: string) =>
  queryOptions({
    queryKey: ["chronicle-entries", slug],
    queryFn: () => fetchChronicleEntries(slug),
    retry: false,
  });

export const chronicleEntryQueryOptions = (slug: string, entrySlug: string) =>
  queryOptions({
    queryKey: ["chronicle-entries", slug, entrySlug],
    queryFn: () => fetchChronicleEntry(slug, entrySlug),
    retry: false,
  });

export async function createChronicleEntry(slug: string, data: CreateChronicleEntryData): Promise<ChronicleEntry> {
  const res = await fetch(`/api/v1/campaigns/${slug}/chronicle/entries`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify(data),
  });
  if (res.status === 409) throw new Error("A chronicle entry with that slug already exists in this campaign");
  if (!res.ok) throw new Error("Failed to create chronicle entry");
  return res.json();
}

export async function patchChronicleEntry(
  slug: string,
  entrySlug: string,
  data: PatchChronicleEntryData
): Promise<ChronicleEntry> {
  const res = await fetch(`/api/v1/campaigns/${slug}/chronicle/entries/${entrySlug}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error("Failed to update chronicle entry");
  return res.json();
}

export async function deleteChronicleEntry(slug: string, entrySlug: string): Promise<void> {
  const res = await fetch(`/api/v1/campaigns/${slug}/chronicle/entries/${entrySlug}`, {
    method: "DELETE",
    credentials: "include",
  });
  if (!res.ok) throw new Error("Failed to delete chronicle entry");
}
