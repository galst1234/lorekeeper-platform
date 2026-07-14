import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Link, useRouter } from "@tanstack/react-router";
import { Pencil, Trash2 } from "lucide-react";
import { useState } from "react";
import type { CharacterResponse } from "@/api/generated";
import { deleteCharacterMutation, listCharactersQueryKey } from "@/api/generated/@tanstack/react-query.gen";
import { MarkdownContent } from "@/components/markdown/markdown-content";
import { TagRow } from "@/components/tags/tag-row";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";

interface CharacterInfoProps {
  character: CharacterResponse;
  campaignSlug: string;
}

export function CharacterInfo({ character, campaignSlug }: CharacterInfoProps) {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [deleteOpen, setDeleteOpen] = useState(false);

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
          <Badge variant="secondary" className="translate-y-1">
            {character.character_type.toUpperCase()}
          </Badge>
          {character.restricted && (
            <Badge variant="outline" className="translate-y-1">
              Restricted
            </Badge>
          )}
        </div>
        <div className="flex items-center gap-1 shrink-0">
          <Button variant="ghost" size="icon" asChild aria-label="Edit character">
            <Link
              to="/campaigns/$slug/characters/$characterSlug/edit"
              params={{ slug: campaignSlug, characterSlug: character.slug }}
            >
              <Pencil className="h-4 w-4" />
            </Link>
          </Button>
          <Button variant="ghost" size="icon" onClick={() => setDeleteOpen(true)} aria-label="Delete character">
            <Trash2 className="h-4 w-4 text-destructive" />
          </Button>
        </div>
      </div>

      <TagRow tags={character.tags} className="mt-3" />

      <div className="mt-4">
        {character.description ? (
          <MarkdownContent
            content={character.description}
            campaignSlug={campaignSlug}
            className="text-muted-foreground"
          />
        ) : (
          <p className="text-muted-foreground italic">No description yet.</p>
        )}
      </div>

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
