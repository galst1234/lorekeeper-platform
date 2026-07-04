import { useSuspenseQuery } from "@tanstack/react-query";
import { Link } from "@tanstack/react-router";
import { ChevronRight, Plus, ScrollText } from "lucide-react";
import { listChronicleEntriesOptions } from "@/api/generated/@tanstack/react-query.gen";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

function formatOccurredAt(dateString: string): string {
  return new Date(dateString).toLocaleDateString(undefined, {
    year: "numeric",
    month: "long",
    day: "numeric",
  });
}

interface ChronicleSectionProps {
  slug: string;
}

export function ChronicleSection({ slug }: ChronicleSectionProps) {
  const { data: entries } = useSuspenseQuery(listChronicleEntriesOptions({ path: { slug } }));

  return (
    <div>
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-lg font-semibold">Chronicle</h2>
        <Button variant="ghost" size="icon" asChild aria-label="Create Chronicle Entry" className="-my-1">
          <Link to="/campaigns/$slug/chronicle/new" params={{ slug }}>
            <Plus className="h-4 w-4" />
          </Link>
        </Button>
      </div>

      {entries.length === 0 ? (
        <div className="flex flex-col items-center gap-2 py-8 text-center">
          <ScrollText className="h-8 w-8 text-muted-foreground" />
          <p className="text-sm text-muted-foreground italic">No chronicle entries yet.</p>
        </div>
      ) : (
        <div className="space-y-2">
          {entries.map((entry) => (
            <Card key={entry.id} className="px-4 py-3">
              <Link
                to="/campaigns/$slug/chronicle/$entrySlug"
                params={{ slug, entrySlug: entry.slug }}
                className="block"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium hover:underline">{entry.title}</p>
                    <p className="text-xs text-muted-foreground">{formatOccurredAt(entry.occurred_at)}</p>
                  </div>
                  <ChevronRight className="h-4 w-4 text-muted-foreground shrink-0" />
                </div>
                {entry.body && <p className="text-sm text-muted-foreground mt-2 line-clamp-2">{entry.body}</p>}
              </Link>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
