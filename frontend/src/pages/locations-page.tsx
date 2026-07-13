import { getRouteApi, Link } from "@tanstack/react-router";
import { Plus } from "lucide-react";
import { PageContainer } from "@/components/layout/page-container";
import { LocationsSection } from "@/components/location/locations-section";
import { Button } from "@/components/ui/button";
import { SearchInput } from "@/components/ui/search-input";

const Route = getRouteApi("/campaigns/$slug/locations/");

export function LocationsPage() {
  const { slug } = Route.useParams();
  const { q: query = "" } = Route.useSearch();
  const navigate = Route.useNavigate();

  return (
    <PageContainer className="space-y-8">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Locations</h1>
        <Button asChild size="sm">
          <Link to="/campaigns/$slug/locations/new" params={{ slug }}>
            <Plus className="h-4 w-4" />
            New Location
          </Link>
        </Button>
      </div>
      <SearchInput
        value={query}
        onChange={(value) => navigate({ search: value.trim() ? { q: value } : {}, replace: true })}
        placeholder="Search locations"
        aria-label="Search locations"
      />
      <LocationsSection slug={slug} query={query} />
    </PageContainer>
  );
}
