import { useSuspenseQuery } from "@tanstack/react-query";
import { Link } from "@tanstack/react-router";
import { ChevronRight, Swords } from "lucide-react";
import { listItemsOptions } from "@/api/generated/@tanstack/react-query.gen";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";

interface ItemsSectionProps {
  slug: string;
}

export function ItemsSection({ slug }: ItemsSectionProps) {
  const { data: items } = useSuspenseQuery(listItemsOptions({ path: { slug } }));

  return (
    <div>
      {items.length === 0 ? (
        <p className="text-sm text-muted-foreground italic">No items yet.</p>
      ) : (
        <div className="space-y-2">
          {items.map((item) => (
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
