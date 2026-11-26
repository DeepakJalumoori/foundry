import type { Metadata } from "next";
import { AppPlaceholderPage } from "@/components/app/app-placeholder-page";

export const metadata: Metadata = {
  title: "Founder Contacts",
};

export default function FounderContactsPage() {
  return (
    <AppPlaceholderPage
      title="Founder Contacts"
      subtitle="Inspect founder and hiring-contact records with explicit source attribution and verification status."
      plannedScope={[
        "Founder and technical leader profiles linked to researched startups.",
        "Explicit verified, unverified, and unavailable contact status.",
        "Source links without fabricated emails or guessed contact details.",
      ]}
    />
  );
}
