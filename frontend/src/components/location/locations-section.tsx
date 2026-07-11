import { useSuspenseQuery } from "@tanstack/react-query";
import { Link } from "@tanstack/react-router";
import { ChevronRight, MapPin } from "lucide-react";
import { listLocationsOptions } from "@/api/generated/@tanstack/react-query.gen";
import { Card } from "@/components/ui/card";
import { matchesQuery } from "@/lib/search";

interface LocationsSectionProps {
  slug: string;
  query?: string;
}

export function LocationsSection({ slug, query = "" }: LocationsSectionProps) {
  const { data: locations } = useSuspenseQuery(listLocationsOptions({ path: { slug } }));

  const filtered = locations.filter((location) => matchesQuery(location.name, query));
  const noMatchText = `No matches for "${query}".`;

  return (
    <div>
      {filtered.length === 0 ? (
        <p className="text-sm text-muted-foreground italic">
          {locations.length === 0 ? "No locations yet." : noMatchText}
        </p>
      ) : (
        <div className="space-y-2">
          {filtered.map((location) => (
            <Card key={location.id} className="px-4 py-3">
              <Link
                to="/campaigns/$slug/locations/$locationSlug"
                params={{ slug, locationSlug: location.slug }}
                className="flex items-center gap-3"
              >
                <div className="h-24 w-24 shrink-0 overflow-hidden rounded-md bg-muted flex items-center justify-center">
                  <MapPin className="h-10 w-10 text-muted-foreground" />
                </div>
                <div className="flex flex-1 items-center justify-between min-w-0 gap-2">
                  <span className="font-medium hover:underline truncate">{location.name}</span>
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
