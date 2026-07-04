import { createFileRoute } from "@tanstack/react-router";
import { ItemsPage } from "@/pages/items-page";

export const Route = createFileRoute("/campaigns/$slug/items/")({
  component: ItemsPage,
});
