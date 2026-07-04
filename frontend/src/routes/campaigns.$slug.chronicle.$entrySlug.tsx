import { useSuspenseQuery } from "@tanstack/react-query";
import { createFileRoute, Link } from "@tanstack/react-router";
import { chronicleEntryQueryOptions } from "@/api/chronicle";
import { ChronicleEntryInfo } from "@/components/chronicle/chronicle-entry-info";
import { ChronicleEntrySidebarCard } from "@/components/chronicle/chronicle-entry-sidebar-card";

export const Route = createFileRoute("/campaigns/$slug/chronicle/$entrySlug")({
  component: ChronicleEntryDetailPage,
});

function ChronicleEntryDetailPage() {
  const { slug, entrySlug } = Route.useParams();
  const { data: entry } = useSuspenseQuery(chronicleEntryQueryOptions(slug, entrySlug));

  return (
    <div className="max-w-4xl mx-auto px-6 py-8">
      <Link
        to="/campaigns/$slug/chronicle"
        params={{ slug }}
        className="text-sm text-muted-foreground hover:text-foreground inline-block mb-6"
      >
        ← Back to Chronicle
      </Link>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        <div className="md:col-span-2">
          <ChronicleEntryInfo entry={entry} campaignSlug={slug} />
        </div>
        <div>
          <ChronicleEntrySidebarCard entry={entry} />
        </div>
      </div>
    </div>
  );
}
