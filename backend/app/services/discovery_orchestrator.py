import logging

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.m4 import Company, CompanyResearch, DiscoveryRun, SourceEvidence
from app.providers.m4_base import (
    CompanyResearchProvider,
    DiscoveryQuery,
    FounderProvider,
    FundingProvider,
    HiringSignalProvider,
    M4ProviderError,
    StartupDiscoveryProvider,
)
from app.providers.m4_demo import (
    get_company_research_provider,
    get_discovery_provider,
    get_founder_provider,
    get_funding_provider,
    get_hiring_signal_provider,
)
from app.repositories.m4_repository import M4Repository
from app.repositories.profile_repository import ProfileRepository
from app.schemas.candidate_profile import StructuredCandidateProfile
from app.schemas.m4 import (
    CompanyDetailResponse,
    CompanyFoundersResponse,
    CompanyFundingResponse,
    CompanyHiringSignalsResponse,
    CompanyListResponse,
    CompanyResearchResponse,
    CompanySummaryResponse,
    DiscoveryCriteriaRequest,
    DiscoveryRunResponse,
    FounderResponse,
    FundingEventResponse,
    HiringSignalResponse,
    JobOpportunityResponse,
    SourceEvidenceResponse,
)
from app.services.candidate_profile_service import CandidateNotFoundError, ProfileNotFoundError
from app.services.company_identity import resolve_or_create_company
from app.services.company_research_service import run_company_research
from app.services.founder_service import discover_company_founders
from app.services.funding_service import collect_company_funding
from app.services.hiring_service import detect_hiring_signals

logger = logging.getLogger(__name__)


class DiscoveryRunNotFoundError(Exception):
    """Raised when an M4 discovery run cannot be found."""

    status_code: int = 404
    code: str = "DISCOVERY_RUN_NOT_FOUND"
    detail: str = "Discovery run not found."


class CompanyNotFoundError(Exception):
    """Raised when a company cannot be found."""

    status_code: int = 404
    code: str = "COMPANY_NOT_FOUND"
    detail: str = "Company not found."


def _to_ev_list(items: list[SourceEvidence]) -> list[SourceEvidenceResponse]:
    return [SourceEvidenceResponse.model_validate(ev) for ev in items]


def _to_discovery_response(run: DiscoveryRun) -> DiscoveryRunResponse:
    return DiscoveryRunResponse(
        run_id=run.id,
        candidate_id=run.candidate_id,
        status=run.status,  # type: ignore[arg-type]
        discovered_count=run.discovered_count,
        company_ids=list(run.company_ids or []),
        warnings=list(run.warnings or []),
        error_code=run.error_code,
        error_message=run.error_message,
        created_at=run.created_at,
        started_at=run.started_at,
        completed_at=run.completed_at,
    )


def _to_research_response(
    research: CompanyResearch,
    evidence: list[SourceEvidence],
) -> CompanyResearchResponse:
    return CompanyResearchResponse(
        id=research.id,
        company_id=research.company_id,
        discovery_run_id=research.discovery_run_id,
        summary=research.summary,
        raw_claims=list(research.raw_claims or []),
        conflicts=list(research.conflicts or []),
        status=research.status,  # type: ignore[arg-type]
        data_origin=research.data_origin,  # type: ignore[arg-type]
        warnings=list(research.warnings or []),
        researched_at=research.researched_at,
        evidence=_to_ev_list(evidence),
    )


