import { useSuspenseQuery } from "@tanstack/react-query";
import { getRouteApi, Link, useRouter } from "@tanstack/react-router";
import { getLocationOptions } from "@/api/generated/@tanstack/react-query.gen";
import { PageContainer } from "@/components/layout/page-container";
import { LocationInfo } from "@/components/location/location-info";
import { LocationSidebarCard } from "@/components/location/location-sidebar-card";

const Route = getRouteApi("/campaigns/$slug/locations/$locationSlug");

export function LocationDetailPage() {
  const { slug, locationSlug } = Route.useParams();
  const { data: location } = useSuspenseQuery(getLocationOptions({ path: { slug, location_slug: locationSlug } }));
  const router = useRouter();
  const imageUploadFailed = Boolean(router.state.location.state.imageUploadFailed);

  return (
    <PageContainer>
      <Link
        to="/campaigns/$slug/locations"
        params={{ slug }}
        className="text-sm text-muted-foreground hover:text-foreground inline-block mb-6"
      >
        ← Back to Locations
      </Link>

      {imageUploadFailed && (
        <p className="text-sm text-destructive mb-4">Image failed to upload — try again from the edit page.</p>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        <div className="md:col-span-2">
          <LocationInfo location={location} campaignSlug={slug} />
        </div>
        <div>
          <LocationSidebarCard location={location} />
        </div>
      </div>
    </PageContainer>
  );
}
