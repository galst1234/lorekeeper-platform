import { CreateCampaignForm } from "@/components/campaign/create-campaign-form";
import { HomeShell } from "@/layouts/home-shell";

export function NewCampaignPage() {
  return (
    <HomeShell>
      <div className="flex justify-center py-12 px-6">
        <CreateCampaignForm />
      </div>
    </HomeShell>
  );
}
