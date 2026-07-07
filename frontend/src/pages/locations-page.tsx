import { getRouteApi } from "@tanstack/react-router";
import { PageContainer } from "@/components/layout/page-container";
import { LocationsSection } from "@/components/location/locations-section";

const Route = getRouteApi("/campaigns/$slug/locations/");

export function LocationsPage() {
  const { slug } = Route.useParams();
  const { active_only: activeOnly } = Route.useSearch();

  return (
    <PageContainer className="space-y-8">
      <LocationsSection slug={slug} activeOnly={activeOnly} />
    </PageContainer>
  );
}
