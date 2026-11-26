import { MarketingHeader } from "@/components/marketing/marketing-header";
import { HeroSection } from "@/components/marketing/hero-section";
import { ProblemSection } from "@/components/marketing/problem-section";
import { WorkflowSection } from "@/components/marketing/workflow-section";
import { StartupDiscoverySection } from "@/components/marketing/startup-discovery-section";
import { ProductPreviewSection } from "@/components/marketing/product-preview-section";
import { FounderIntelligenceSection } from "@/components/marketing/founder-intelligence-section";
import { OutreachPreviewSection } from "@/components/marketing/outreach-preview-section";

export default function Home() {
  return (
    <div className="flex min-h-full flex-1 flex-col">
      <MarketingHeader />
      <main id="main-content" tabIndex={-1} className="flex flex-1 flex-col focus:outline-none">
        <HeroSection />
        <ProblemSection />
        <WorkflowSection />
        <StartupDiscoverySection />
        <ProductPreviewSection />
        <FounderIntelligenceSection />
        <OutreachPreviewSection />
      </main>
    </div>
  );
}
