import { Swords } from "lucide-react";
import type { Item } from "@/api/items";
import { Card, CardContent } from "@/components/ui/card";

interface ItemSidebarCardProps {
  item: Item;
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

export function ItemSidebarCard({ item }: ItemSidebarCardProps) {
  return (
    <Card className="sticky top-6">
      <CardContent className="pt-6 space-y-4">
        <div className="aspect-square w-full bg-muted rounded-md flex items-center justify-center">
          <Swords className="h-12 w-12 text-muted-foreground" />
        </div>
        <div>
          <p className="text-xs text-muted-foreground">Last updated</p>
          <p className="text-xs text-muted-foreground">{formatRelativeDate(item.updated_at)}</p>
        </div>
      </CardContent>
    </Card>
  );
}
