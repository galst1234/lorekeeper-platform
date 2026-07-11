import { useSuspenseQuery } from "@tanstack/react-query";
import { Link } from "@tanstack/react-router";
import { ChevronRight, ScrollText } from "lucide-react";
import { listChronicleEntriesOptions } from "@/api/generated/@tanstack/react-query.gen";
import { MarkdownExcerpt } from "@/components/markdown/markdown-excerpt";
import { Badge } from "@/components/ui/badge";
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
                    <div className="flex items-center gap-2">
                      <p className="font-medium hover:underline">{entry.title}</p>
                      {entry.restricted && <Badge variant="outline">Restricted</Badge>}
                    </div>
                    <p className="text-xs text-muted-foreground">{formatOccurredAt(entry.occurred_at)}</p>
                  </div>
                  <ChevronRight className="h-4 w-4 text-muted-foreground shrink-0" />
                </div>
                {entry.body && (
                  <MarkdownExcerpt
                    content={entry.body}
                    campaignSlug={slug}
                    className="text-sm text-muted-foreground mt-2 line-clamp-2"
                  />
                )}
              </Link>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
