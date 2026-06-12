import { queryOptions } from "@tanstack/react-query";

export interface Campaign {
  id: string;
  name: string;
  description: string | null;
  slug: string;
  created_at: string;
  updated_at: string;
}

export interface CreateCampaignData {
  name: string;
  description?: string;
  slug_label: string;
}

export interface PatchCampaignData {
  name?: string;
  description?: string | null;
  slug_label?: string;
}

async function fetchCampaigns(): Promise<Campaign[]> {
  const res = await fetch("/api/v1/campaigns", { credentials: "include" });
  if (!res.ok) throw new Error("Failed to fetch campaigns");
  return res.json();
}

async function fetchCampaign(slug: string): Promise<Campaign> {
  const res = await fetch(`/api/v1/campaigns/${slug}`, { credentials: "include" });
  if (res.status === 404) throw new Error("Campaign not found");
  if (res.status === 403) throw new Error("Forbidden");
  if (!res.ok) throw new Error("Failed to fetch campaign");
  return res.json();
}

export const campaignsQueryOptions = (userId: string) =>
  queryOptions({
    queryKey: ["campaigns", userId],
    queryFn: fetchCampaigns,
    retry: false,
  });

export const campaignQueryOptions = (userId: string, slug: string) =>
  queryOptions({
    queryKey: ["campaigns", userId, slug],
    queryFn: () => fetchCampaign(slug),
    retry: false,
  });

export async function createCampaign(data: CreateCampaignData): Promise<Campaign> {
  const res = await fetch("/api/v1/campaigns", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error("Failed to create campaign");
  return res.json();
}

export async function patchCampaign(slug: string, data: PatchCampaignData): Promise<Campaign> {
  const res = await fetch(`/api/v1/campaigns/${slug}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error("Failed to update campaign");
  return res.json();
}

export async function deleteCampaign(slug: string): Promise<void> {
  const res = await fetch(`/api/v1/campaigns/${slug}`, {
    method: "DELETE",
    credentials: "include",
  });
  if (!res.ok) throw new Error("Failed to delete campaign");
}

export function toSlugLabel(name: string): string {
  return name
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}
