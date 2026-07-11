import { createFileRoute } from "@tanstack/react-router";
import { ItemsPage } from "@/pages/items-page";

export const Route = createFileRoute("/campaigns/$slug/items/")({
  validateSearch: (search: Record<string, unknown>): { q?: string } => ({
    ...(typeof search.q === "string" && search.q.trim() !== "" ? { q: search.q } : {}),
  }),
  component: ItemsPage,
});
