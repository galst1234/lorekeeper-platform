import { queryOptions } from "@tanstack/react-query";
import type { Campaign } from "./campaigns";

export interface MemberResponse {
  user_id: string;
  display_name: string | null;
  role: "gm" | "player";
  joined_at: string;
}

export interface InviteResponse {
  invite_code: string;
  invite_url: string;
}

export interface JoinPreviewResponse {
  name: string;
  slug: string;
}

async function fetchMembers(slug: string): Promise<MemberResponse[]> {
  const res = await fetch(`/api/v1/campaigns/${slug}/members`, { credentials: "include" });
  if (!res.ok) throw new Error("Failed to fetch members");
  return res.json();
}

export const membersQueryOptions = (slug: string) =>
  queryOptions({
    queryKey: ["members", slug],
    queryFn: () => fetchMembers(slug),
    retry: false,
  });

export async function generateInvite(slug: string): Promise<InviteResponse> {
  const res = await fetch(`/api/v1/campaigns/${slug}/invites`, {
    method: "POST",
    credentials: "include",
  });
  if (!res.ok) throw new Error("Failed to generate invite");
  return res.json();
}

export async function revokeInvite(slug: string): Promise<void> {
  const res = await fetch(`/api/v1/campaigns/${slug}/invites`, {
    method: "DELETE",
    credentials: "include",
  });
  if (!res.ok) throw new Error("Failed to revoke invite");
}

export async function fetchJoinPreview(slug: string, inviteCode: string): Promise<JoinPreviewResponse> {
  const res = await fetch(`/api/v1/campaigns/${slug}/join/${inviteCode}`, {
    credentials: "include",
  });
  if (res.status === 404) throw new Error("Invite not found");
  if (!res.ok) throw new Error("Failed to fetch join preview");
  return res.json();
}

export async function joinCampaign(slug: string, inviteCode: string): Promise<Campaign> {
  const res = await fetch(`/api/v1/campaigns/${slug}/join/${inviteCode}`, {
    method: "POST",
    credentials: "include",
  });
  if (res.status === 404) throw new Error("Invite not found");
  if (!res.ok) throw new Error("Failed to join campaign");
  return res.json();
}
