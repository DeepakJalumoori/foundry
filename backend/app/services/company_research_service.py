from collections import defaultdict
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from app.models.m4 import Company, CompanyResearch
from app.providers.m4_base import CompanyIdentityDTO, CompanyResearchProvider
from app.services.source_validation import persist_and_link_evidence


def _utc_now() -> datetime:
    return datetime.now(UTC)


def run_company_research(
    db: Session,
    company: Company,
    provider: CompanyResearchProvider,
    *,
    discovery_run_id: str | None = None,
) -> CompanyResearch:
    """Gather, normalize, and persist company research with conflict detection."""
    identity = CompanyIdentityDTO(
        company_id=company.id,
        name=company.name,
        official_website=company.official_website,
        normalized_domain=company.normalized_domain,
        external_id=company.external_id,
        stage=company.stage,  # type: ignore[arg-type]
    )
    dto = provider.research_company(identity)
    now = _utc_now()

    claims_by_field: dict[str, list[str]] = defaultdict(list)
    raw_claims: list[dict[str, Any]] = []
    all_evidence = list(dto.evidence)

    for claim in dto.claims:
        claims_by_field[claim.field_name].append(claim.value.strip())
        all_evidence.append(claim.evidence)
        raw_claims.append(
            {
                "field_name": claim.field_name,
                "value": claim.value,
                "source_url": str(claim.evidence.source_url),
            }
        )

    conflicts: list[dict[str, Any]] = []
    warnings = list(dto.warnings)
    for field_name, values in claims_by_field.items():
        distinct = list(dict.fromkeys(v for v in values if v))
        if len(distinct) > 1:
            conflicts.append({"field_name": field_name, "conflicting_values": distinct})
            warnings.append(f"Conflicting sources found for '{field_name}'; marked for review.")

    status = dto.status
    if conflicts:
        status = "requires_review"
    elif warnings and status == "completed":
        status = "completed_with_warnings"

    if dto.description and not company.description:
        company.description = dto.description
    if dto.industry and not company.industry:
        company.industry = dto.industry
    if dto.product_or_service:
        company.product_or_service = dto.product_or_service
    if dto.headquarters and not company.headquarters:
        company.headquarters = dto.headquarters
    if dto.founded_year is not None:
        company.founded_year = dto.founded_year
    if dto.stage and dto.stage != "unknown" and company.stage == "unknown":
        company.stage = dto.stage
    if dto.employee_range and not company.employee_range:
        company.employee_range = dto.employee_range
    if dto.tech_stack:
        company.tech_stack = list(dict.fromkeys([*(company.tech_stack or []), *dto.tech_stack]))
    if dto.business_model:
        company.business_model = dto.business_model

    company.research_status = status
    company.last_researched_at = now

    research = CompanyResearch(
        company_id=company.id,
        discovery_run_id=discovery_run_id,
        summary=dto.summary,
        raw_claims=raw_claims,
        conflicts=conflicts,
        status=status,
        data_origin=dto.data_origin,
        warnings=warnings,
        researched_at=now,
    )
    db.add(research)
    db.flush()

    persist_and_link_evidence(
        db,
        entity_type="company_research",
        entity_id=research.id,
        evidence_items=all_evidence,
    )
    persist_and_link_evidence(
        db,
        entity_type="company",
        entity_id=company.id,
        evidence_items=all_evidence,
    )
    return research
