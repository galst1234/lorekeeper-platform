import { createFileRoute } from "@tanstack/react-router";
import { ItemEditPage } from "@/pages/item-edit-page";

export const Route = createFileRoute("/campaigns/$slug/items/$itemSlug_/edit")({
  component: ItemEditPage,
});
