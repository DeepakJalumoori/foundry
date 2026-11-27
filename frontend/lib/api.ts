export type OutreachIntent = "job_interest" | "exploratory" | "general_interest";
export type OutreachDraftStatus = "draft" | "reviewed" | "approved" | "archived";
export type VerificationStatus = "verified" | "unverified" | "requires_review";
export type DataOrigin = "real" | "demo";

export interface ApiErrorPayload {
  code?: string;
  detail?: string;
}

export class ApiRequestError extends Error {
  status: number;
  code: string;

  constructor(status: number, code: string, message: string) {
    super(message);
    this.name = "ApiRequestError";
    this.status = status;
    this.code = code;
  }
}

export interface FounderSummary {
  founder_id: string;
  full_name: string;
  role_title: string | null;
  public_profile_url: string | null;
  email: string | null;
  verification_status: VerificationStatus;
  data_origin: DataOrigin;
  conflict_notes: string | null;
}

export interface CompanyFounderItem {
  id: string;
  company_id: string;
  full_name: string;
  role_title: string | null;
  public_profile_url: string | null;
  biography: string | null;
  verification_status: VerificationStatus;
  conflict_notes: string | null;
  data_origin: DataOrigin;
}

export interface CompanyFoundersResponse {
  company_id: string;
  items: CompanyFounderItem[];
}

export interface MatchResultSummary {
  match_id: string;
  matching_run_id: string;
  company_id: string;
  company_name: string;
  fit_score: number;
  fit_coverage: number;
  opportunity_type: "active" | "hidden" | "insufficient_evidence";
  evidence_strength: "strong" | "moderate" | "weak" | "insufficient";
  ranking_position: number;
  ranking_score: number;
  explanation: string;
  requires_review: boolean;
  data_origin: DataOrigin;
}

export interface MatchResultsListResponse {
  matching_run_id: string;
  items: MatchResultSummary[];
  total: number;
  limit: number;
  offset: number;
}

export interface OutreachStrategy {
  why_company_relevant: string;
  why_founder_appropriate: string;
  relevant_candidate_strengths: string[];
  company_facts_for_personalization: string[];
  opportunity_assessment_summary: string;
  candidate_ask: string;
  verified_facts: string[];
  candidate_provided_facts: string[];
  inferences: string[];
  claims_requiring_review: string[];
  missing_information: string[];
}

export interface OutreachDraft {
  id: string;
  candidate_id: string;
  matching_run_id: string;
  match_result_id: string;
  company_id: string;
  company_name: string;
  founder_id: string;
  founder: FounderSummary;
  outreach_intent: OutreachIntent;
  status: OutreachDraftStatus;
  subject: string;
  body: string;
  original_subject: string;
  original_body: string;
  personalization_rationale: string;
  strategy: OutreachStrategy;
  structured_sections: Record<string, string>;
  candidate_strengths_used: string[];
  company_facts_used: string[];
  unsupported_claims: string[];
  review_warnings: string[];
  requires_review: boolean;
  generation_provider: string;
  generation_model: string | null;
  data_origin: DataOrigin;
  version: number;
  evidence_count: number;
  created_at: string;
  updated_at: string;
  reviewed_at: string | null;
  approved_at: string | null;
  archived_at: string | null;
}

export interface OutreachDraftListResponse {
  items: OutreachDraft[];
  total: number;
  limit: number;
  offset: number;
}

export interface OutreachDraftEvidenceItem {
  id: string;
  outreach_draft_id: string;
  source_evidence_id: string | null;
  company_id: string | null;
  claim_category: string;
  claim_text: string;
  verification_status: VerificationStatus;
  support_status: "supported" | "partially_supported" | "unsupported";
  requires_review: boolean;
  source_url: string | null;
  source_title: string | null;
  excerpt: string | null;
  publication_date: string | null;
  created_at: string;
}

export interface OutreachDraftEvidenceListResponse {
  outreach_draft_id: string;
  items: OutreachDraftEvidenceItem[];
}

export interface OutreachDraftVersionItem {
  id: string;
  outreach_draft_id: string;
  version: number;
  subject: string;
  body: string;
  change_type: "generated" | "edited" | "status_change";
  status_at_version: OutreachDraftStatus;
  created_at: string;
}

