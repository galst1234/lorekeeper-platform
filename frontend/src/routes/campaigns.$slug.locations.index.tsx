import { createFileRoute } from "@tanstack/react-router";
import { LocationsPage } from "@/pages/locations-page";

export const Route = createFileRoute("/campaigns/$slug/locations/")({
  validateSearch: (search: Record<string, unknown>): { active_only?: boolean } => ({
    ...(search.active_only === true || search.active_only === "true" ? { active_only: true } : {}),
  }),
  component: LocationsPage,
});
