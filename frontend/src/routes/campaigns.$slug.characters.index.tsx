import { createFileRoute } from "@tanstack/react-router";
import { CharactersPage } from "@/pages/characters-page";

export const Route = createFileRoute("/campaigns/$slug/characters/")({
  validateSearch: (search: Record<string, unknown>): { q?: string } => ({
    ...(typeof search.q === "string" && search.q.trim() !== "" ? { q: search.q } : {}),
  }),
  component: CharactersPage,
});
