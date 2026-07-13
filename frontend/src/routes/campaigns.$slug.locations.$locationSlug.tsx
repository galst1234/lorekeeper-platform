import { createFileRoute } from "@tanstack/react-router";
import { LocationDetailPage } from "@/pages/location-detail-page";

export const Route = createFileRoute("/campaigns/$slug/locations/$locationSlug")({
  component: LocationDetailPage,
});
