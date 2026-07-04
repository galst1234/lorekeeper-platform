import { getRouteApi } from "@tanstack/react-router";
import { ItemsSection } from "@/components/item/items-section";

const Route = getRouteApi("/campaigns/$slug/items/");

export function ItemsPage() {
  const { slug } = Route.useParams();

  return (
    <div className="max-w-4xl mx-auto px-6 py-8 space-y-8">
      <ItemsSection slug={slug} />
    </div>
  );
}
