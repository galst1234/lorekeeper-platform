import { createFileRoute, redirect } from "@tanstack/react-router";
import { CreateCampaignForm } from "@/components/campaign/create-campaign-form";
import { HomeShell } from "@/layouts/home-shell";
import { doesSessionExist, getCurrentUserOptions } from "@/lib/auth";

export const Route = createFileRoute("/campaigns/new")({
  beforeLoad: async ({ context }) => {
    if (!(await doesSessionExist())) {
      context.queryClient.clear();
      throw redirect({ to: "/login" });
    }
    const me = await context.queryClient.fetchQuery(getCurrentUserOptions(context.queryClient));
    if (me.display_name === null) {
      throw redirect({ to: "/onboarding" });
    }
  },
  component: NewCampaignPage,
});

function NewCampaignPage() {
  return (
    <HomeShell>
      <div className="flex justify-center py-12 px-6">
        <CreateCampaignForm />
      </div>
    </HomeShell>
  );
}
