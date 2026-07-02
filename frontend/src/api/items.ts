import { queryOptions } from "@tanstack/react-query";

export interface Item {
  id: string;
  slug: string;
  name: string;
  description: string | null;
  created_at: string;
  updated_at: string;
}

export interface CreateItemData {
  slug: string;
  name: string;
  description?: string;
}

export interface PatchItemData {
  name?: string;
  description?: string | null;
}

async function fetchItems(slug: string): Promise<Item[]> {
  const res = await fetch(`/api/v1/campaigns/${slug}/items`, { credentials: "include" });
  if (!res.ok) throw new Error("Failed to fetch items");
  return res.json();
}

async function fetchItem(slug: string, itemSlug: string): Promise<Item> {
  const res = await fetch(`/api/v1/campaigns/${slug}/items/${itemSlug}`, { credentials: "include" });
  if (res.status === 404) throw new Error("Item not found");
  if (res.status === 403) throw new Error("Forbidden");
  if (!res.ok) throw new Error("Failed to fetch item");
  return res.json();
}

export const itemsQueryOptions = (slug: string) =>
  queryOptions({
    queryKey: ["items", slug],
    queryFn: () => fetchItems(slug),
    retry: false,
  });

export const itemQueryOptions = (slug: string, itemSlug: string) =>
  queryOptions({
    queryKey: ["items", slug, itemSlug],
    queryFn: () => fetchItem(slug, itemSlug),
    retry: false,
  });

export async function createItem(slug: string, data: CreateItemData): Promise<Item> {
  const res = await fetch(`/api/v1/campaigns/${slug}/items`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify(data),
  });
  if (res.status === 409) throw new Error("An item with that slug already exists in this campaign");
  if (!res.ok) throw new Error("Failed to create item");
  return res.json();
}

export async function patchItem(slug: string, itemSlug: string, data: PatchItemData): Promise<Item> {
  const res = await fetch(`/api/v1/campaigns/${slug}/items/${itemSlug}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error("Failed to update item");
  return res.json();
}

export async function deleteItem(slug: string, itemSlug: string): Promise<void> {
  const res = await fetch(`/api/v1/campaigns/${slug}/items/${itemSlug}`, {
    method: "DELETE",
    credentials: "include",
  });
  if (!res.ok) throw new Error("Failed to delete item");
}
