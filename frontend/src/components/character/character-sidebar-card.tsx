import { User } from "lucide-react";
import type { CharacterResponse } from "@/api/generated";
import { TagRow } from "@/components/tags/tag-row";
import { Card, CardContent } from "@/components/ui/card";

interface CharacterSidebarCardProps {
  character: CharacterResponse;
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

export function CharacterSidebarCard({ character }: CharacterSidebarCardProps) {
  return (
    <Card className="sticky top-6">
      <CardContent className="pt-6 space-y-4">
        <div className="aspect-square w-full overflow-hidden rounded-md bg-muted flex items-center justify-center">
          {character.image_url ? (
            <img src={character.image_url} alt="" className="h-full w-full object-cover" />
          ) : (
            <User className="h-12 w-12 text-muted-foreground" />
          )}
        </div>
        <div>
          <p className="text-xs text-muted-foreground">Last updated</p>
          <p className="text-xs text-muted-foreground">{formatRelativeDate(character.updated_at)}</p>
        </div>
        {/* TEMP A/B (#23): tags shown both here and under the title on characters; delete the loser after review. */}
        {character.tags.length > 0 && (
          <div>
            <p className="text-xs text-muted-foreground">Tags</p>
            <TagRow tags={character.tags} className="mt-1" />
          </div>
        )}
      </CardContent>
    </Card>
  );
}
