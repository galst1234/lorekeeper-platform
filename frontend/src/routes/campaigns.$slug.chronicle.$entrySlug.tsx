import { useSuspenseQuery } from "@tanstack/react-query";
import { createFileRoute, Link } from "@tanstack/react-router";
import { chronicleEntryQueryOptions } from "@/api/chronicle";

export const Route = createFileRoute("/campaigns/$slug/chronicle/$entrySlug")({
  component: ChronicleDetailPage,
});

function ChronicleDetailPage() {
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

      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold mb-2">{entry.title}</h1>
          <p className="text-sm text-muted-foreground">
            {new Date(entry.occurred_at).toLocaleDateString(undefined, {
              year: "numeric",
              month: "long",
              day: "numeric",
            })}
          </p>
        </div>

        {entry.body && <div className="prose prose-sm dark:prose-invert max-w-none">{entry.body}</div>}
      </div>
    </div>
  );
}
