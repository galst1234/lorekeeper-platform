import { useSuspenseQuery } from "@tanstack/react-query";
import { Link } from "@tanstack/react-router";
import { ChevronRight, Plus } from "lucide-react";
import { listItemsOptions } from "@/api/generated/@tanstack/react-query.gen";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

interface ItemsSectionProps {
  slug: string;
}

export function ItemsSection({ slug }: ItemsSectionProps) {
  const { data: items } = useSuspenseQuery(listItemsOptions({ path: { slug } }));

  return (
    <div>
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-lg font-semibold">Items</h2>
        <Button variant="ghost" size="icon" asChild aria-label="Create Item" className="-my-1">
          <Link to="/campaigns/$slug/items/new" params={{ slug }}>
            <Plus className="h-4 w-4" />
          </Link>
        </Button>
      </div>

      {items.length === 0 ? (
        <p className="text-sm text-muted-foreground italic">No items yet.</p>
      ) : (
        <div className="space-y-2">
          {items.map((item) => (
            <Card key={item.id} className="px-4 py-3">
              <div className="flex items-center justify-between">
                <Link
                  to="/campaigns/$slug/items/$itemSlug"
                  params={{ slug, itemSlug: item.slug }}
                  className="font-medium hover:underline"
                >
                  {item.name}
                </Link>
                <ChevronRight className="h-4 w-4 text-muted-foreground" />
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
