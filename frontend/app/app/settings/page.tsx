import type { Metadata } from "next";
import { AppPlaceholderPage } from "@/components/app/app-placeholder-page";

export const metadata: Metadata = {
  title: "Settings",
};

export default function SettingsPage() {
  return (
    <AppPlaceholderPage
      title="Settings"
      subtitle="View workspace configuration, demo/live provider status, and privacy controls."
      plannedScope={[
        "Clear visibility into demo vs. live AI and search provider modes.",
        "Candidate data retention and session controls.",
        "Honest indication of capabilities deferred beyond the MVP.",
      ]}
    />
  );
}
