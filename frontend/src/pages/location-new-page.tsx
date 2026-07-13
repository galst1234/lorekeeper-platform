import { getRouteApi } from "@tanstack/react-router";
import { LocationPageEditor } from "@/components/location/location-page-editor";

const Route = getRouteApi("/campaigns/$slug/locations/new");

export function LocationNewPage() {
  const { slug } = Route.useParams();
  return <LocationPageEditor mode="create" campaignSlug={slug} />;
}
