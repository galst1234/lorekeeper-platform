import { useSuspenseQuery } from "@tanstack/react-query";
import { Link } from "@tanstack/react-router";
import { ChevronRight, Plus } from "lucide-react";
import { listLocationsOptions } from "@/api/generated/@tanstack/react-query.gen";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

interface LocationsSectionProps {
  slug: string;
}

export function LocationsSection({ slug }: LocationsSectionProps) {
  const { data: locations } = useSuspenseQuery(listLocationsOptions({ path: { slug } }));

  return (
    <div>
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-lg font-semibold">Locations</h2>
        <Button variant="ghost" size="icon" asChild aria-label="Create Location" className="-my-1">
          <Link to="/campaigns/$slug/locations/new" params={{ slug }}>
            <Plus className="h-4 w-4" />
          </Link>
        </Button>
      </div>

      {locations.length === 0 ? (
        <p className="text-sm text-muted-foreground italic">No locations yet.</p>
      ) : (
        <div className="space-y-2">
          {locations.map((location) => (
            <Card key={location.id} className="px-4 py-3">
              <div className="flex items-center justify-between">
                <Link
                  to="/campaigns/$slug/locations/$locationSlug"
                  params={{ slug, locationSlug: location.slug }}
                  className="font-medium hover:underline"
                >
                  {location.name}
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
