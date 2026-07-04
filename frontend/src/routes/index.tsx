import { useSuspenseQuery } from "@tanstack/react-query";
import { createFileRoute, Link, redirect } from "@tanstack/react-router";
import { Scroll } from "lucide-react";
import { getMeOptions, listCampaignsOptions } from "@/api/generated/@tanstack/react-query.gen";
import { CampaignCard } from "@/components/campaign/campaign-card";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { HomeShell } from "@/layouts/home-shell";
import { doesSessionExist } from "@/lib/auth";

export const Route = createFileRoute("/")({
  beforeLoad: async ({ context }) => {
    if (!(await doesSessionExist())) {
      throw redirect({ to: "/login" });
    }
    const me = await context.queryClient.fetchQuery(getMeOptions());
    if (me.display_name === null) {
      throw redirect({ to: "/onboarding" });
    }
    await context.queryClient.ensureQueryData(listCampaignsOptions());
  },
  pendingComponent: HomePendingComponent,
  pendingMs: 0,
  component: HomePage,
});

function HomePendingComponent() {
  return (
    <div className="min-h-screen bg-background">
      <div className="h-14 border-b" />
      <div className="max-w-3xl mx-auto px-6 py-8">
        <div className="flex items-center justify-between mb-8">
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-9 w-36" />
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-36 rounded-lg" />
          ))}
        </div>
      </div>
    </div>
  );
}

function HomePage() {
  const { data: campaigns } = useSuspenseQuery(listCampaignsOptions());

  return (
    <HomeShell>
      <div className="max-w-3xl mx-auto px-6 py-8">
        <div className="flex items-center justify-between mb-8">
          <h1 className="text-2xl font-semibold">Your Campaigns</h1>
          <Button asChild>
            <Link to="/campaigns/new">+ New Campaign</Link>
          </Button>
        </div>

        {campaigns.length === 0 ? (
          <Card className="border-dashed">
            <CardContent className="flex flex-col items-center text-center py-12 gap-4">
              <Scroll className="h-10 w-10 text-muted-foreground" />
              <h2 className="text-lg font-semibold">No campaigns yet</h2>
              <p className="text-sm text-muted-foreground">Create your first campaign to get started.</p>
              <Button asChild>
                <Link to="/campaigns/new">Create your first campaign</Link>
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {campaigns.map((campaign) => (
              <CampaignCard key={campaign.id} campaign={campaign} />
            ))}
          </div>
        )}
      </div>
    </HomeShell>
  );
}
