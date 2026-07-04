import { createFileRoute } from "@tanstack/react-router";
import { ChronicleEntryPageEditor } from "@/components/chronicle/chronicle-entry-page-editor";

export const Route = createFileRoute("/campaigns/$slug/chronicle/new")({
  component: NewChronicleEntryRoute,
});

function NewChronicleEntryRoute() {
  const { slug } = Route.useParams();
  return <ChronicleEntryPageEditor mode="create" campaignSlug={slug} />;
}
