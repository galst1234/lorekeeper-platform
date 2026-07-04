import { getRouteApi } from "@tanstack/react-router";
import { ChronicleEntryPageEditor } from "@/components/chronicle/chronicle-entry-page-editor";

const Route = getRouteApi("/campaigns/$slug/chronicle/new");

export function ChronicleEntryNewPage() {
  const { slug } = Route.useParams();
  return <ChronicleEntryPageEditor mode="create" campaignSlug={slug} />;
}
