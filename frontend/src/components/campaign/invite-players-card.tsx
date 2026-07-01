import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Copy, Users } from "lucide-react";
import { useState } from "react";
import { generateInvite, revokeInvite } from "@/api/membership";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

interface InvitePlayersCardProps {
  campaignSlug: string;
  existingInviteCode: string | null;
}

export function InvitePlayersCard({ campaignSlug, existingInviteCode }: InvitePlayersCardProps) {
  const queryClient = useQueryClient();
  const [inviteUrl, setInviteUrl] = useState<string | null>(
    existingInviteCode ? `${window.location.origin}/campaigns/${campaignSlug}/join/${existingInviteCode}` : null
  );

  const generateMutation = useMutation({
    mutationFn: () => generateInvite(campaignSlug),
    onSuccess: (data) => {
      setInviteUrl(`${window.location.origin}${data.invite_url}`);
      queryClient.invalidateQueries({ queryKey: ["campaigns"] });
    },
  });

  const revokeMutation = useMutation({
    mutationFn: () => revokeInvite(campaignSlug),
    onSuccess: () => {
      setInviteUrl(null);
      queryClient.invalidateQueries({ queryKey: ["campaigns"] });
    },
  });

  return (
    <Card>
      <CardHeader className="flex flex-row items-center gap-3 pb-3">
        <Users className="h-5 w-5 text-muted-foreground" />
        <CardTitle className="text-base">Invite Players</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {inviteUrl ? (
          <>
            <div className="flex gap-2">
              <Input readOnly value={inviteUrl} className="text-xs font-mono" />
              <Button
                variant="outline"
                size="icon"
                onClick={() => navigator.clipboard.writeText(inviteUrl)}
                aria-label="Copy invite link"
              >
                <Copy className="h-4 w-4" />
              </Button>
            </div>
            <Button
              variant="link"
              className="text-destructive p-0 h-auto text-sm"
              onClick={() => revokeMutation.mutate()}
              disabled={revokeMutation.isPending}
            >
              {revokeMutation.isPending ? "Revoking…" : "Revoke"}
            </Button>
          </>
        ) : (
          <Button variant="outline" onClick={() => generateMutation.mutate()} disabled={generateMutation.isPending}>
            {generateMutation.isPending ? "Generating…" : "Generate Invite Link"}
          </Button>
        )}
        {generateMutation.isError && <p className="text-sm text-destructive">Failed to generate invite link.</p>}
        {revokeMutation.isError && <p className="text-sm text-destructive">Failed to revoke invite link.</p>}
      </CardContent>
    </Card>
  );
}