def _enrich_company_safely(
    db: Session,
    company: Company,
    *,
    discovery_run_id: str | None,
    research_provider: CompanyResearchProvider,
    funding_provider: FundingProvider,
    hiring_provider: HiringSignalProvider,
    founder_provider: FounderProvider,
    warnings: list[str],
) -> None:
    try:
        research = run_company_research(db, company, research_provider, discovery_run_id=discovery_run_id)
        warnings.extend(research.warnings or [])
    except M4ProviderError as exc:
        logger.warning("Research provider failed for company=%s (%s)", company.id, exc.code)
        warnings.append(f"Research failed for '{company.name}': {exc.detail}")

    try:
        collect_company_funding(db, company, funding_provider)
    except M4ProviderError as exc:
        logger.warning("Funding provider failed for company=%s (%s)", company.id, exc.code)
        warnings.append(f"Funding collection failed for '{company.name}': {exc.detail}")

    try:
        detect_hiring_signals(db, company, hiring_provider)
    except M4ProviderError as exc:
        logger.warning("Hiring provider failed for company=%s (%s)", company.id, exc.code)
        warnings.append(f"Hiring signal detection failed for '{company.name}': {exc.detail}")

    try:
        discover_company_founders(db, company, founder_provider)
    except M4ProviderError as exc:
        logger.warning("Founder provider failed for company=%s (%s)", company.id, exc.code)
        warnings.append(f"Founder discovery failed for '{company.name}': {exc.detail}")


def run_startup_discovery_pipeline(
    db: Session,
    settings: Settings,
    request: DiscoveryCriteriaRequest,
    *,
    discovery_provider: StartupDiscoveryProvider | None = None,
    research_provider: CompanyResearchProvider | None = None,
    funding_provider: FundingProvider | None = None,
    hiring_provider: HiringSignalProvider | None = None,
    founder_provider: FounderProvider | None = None,
) -> DiscoveryRunResponse:
    """Execute the M4 startup discovery and intelligence pipeline synchronously."""
    candidate = ProfileRepository.get_candidate_by_id(db, request.candidate_id)
    if candidate is None:
        raise CandidateNotFoundError()

    profile = ProfileRepository.get_by_candidate_id(db, request.candidate_id)
    if profile is None or profile.profile_data is None:
        raise ProfileNotFoundError()

    structured = StructuredCandidateProfile.model_validate(profile.profile_data)
    candidate_skills = [s.name for s in structured.skills]

    query = DiscoveryQuery(
        target_industries=request.target_industries,
        technologies=request.technologies or candidate_skills,
        company_stages=request.company_stages,
        geographic_preferences=request.geographic_preferences,
        company_size_range=request.company_size_range,
        candidate_skills=candidate_skills,
        max_companies=request.max_companies,
    )

    run = M4Repository.create_discovery_run(db, request.candidate_id, request.model_dump(mode="json"))
    M4Repository.mark_discovery_processing(db, run)

    try:
        disc_prov = discovery_provider or get_discovery_provider(settings)
        res_prov = research_provider or get_company_research_provider(settings)
        fund_prov = funding_provider or get_funding_provider(settings)
        hire_prov = hiring_provider or get_hiring_signal_provider(settings)
        found_prov = founder_provider or get_founder_provider(settings)

        discovered_dtos = disc_prov.discover_startups(query)
        warnings: list[str] = []
        if not discovered_dtos:
            warnings.append("Discovery provider returned zero startups matching the criteria.")

        company_ids: list[str] = []
        seen_ids: set[str] = set()

        for dto in discovered_dtos[: request.max_companies]:
            if not dto.name or not dto.name.strip():
                warnings.append("Skipped a discovered startup record with an empty name.")
                continue
            company, _created = resolve_or_create_company(db, dto)
            if company.id in seen_ids:
                continue
            seen_ids.add(company.id)
            company_ids.append(company.id)

            _enrich_company_safely(
                db,
                company,
                discovery_run_id=run.id,
                research_provider=res_prov,
                funding_provider=fund_prov,
                hiring_provider=hire_prov,
                founder_provider=found_prov,
                warnings=warnings,
            )

        db.commit()
        M4Repository.mark_discovery_completed(db, run, company_ids=company_ids, warnings=warnings)
        return _to_discovery_response(run)
    except M4ProviderError as exc:
        db.rollback()
        M4Repository.mark_discovery_failed(db, run, error_code=exc.code, error_message=exc.detail)
        raise
    except Exception as exc:
        db.rollback()
        logger.warning("Unexpected M4 discovery error (%s)", type(exc).__name__)
        M4Repository.mark_discovery_failed(
            db,
            run,
            error_code="DISCOVERY_PIPELINE_ERROR",
            error_message="Startup discovery pipeline failed unexpectedly.",
        )
        raise


