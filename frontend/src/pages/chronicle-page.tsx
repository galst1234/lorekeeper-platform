import { getRouteApi } from "@tanstack/react-router";
import { ChronicleSection } from "@/components/chronicle/chronicle-section";

const Route = getRouteApi("/campaigns/$slug/chronicle/");

export function ChroniclePage() {
  const { slug } = Route.useParams();

  return (
    <div className="max-w-4xl mx-auto px-6 py-8 space-y-8">
      <ChronicleSection slug={slug} />
    </div>
  );
}
