import { useSuspenseQuery } from "@tanstack/react-query";
import { getRouteApi } from "@tanstack/react-router";
import { getCampaignOptions } from "@/api/generated/@tanstack/react-query.gen";
import { CampaignHeader } from "@/components/campaign/campaign-header";
import { MembersList } from "@/components/campaign/members-list";
import { PageContainer } from "@/components/layout/page-container";

const Route = getRouteApi("/campaigns/$slug/");

export function CampaignDetailPage() {
  const { slug } = Route.useParams();
  const { data: campaign } = useSuspenseQuery(getCampaignOptions({ path: { slug } }));

  return (
    <PageContainer className="space-y-8">
      <CampaignHeader campaign={campaign} />
      <MembersList slug={slug} />
    </PageContainer>
  );
}
