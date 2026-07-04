import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "@tanstack/react-router";
import { Pencil, Trash2 } from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import type { CharacterResponse } from "@/api/generated";
import {
  deleteCharacterMutation,
  getCharacterQueryKey,
  listCharactersQueryKey,
  patchCharacterMutation,
} from "@/api/generated/@tanstack/react-query.gen";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";

const editSchema = z.object({
  name: z.string().trim().min(1, "Name is required"),
  character_type: z.enum(["pc", "npc"]),
  description: z.string(),
});

type EditFormValues = z.infer<typeof editSchema>;

interface CharacterInfoProps {
  character: CharacterResponse;
  campaignSlug: string;
}

export function CharacterInfo({ character, campaignSlug }: CharacterInfoProps) {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [editOpen, setEditOpen] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);

  const editForm = useForm<EditFormValues>({
    resolver: zodResolver(editSchema),
    values: {
      name: character.name,
      character_type: character.character_type,
      description: character.description ?? "",
    },
  });

  const patchMutation = useMutation({
    ...patchCharacterMutation(),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: listCharactersQueryKey({ path: { slug: campaignSlug } }) });
      await queryClient.invalidateQueries({
        queryKey: getCharacterQueryKey({ path: { slug: campaignSlug, character_slug: character.slug } }),
      });
      setEditOpen(false);
    },
  });

  const deleteMutation = useMutation({
    ...deleteCharacterMutation(),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: listCharactersQueryKey({ path: { slug: campaignSlug } }) });
      await router.navigate({ to: "/campaigns/$slug/characters", params: { slug: campaignSlug } });
    },
  });

  return (
    <div>
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-center gap-3 flex-wrap">
          <h1 className="text-3xl font-bold">{character.name}</h1>
          <Badge variant="secondary">{character.character_type.toUpperCase()}</Badge>
        </div>
        <div className="flex items-center gap-1 shrink-0">
          <Button variant="ghost" size="icon" onClick={() => setEditOpen(true)} aria-label="Edit character">
            <Pencil className="h-4 w-4" />
          </Button>
          <Button variant="ghost" size="icon" onClick={() => setDeleteOpen(true)} aria-label="Delete character">
            <Trash2 className="h-4 w-4 text-destructive" />
          </Button>
        </div>
      </div>

      <div className="mt-4">
        {character.description ? (
          <p className="text-muted-foreground">{character.description}</p>
        ) : (
          <p className="text-muted-foreground italic">No description yet.</p>
        )}
      </div>

      {/* Edit dialog */}
      <Dialog open={editOpen} onOpenChange={setEditOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Edit Character</DialogTitle>
          </DialogHeader>
          <Form {...editForm}>
            <form
              onSubmit={editForm.handleSubmit((v) =>
                patchMutation.mutate({
                  path: { slug: campaignSlug, character_slug: character.slug },
                  body: {
                    name: v.name.trim(),
                    character_type: v.character_type,
                    description: v.description.trim() || null,
                  },
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
                name="character_type"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Type</FormLabel>
                    <Select onValueChange={field.onChange} value={field.value}>
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        <SelectItem value="pc">PC</SelectItem>
                        <SelectItem value="npc">NPC</SelectItem>
                      </SelectContent>
                    </Select>
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
            <DialogTitle>Delete "{character.name}"?</DialogTitle>
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
              onClick={() => deleteMutation.mutate({ path: { slug: campaignSlug, character_slug: character.slug } })}
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
