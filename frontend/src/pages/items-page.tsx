import { getRouteApi, Link } from "@tanstack/react-router";
import { Plus } from "lucide-react";
import { ItemsSection } from "@/components/item/items-section";
import { PageContainer } from "@/components/layout/page-container";
import { Button } from "@/components/ui/button";
import { SearchInput } from "@/components/ui/search-input";

const Route = getRouteApi("/campaigns/$slug/items/");

export function ItemsPage() {
  const { slug } = Route.useParams();
  const { q: query = "" } = Route.useSearch();
  const navigate = Route.useNavigate();

  return (
    <PageContainer className="space-y-8">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Items</h1>
        <Button asChild size="sm">
          <Link to="/campaigns/$slug/items/new" params={{ slug }}>
            <Plus className="h-4 w-4" />
            New Item
          </Link>
        </Button>
      </div>
      <SearchInput
        value={query}
        onChange={(value) => navigate({ search: value.trim() ? { q: value } : {}, replace: true })}
        placeholder="Search items"
        aria-label="Search items"
      />
      <ItemsSection slug={slug} query={query} />
    </PageContainer>
  );
}
