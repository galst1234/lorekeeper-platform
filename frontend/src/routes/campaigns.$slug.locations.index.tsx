import { createFileRoute } from "@tanstack/react-router";
import { LocationsPage } from "@/pages/locations-page";

export const Route = createFileRoute("/campaigns/$slug/locations/")({
  validateSearch: (search: Record<string, unknown>): { q?: string } => ({
    ...(typeof search.q === "string" && search.q.trim() !== "" ? { q: search.q } : {}),
  }),
  component: LocationsPage,
});
