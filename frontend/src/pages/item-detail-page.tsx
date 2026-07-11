import { useSuspenseQuery } from "@tanstack/react-query";
import { getRouteApi, Link, useRouter } from "@tanstack/react-router";
import { getItemOptions } from "@/api/generated/@tanstack/react-query.gen";
import { ItemInfo } from "@/components/item/item-info";
import { ItemSidebarCard } from "@/components/item/item-sidebar-card";
import { PageContainer } from "@/components/layout/page-container";

const Route = getRouteApi("/campaigns/$slug/items/$itemSlug");

export function ItemDetailPage() {
  const { slug, itemSlug } = Route.useParams();
  const { data: item } = useSuspenseQuery(getItemOptions({ path: { slug, item_slug: itemSlug } }));
  const router = useRouter();
  const imageUploadFailed = Boolean(router.state.location.state.imageUploadFailed);

  return (
    <PageContainer>
      <Link
        to="/campaigns/$slug/items"
        params={{ slug }}
        className="text-sm text-muted-foreground hover:text-foreground inline-block mb-6"
      >
        ← Back to Items
      </Link>

      {imageUploadFailed && (
        <p className="text-sm text-destructive mb-4">Image failed to upload — try again from the edit page.</p>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        <div className="md:col-span-2">
          <ItemInfo item={item} campaignSlug={slug} />
        </div>
        <div>
          <ItemSidebarCard item={item} />
        </div>
      </div>
    </PageContainer>
  );
}
