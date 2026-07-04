import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQueryClient, useSuspenseQuery } from "@tanstack/react-query";
import { Link } from "@tanstack/react-router";
import { ChevronRight, Plus, ScrollText } from "lucide-react";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { chronicleEntriesQueryOptions, createChronicleEntry } from "@/api/chronicle";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { datetimeLocalToIso, toDatetimeLocalValue } from "@/lib/datetime";

function toEntrySlug(title: string): string {
  return title
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

function formatOccurredAt(dateString: string): string {
  return new Date(dateString).toLocaleDateString(undefined, {
    year: "numeric",
    month: "long",
    day: "numeric",
  });
}

const addSchema = z.object({
  title: z.string().trim().min(1, "Title is required"),
  slug: z
    .string()
    .trim()
    .min(1, "Slug is required")
    .regex(/^[a-z0-9]+(-[a-z0-9]+)*$/, "Slug must be lowercase letters, numbers, and hyphens"),
  occurredAt: z.string().min(1, "Session date is required"),
  body: z.string(),
});

type AddFormValues = z.infer<typeof addSchema>;

function defaultAddValues(): AddFormValues {
  return { title: "", slug: "", occurredAt: toDatetimeLocalValue(new Date()), body: "" };
}

interface ChronicleSectionProps {
  slug: string;
}

export function ChronicleSection({ slug }: ChronicleSectionProps) {
  const queryClient = useQueryClient();
  const [addOpen, setAddOpen] = useState(false);
  const [slugEdited, setSlugEdited] = useState(false);
  const { data: entries } = useSuspenseQuery(chronicleEntriesQueryOptions(slug));

  const addForm = useForm<AddFormValues>({
    resolver: zodResolver(addSchema),
    defaultValues: defaultAddValues(),
  });

  const titleValue = addForm.watch("title");

  useEffect(() => {
    if (!slugEdited) {
      addForm.setValue("slug", toEntrySlug(titleValue), { shouldValidate: false });
    }
  }, [titleValue, slugEdited, addForm]);

  const createMutation = useMutation({
    mutationFn: (values: AddFormValues) =>
      createChronicleEntry(slug, {
        title: values.title.trim(),
        slug: values.slug.trim(),
        occurred_at: datetimeLocalToIso(values.occurredAt),
        body: values.body.trim() || undefined,
      }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["chronicle-entries", slug] });
      setAddOpen(false);
      setSlugEdited(false);
      addForm.reset(defaultAddValues());
    },
  });

  function closeAdd() {
    setAddOpen(false);
    setSlugEdited(false);
    addForm.reset(defaultAddValues());
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-lg font-semibold">Chronicle</h2>
        <Button
          variant="ghost"
          size="icon"
          onClick={() => setAddOpen(true)}
          aria-label="Create Chronicle Entry"
          className="-my-1"
        >
          <Plus className="h-4 w-4" />
        </Button>
      </div>

      {entries.length === 0 ? (
        <div className="flex flex-col items-center gap-2 py-8 text-center">
          <ScrollText className="h-8 w-8 text-muted-foreground" />
          <p className="text-sm text-muted-foreground italic">No chronicle entries yet.</p>
        </div>
      ) : (
        <div className="space-y-2">
          {entries.map((entry) => (
            <Card key={entry.id} className="px-4 py-3">
              <Link
                to="/campaigns/$slug/chronicle/$entrySlug"
                params={{ slug, entrySlug: entry.slug }}
                className="block"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium hover:underline">{entry.title}</p>
                    <p className="text-xs text-muted-foreground">{formatOccurredAt(entry.occurred_at)}</p>
                  </div>
                  <ChevronRight className="h-4 w-4 text-muted-foreground shrink-0" />
                </div>
                {entry.body && <p className="text-sm text-muted-foreground mt-2 line-clamp-2">{entry.body}</p>}
              </Link>
            </Card>
          ))}
        </div>
      )}

      <Dialog open={addOpen} onOpenChange={(open) => (open ? setAddOpen(true) : closeAdd())}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create Chronicle Entry</DialogTitle>
          </DialogHeader>
          <Form {...addForm}>
            <form
              onSubmit={addForm.handleSubmit((v) => createMutation.mutate(v))}
              onKeyDown={(e) => {
                if (e.key === "Enter" && e.ctrlKey) {
                  e.preventDefault();
                  addForm.handleSubmit((v) => createMutation.mutate(v))();
                }
              }}
              className="space-y-4"
            >
              <FormField
                control={addForm.control}
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
                control={addForm.control}
                name="slug"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Slug</FormLabel>
                    <FormControl>
                      <Input
                        {...field}
                        onChange={(e) => {
                          setSlugEdited(true);
                          field.onChange(e);
                        }}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={addForm.control}
                name="occurredAt"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Session date</FormLabel>
                    <FormControl>
                      <Input type="datetime-local" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={addForm.control}
                name="body"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Write-up</FormLabel>
                    <FormControl>
                      <Textarea rows={4} {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              {createMutation.isError && (
                <p className="text-sm text-destructive">
                  {createMutation.error instanceof Error ? createMutation.error.message : "Failed to create entry."}
                </p>
              )}
              <DialogFooter>
                <Button type="button" variant="ghost" onClick={closeAdd} disabled={createMutation.isPending}>
                  Cancel
                </Button>
                <Button type="submit" variant="create" disabled={createMutation.isPending}>
                  {createMutation.isPending ? "Creating…" : "Create"}
                </Button>
              </DialogFooter>
            </form>
          </Form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
