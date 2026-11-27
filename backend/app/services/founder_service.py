import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.m4 import Company, Founder
from app.providers.m4_base import CompanyIdentityDTO, FounderProvider
from app.services.source_validation import persist_and_link_evidence, validate_http_url


def _normalize_founder_name(name: str) -> str:
    cleaned = re.sub(r"[^a-z0-9\s]", " ", name.lower())
    return re.sub(r"\s+", " ", cleaned).strip()[:255]


def discover_company_founders(
    db: Session,
    company: Company,
    provider: FounderProvider,
) -> list[Founder]:
    """Discover, deduplicate, and persist founder records with conflict handling."""
    identity = CompanyIdentityDTO(
        company_id=company.id,
        name=company.name,
        official_website=company.official_website,
        normalized_domain=company.normalized_domain,
        external_id=company.external_id,
        stage=company.stage,  # type: ignore[arg-type]
    )
    dtos = provider.discover_founders(identity)
    persisted: list[Founder] = []

    for dto in dtos:
        norm_name = _normalize_founder_name(dto.full_name)
        if not norm_name:
            continue

        valid_profile_url = validate_http_url(dto.public_profile_url)
        has_evidence = len(dto.evidence) > 0
        verification_status = dto.verification_status if has_evidence else "unverified"

        existing = db.scalar(
            select(Founder).where(
                Founder.company_id == company.id,
                Founder.normalized_name == norm_name,
            )
        )
        if existing is not None:
            if (
                dto.role_title
                and existing.role_title
                and dto.role_title.strip().lower() != existing.role_title.strip().lower()
            ):
                existing.verification_status = "requires_review"
                note = f"Conflicting role titles: '{existing.role_title}' vs '{dto.role_title}'."
                existing.conflict_notes = (
                    f"{existing.conflict_notes} | {note}" if existing.conflict_notes else note
                )
            elif dto.role_title and not existing.role_title:
                existing.role_title = dto.role_title.strip()[:255]

            if valid_profile_url and not existing.public_profile_url:
                existing.public_profile_url = valid_profile_url
            if dto.biography and not existing.biography:
                existing.biography = dto.biography

            db.flush()
            persist_and_link_evidence(
                db,
                entity_type="founder",
                entity_id=existing.id,
                evidence_items=dto.evidence,
            )
            persisted.append(existing)
            continue

        founder = Founder(
            company_id=company.id,
            full_name=dto.full_name.strip()[:255],
            normalized_name=norm_name,
            role_title=dto.role_title.strip()[:255] if dto.role_title else None,
            public_profile_url=valid_profile_url,
            biography=dto.biography,
            verification_status=verification_status,
            data_origin=dto.data_origin,
        )
        db.add(founder)
        db.flush()
        persist_and_link_evidence(
            db,
            entity_type="founder",
            entity_id=founder.id,
            evidence_items=dto.evidence,
        )
        persisted.append(founder)

    return persisted
