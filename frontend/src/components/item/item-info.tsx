import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "@tanstack/react-router";
import { Pencil, Trash2 } from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import type { ItemResponse } from "@/api/generated";
import {
  deleteItemMutation,
  getItemQueryKey,
  listItemsQueryKey,
  patchItemMutation,
} from "@/api/generated/@tanstack/react-query.gen";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";

const editSchema = z.object({
  name: z.string().trim().min(1, "Name is required"),
  description: z.string(),
});

type EditFormValues = z.infer<typeof editSchema>;

interface ItemInfoProps {
  item: ItemResponse;
  campaignSlug: string;
}

export function ItemInfo({ item, campaignSlug }: ItemInfoProps) {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [editOpen, setEditOpen] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);

  const editForm = useForm<EditFormValues>({
    resolver: zodResolver(editSchema),
    values: {
      name: item.name,
      description: item.description ?? "",
    },
  });

  const patchMutation = useMutation({
    ...patchItemMutation(),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: listItemsQueryKey({ path: { slug: campaignSlug } }) });
      await queryClient.invalidateQueries({
        queryKey: getItemQueryKey({ path: { slug: campaignSlug, item_slug: item.slug } }),
      });
      setEditOpen(false);
    },
  });

  const deleteMutation = useMutation({
    ...deleteItemMutation(),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: listItemsQueryKey({ path: { slug: campaignSlug } }) });
      await router.navigate({ to: "/campaigns/$slug/items", params: { slug: campaignSlug } });
    },
  });

  return (
    <div>
      <div className="flex items-start justify-between gap-4">
        <h1 className="text-3xl font-bold">{item.name}</h1>
        <div className="flex items-center gap-1 shrink-0">
          <Button variant="ghost" size="icon" onClick={() => setEditOpen(true)} aria-label="Edit item">
            <Pencil className="h-4 w-4" />
          </Button>
          <Button variant="ghost" size="icon" onClick={() => setDeleteOpen(true)} aria-label="Delete item">
            <Trash2 className="h-4 w-4 text-destructive" />
          </Button>
        </div>
      </div>

      <div className="mt-4">
        {item.description ? (
          <p className="text-muted-foreground">{item.description}</p>
        ) : (
          <p className="text-muted-foreground italic">No description yet.</p>
        )}
      </div>

      {/* Edit dialog */}
      <Dialog open={editOpen} onOpenChange={setEditOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Edit Item</DialogTitle>
          </DialogHeader>
          <Form {...editForm}>
            <form
              onSubmit={editForm.handleSubmit((v) =>
                patchMutation.mutate({
                  path: { slug: campaignSlug, item_slug: item.slug },
                  body: { name: v.name.trim(), description: v.description.trim() || null },
                })
              )}
              className="space-y-4"
            >
              <FormField
                control={editForm.control}
                name="name"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Name</FormLabel>
                    <FormControl>
                      <Input {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={editForm.control}
                name="description"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Description</FormLabel>
                    <FormControl>
                      <Textarea rows={3} {...field} />
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
            <DialogTitle>Delete "{item.name}"?</DialogTitle>
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
              onClick={() => deleteMutation.mutate({ path: { slug: campaignSlug, item_slug: item.slug } })}
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
