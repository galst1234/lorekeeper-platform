import { useSuspenseQuery } from "@tanstack/react-query";
import { Link, useNavigate } from "@tanstack/react-router";
import { ChevronRight, Plus } from "lucide-react";
import { listLocationsOptions } from "@/api/generated/@tanstack/react-query.gen";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

interface LocationsSectionProps {
  slug: string;
  activeOnly?: boolean;
}

export function LocationsSection({ slug, activeOnly }: LocationsSectionProps) {
  const navigate = useNavigate();
  const { data: locations } = useSuspenseQuery(
    listLocationsOptions({
      path: { slug },
      query: activeOnly ? { active_only: true } : undefined,
    })
  );

  const handleToggleActiveOnly = () => {
    navigate({
      to: "/campaigns/$slug/locations",
      params: { slug },
      search: activeOnly ? {} : { active_only: true },
    });
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-lg font-semibold">Locations</h2>
        <div className="flex items-center gap-1 -my-1">
          <Button
            variant={activeOnly ? "secondary" : "ghost"}
            size="sm"
            onClick={handleToggleActiveOnly}
            className="text-xs"
          >
            Active only
          </Button>
          <Button variant="ghost" size="icon" asChild aria-label="Create Location">
            <Link to="/campaigns/$slug/locations/new" params={{ slug }}>
              <Plus className="h-4 w-4" />
            </Link>
          </Button>
        </div>
      </div>

      {locations.length === 0 ? (
        activeOnly ? (
          <p className="text-sm text-muted-foreground italic">No active locations.</p>
        ) : (
          <p className="text-sm text-muted-foreground italic">No locations yet.</p>
        )
      ) : (
        <div className="space-y-2">
          {locations.map((location) => (
            <Card key={location.id} className="px-4 py-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 min-w-0">
                  <Link
                    to="/campaigns/$slug/locations/$locationSlug"
                    params={{ slug, locationSlug: location.slug }}
                    className="font-medium hover:underline truncate"
                  >
                    {location.name}
                  </Link>
                  {!location.is_active && (
                    <Badge variant="secondary" className="shrink-0">
                      Inactive
                    </Badge>
                  )}
                </div>
                <ChevronRight className="h-4 w-4 text-muted-foreground shrink-0" />
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
