import { getRouteApi, Outlet } from "@tanstack/react-router";
import { CampaignShell } from "@/layouts/campaign-shell";

const Route = getRouteApi("/campaigns/$slug");

export function CampaignLayout() {
  const { slug } = Route.useParams();
  return (
    <CampaignShell slug={slug}>
      <Outlet key={slug} />
    </CampaignShell>
  );
}
