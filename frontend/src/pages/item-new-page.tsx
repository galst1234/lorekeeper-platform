import { getRouteApi } from "@tanstack/react-router";
import { ItemPageEditor } from "@/components/item/item-page-editor";

const Route = getRouteApi("/campaigns/$slug/items/new");

export function ItemNewPage() {
  const { slug } = Route.useParams();
  return <ItemPageEditor mode="create" campaignSlug={slug} />;
}
