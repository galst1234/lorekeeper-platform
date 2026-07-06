import { CreateCampaignForm } from "@/components/campaign/create-campaign-form";
import { PageContainer } from "@/components/layout/page-container";
import { HomeShell } from "@/layouts/home-shell";

export function NewCampaignPage() {
  return (
    <HomeShell>
      <PageContainer className="flex justify-center">
        <CreateCampaignForm />
      </PageContainer>
    </HomeShell>
  );
}
