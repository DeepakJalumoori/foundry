import type { Metadata } from "next";
import { AppPlaceholderPage } from "@/components/app/app-placeholder-page";

export const metadata: Metadata = {
  title: "My Profile",
};

export default function MyProfilePage() {
  return (
    <AppPlaceholderPage
      title="My Profile"
      subtitle="Upload a PDF resume, review extracted candidate details, and configure your opportunity preferences."
      phaseLabel="Profile & preferences UI: T020–T022"
      plannedScope={[
        "PDF resume upload and structured profile review/editing.",
        "Skills, education, experience, projects, and portfolio links.",
        "Role, technology, location, work-mode, and stage preferences.",
      ]}
    />
  );
}
