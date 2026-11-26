import type { Metadata } from "next";
import { AppPlaceholderPage } from "@/components/app/app-placeholder-page";

export const metadata: Metadata = {
  title: "Discover Startups",
};

export default function DiscoverStartupsPage() {
  return (
    <AppPlaceholderPage
      title="Discover Startups"
      subtitle="Run startup discovery workflows aligned with your candidate profile and preferences, and inspect company research evidence."
      plannedScope={[
        "Start a discovery workflow through the SearchProvider interface.",
        "Inspect clearly labelled demo vs. live company records.",
        "View company research summaries backed by traceable sources.",
      ]}
    />
  );
}
