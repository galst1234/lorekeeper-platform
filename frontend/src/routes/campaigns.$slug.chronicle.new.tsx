import { createFileRoute } from "@tanstack/react-router";
import { ChronicleEntryNewPage } from "@/pages/chronicle-entry-new-page";

export const Route = createFileRoute("/campaigns/$slug/chronicle/new")({
  component: ChronicleEntryNewPage,
});
