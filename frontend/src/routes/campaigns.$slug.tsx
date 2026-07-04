import { createFileRoute, Outlet, redirect } from "@tanstack/react-router";
import { campaignQueryOptions } from "@/api/campaigns";
import { charactersQueryOptions } from "@/api/characters";
import { chronicleEntriesQueryOptions } from "@/api/chronicle";
import { itemsQueryOptions } from "@/api/items";
import { meQueryOptions } from "@/api/me";
import { membersQueryOptions } from "@/api/membership";
import { CampaignShell } from "@/layouts/campaign-shell";
import { doesSessionExist } from "@/lib/auth";

export const Route = createFileRoute("/campaigns/$slug")({
  beforeLoad: async ({ context, params }) => {
    if (!(await doesSessionExist())) {
      throw redirect({ to: "/login" });
    }
    const me = await context.queryClient.fetchQuery(meQueryOptions);
    if (me.display_name === null) {
      throw redirect({ to: "/onboarding" });
    }
    const campaign = await context.queryClient.ensureQueryData(campaignQueryOptions(me.id, params.slug));
    if (campaign.slug !== params.slug) {
      throw redirect({ to: "/campaigns/$slug", params: { slug: campaign.slug } });
    }
    await context.queryClient.ensureQueryData(charactersQueryOptions(params.slug));
    await context.queryClient.ensureQueryData(itemsQueryOptions(params.slug));
    await context.queryClient.ensureQueryData(chronicleEntriesQueryOptions(params.slug));
    await context.queryClient.ensureQueryData(membersQueryOptions(params.slug));
  },
  component: SlugLayout,
});

function SlugLayout() {
  const { slug } = Route.useParams();
  return (
    <CampaignShell slug={slug}>
      <Outlet key={slug} />
    </CampaignShell>
  );
}