def get_discovery_run(db: Session, run_id: str) -> DiscoveryRunResponse:
    run = M4Repository.get_discovery_run(db, run_id)
    if run is None:
        raise DiscoveryRunNotFoundError()
    return _to_discovery_response(run)


def list_companies(
    db: Session,
    *,
    limit: int = 20,
    offset: int = 0,
    stage: str | None = None,
    opportunity_type: str | None = None,
    industry: str | None = None,
) -> CompanyListResponse:
    items, total = M4Repository.list_companies(
        db,
        limit=limit,
        offset=offset,
        stage=stage,
        opportunity_type=opportunity_type,
        industry=industry,
    )
    return CompanyListResponse(
        items=[CompanySummaryResponse.model_validate(c) for c in items],
        total=total,
        limit=limit,
        offset=offset,
    )


def get_company_detail(db: Session, company_id: str) -> CompanyDetailResponse:
    company = M4Repository.get_company_by_id(db, company_id)
    if company is None:
        raise CompanyNotFoundError()

    ev_map = M4Repository.get_evidence_map(db, "company", [company.id])
    latest_research = M4Repository.get_latest_research(db, company.id)
    research_resp: CompanyResearchResponse | None = None
    if latest_research is not None:
        res_ev = M4Repository.get_evidence_map(db, "company_research", [latest_research.id])
        research_resp = _to_research_response(latest_research, res_ev.get(latest_research.id, []))

    return CompanyDetailResponse(
        id=company.id,
        name=company.name,
        official_website=company.official_website,
        normalized_domain=company.normalized_domain,
        external_id=company.external_id,
        description=company.description,
        industry=company.industry,
        product_or_service=company.product_or_service,
        headquarters=company.headquarters,
        founded_year=company.founded_year,
        stage=company.stage,  # type: ignore[arg-type]
        employee_range=company.employee_range,
        tech_stack=list(company.tech_stack or []),
        business_model=company.business_model,
        research_status=company.research_status,  # type: ignore[arg-type]
        opportunity_type=company.opportunity_type,  # type: ignore[arg-type]
        data_origin=company.data_origin,  # type: ignore[arg-type]
        last_researched_at=company.last_researched_at,
        created_at=company.created_at,
        updated_at=company.updated_at,
        evidence=_to_ev_list(ev_map.get(company.id, [])),
        latest_research=research_resp,
    )


def refresh_company_intelligence(
    db: Session,
    settings: Settings,
    company_id: str,
    *,
    research_provider: CompanyResearchProvider | None = None,
    funding_provider: FundingProvider | None = None,
    hiring_provider: HiringSignalProvider | None = None,
    founder_provider: FounderProvider | None = None,
) -> CompanyDetailResponse:
    company = M4Repository.get_company_by_id(db, company_id)
    if company is None:
        raise CompanyNotFoundError()

    res_prov = research_provider or get_company_research_provider(settings)
    fund_prov = funding_provider or get_funding_provider(settings)
    hire_prov = hiring_provider or get_hiring_signal_provider(settings)
    found_prov = founder_provider or get_founder_provider(settings)

    warnings: list[str] = []
    _enrich_company_safely(
        db,
        company,
        discovery_run_id=None,
        research_provider=res_prov,
        funding_provider=fund_prov,
        hiring_provider=hire_prov,
        founder_provider=found_prov,
        warnings=warnings,
    )
    db.commit()
    return get_company_detail(db, company_id)


