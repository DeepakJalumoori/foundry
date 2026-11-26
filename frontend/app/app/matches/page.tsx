import type { Metadata } from "next";
import { AppPlaceholderPage } from "@/components/app/app-placeholder-page";

export const metadata: Metadata = {
  title: "My Matches",
};

export default function MyMatchesPage() {
  return (
    <AppPlaceholderPage
      title="My Matches"
      subtitle="Review deterministic candidate-company fit scores, dimension breakdowns, and missing-skill gaps."
      plannedScope={[
        "Weighted fit scores (Skills 30%, Role 25%, Experience 15%, Projects 15%, Preferences 10%, Work mode 5%).",
        "Inspectable explanations and missing-skill indicators.",
        "Direct navigation to company detail and research evidence.",
      ]}
    />
  );
}
