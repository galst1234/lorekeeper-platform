import { useSuspenseQuery } from "@tanstack/react-query";
import { createFileRoute, Link } from "@tanstack/react-router";
import { itemQueryOptions } from "@/api/items";
import { ItemInfo } from "@/components/item/item-info";
import { ItemSidebarCard } from "@/components/item/item-sidebar-card";

export const Route = createFileRoute("/campaigns/$slug/items/$itemSlug")({
  component: ItemDetailPage,
});

function ItemDetailPage() {
  const { slug, itemSlug } = Route.useParams();
  const { data: item } = useSuspenseQuery(itemQueryOptions(slug, itemSlug));

  return (
    <div className="max-w-4xl mx-auto px-6 py-8">
      <Link
        to="/campaigns/$slug/items"
        params={{ slug }}
        className="text-sm text-muted-foreground hover:text-foreground inline-block mb-6"
      >
        ← Back to Items
      </Link>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        <div className="md:col-span-2">
          <ItemInfo item={item} campaignSlug={slug} />
        </div>
        <div>
          <ItemSidebarCard item={item} />
        </div>
      </div>
    </div>
  );
}
