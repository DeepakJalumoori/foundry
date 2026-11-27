from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.m4 import DataOrigin, VerificationStatus

MatchingRunStatus = Literal["pending", "processing", "completed", "completed_with_warnings", "failed"]
M5OpportunityType = Literal["active", "hidden", "insufficient_evidence"]
EvidenceStrength = Literal["strong", "moderate", "weak", "insufficient"]


class RetrievalConfigInput(BaseModel):
    """Optional retrieval parameters for a matching run."""

    limit_per_company: int = Field(default=12, ge=1, le=50)
    include_unverified: bool = True
    data_origin: DataOrigin | None = None


class MatchingRunCreateRequest(BaseModel):
    """Request payload to start an M5 candidate-company matching run."""

    candidate_id: str = Field(min_length=1)
    discovery_run_id: str | None = Field(default=None, min_length=1)
    company_ids: list[str] | None = None
    retrieval_config: RetrievalConfigInput = Field(default_factory=RetrievalConfigInput)

    @model_validator(mode="after")
    def _validate_company_selection(self) -> "MatchingRunCreateRequest":
        if self.company_ids is not None:
            cleaned = [cid.strip() for cid in self.company_ids if cid and cid.strip()]
            if not cleaned:
                raise ValueError("company_ids cannot be empty when explicitly provided.")
            self.company_ids = list(dict.fromkeys(cleaned))
        if self.discovery_run_id is None and not self.company_ids:
            raise ValueError("Either discovery_run_id or company_ids must be provided.")
        return self


class RetrievedEvidenceItem(BaseModel):
    """Normalized retrieved evidence document with full M4 provenance."""

    evidence_document_id: str
    source_evidence_id: str
    company_id: str
    entity_type: str
    document_title: str
    content: str
    source_url: str
    source_title: str
    publication_date: datetime | None = None
    retrieved_at: datetime
    verification_status: VerificationStatus
    data_origin: DataOrigin
    bm25_score: float | None = None


class EvidenceQualityReport(BaseModel):
    """Deterministic assessment of retrieved evidence quality for a company."""

    company_id: str
    total_documents: int = Field(ge=0)
    verified_documents: int = Field(ge=0)
    has_research_evidence: bool = False
    has_funding_evidence: bool = False
    has_hiring_evidence: bool = False
    has_job_evidence: bool = False
    sufficient_for_fit: bool = False
    warnings: list[str] = Field(default_factory=list)


class StructuredCompanyAssessment(BaseModel):
    """Validated qualitative LLM assessment of candidate-company fit."""

    relevant_company_capabilities: list[str] = Field(default_factory=list)
    required_technical_skills: list[str] = Field(default_factory=list)
    candidate_matching_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    relevant_experience_notes: list[str] = Field(default_factory=list)
    project_relevance_notes: list[str] = Field(default_factory=list)
    domain_relevance_notes: list[str] = Field(default_factory=list)
    role_compatibility_notes: list[str] = Field(default_factory=list)
    evidence_references: list[str] = Field(default_factory=list)
    explanation: str = Field(min_length=1)
    uncertainties: list[str] = Field(default_factory=list)
    requires_review: bool = False


class DimensionScore(BaseModel):
    """Single deterministic scoring dimension breakdown."""

    dimension: str
    raw_score: float | None = Field(default=None, ge=0.0, le=100.0)
    max_score: float = Field(default=100.0, gt=0.0)
    weight: float = Field(gt=0.0, le=100.0)
    weighted_contribution: float = Field(default=0.0, ge=0.0, le=100.0)
    assessable: bool = True
    supporting_evidence_ids: list[str] = Field(default_factory=list)
    explanation: str


class FitScoreResult(BaseModel):
    """Deterministic candidate-company fit score result."""

    scoring_version: str = "fit_v1"
    fit_score: float = Field(ge=0.0, le=100.0)
    fit_coverage: float = Field(ge=0.0, le=100.0)
    assessable_weight: float = Field(ge=0.0, le=100.0)
    total_weight: float = Field(default=100.0, gt=0.0)
    dimensions: list[DimensionScore]
    requires_review: bool = False


class OpportunityAssessment(BaseModel):
    """Independent deterministic opportunity evidence classification."""

    opportunity_type: M5OpportunityType
    evidence_strength: EvidenceStrength
    observed_facts: list[str] = Field(default_factory=list)
    supporting_evidence_ids: list[str] = Field(default_factory=list)
    classification_reason: str
    uncertainties: list[str] = Field(default_factory=list)
    missing_evidence: list[str] = Field(default_factory=list)
    requires_review: bool = False


class MatchingRunResponse(BaseModel):
    """Public response for an M5 matching run."""

    model_config = ConfigDict(from_attributes=True)

    run_id: str
    candidate_id: str
    discovery_run_id: str | None = None
    company_ids: list[str] = Field(default_factory=list)
    status: MatchingRunStatus
    scoring_version: str
    ranking_version: str
    retrieval_config: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    error_code: str | None = None
    error_message: str | None = None
    requires_review: bool = False
    result_count: int = 0
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None


class MatchResultSummaryResponse(BaseModel):
    """Ranked match result item exposed by GET /api/matching-runs/{run_id}/results."""

    match_id: str
    matching_run_id: str
    company_id: str
    company_name: str
    company_stage: str
    company_industry: str | None = None
    ranking_position: int
    ranking_version: str
    ranking_explanation: str
    ranking_factors: dict[str, Any] = Field(default_factory=dict)
    fit_score: float
    fit_coverage: float
    scoring_version: str
    opportunity_type: M5OpportunityType
    evidence_strength: EvidenceStrength
    explanation: str
    requires_review: bool
    data_origin: DataOrigin
    created_at: datetime


class MatchResultsListResponse(BaseModel):
    """Paginated ranked match results for a matching run."""

    matching_run_id: str
    items: list[MatchResultSummaryResponse]
    total: int
    limit: int
    offset: int


class MatchDetailResponse(BaseModel):
    """Full individual match assessment exposed by GET /api/matches/{match_id}."""

    match_id: str
    matching_run_id: str
    company_id: str
    company_snapshot: dict[str, Any]
    ranking_position: int
    ranking_version: str
    ranking_explanation: str
    ranking_factors: dict[str, Any]
    fit_score: float
    fit_coverage: float
    scoring_version: str
    dimension_breakdown: list[DimensionScore]
    opportunity_assessment: OpportunityAssessment
    qualitative_assessment: StructuredCompanyAssessment | None = None
    explanation: str
    requires_review: bool
    data_origin: DataOrigin
    created_at: datetime


class MatchEvidenceItemResponse(BaseModel):
    """Retrieved evidence record exposed by GET /api/matches/{match_id}/evidence."""

    retrieval_record_id: str
    evidence_document_id: str | None = None
    source_evidence_id: str | None = None
    company_id: str
    query_text: str
    rank_order: int
    bm25_score: float | None = None
    entity_type: str
    document_title: str
    content: str
    source_url: str | None = None
    source_title: str | None = None
    publication_date: str | None = None
    retrieved_at: str | None = None
    verification_status: str
    data_origin: str


class MatchEvidenceListResponse(BaseModel):
    """Paginated evidence references for a match result."""

    match_id: str
    matching_run_id: str
    company_id: str
    items: list[MatchEvidenceItemResponse]
    total: int
    limit: int
    offset: int
