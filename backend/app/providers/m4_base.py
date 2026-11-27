from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app.schemas.m4 import (
    CompanyStage,
    DataOrigin,
    HiringSignalType,
    ResearchStatus,
    SourceEvidenceInput,
    VerificationStatus,
)


class M4ProviderError(Exception):
    """Safe domain error raised when an M4 external or demo provider fails."""

    def __init__(self, code: str, detail: str, status_code: int = 502) -> None:
        super().__init__(detail)
        self.code = code
        self.detail = detail
        self.status_code = status_code


@dataclass(frozen=True, slots=True)
class DiscoveryQuery:
    """Resolved query parameters passed to StartupDiscoveryProvider."""

    target_industries: list[str] = field(default_factory=list)
    technologies: list[str] = field(default_factory=list)
    company_stages: list[CompanyStage] = field(default_factory=list)
    geographic_preferences: list[str] = field(default_factory=list)
    company_size_range: str | None = None
    candidate_skills: list[str] = field(default_factory=list)
    max_companies: int = 10


@dataclass(frozen=True, slots=True)
class CompanyIdentityDTO:
    """Minimal company identity passed to enrichment providers."""

    company_id: str
    name: str
    official_website: str | None = None
    normalized_domain: str | None = None
    external_id: str | None = None
    stage: CompanyStage = "unknown"


@dataclass(frozen=True, slots=True)
class DiscoveredStartupDTO:
    """Raw startup candidate returned by a StartupDiscoveryProvider."""

    name: str
    official_website: str | None = None
    external_id: str | None = None
    description: str | None = None
    industry: str | None = None
    headquarters: str | None = None
    stage: CompanyStage = "unknown"
    employee_range: str | None = None
    tech_stack: list[str] = field(default_factory=list)
    data_origin: DataOrigin = "demo"
    evidence: list[SourceEvidenceInput] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class ResearchClaimDTO:
    """Individual sourced claim collected during company research."""

    field_name: str
    value: str
    evidence: SourceEvidenceInput


@dataclass(frozen=True, slots=True)
class CompanyResearchDTO:
    """Structured company research returned by a CompanyResearchProvider."""

    description: str | None = None
    industry: str | None = None
    product_or_service: str | None = None
    headquarters: str | None = None
    founded_year: int | None = None
    stage: CompanyStage | None = None
    employee_range: str | None = None
    tech_stack: list[str] = field(default_factory=list)
    business_model: str | None = None
    summary: str | None = None
    claims: list[ResearchClaimDTO] = field(default_factory=list)
    status: ResearchStatus = "completed"
    data_origin: DataOrigin = "demo"
    warnings: list[str] = field(default_factory=list)
    evidence: list[SourceEvidenceInput] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class FundingEventDTO:
    """Raw funding event returned by a FundingProvider."""

    round_type: CompanyStage = "unknown"
    amount: float | None = None
    currency: str | None = None
    announced_date: datetime | None = None
    retrieved_at: datetime | None = None
    investors: list[str] = field(default_factory=list)
    lead_investor: str | None = None
    original_claim: str = ""
    confirmed: bool = True
    data_origin: DataOrigin = "demo"
    evidence: list[SourceEvidenceInput] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class JobPostingDTO:
    """Public job opening returned by a HiringSignalProvider."""

    title: str
    job_url: str
    location: str | None = None
    employment_type: str | None = None
    posting_date: datetime | None = None
    is_currently_confirmed: bool = True
    data_origin: DataOrigin = "demo"
    evidence: list[SourceEvidenceInput] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class HiringSignalDTO:
    """Raw hiring signal returned by a HiringSignalProvider."""

    signal_type: HiringSignalType
    title: str
    observed_fact: str
    description: str | None = None
    role_titles: list[str] = field(default_factory=list)
    department: str | None = None
    location: str | None = None
    job_posting_url: str | None = None
    publication_date: datetime | None = None
    is_funding_only: bool = False
    has_confirmed_open_role: bool = False
    is_stale: bool = False
    uncertainties: str | None = None
    confidence: float | None = None
    data_origin: DataOrigin = "demo"
    evidence: list[SourceEvidenceInput] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class HiringIntelligenceDTO:
    """Combined hiring signals and job postings from a HiringSignalProvider."""

    signals: list[HiringSignalDTO] = field(default_factory=list)
    job_postings: list[JobPostingDTO] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class FounderDTO:
    """Raw founder record returned by a FounderProvider."""

    full_name: str
    role_title: str | None = None
    public_profile_url: str | None = None
    biography: str | None = None
    verification_status: VerificationStatus = "unverified"
    data_origin: DataOrigin = "demo"
    evidence: list[SourceEvidenceInput] = field(default_factory=list)


class StartupDiscoveryProvider(ABC):
    """Interface for discovering candidate startups."""

    @abstractmethod
    def discover_startups(self, query: DiscoveryQuery) -> list[DiscoveredStartupDTO]:
        """Discover startups matching the supplied query."""


class CompanyResearchProvider(ABC):
    """Interface for gathering public company profile information."""

    @abstractmethod
    def research_company(self, company: CompanyIdentityDTO) -> CompanyResearchDTO:
        """Collect public information for a company."""


class FundingProvider(ABC):
    """Interface for gathering company funding events."""

    @abstractmethod
    def get_funding_events(self, company: CompanyIdentityDTO) -> list[FundingEventDTO]:
        """Collect funding events for a company."""


class HiringSignalProvider(ABC):
    """Interface for detecting hiring signals and public job postings."""

    @abstractmethod
    def get_hiring_signals(self, company: CompanyIdentityDTO) -> HiringIntelligenceDTO:
        """Collect hiring signals and job openings for a company."""


class FounderProvider(ABC):
    """Interface for discovering company founders from permitted public sources."""

    @abstractmethod
    def discover_founders(self, company: CompanyIdentityDTO) -> list[FounderDTO]:
        """Collect founder records for a company."""
