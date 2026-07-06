import { getRouteApi } from "@tanstack/react-router";
import { ItemsSection } from "@/components/item/items-section";
import { PageContainer } from "@/components/layout/page-container";

const Route = getRouteApi("/campaigns/$slug/items/");

export function ItemsPage() {
  const { slug } = Route.useParams();

  return (
    <PageContainer className="space-y-8">
      <ItemsSection slug={slug} />
    </PageContainer>
  );
}
