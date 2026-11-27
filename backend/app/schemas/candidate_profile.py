from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.run import RunErrorResponse, RunStatus

EvidenceStatus = Literal["explicitly_stated", "inferred", "not_available", "requires_review"]

SkillCategory = Literal[
    "programming_languages",
    "frameworks",
    "databases",
    "cloud_infrastructure",
    "ai_ml",
    "tools_platforms",
    "other_technical",
    "domain_skills",
]

ProfileExtractionStatus = Literal[
    "extracted",
    "extracted_with_warnings",
    "requires_manual_review",
    "failed",
]

DataOrigin = Literal["real", "demo"]


class EvidenceItem(BaseModel):
    """Source evidence linking an extracted claim to a resume snippet and page."""

    claim: str = Field(min_length=1)
    snippet: str | None = None
    page_number: int | None = Field(default=None, ge=1)
    status: EvidenceStatus = "explicitly_stated"
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)


class BasicInfo(BaseModel):
    """Core candidate identity and summary fields."""

    full_name: str | None = None
    headline: str | None = None
    location: str | None = None
    current_role: str | None = None
    years_of_experience: float | None = Field(default=None, ge=0.0, le=70.0)
    evidence: list[EvidenceItem] = Field(default_factory=list)


class SkillItem(BaseModel):
    """A single extracted candidate skill with category and source evidence."""

    name: str = Field(min_length=1)
    category: SkillCategory = "other_technical"
    proficiency: str | None = None
    evidence_snippet: str | None = None
    page_number: int | None = Field(default=None, ge=1)
    evidence_status: EvidenceStatus = "explicitly_stated"


class WorkExperienceItem(BaseModel):
    """A single work experience entry."""

    organization: str = Field(min_length=1)
    job_title: str = Field(min_length=1)
    employment_type: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    is_current: bool = False
    description: str | None = None
    responsibilities: list[str] = Field(default_factory=list)
    achievements: list[str] = Field(default_factory=list)
    technologies: list[str] = Field(default_factory=list)
    evidence_snippet: str | None = None
    page_number: int | None = Field(default=None, ge=1)
    evidence_status: EvidenceStatus = "explicitly_stated"


class EducationItem(BaseModel):
    """A single education record."""

    institution: str = Field(min_length=1)
    degree: str | None = None
    field_of_study: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    grade_or_cgpa: str | None = None
    evidence_snippet: str | None = None
    page_number: int | None = Field(default=None, ge=1)
    evidence_status: EvidenceStatus = "explicitly_stated"


class ProjectItem(BaseModel):
    """A single candidate project."""

    name: str = Field(min_length=1)
    description: str | None = None
    technologies: list[str] = Field(default_factory=list)
    responsibilities: list[str] = Field(default_factory=list)
    outcomes: list[str] = Field(default_factory=list)
    evidence_snippet: str | None = None
    page_number: int | None = Field(default=None, ge=1)
    evidence_status: EvidenceStatus = "explicitly_stated"


class CertificationOrAchievementItem(BaseModel):
    """A certification or notable achievement supported by the resume."""

    title: str = Field(min_length=1)
    issuer: str | None = None
    date: str | None = None
    description: str | None = None
    evidence_snippet: str | None = None
    page_number: int | None = Field(default=None, ge=1)
    evidence_status: EvidenceStatus = "explicitly_stated"


class AdditionalInfo(BaseModel):
    """Additional resume metadata."""

    summary: str | None = None
    interests: list[str] = Field(default_factory=list)
    relevant_domains: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)


class StructuredCandidateProfile(BaseModel):
    """Complete structured, evidence-backed candidate profile."""

    basic_info: BasicInfo = Field(default_factory=BasicInfo)
    skills: list[SkillItem] = Field(default_factory=list)
    work_experience: list[WorkExperienceItem] = Field(default_factory=list)
    education: list[EducationItem] = Field(default_factory=list)
    projects: list[ProjectItem] = Field(default_factory=list)
    certifications_and_achievements: list[CertificationOrAchievementItem] = Field(default_factory=list)
    additional_info: AdditionalInfo = Field(default_factory=AdditionalInfo)
    evidence: list[EvidenceItem] = Field(default_factory=list)


class CandidateProfileResponse(BaseModel):
    """Public API response for retrieving a candidate's structured profile."""

    profile_id: str
    candidate_id: str
    research_run_id: str | None = None
    extraction_status: ProfileExtractionStatus
    source_type: Literal["resume_pdf", "linkedin_url"]
    data_origin: DataOrigin
    provider_name: str
    model_name: str | None = None
    page_count: int | None = None
    warnings: list[str] = Field(default_factory=list)
    profile: StructuredCandidateProfile | None = None
    error_code: str | None = None
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime


class ProcessRunResponse(BaseModel):
    """Public API response after triggering candidate profile extraction."""

    run_id: str
    candidate_id: str
    status: RunStatus
    extraction_status: ProfileExtractionStatus | None = None
    profile_id: str | None = None
    warnings: list[str] = Field(default_factory=list)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error: RunErrorResponse | None = None
