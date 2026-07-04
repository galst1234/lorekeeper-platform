import { createFileRoute } from "@tanstack/react-router";
import { ChronicleEntryEditPage } from "@/pages/chronicle-entry-edit-page";

export const Route = createFileRoute("/campaigns/$slug/chronicle/$entrySlug_/edit")({
  component: ChronicleEntryEditPage,
});
