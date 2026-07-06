import { useSuspenseQuery } from "@tanstack/react-query";
import { getRouteApi } from "@tanstack/react-router";
import { getItemOptions } from "@/api/generated/@tanstack/react-query.gen";
import { ItemPageEditor } from "@/components/item/item-page-editor";

const Route = getRouteApi("/campaigns/$slug/items/$itemSlug_/edit");

export function ItemEditPage() {
  const { slug, itemSlug } = Route.useParams();
  const { data: item } = useSuspenseQuery(getItemOptions({ path: { slug, item_slug: itemSlug } }));

  return <ItemPageEditor mode="edit" campaignSlug={slug} item={item} />;
}
