import { createFileRoute } from "@tanstack/react-router";
import { CampaignDetailPage } from "@/pages/campaign-detail-page";

export const Route = createFileRoute("/campaigns/$slug/")({
  component: CampaignDetailPage,
});
