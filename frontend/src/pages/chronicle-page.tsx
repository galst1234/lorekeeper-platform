import { getRouteApi, Link } from "@tanstack/react-router";
import { Plus } from "lucide-react";
import { ChronicleSection } from "@/components/chronicle/chronicle-section";
import { PageContainer } from "@/components/layout/page-container";
import { Button } from "@/components/ui/button";
import { SearchInput } from "@/components/ui/search-input";

const Route = getRouteApi("/campaigns/$slug/chronicle/");

export function ChroniclePage() {
  const { slug } = Route.useParams();
  const { q: query = "" } = Route.useSearch();
  const navigate = Route.useNavigate();

  return (
    <PageContainer className="space-y-8">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Chronicle</h1>
        <Button asChild size="sm">
          <Link to="/campaigns/$slug/chronicle/new" params={{ slug }}>
            <Plus className="h-4 w-4" />
            New Entry
          </Link>
        </Button>
      </div>
      <SearchInput
        value={query}
        onChange={(value) => navigate({ search: value.trim() ? { q: value } : {}, replace: true })}
        placeholder="Search chronicle"
        aria-label="Search chronicle"
      />
      <ChronicleSection slug={slug} query={query} />
    </PageContainer>
  );
}
