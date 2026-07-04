import { useSuspenseQuery } from "@tanstack/react-query";
import { createFileRoute, Link } from "@tanstack/react-router";
import { getChronicleEntryOptions } from "@/api/generated/@tanstack/react-query.gen";
import { ChronicleEntryInfo } from "@/components/chronicle/chronicle-entry-info";
import { ChronicleEntrySidebarCard } from "@/components/chronicle/chronicle-entry-sidebar-card";

export const Route = createFileRoute("/campaigns/$slug/chronicle/$entrySlug")({
  component: ChronicleEntryDetailPage,
});

function ChronicleEntryDetailPage() {
  const { slug, entrySlug } = Route.useParams();
  const { data: entry } = useSuspenseQuery(getChronicleEntryOptions({ path: { slug, entry_slug: entrySlug } }));

  return (
    <div className="mx-auto w-full max-w-7xl px-6 py-8">
      <Link
        to="/campaigns/$slug/chronicle"
        params={{ slug }}
        className="mb-6 inline-block text-sm text-muted-foreground hover:text-foreground"
      >
        ← Back to Chronicle
      </Link>

      <div className="grid grid-cols-1 gap-8 lg:grid-cols-[minmax(0,1fr)_14rem]">
        <div className="min-w-0">
          <ChronicleEntryInfo entry={entry} campaignSlug={slug} />
        </div>
        <div className="min-w-0">
          <ChronicleEntrySidebarCard entry={entry} />
        </div>
      </div>
    </div>
  );
}
