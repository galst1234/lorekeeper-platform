import { createFileRoute } from "@tanstack/react-router";
import { ItemDetailPage } from "@/pages/item-detail-page";

export const Route = createFileRoute("/campaigns/$slug/items/$itemSlug")({
  component: ItemDetailPage,
});
