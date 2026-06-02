import { queryOptions } from "@tanstack/react-query";

export interface MeResponse {
  id: string;
  email: string;
  display_name: string | null;
}

async function fetchMe(): Promise<MeResponse> {
  const res = await fetch("/api/v1/me", { credentials: "include" });
  if (res.status === 401) throw new Error("Unauthenticated");
  if (!res.ok) throw new Error("Failed to fetch user");
  return res.json();
}

export const meQueryOptions = queryOptions({
  queryKey: ["me"],
  queryFn: fetchMe,
  retry: false,
});

export async function patchMe(displayName: string): Promise<MeResponse> {
  const res = await fetch("/api/v1/me", {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({ display_name: displayName }),
  });
  if (!res.ok) throw new Error("Failed to update display name");
  return res.json();
}
