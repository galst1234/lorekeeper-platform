import { useSuspenseQuery } from "@tanstack/react-query";
import { getRouteApi } from "@tanstack/react-router";
import { getCampaignOptions } from "@/api/generated/@tanstack/react-query.gen";
import { CampaignEditPageEditor } from "@/components/campaign/campaign-edit-page-editor";

const Route = getRouteApi("/campaigns/$slug/edit");

export function CampaignEditPage() {
  const { slug } = Route.useParams();
  const { data: campaign } = useSuspenseQuery(getCampaignOptions({ path: { slug } }));

  return <CampaignEditPageEditor campaign={campaign} />;
}
