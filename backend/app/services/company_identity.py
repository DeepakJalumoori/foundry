import re
from urllib.parse import urlsplit

from sqlalchemy.orm import Session

from app.models.m4 import Company
from app.providers.m4_base import DiscoveredStartupDTO
from app.repositories.m4_repository import M4Repository
from app.services.source_validation import persist_and_link_evidence, validate_http_url

_SUFFIX_RE = re.compile(r"\b(inc|incorporated|llc|ltd|limited|corp|corporation|co|gmbh|plc)\b\.?", re.IGNORECASE)


def normalize_domain(raw_url: str | None) -> str | None:
    """Extract and normalize an official website domain (e.g. 'kestreldata.example.com')."""
    if not raw_url or not raw_url.strip():
        return None
    candidate = raw_url.strip()
    if "://" not in candidate:
        candidate = f"https://{candidate}"
    try:
        parsed = urlsplit(candidate)
    except ValueError:
        return None
    host = (parsed.hostname or "").strip().lower()
    if not host or "." not in host:
        return None
    if host.startswith("www."):
        host = host[4:]
    return host[:255]


def normalize_company_name(name: str) -> str:
    """Normalize a company name for cautious fallback identity matching."""
    cleaned = _SUFFIX_RE.sub("", name.lower())
    cleaned = re.sub(r"[^a-z0-9\s]", " ", cleaned)
    return re.sub(r"\s+", " ", cleaned).strip()[:255]


def resolve_or_create_company(db: Session, dto: DiscoveredStartupDTO) -> tuple[Company, bool]:
    """Resolve an existing Company or create a new one. Returns (company, created_new).

    Priority:
    1. Normalized official website domain.
    2. Verified external_id.
    3. Normalized company name ONLY when neither side has a conflicting domain.
    """
    valid_url = validate_http_url(dto.official_website)
    norm_domain = normalize_domain(valid_url) if valid_url else None
    norm_name = normalize_company_name(dto.name)

    existing: Company | None = None
    if norm_domain:
        existing = M4Repository.get_company_by_domain(db, norm_domain)

    if existing is None and dto.external_id:
        candidate_by_ext = M4Repository.get_company_by_external_id(db, dto.external_id)
        if candidate_by_ext is not None:
            if not norm_domain or not candidate_by_ext.normalized_domain or candidate_by_ext.normalized_domain == norm_domain:
                existing = candidate_by_ext

    if existing is None and norm_domain is None and norm_name:
        name_matches = M4Repository.get_companies_by_normalized_name(db, norm_name)
        domainless_matches = [c for c in name_matches if c.normalized_domain is None]
        if len(domainless_matches) == 1:
            existing = domainless_matches[0]

    if existing is not None:
        if not existing.description and dto.description:
            existing.description = dto.description
        if not existing.industry and dto.industry:
            existing.industry = dto.industry
        if not existing.headquarters and dto.headquarters:
            existing.headquarters = dto.headquarters
        if existing.stage == "unknown" and dto.stage != "unknown":
            existing.stage = dto.stage
        if not existing.employee_range and dto.employee_range:
            existing.employee_range = dto.employee_range
        if dto.tech_stack:
            merged_stack = list(dict.fromkeys([*(existing.tech_stack or []), *dto.tech_stack]))
            existing.tech_stack = merged_stack
        db.flush()
        persist_and_link_evidence(
            db,
            entity_type="company",
            entity_id=existing.id,
            evidence_items=dto.evidence,
        )
        return existing, False

    company = Company(
        name=dto.name.strip()[:255],
        normalized_name=norm_name or dto.name.strip().lower()[:255],
        official_website=valid_url,
        normalized_domain=norm_domain,
        external_id=dto.external_id,
        description=dto.description,
        industry=dto.industry,
        headquarters=dto.headquarters,
        stage=dto.stage,
        employee_range=dto.employee_range,
        tech_stack=list(dict.fromkeys(dto.tech_stack)),
        research_status="pending",
        opportunity_type="unknown",
        data_origin=dto.data_origin,
    )
    db.add(company)
    db.flush()
    persist_and_link_evidence(
        db,
        entity_type="company",
        entity_id=company.id,
        evidence_items=dto.evidence,
    )
    return company, True
