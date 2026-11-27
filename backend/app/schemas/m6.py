from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.m4 import DataOrigin, VerificationStatus

OutreachIntent = Literal["job_interest", "exploratory", "general_interest"]
OutreachDraftStatus = Literal["draft", "reviewed", "approved", "archived"]
ClaimCategory = Literal[
    "company",
    "founder",
    "hiring",
    "funding",
    "job_opportunity",
    "candidate_profile",
]
SupportStatus = Literal["supported", "partially_supported", "unsupported"]
VersionChangeType = Literal["generated", "edited", "status_change"]


class OutreachDraftCreateRequest(BaseModel):
    """Request payload to generate an evidence-grounded founder outreach draft."""

    candidate_id: str = Field(min_length=1)
    matching_run_id: str = Field(min_length=1)
    match_result_id: str = Field(min_length=1)
    company_id: str = Field(min_length=1)
    founder_id: str = Field(min_length=1)
    outreach_intent: OutreachIntent


class OutreachDraftUpdateRequest(BaseModel):
    """Controlled edit payload requiring expected_version for optimistic concurrency control."""

    model_config = ConfigDict(extra="forbid")

    expected_version: int = Field(ge=1)
    subject: str | None = Field(default=None, min_length=1, max_length=500)
    body: str | None = Field(default=None, min_length=1)

    @field_validator("subject", "body")
    @classmethod
    def _strip_and_require_non_empty(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Field cannot be empty or whitespace-only.")
        return cleaned


class OutreachStrategy(BaseModel):
    """Structured outreach strategy distinguishing verified facts, candidate info, inferences, and gaps."""

    why_company_relevant: str = Field(min_length=1)
    why_founder_appropriate: str = Field(min_length=1)
    relevant_candidate_strengths: list[str] = Field(default_factory=list)
    company_facts_for_personalization: list[str] = Field(default_factory=list)
    opportunity_assessment_summary: str = Field(min_length=1)
    candidate_ask: str = Field(min_length=1)
    verified_facts: list[str] = Field(default_factory=list)
    candidate_provided_facts: list[str] = Field(default_factory=list)
    inferences: list[str] = Field(default_factory=list)
    claims_requiring_review: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)


class StructuredOutreachClaim(BaseModel):
    """Single factual personalization claim linked to its evidence basis."""

    claim_text: str = Field(min_length=1)
    claim_category: ClaimCategory
    evidence_ids: list[str] = Field(default_factory=list)
    verification_status: VerificationStatus = "unverified"
    support_status: SupportStatus = "supported"
    requires_review: bool = False


class StructuredOutreachEmail(BaseModel):
    """Structured LLM output for personalized founder outreach."""

    subject: str = Field(min_length=1, max_length=500)
    greeting: str = Field(min_length=1)
    opening_personalization: str = Field(min_length=1)
    candidate_introduction: str = Field(min_length=1)
    relevant_skills_experience: str = Field(min_length=1)
    reason_for_contacting: str = Field(min_length=1)
    value_proposition: str = Field(min_length=1)
    call_to_action: str = Field(min_length=1)
    closing: str = Field(min_length=1)
    body: str = Field(min_length=1)

    outreach_intent: OutreachIntent
    personalization_rationale: str = Field(min_length=1)
    candidate_strengths_used: list[str] = Field(default_factory=list)
    company_facts_used: list[str] = Field(default_factory=list)
    evidence_references: list[str] = Field(default_factory=list)
    claims: list[StructuredOutreachClaim] = Field(default_factory=list)
    unsupported_or_uncertain_claims: list[str] = Field(default_factory=list)
    review_warnings: list[str] = Field(default_factory=list)


class FounderSummaryResponse(BaseModel):
    """Conservative founder summary without fabricated contact details."""

    founder_id: str
    full_name: str
    role_title: str | None = None
    public_profile_url: str | None = None
    email: str | None = None
    verification_status: VerificationStatus
    data_origin: DataOrigin
    conflict_notes: str | None = None


class OutreachDraftEvidenceItemResponse(BaseModel):
    """Persisted claim-level evidence grounding item with SourceEvidence provenance."""

    id: str
    outreach_draft_id: str
    source_evidence_id: str | None = None
    company_id: str | None = None
    claim_category: ClaimCategory
    claim_text: str
    verification_status: VerificationStatus
    support_status: SupportStatus
    requires_review: bool
    source_url: str | None = None
    source_title: str | None = None
    excerpt: str | None = None
    publication_date: datetime | None = None
    created_at: datetime


class OutreachDraftEvidenceListResponse(BaseModel):
    """Response for GET /api/outreach-drafts/{draft_id}/evidence."""

    outreach_draft_id: str
    items: list[OutreachDraftEvidenceItemResponse]


class OutreachDraftVersionResponse(BaseModel):
    """Version snapshot for GET /api/outreach-drafts/{draft_id}/versions."""

    id: str
    outreach_draft_id: str
    version: int
    subject: str
    body: str
    change_type: VersionChangeType
    status_at_version: OutreachDraftStatus
    created_at: datetime


class OutreachDraftVersionListResponse(BaseModel):
    """Response for GET /api/outreach-drafts/{draft_id}/versions."""

    outreach_draft_id: str
    current_version: int
    items: list[OutreachDraftVersionResponse]


class OutreachDraftResponse(BaseModel):
    """Full outreach draft response."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    candidate_id: str
    matching_run_id: str
    match_result_id: str
    company_id: str
    company_name: str
    founder_id: str
    founder: FounderSummaryResponse
    outreach_intent: OutreachIntent
    status: OutreachDraftStatus
    subject: str
    body: str
    original_subject: str
    original_body: str
    personalization_rationale: str
    strategy: OutreachStrategy
    structured_sections: dict[str, str] = Field(default_factory=dict)
    candidate_strengths_used: list[str] = Field(default_factory=list)
    company_facts_used: list[str] = Field(default_factory=list)
    unsupported_claims: list[str] = Field(default_factory=list)
    review_warnings: list[str] = Field(default_factory=list)
    requires_review: bool = False
    generation_provider: str
    generation_model: str | None = None
    data_origin: DataOrigin
    version: int
    evidence_count: int = 0
    created_at: datetime
    updated_at: datetime
    reviewed_at: datetime | None = None
    approved_at: datetime | None = None
    archived_at: datetime | None = None


class OutreachDraftListResponse(BaseModel):
    """Paginated list of outreach drafts."""

    items: list[OutreachDraftResponse]
    total: int
    limit: int
    offset: int
