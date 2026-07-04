import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "@tanstack/react-router";
import { Pencil, Trash2 } from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import type { CampaignResponse } from "@/api/generated";
import {
  deleteCampaignMutation,
  getCampaignQueryKey,
  listCampaignsQueryKey,
  patchCampaignMutation,
} from "@/api/generated/@tanstack/react-query.gen";
import { Badge } from "@/components/ui/badge";
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

interface CampaignHeaderProps {
  campaign: CampaignResponse;
}

export function CampaignHeader({ campaign }: CampaignHeaderProps) {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [editOpen, setEditOpen] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);

  const isGm = campaign.role === "gm";

  const editForm = useForm<EditFormValues>({
    resolver: zodResolver(editSchema),
    values: { name: campaign.name, description: campaign.description ?? "" },
  });

  const patchMutation = useMutation({
    ...patchCampaignMutation(),
    onSuccess: async (updated) => {
      await queryClient.invalidateQueries({ queryKey: listCampaignsQueryKey() });
      await queryClient.invalidateQueries({ queryKey: getCampaignQueryKey({ path: { slug: campaign.slug } }) });
      setEditOpen(false);
      if (updated.slug !== campaign.slug) {
        await router.navigate({ to: "/campaigns/$slug", params: { slug: updated.slug } });
      }
    },
  });

  const deleteMutation = useMutation({
    ...deleteCampaignMutation(),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: listCampaignsQueryKey() });
      await router.navigate({ to: "/", replace: true });
    },
  });

  function handleEdit(values: EditFormValues) {
    patchMutation.mutate({
      path: { slug: campaign.slug },
      body: {
        name: values.name.trim(),
        description: values.description.trim() || null,
      },
    });
  }

  return (
    <div>
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-center gap-3 flex-wrap">
          <h1 className="text-3xl font-bold">{campaign.name}</h1>
          <Badge variant={isGm ? "default" : "secondary"}>{isGm ? "GM" : "Player"}</Badge>
        </div>
        {isGm && (
          <div className="flex items-center gap-1 shrink-0">
            <Button variant="ghost" size="icon" onClick={() => setEditOpen(true)} aria-label="Edit campaign">
              <Pencil className="h-4 w-4" />
            </Button>
            <Button variant="ghost" size="icon" onClick={() => setDeleteOpen(true)} aria-label="Delete campaign">
              <Trash2 className="h-4 w-4 text-destructive" />
            </Button>
          </div>
        )}
      </div>

      {campaign.description !== null && <p className="mt-2 text-muted-foreground">{campaign.description}</p>}

      {/* Edit dialog */}
      <Dialog open={editOpen} onOpenChange={setEditOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Edit Campaign</DialogTitle>
          </DialogHeader>
          <Form {...editForm}>
            <form onSubmit={editForm.handleSubmit(handleEdit)} className="space-y-4">
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
            <DialogTitle>Delete "{campaign.name}"?</DialogTitle>
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
              onClick={() => deleteMutation.mutate({ path: { slug: campaign.slug } })}
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
