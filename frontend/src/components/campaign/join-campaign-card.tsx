import { useMutation } from "@tanstack/react-query";
import { Link, useRouter } from "@tanstack/react-router";
import { useState } from "react";
import { joinCampaign } from "@/api/membership";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface JoinCampaignCardProps {
  campaignName: string;
  campaignSlug: string;
  inviteCode: string;
}

export function JoinCampaignCard({ campaignName, campaignSlug, inviteCode }: JoinCampaignCardProps) {
  const router = useRouter();
  const [error, setError] = useState("");

  const joinMutation = useMutation({
    mutationFn: () => joinCampaign(campaignSlug, inviteCode),
    onSuccess: async (campaign) => {
      await router.navigate({ to: "/campaigns/$slug", params: { slug: campaign.slug } });
    },
    onError: () => setError("Failed to join campaign. The invite link may have been revoked."),
  });

  return (
    <Card className="w-full max-w-sm">
      <CardHeader>
        <CardTitle>You've been invited to join {campaignName}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <p className="text-sm text-muted-foreground">Click the button below to join this campaign.</p>
        {error && <p className="text-sm text-destructive">{error}</p>}
        <div className="flex gap-3">
          <Button onClick={() => joinMutation.mutate()} disabled={joinMutation.isPending}>
            {joinMutation.isPending ? "Joining…" : "Join Campaign"}
          </Button>
          <Button variant="ghost" asChild>
            <Link to="/">Decline</Link>
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
