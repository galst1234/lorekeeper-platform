import { useSuspenseQuery } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";
import { chronicleEntryQueryOptions } from "@/api/chronicle";
import { ChronicleEntryPageEditor } from "@/components/chronicle/chronicle-entry-page-editor";

export const Route = createFileRoute("/campaigns/$slug/chronicle/$entrySlug_/edit")({
  component: EditChronicleEntryRoute,
});

function EditChronicleEntryRoute() {
  const { slug, entrySlug } = Route.useParams();
  const { data: entry } = useSuspenseQuery(chronicleEntryQueryOptions(slug, entrySlug));

  return <ChronicleEntryPageEditor mode="edit" campaignSlug={slug} entry={entry} />;
}
