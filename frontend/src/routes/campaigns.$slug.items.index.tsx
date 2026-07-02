import { createFileRoute } from "@tanstack/react-router";
import { ItemsSection } from "@/components/item/items-section";

export const Route = createFileRoute("/campaigns/$slug/items/")({
  component: ItemsPage,
});

function ItemsPage() {
  const { slug } = Route.useParams();

  return (
    <div className="max-w-4xl mx-auto px-6 py-8 space-y-8">
      <ItemsSection slug={slug} />
    </div>
  );
}
