from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

VerificationStatus = Literal["verified", "unverified", "requires_review"]
DataOrigin = Literal["real", "demo"]
CompanyStage = Literal["pre_seed", "seed", "series_a", "series_b", "series_c", "other", "unknown"]
OpportunityType = Literal["active", "hidden", "unknown"]
SourceType = Literal[
    "official_website",
    "careers_page",
    "job_board",
    "press_release",
    "news_article",
    "founder_interview",
    "public_registry",
    "demo",
]
HiringSignalType = Literal[
    "public_job_posting",
    "careers_page",
    "team_expansion",
    "new_unit",
    "leadership_statement",
    "expansion_report",
    "other",
]
DiscoveryRunStatus = Literal["pending", "processing", "completed", "completed_with_warnings", "failed"]
ResearchStatus = Literal["pending", "completed", "completed_with_warnings", "requires_review", "failed"]


class SourceEvidenceInput(BaseModel):
    """Normalized source evidence payload produced by providers or services."""

    source_url: HttpUrl
    source_title: str = Field(min_length=1, max_length=500)
    source_domain: str = Field(min_length=1, max_length=255)
    source_type: SourceType
    publication_date: datetime | None = None
    retrieved_at: datetime
    excerpt: str | None = Field(default=None, max_length=2000)
    verification_status: VerificationStatus = "unverified"
    data_origin: DataOrigin = "demo"


class SourceEvidenceResponse(BaseModel):
    """Public API representation of a stored source evidence record."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    source_url: str
    source_title: str
    source_domain: str
    source_type: SourceType
    publication_date: datetime | None = None
    retrieved_at: datetime
    excerpt: str | None = None
    verification_status: VerificationStatus
    data_origin: DataOrigin


class DiscoveryCriteriaRequest(BaseModel):
    """Input criteria for discovering startups for a candidate."""

    candidate_id: str = Field(min_length=1)
    target_industries: list[str] = Field(default_factory=list)
    technologies: list[str] = Field(default_factory=list)
    company_stages: list[CompanyStage] = Field(
        default_factory=lambda: ["pre_seed", "seed", "series_a", "series_b", "series_c"]
    )
    geographic_preferences: list[str] = Field(default_factory=list)
    company_size_range: str | None = None
    max_companies: int = Field(default=10, ge=1, le=50)


class DiscoveryRunResponse(BaseModel):
    """Public response for a startup discovery run."""

    run_id: str
    candidate_id: str
    status: DiscoveryRunStatus
    discovered_count: int
    company_ids: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    error_code: str | None = None
    error_message: str | None = None
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None


class CompanySummaryResponse(BaseModel):
    """Summary company record for paginated listings."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    official_website: str | None = None
    normalized_domain: str | None = None
    description: str | None = None
    industry: str | None = None
    headquarters: str | None = None
    stage: CompanyStage
    opportunity_type: OpportunityType
    research_status: ResearchStatus
    data_origin: DataOrigin
    last_researched_at: datetime | None = None


class CompanyListResponse(BaseModel):
    """Paginated list of discovered companies."""

    items: list[CompanySummaryResponse]
    total: int
    limit: int
    offset: int


class CompanyResearchResponse(BaseModel):
    """Structured company research record."""

    id: str
    company_id: str
    discovery_run_id: str | None = None
    summary: str | None = None
    raw_claims: list[dict[str, Any]] = Field(default_factory=list)
    conflicts: list[dict[str, Any]] = Field(default_factory=list)
    status: ResearchStatus
    data_origin: DataOrigin
    warnings: list[str] = Field(default_factory=list)
    researched_at: datetime
    evidence: list[SourceEvidenceResponse] = Field(default_factory=list)


class CompanyDetailResponse(BaseModel):
    """Detailed normalized company profile with research and evidence."""

    id: str
    name: str
    official_website: str | None = None
    normalized_domain: str | None = None
    external_id: str | None = None
    description: str | None = None
    industry: str | None = None
    product_or_service: str | None = None
    headquarters: str | None = None
    founded_year: int | None = None
    stage: CompanyStage
    employee_range: str | None = None
    tech_stack: list[str] = Field(default_factory=list)
    business_model: str | None = None
    research_status: ResearchStatus
    opportunity_type: OpportunityType
    data_origin: DataOrigin
    last_researched_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    evidence: list[SourceEvidenceResponse] = Field(default_factory=list)
    latest_research: CompanyResearchResponse | None = None


class FundingEventResponse(BaseModel):
    """Funding event with evidence provenance."""

    id: str
    company_id: str
    round_type: CompanyStage
    amount: float | None = None
    currency: str | None = None
    announced_date: datetime | None = None
    retrieved_at: datetime
    investors: list[str] = Field(default_factory=list)
    lead_investor: str | None = None
    original_claim: str | None = None
    normalized_summary: str | None = None
    is_recent: bool | None = None
    verification_status: VerificationStatus
    data_origin: DataOrigin
    evidence: list[SourceEvidenceResponse] = Field(default_factory=list)


class CompanyFundingResponse(BaseModel):
    """Funding events response for a company."""

    company_id: str
    items: list[FundingEventResponse]


class JobOpportunityResponse(BaseModel):
    """Active or conservative job opportunity record."""

    id: str
    company_id: str
    hiring_signal_id: str | None = None
    title: str
    job_url: str
    location: str | None = None
    employment_type: str | None = None
    posting_date: datetime | None = None
    last_verified_at: datetime
    verification_status: VerificationStatus
    is_active: bool
    data_origin: DataOrigin
    evidence: list[SourceEvidenceResponse] = Field(default_factory=list)


class HiringSignalResponse(BaseModel):
    """Explainable hiring signal record."""

    id: str
    company_id: str
    signal_type: HiringSignalType
    opportunity_category: Literal["active", "hidden"]
    title: str
    description: str | None = None
    role_titles: list[str] = Field(default_factory=list)
    department: str | None = None
    location: str | None = None
    job_posting_url: str | None = None
    publication_date: datetime | None = None
    retrieved_at: datetime
    observed_fact: str
    classification_reason: str
    conclusion_type: Literal["verified", "inferred"]
    uncertainties: str | None = None
    verification_status: VerificationStatus
    confidence: float | None = None
    data_origin: DataOrigin
    evidence: list[SourceEvidenceResponse] = Field(default_factory=list)


class CompanyHiringSignalsResponse(BaseModel):
    """Hiring signals and job opportunities for a company."""

    company_id: str
    opportunity_type: OpportunityType
    signals: list[HiringSignalResponse]
    job_opportunities: list[JobOpportunityResponse]


class FounderResponse(BaseModel):
    """Discovered founder record with provenance."""

    id: str
    company_id: str
    full_name: str
    role_title: str | None = None
    public_profile_url: str | None = None
    biography: str | None = None
    verification_status: VerificationStatus
    conflict_notes: str | None = None
    data_origin: DataOrigin
    evidence: list[SourceEvidenceResponse] = Field(default_factory=list)


class CompanyFoundersResponse(BaseModel):
    """Founders response for a company."""

    company_id: str
    items: list[FounderResponse]