export interface OutreachDraftVersionListResponse {
  outreach_draft_id: string;
  current_version: number;
  items: OutreachDraftVersionItem[];
}

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ||
  "http://localhost:8000/api";

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
  });

  if (!response.ok) {
    let payload: ApiErrorPayload = {};
    try {
      payload = (await response.json()) as ApiErrorPayload;
    } catch {
      payload = {};
    }
    throw new ApiRequestError(
      response.status,
      payload.code ?? "API_ERROR",
      payload.detail ?? `Request failed with status ${response.status}`,
    );
  }

  return (await response.json()) as T;
}

export function getMatchingRunResults(
  runId: string,
  limit = 20,
  offset = 0,
): Promise<MatchResultsListResponse> {
  return requestJson<MatchResultsListResponse>(
    `/matching-runs/${encodeURIComponent(runId)}/results?limit=${limit}&offset=${offset}`,
  );
}

export function getCompanyFounders(
  companyId: string,
): Promise<CompanyFoundersResponse> {
  return requestJson<CompanyFoundersResponse>(
    `/companies/${encodeURIComponent(companyId)}/founders`,
  );
}

export function generateOutreachDraft(payload: {
  candidate_id: string;
  matching_run_id: string;
  match_result_id: string;
  company_id: string;
  founder_id: string;
  outreach_intent: OutreachIntent;
}): Promise<OutreachDraft> {
  return requestJson<OutreachDraft>("/outreach-drafts", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function listOutreachDrafts(filters?: {
  candidate_id?: string;
  company_id?: string;
  matching_run_id?: string;
  status?: OutreachDraftStatus;
  limit?: number;
  offset?: number;
}): Promise<OutreachDraftListResponse> {
  const params = new URLSearchParams();
  if (filters?.candidate_id) params.set("candidate_id", filters.candidate_id);
  if (filters?.company_id) params.set("company_id", filters.company_id);
  if (filters?.matching_run_id) {
    params.set("matching_run_id", filters.matching_run_id);
  }
  if (filters?.status) params.set("status", filters.status);
  if (filters?.limit !== undefined) params.set("limit", String(filters.limit));
  if (filters?.offset !== undefined) params.set("offset", String(filters.offset));
  const qs = params.toString();
  return requestJson<OutreachDraftListResponse>(
    `/outreach-drafts${qs ? `?${qs}` : ""}`,
  );
}

export function getOutreachDraft(draftId: string): Promise<OutreachDraft> {
  return requestJson<OutreachDraft>(
    `/outreach-drafts/${encodeURIComponent(draftId)}`,
  );
}

export function updateOutreachDraft(
  draftId: string,
  payload: { expected_version: number; subject?: string; body?: string },
): Promise<OutreachDraft> {
  return requestJson<OutreachDraft>(
    `/outreach-drafts/${encodeURIComponent(draftId)}`,
    {
      method: "PATCH",
      body: JSON.stringify(payload),
    },
  );
}

export function reviewOutreachDraft(draftId: string): Promise<OutreachDraft> {
  return requestJson<OutreachDraft>(
    `/outreach-drafts/${encodeURIComponent(draftId)}/review`,
    { method: "POST" },
  );
}

export function approveOutreachDraft(draftId: string): Promise<OutreachDraft> {
  return requestJson<OutreachDraft>(
    `/outreach-drafts/${encodeURIComponent(draftId)}/approve`,
    { method: "POST" },
  );
}

export function archiveOutreachDraft(draftId: string): Promise<OutreachDraft> {
  return requestJson<OutreachDraft>(
    `/outreach-drafts/${encodeURIComponent(draftId)}/archive`,
    { method: "POST" },
  );
}

export function getOutreachDraftEvidence(
  draftId: string,
): Promise<OutreachDraftEvidenceListResponse> {
  return requestJson<OutreachDraftEvidenceListResponse>(
    `/outreach-drafts/${encodeURIComponent(draftId)}/evidence`,
  );
}

export function getOutreachDraftVersions(
  draftId: string,
): Promise<OutreachDraftVersionListResponse> {
  return requestJson<OutreachDraftVersionListResponse>(
    `/outreach-drafts/${encodeURIComponent(draftId)}/versions`,
  );
}
