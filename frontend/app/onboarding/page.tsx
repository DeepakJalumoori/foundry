import type { Metadata } from "next";
import { MarketingHeader } from "@/components/marketing/marketing-header";
import { OnboardingFlow } from "@/components/onboarding/onboarding-flow";

export const metadata: Metadata = {
  title: "Onboarding Preview",
  description:
    "Preview Foundry's candidate profile and opportunity preferences onboarding flow.",
};

export default function OnboardingPage() {
  return (
    <div className="flex min-h-full flex-1 flex-col">
      <MarketingHeader />
      <main
        id="main-content"
        tabIndex={-1}
        className="flex flex-1 flex-col focus:outline-none"
      >
        <OnboardingFlow />
      </main>
    </div>
  );
}
