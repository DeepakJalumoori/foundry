export type OpportunityType = "active" | "hidden";

export type EmailVerificationStatus = "verified" | "unverified" | "unavailable";

export interface SignalItem {
  label: string;
  detail: string;
  sourceLabel: string;
  sourceUrl: string;
  date: string;
}

export interface DemoStartupResult {
  id: string;
  companyName: string;
  description: string;
  fundingStage: string;
  fundingEvidence: SignalItem;
  opportunityType: OpportunityType;
  hiringSignals: SignalItem[];
  whyReachOut: string;
  founderName: string;
  founderRole: string;
  founderEmail: string | null;
  emailSource: string;
  emailVerification: EmailVerificationStatus;
  matchScore: number;
  matchExplanation: string;
  emailDraftSubject: string;
  emailDraftBody: string;
}
