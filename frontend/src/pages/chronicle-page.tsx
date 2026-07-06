import { getRouteApi } from "@tanstack/react-router";
import { ChronicleSection } from "@/components/chronicle/chronicle-section";
import { PageContainer } from "@/components/layout/page-container";

const Route = getRouteApi("/campaigns/$slug/chronicle/");

export function ChroniclePage() {
  const { slug } = Route.useParams();

  return (
    <PageContainer className="space-y-8">
      <ChronicleSection slug={slug} />
    </PageContainer>
  );
}
