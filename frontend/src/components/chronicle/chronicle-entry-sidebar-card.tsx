import type { ChronicleEntryDetailResponse } from "@/api/generated";
import { Card, CardContent } from "@/components/ui/card";

interface ChronicleEntrySidebarCardProps {
  entry: ChronicleEntryDetailResponse;
}

function formatRelativeDate(dateString: string): string {
  const date = new Date(dateString);
  const diffDays = Math.floor((Date.now() - date.getTime()) / (1000 * 60 * 60 * 24));
  if (diffDays === 0) return "Today";
  if (diffDays === 1) return "Yesterday";
  if (diffDays < 7) return `${diffDays} days ago`;
  if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`;
  if (diffDays < 365) return `${Math.floor(diffDays / 30)} months ago`;
  return `${Math.floor(diffDays / 365)} years ago`;
}

export function ChronicleEntrySidebarCard({ entry }: ChronicleEntrySidebarCardProps) {
  return (
    <Card className="sticky top-6">
      <CardContent className="flex flex-col gap-4 pt-6">
        <div>
          <p className="text-xs text-muted-foreground">Author</p>
          <p className="text-xs text-muted-foreground">{entry.author?.display_name ?? "Unknown"}</p>
        </div>
        <div>
          <p className="text-xs text-muted-foreground">Last updated</p>
          <p className="text-xs text-muted-foreground">{formatRelativeDate(entry.updated_at)}</p>
        </div>
      </CardContent>
    </Card>
  );
}
