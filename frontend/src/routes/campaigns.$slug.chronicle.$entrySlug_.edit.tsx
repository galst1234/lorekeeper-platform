import { useSuspenseQuery } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";
import { getChronicleEntryOptions } from "@/api/generated/@tanstack/react-query.gen";
import { ChronicleEntryPageEditor } from "@/components/chronicle/chronicle-entry-page-editor";

export const Route = createFileRoute("/campaigns/$slug/chronicle/$entrySlug_/edit")({
  component: EditChronicleEntryRoute,
});

function EditChronicleEntryRoute() {
  const { slug, entrySlug } = Route.useParams();
  const { data: entry } = useSuspenseQuery(getChronicleEntryOptions({ path: { slug, entry_slug: entrySlug } }));

  return <ChronicleEntryPageEditor mode="edit" campaignSlug={slug} entry={entry} />;
}
