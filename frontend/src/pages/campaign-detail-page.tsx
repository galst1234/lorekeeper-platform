import { useSuspenseQuery } from "@tanstack/react-query";
import { getRouteApi } from "@tanstack/react-router";
import { getCampaignOptions } from "@/api/generated/@tanstack/react-query.gen";
import { CampaignHeader } from "@/components/campaign/campaign-header";
import { MembersList } from "@/components/campaign/members-list";

const Route = getRouteApi("/campaigns/$slug/");

export function CampaignDetailPage() {
  const { slug } = Route.useParams();
  const { data: campaign } = useSuspenseQuery(getCampaignOptions({ path: { slug } }));

  return (
    <div className="max-w-4xl mx-auto px-6 py-8 space-y-8">
      <CampaignHeader campaign={campaign} />
      <MembersList slug={slug} />
    </div>
  );
}
