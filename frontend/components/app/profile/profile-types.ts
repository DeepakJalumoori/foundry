export interface ResumeFileMeta {
  name: string;
  sizeBytes: number;
}

export interface ProfileFormData {
  fullName: string;
  email: string;
  headline: string;
  summary: string;
  linkedinUrl: string;
  githubUrl: string;
  portfolioUrl: string;
  skills: string[];
  resume: ResumeFileMeta | null;
}

export const INITIAL_PROFILE_DATA: ProfileFormData = {
  fullName: "",
  email: "",
  headline: "",
  summary: "",
  linkedinUrl: "",
  githubUrl: "",
  portfolioUrl: "",
  skills: [],
  resume: null,
};

export function isValidEmail(value: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value.trim());
}

export function isValidHttpUrl(value: string): boolean {
  try {
    const parsed = new URL(value.trim());
    return parsed.protocol === "http:" || parsed.protocol === "https:";
  } catch {
    return false;
  }
}

export function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

export interface CompletionSection {
  id: string;
  label: string;
  weight: number;
  complete: boolean;
  hint: string;
}

export interface ProfileCompletionResult {
  percentage: number;
  sections: CompletionSection[];
  incompleteLabels: string[];
}

/**
 * Deterministic profile completion across 5 equal sections (20% each):
 * 1. Basic identity (full name + valid email)
 * 2. Headline & summary
 * 3. At least one valid profile link (LinkedIn, GitHub, or Portfolio)
 * 4. At least one skill/technology
 * 5. Resume PDF attached
 */
export function calculateProfileCompletion(
  data: ProfileFormData
): ProfileCompletionResult {
  const hasValidIdentity =
    data.fullName.trim().length > 0 && isValidEmail(data.email);
  const hasHeadlineAndSummary =
    data.headline.trim().length > 0 && data.summary.trim().length > 0;
  const hasValidLink = [
    data.linkedinUrl,
    data.githubUrl,
    data.portfolioUrl,
  ].some((url) => url.trim().length > 0 && isValidHttpUrl(url));
  const hasSkills = data.skills.length > 0;
  const hasResume = data.resume !== null;

  const sections: CompletionSection[] = [
    {
      id: "identity",
      label: "Basic identity",
      weight: 20,
      complete: hasValidIdentity,
      hint: "Full name and valid email",
    },
    {
      id: "summary",
      label: "Headline & summary",
      weight: 20,
      complete: hasHeadlineAndSummary,
      hint: "Professional headline and short summary",
    },
    {
      id: "links",
      label: "Profile links",
      weight: 20,
      complete: hasValidLink,
      hint: "At least one valid LinkedIn, GitHub, or portfolio URL",
    },
    {
      id: "skills",
      label: "Skills & technologies",
      weight: 20,
      complete: hasSkills,
      hint: "At least one skill tag",
    },
    {
      id: "resume",
      label: "Resume PDF",
      weight: 20,
      complete: hasResume,
      hint: "PDF file attached (max 5 MB)",
    },
  ];

  const percentage = sections.reduce(
    (sum, section) => sum + (section.complete ? section.weight : 0),
    0
  );
  const incompleteLabels = sections
    .filter((section) => !section.complete)
    .map((section) => section.label);

  return { percentage, sections, incompleteLabels };
}
