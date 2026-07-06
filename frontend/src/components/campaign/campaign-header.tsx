import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Link, useRouter } from "@tanstack/react-router";
import { Pencil, Trash2 } from "lucide-react";
import { useState } from "react";
import type { CampaignResponse } from "@/api/generated";
import { deleteCampaignMutation, listCampaignsQueryKey } from "@/api/generated/@tanstack/react-query.gen";
import { MarkdownContent } from "@/components/markdown/markdown-content";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";

interface CampaignHeaderProps {
  campaign: CampaignResponse;
}

export function CampaignHeader({ campaign }: CampaignHeaderProps) {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [deleteOpen, setDeleteOpen] = useState(false);

  const isGm = campaign.role === "gm";

  const deleteMutation = useMutation({
    ...deleteCampaignMutation(),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: listCampaignsQueryKey() });
      await router.navigate({ to: "/", replace: true });
    },
  });

  return (
    <div>
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-center gap-3 flex-wrap">
          <h1 className="text-3xl font-bold">{campaign.name}</h1>
          <Badge variant={isGm ? "default" : "secondary"}>{isGm ? "GM" : "Player"}</Badge>
        </div>
        {isGm && (
          <div className="flex items-center gap-1 shrink-0">
            <Button variant="ghost" size="icon" asChild aria-label="Edit campaign">
              <Link to="/campaigns/$slug/edit" params={{ slug: campaign.slug }}>
                <Pencil className="h-4 w-4" />
              </Link>
            </Button>
            <Button variant="ghost" size="icon" onClick={() => setDeleteOpen(true)} aria-label="Delete campaign">
              <Trash2 className="h-4 w-4 text-destructive" />
            </Button>
          </div>
        )}
      </div>

      {campaign.description !== null && (
        <MarkdownContent
          content={campaign.description}
          campaignSlug={campaign.slug}
          className="mt-2 text-muted-foreground"
        />
      )}

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
