import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Link, useRouter } from "@tanstack/react-router";
import { Pencil, Trash2 } from "lucide-react";
import { useState } from "react";
import type { LocationResponse } from "@/api/generated";
import { deleteLocationMutation, listLocationsQueryKey } from "@/api/generated/@tanstack/react-query.gen";
import { MarkdownContent } from "@/components/markdown/markdown-content";
import { TagRow } from "@/components/tags/tag-row";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";

interface LocationInfoProps {
  location: LocationResponse;
  campaignSlug: string;
}

export function LocationInfo({ location, campaignSlug }: LocationInfoProps) {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [deleteOpen, setDeleteOpen] = useState(false);

  const deleteMutation = useMutation({
    ...deleteLocationMutation(),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: listLocationsQueryKey({ path: { slug: campaignSlug } }) });
      await router.navigate({ to: "/campaigns/$slug/locations", params: { slug: campaignSlug } });
    },
  });

  return (
    <div>
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-center gap-2 min-w-0">
          <h1 className="text-3xl font-bold">{location.name}</h1>
          {location.restricted && (
            <Badge variant="outline" className="translate-y-1">
              Restricted
            </Badge>
          )}
        </div>
        <div className="flex items-center gap-1 shrink-0">
          <Button variant="ghost" size="icon" asChild aria-label="Edit location">
            <Link
              to="/campaigns/$slug/locations/$locationSlug/edit"
              params={{ slug: campaignSlug, locationSlug: location.slug }}
            >
              <Pencil className="h-4 w-4" />
            </Link>
          </Button>
          <Button variant="ghost" size="icon" onClick={() => setDeleteOpen(true)} aria-label="Delete location">
            <Trash2 className="h-4 w-4 text-destructive" />
          </Button>
        </div>
      </div>

      <TagRow tags={location.tags} className="mt-3" />

      <div className="mt-4">
        {location.description ? (
          <MarkdownContent
            content={location.description}
            campaignSlug={campaignSlug}
            className="text-muted-foreground"
          />
        ) : (
          <p className="text-muted-foreground italic">No description yet.</p>
        )}
      </div>

      <Dialog open={deleteOpen} onOpenChange={setDeleteOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete "{location.name}"?</DialogTitle>
          </DialogHeader>
          <p className="text-sm text-muted-foreground">This cannot be undone.</p>
          {deleteMutation.isError && <p className="text-sm text-destructive">Failed to delete. Please try again.</p>}
          <DialogFooter>
            <Button
              type="button"
              variant="ghost"
              onClick={() => setDeleteOpen(false)}
              disabled={deleteMutation.isPending}
            >
              Cancel
            </Button>
            <Button
              type="button"
              variant="destructive"
              onClick={() => deleteMutation.mutate({ path: { slug: campaignSlug, location_slug: location.slug } })}
              disabled={deleteMutation.isPending}
            >
              {deleteMutation.isPending ? "Deleting…" : "Delete"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
