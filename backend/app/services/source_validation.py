from datetime import UTC, datetime
from urllib.parse import urlsplit

from sqlalchemy.orm import Session

from app.models.m4 import SourceEvidence
from app.repositories.m4_repository import M4Repository
from app.schemas.m4 import SourceEvidenceInput


def ensure_utc(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def validate_http_url(raw_url: str | None) -> str | None:
    """Validate and normalize an HTTP/HTTPS URL, returning None if invalid or empty."""
    if not raw_url or not raw_url.strip():
        return None
    cleaned = raw_url.strip()
    try:
        parsed = urlsplit(cleaned)
    except ValueError:
        return None
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.netloc:
        return None
    return cleaned


def persist_and_link_evidence(
    db: Session,
    *,
    entity_type: str,
    entity_id: str,
    evidence_items: list[SourceEvidenceInput],
) -> list[SourceEvidence]:
    """Validate, deduplicate, persist, and link SourceEvidence items to a domain entity."""
    persisted: list[SourceEvidence] = []
    for item in evidence_items:
        url_str = str(item.source_url)
        if validate_http_url(url_str) is None:
            continue

        ev = M4Repository.get_or_create_evidence(
            db,
            source_url=url_str,
            source_title=item.source_title.strip()[:500],
            source_domain=item.source_domain.strip().lower()[:255],
            source_type=item.source_type,
            publication_date=ensure_utc(item.publication_date),
            retrieved_at=ensure_utc(item.retrieved_at) or datetime.now(UTC),
            excerpt=item.excerpt.strip()[:2000] if item.excerpt else None,
            verification_status=item.verification_status,
            data_origin=item.data_origin,
        )
        M4Repository.link_evidence(db, entity_type, entity_id, ev.id)
        persisted.append(ev)
    return persisted
