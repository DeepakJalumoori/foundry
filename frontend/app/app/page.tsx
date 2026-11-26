import type { Metadata } from "next";
import { AppPlaceholderPage } from "@/components/app/app-placeholder-page";

export const metadata: Metadata = {
  title: "Overview",
};

export default function AppOverviewPage() {
  return (
    <AppPlaceholderPage
      title="Workspace Overview"
      subtitle="Your central view for discovery workflow status, relevant startup matches, outreach drafts awaiting approval, and recent agent activity."
      phaseLabel="Dashboard implementation: T023"
      plannedScope={[
        "Current discovery workflow status and step-by-step progress.",
        "Recent startup matches with transparent dimension-level fit reasons.",
        "Outreach drafts awaiting explicit candidate review and approval.",
        "Clear next actions and honest empty or demo states.",
      ]}
    />
  );
}
