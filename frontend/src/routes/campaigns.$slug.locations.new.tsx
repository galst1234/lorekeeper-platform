import { createFileRoute } from "@tanstack/react-router";
import { LocationNewPage } from "@/pages/location-new-page";

export const Route = createFileRoute("/campaigns/$slug/locations/new")({
  component: LocationNewPage,
});
