import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "@tanstack/react-router";
import { Pencil, Trash2 } from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { type ChronicleEntryDetail, deleteChronicleEntry, patchChronicleEntry } from "@/api/chronicle";
import { Button } from "@/components/ui/button";
import { DateTimePicker } from "@/components/ui/datetime-picker";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { datetimeLocalToIso, toDatetimeLocalValue } from "@/lib/datetime";

function formatOccurredAt(dateString: string): string {
  return new Date(dateString).toLocaleDateString(undefined, {
    year: "numeric",
    month: "long",
    day: "numeric",
  });
}

const editSchema = z.object({
  title: z.string().trim().min(1, "Title is required"),
  occurredAt: z.string().min(1, "Session date is required"),
  body: z.string(),
});

type EditFormValues = z.infer<typeof editSchema>;

interface ChronicleEntryInfoProps {
  entry: ChronicleEntryDetail;
  campaignSlug: string;
}

export function ChronicleEntryInfo({ entry, campaignSlug }: ChronicleEntryInfoProps) {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [editOpen, setEditOpen] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);

  const editForm = useForm<EditFormValues>({
    resolver: zodResolver(editSchema),
    values: {
      title: entry.title,
      occurredAt: toDatetimeLocalValue(new Date(entry.occurred_at)),
      body: entry.body ?? "",
    },
  });

  const patchMutation = useMutation({
    mutationFn: (values: EditFormValues) =>
      patchChronicleEntry(campaignSlug, entry.slug, {
        title: values.title.trim(),
        occurred_at: datetimeLocalToIso(values.occurredAt),
        body: values.body.trim() || null,
      }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["chronicle-entries", campaignSlug] });
      setEditOpen(false);
    },
  });

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
          <p className="text-sm text-muted-foreground mt-1">
            {formatOccurredAt(entry.occurred_at)} · by {entry.author?.display_name ?? "Unknown"}
          </p>
        </div>
        <div className="flex items-center gap-1 shrink-0">
          <Button variant="ghost" size="icon" onClick={() => setEditOpen(true)} aria-label="Edit chronicle entry">
            <Pencil className="h-4 w-4" />
          </Button>
          <Button variant="ghost" size="icon" onClick={() => setDeleteOpen(true)} aria-label="Delete chronicle entry">
            <Trash2 className="h-4 w-4 text-destructive" />
          </Button>
        </div>
      </div>

      <div className="mt-4">
        {entry.body ? (
          <p className="text-muted-foreground whitespace-pre-wrap">{entry.body}</p>
        ) : (
          <p className="text-muted-foreground italic">No write-up yet.</p>
        )}
      </div>

      {/* Edit dialog */}
      <Dialog open={editOpen} onOpenChange={setEditOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Edit Chronicle Entry</DialogTitle>
          </DialogHeader>
          <Form {...editForm}>
            <form onSubmit={editForm.handleSubmit((v) => patchMutation.mutate(v))} className="space-y-4">
              <FormField
                control={editForm.control}
                name="title"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Title</FormLabel>
                    <FormControl>
                      <Input {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={editForm.control}
                name="occurredAt"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Session date and time</FormLabel>
                    <FormControl>
                      <DateTimePicker {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={editForm.control}
                name="body"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Write-up</FormLabel>
                    <FormControl>
                      <Textarea rows={6} {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              {patchMutation.isError && <p className="text-sm text-destructive">Failed to save. Please try again.</p>}
              <DialogFooter>
                <Button
                  type="button"
                  variant="ghost"
                  onClick={() => setEditOpen(false)}
                  disabled={patchMutation.isPending}
                >
                  Cancel
                </Button>
                <Button type="submit" disabled={patchMutation.isPending}>
                  {patchMutation.isPending ? "Saving…" : "Save"}
                </Button>
              </DialogFooter>
            </form>
          </Form>
        </DialogContent>
      </Dialog>

      {/* Delete dialog */}
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
              {deleteMutation.isPending ? "Deleting…" : "Delete"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
