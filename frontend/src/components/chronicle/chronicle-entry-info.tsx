import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Link, useRouter } from "@tanstack/react-router";
import { Pencil, Trash2 } from "lucide-react";
import { useState } from "react";
import { type ChronicleEntryDetail, deleteChronicleEntry } from "@/api/chronicle";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";

function formatOccurredAt(dateString: string): string {
  return new Date(dateString).toLocaleDateString(undefined, {
    year: "numeric",
    month: "long",
    day: "numeric",
  });
}

interface ChronicleEntryInfoProps {
  entry: ChronicleEntryDetail;
  campaignSlug: string;
}

export function ChronicleEntryInfo({ entry, campaignSlug }: ChronicleEntryInfoProps) {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [deleteOpen, setDeleteOpen] = useState(false);

  const deleteMutation = useMutation({
    mutationFn: () => deleteChronicleEntry(campaignSlug, entry.slug),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["chronicle-entries", campaignSlug] });
      await router.navigate({ to: "/campaigns/$slug/chronicle", params: { slug: campaignSlug } });
    },
  });

  return (
    <div>
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold">{entry.title}</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            {formatOccurredAt(entry.occurred_at)} - by {entry.author?.display_name ?? "Unknown"}
          </p>
        </div>
        <div className="flex shrink-0 items-center gap-1">
          <Button variant="ghost" size="icon" asChild>
            <Link
              to="/campaigns/$slug/chronicle/$entrySlug/edit"
              params={{ slug: campaignSlug, entrySlug: entry.slug }}
              aria-label="Edit chronicle entry"
            >
              <Pencil data-icon="inline" />
            </Link>
          </Button>
          <Button variant="ghost" size="icon" onClick={() => setDeleteOpen(true)} aria-label="Delete chronicle entry">
            <Trash2 data-icon="inline" className="text-destructive" />
          </Button>
        </div>
      </div>

      <div className="mt-4">
        {entry.body ? (
          <p className="whitespace-pre-wrap text-muted-foreground">{entry.body}</p>
        ) : (
          <p className="text-muted-foreground italic">No write-up yet.</p>
        )}
      </div>

      <Dialog open={deleteOpen} onOpenChange={setDeleteOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete "{entry.title}"?</DialogTitle>
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
              onClick={() => deleteMutation.mutate()}
              disabled={deleteMutation.isPending}
            >
              {deleteMutation.isPending ? "Deleting..." : "Delete"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
