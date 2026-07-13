import { createFileRoute } from "@tanstack/react-router";
import { LocationEditPage } from "@/pages/location-edit-page";

export const Route = createFileRoute("/campaigns/$slug/locations/$locationSlug_/edit")({
  component: LocationEditPage,
});
