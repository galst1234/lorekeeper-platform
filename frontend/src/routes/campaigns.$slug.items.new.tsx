import { createFileRoute } from "@tanstack/react-router";
import { ItemNewPage } from "@/pages/item-new-page";

export const Route = createFileRoute("/campaigns/$slug/items/new")({
  component: ItemNewPage,
});
