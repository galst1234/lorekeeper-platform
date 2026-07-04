import { getRouteApi } from "@tanstack/react-router";
import { OnboardingForm } from "@/components/onboarding/onboarding-form";

const Route = getRouteApi("/onboarding");

export function OnboardingPage() {
  const { redirectToPath } = Route.useSearch();
  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      <OnboardingForm redirectToPath={redirectToPath} />
    </div>
  );
}