def get_company_funding(db: Session, company_id: str) -> CompanyFundingResponse:
    company = M4Repository.get_company_by_id(db, company_id)
    if company is None:
        raise CompanyNotFoundError()

    events = M4Repository.list_funding_events(db, company_id)
    ev_map = M4Repository.get_evidence_map(db, "funding_event", [e.id for e in events])
    return CompanyFundingResponse(
        company_id=company_id,
        items=[
            FundingEventResponse(
                id=e.id,
                company_id=e.company_id,
                round_type=e.round_type,  # type: ignore[arg-type]
                amount=e.amount,
                currency=e.currency,
                announced_date=e.announced_date,
                retrieved_at=e.retrieved_at,
                investors=list(e.investors or []),
                lead_investor=e.lead_investor,
                original_claim=e.original_claim,
                normalized_summary=e.normalized_summary,
                is_recent=e.is_recent,
                verification_status=e.verification_status,  # type: ignore[arg-type]
                data_origin=e.data_origin,  # type: ignore[arg-type]
                evidence=_to_ev_list(ev_map.get(e.id, [])),
            )
            for e in events
        ],
    )


def get_company_hiring_signals(db: Session, company_id: str) -> CompanyHiringSignalsResponse:
    company = M4Repository.get_company_by_id(db, company_id)
    if company is None:
        raise CompanyNotFoundError()

    signals = M4Repository.list_hiring_signals(db, company_id)
    jobs = M4Repository.list_job_opportunities(db, company_id)
    sig_ev = M4Repository.get_evidence_map(db, "hiring_signal", [s.id for s in signals])
    job_ev = M4Repository.get_evidence_map(db, "job_opportunity", [j.id for j in jobs])

    return CompanyHiringSignalsResponse(
        company_id=company_id,
        opportunity_type=company.opportunity_type,  # type: ignore[arg-type]
        signals=[
            HiringSignalResponse(
                id=s.id,
                company_id=s.company_id,
                signal_type=s.signal_type,  # type: ignore[arg-type]
                opportunity_category=s.opportunity_category,  # type: ignore[arg-type]
                title=s.title,
                description=s.description,
                role_titles=list(s.role_titles or []),
                department=s.department,
                location=s.location,
                job_posting_url=s.job_posting_url,
                publication_date=s.publication_date,
                retrieved_at=s.retrieved_at,
                observed_fact=s.observed_fact,
                classification_reason=s.classification_reason,
                conclusion_type=s.conclusion_type,  # type: ignore[arg-type]
                uncertainties=s.uncertainties,
                verification_status=s.verification_status,  # type: ignore[arg-type]
                confidence=s.confidence,
                data_origin=s.data_origin,  # type: ignore[arg-type]
                evidence=_to_ev_list(sig_ev.get(s.id, [])),
            )
            for s in signals
        ],
        job_opportunities=[
            JobOpportunityResponse(
                id=j.id,
                company_id=j.company_id,
                hiring_signal_id=j.hiring_signal_id,
                title=j.title,
                job_url=j.job_url,
                location=j.location,
                employment_type=j.employment_type,
                posting_date=j.posting_date,
                last_verified_at=j.last_verified_at,
                verification_status=j.verification_status,  # type: ignore[arg-type]
                is_active=j.is_active,
                data_origin=j.data_origin,  # type: ignore[arg-type]
                evidence=_to_ev_list(job_ev.get(j.id, [])),
            )
            for j in jobs
        ],
    )


def get_company_founders(db: Session, company_id: str) -> CompanyFoundersResponse:
    company = M4Repository.get_company_by_id(db, company_id)
    if company is None:
        raise CompanyNotFoundError()

    founders = M4Repository.list_founders(db, company_id)
    ev_map = M4Repository.get_evidence_map(db, "founder", [f.id for f in founders])
    return CompanyFoundersResponse(
        company_id=company_id,
        items=[
            FounderResponse(
                id=f.id,
                company_id=f.company_id,
                full_name=f.full_name,
                role_title=f.role_title,
                public_profile_url=f.public_profile_url,
                biography=f.biography,
                verification_status=f.verification_status,  # type: ignore[arg-type]
                conflict_notes=f.conflict_notes,
                data_origin=f.data_origin,  # type: ignore[arg-type]
                evidence=_to_ev_list(ev_map.get(f.id, [])),
            )
            for f in founders
        ],
    )
