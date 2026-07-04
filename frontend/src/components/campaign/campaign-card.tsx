import { Link } from "@tanstack/react-router";
import type { CampaignResponse } from "@/api/generated";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";

interface CampaignCardProps {
  campaign: CampaignResponse;
}

export function CampaignCard({ campaign }: CampaignCardProps) {
  return (
    <Link to="/campaigns/$slug" params={{ slug: campaign.slug }} className="block">
      <Card className="hover:shadow-md transition-shadow h-full">
        <CardHeader className="pb-2">
          <div className="flex items-center gap-2 flex-wrap">
            <CardTitle className="text-base">{campaign.name}</CardTitle>
            <Badge variant={campaign.role === "gm" ? "default" : "secondary"}>
              {campaign.role === "gm" ? "GM" : "Player"}
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="pb-2">
          {campaign.description ? (
            <p className="text-sm text-muted-foreground line-clamp-2">{campaign.description}</p>
          ) : (
            <p className="text-sm text-muted-foreground italic">No description.</p>
          )}
        </CardContent>
        <CardFooter>
          <p className="text-xs text-muted-foreground">Created {new Date(campaign.created_at).toLocaleDateString()}</p>
        </CardFooter>
      </Card>
    </Link>
  );
}
