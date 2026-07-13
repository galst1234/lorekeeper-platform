import { useSuspenseQuery } from "@tanstack/react-query";
import { getRouteApi } from "@tanstack/react-router";
import { getLocationOptions } from "@/api/generated/@tanstack/react-query.gen";
import { LocationPageEditor } from "@/components/location/location-page-editor";

const Route = getRouteApi("/campaigns/$slug/locations/$locationSlug_/edit");

export function LocationEditPage() {
  const { slug, locationSlug } = Route.useParams();
  const { data: location } = useSuspenseQuery(getLocationOptions({ path: { slug, location_slug: locationSlug } }));

  return <LocationPageEditor mode="edit" campaignSlug={slug} location={location} />;
}
