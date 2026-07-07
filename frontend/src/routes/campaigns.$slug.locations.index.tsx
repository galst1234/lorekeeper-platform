import { createFileRoute } from "@tanstack/react-router";
import { LocationsPage } from "@/pages/locations-page";

export const Route = createFileRoute("/campaigns/$slug/locations/")({
  component: LocationsPage,
});
