import { CreateCampaignForm } from "@/components/campaign/create-campaign-form";
import { HomeShell } from "@/layouts/home-shell";

export function NewCampaignPage() {
  return (
    <HomeShell>
      <CreateCampaignForm />
    </HomeShell>
  );
}
