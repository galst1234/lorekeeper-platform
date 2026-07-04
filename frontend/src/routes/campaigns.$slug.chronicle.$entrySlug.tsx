import { createFileRoute } from "@tanstack/react-router";
import { ChronicleEntryDetailPage } from "@/pages/chronicle-entry-detail-page";

export const Route = createFileRoute("/campaigns/$slug/chronicle/$entrySlug")({
  component: ChronicleEntryDetailPage,
});
