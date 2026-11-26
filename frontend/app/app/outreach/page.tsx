import type { Metadata } from "next";
import { AppPlaceholderPage } from "@/components/app/app-placeholder-page";

export const metadata: Metadata = {
  title: "Outreach Drafts",
};

export default function OutreachDraftsPage() {
  return (
    <AppPlaceholderPage
      title="Outreach Drafts"
      subtitle="Review, edit, approve, or reject personalized founder outreach drafts grounded in your profile and company research."
      plannedScope={[
        "Editable subject line and message body with draft versioning.",
        "Personalization rationale linked to candidate projects and company sources.",
        "Explicit approve and reject actions—no automatic email sending.",
      ]}
    />
  );
}
