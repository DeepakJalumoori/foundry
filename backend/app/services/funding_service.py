from datetime import UTC, datetime, timedelta
import hashlib

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.m4 import Company, FundingEvent
from app.providers.m4_base import CompanyIdentityDTO, FundingEventDTO, FundingProvider
from app.services.source_validation import ensure_utc, persist_and_link_evidence

RECENT_FUNDING_DAYS = 180


def _compute_funding_dedup_key(dto: FundingEventDTO) -> str:
    date_part = dto.announced_date.date().isoformat() if dto.announced_date else "unknown-date"
    raw = f"{dto.round_type}|{date_part}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]


def _classify_is_recent(announced_date: datetime | None, retrieved_at: datetime) -> bool | None:
    if announced_date is None:
        return None
    ann = ensure_utc(announced_date)
    ret = ensure_utc(retrieved_at) or datetime.now(UTC)
    assert ann is not None
    return (ret - ann) <= timedelta(days=RECENT_FUNDING_DAYS)


def collect_company_funding(
    db: Session,
    company: Company,
    provider: FundingProvider,
) -> list[FundingEvent]:
    """Collect, classify, deduplicate, and persist funding events for a company."""
    identity = CompanyIdentityDTO(
        company_id=company.id,
        name=company.name,
        official_website=company.official_website,
        normalized_domain=company.normalized_domain,
        external_id=company.external_id,
        stage=company.stage,  # type: ignore[arg-type]
    )
    dtos = provider.get_funding_events(identity)
    persisted: list[FundingEvent] = []

    for dto in dtos:
        retrieved_at = ensure_utc(dto.retrieved_at) or datetime.now(UTC)
        announced_date = ensure_utc(dto.announced_date)
        dedup_key = _compute_funding_dedup_key(dto)
        is_recent = _classify_is_recent(announced_date, retrieved_at)

        has_evidence = len(dto.evidence) > 0
        verification_status = "verified" if (dto.confirmed and has_evidence) else "unverified"

        amount = dto.amount if (dto.amount is not None and dto.amount >= 0) else None
        currency = dto.currency.strip().upper()[:10] if (dto.currency and amount is not None) else None

        amount_str = f"{amount:g} {currency}" if (amount is not None and currency) else (f"{amount:g}" if amount is not None else "undisclosed amount")
        normalized_summary = f"{dto.round_type.replace('_', ' ').title()} ({amount_str})"

        existing = db.scalar(
            select(FundingEvent).where(
                FundingEvent.company_id == company.id,
                FundingEvent.dedup_key == dedup_key,
            )
        )
        if existing is not None:
            # Preserve conflict if amount or currency disagrees across sources
            if (amount is not None and existing.amount is not None and existing.amount != amount) or (
                currency is not None and existing.currency is not None and existing.currency != currency
            ):
                existing.verification_status = "requires_review"
                if dto.original_claim and dto.original_claim not in (existing.original_claim or ""):
                    existing.original_claim = f"{existing.original_claim or ''} | Conflict: {dto.original_claim}".strip(" |")
            persist_and_link_evidence(
                db,
                entity_type="funding_event",
                entity_id=existing.id,
                evidence_items=dto.evidence,
            )
            persisted.append(existing)
            continue

        event = FundingEvent(
            company_id=company.id,
            dedup_key=dedup_key,
            round_type=dto.round_type,
            amount=amount,
            currency=currency,
            announced_date=announced_date,
            retrieved_at=retrieved_at,
            investors=list(dict.fromkeys(dto.investors)),
            lead_investor=dto.lead_investor,
            original_claim=dto.original_claim or None,
            normalized_summary=normalized_summary,
            is_recent=is_recent,
            verification_status=verification_status,
            data_origin=dto.data_origin,
        )
        db.add(event)
        db.flush()
        persist_and_link_evidence(
            db,
            entity_type="funding_event",
            entity_id=event.id,
            evidence_items=dto.evidence,
        )
        persisted.append(event)

    return persisted
