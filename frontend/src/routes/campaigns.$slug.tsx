import { createFileRoute, redirect } from "@tanstack/react-router";
import {
  getCampaignOptions,
  listCharactersOptions,
  listChronicleEntriesOptions,
  listItemsOptions,
  listMembersOptions,
} from "@/api/generated/@tanstack/react-query.gen";
import { CampaignLayout } from "@/layouts/campaign-layout";
import { doesSessionExist, getCurrentUserOptions } from "@/lib/auth";

export const Route = createFileRoute("/campaigns/$slug")({
  beforeLoad: async ({ context, params }) => {
    if (!(await doesSessionExist())) {
      context.queryClient.clear();
      throw redirect({ to: "/login" });
    }
    const me = await context.queryClient.fetchQuery(getCurrentUserOptions(context.queryClient));
    if (me.display_name === null) {
      throw redirect({ to: "/onboarding" });
    }
    const campaign = await context.queryClient.ensureQueryData(getCampaignOptions({ path: { slug: params.slug } }));
    if (campaign.slug !== params.slug) {
      throw redirect({ to: "/campaigns/$slug", params: { slug: campaign.slug } });
    }
    await context.queryClient.ensureQueryData(listCharactersOptions({ path: { slug: params.slug } }));
    await context.queryClient.ensureQueryData(listItemsOptions({ path: { slug: params.slug } }));
    await context.queryClient.ensureQueryData(listChronicleEntriesOptions({ path: { slug: params.slug } }));
    await context.queryClient.ensureQueryData(listMembersOptions({ path: { slug: params.slug } }));
  },
  component: CampaignLayout,
});
