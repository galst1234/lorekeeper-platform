import { useSuspenseQuery } from "@tanstack/react-query";
import { Link } from "@tanstack/react-router";
import { ChevronRight, Swords } from "lucide-react";
import { listItemsOptions } from "@/api/generated/@tanstack/react-query.gen";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { matchesQuery } from "@/lib/search";

interface ItemsSectionProps {
  slug: string;
  query?: string;
}

export function ItemsSection({ slug, query = "" }: ItemsSectionProps) {
  const { data: items } = useSuspenseQuery(listItemsOptions({ path: { slug } }));

  const filtered = items.filter((item) => matchesQuery(item.name, query));
  const noMatchText = `No matches for "${query}".`;

  return (
    <div>
      {filtered.length === 0 ? (
        <p className="text-sm text-muted-foreground italic">{items.length === 0 ? "No items yet." : noMatchText}</p>
      ) : (
        <div className="space-y-2">
          {filtered.map((item) => (
            <Card key={item.id} className="px-4 py-3">
              <Link
                to="/campaigns/$slug/items/$itemSlug"
                params={{ slug, itemSlug: item.slug }}
                className="flex items-center gap-3"
              >
                <div className="h-24 w-24 shrink-0 overflow-hidden rounded-md bg-muted flex items-center justify-center">
                  {item.image_url ? (
                    <img src={item.image_url} alt="" className="h-full w-full object-cover" />
                  ) : (
                    <Swords className="h-10 w-10 text-muted-foreground" />
                  )}
                </div>
                <div className="flex flex-1 items-center justify-between min-w-0 gap-2">
                  <span className="flex items-center gap-2 min-w-0">
                    <span className="font-medium hover:underline truncate">{item.name}</span>
                    {item.restricted && <Badge variant="outline">Restricted</Badge>}
                  </span>
                  <ChevronRight className="h-4 w-4 text-muted-foreground shrink-0" />
                </div>
              </Link>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
