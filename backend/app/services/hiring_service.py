from datetime import UTC, datetime, timedelta
import hashlib

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.m4 import Company, HiringSignal, JobOpportunity
from app.providers.m4_base import CompanyIdentityDTO, HiringSignalDTO, HiringSignalProvider
from app.services.source_validation import ensure_utc, persist_and_link_evidence, validate_http_url

STALE_JOB_DAYS = 90


def _compute_signal_dedup_key(dto: HiringSignalDTO) -> str:
    raw = f"{dto.signal_type}|{dto.title.strip().lower()}|{dto.job_posting_url or ''}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]


def detect_hiring_signals(
    db: Session,
    company: Company,
    provider: HiringSignalProvider,
) -> tuple[list[HiringSignal], list[JobOpportunity]]:
    """Detect, classify (Active vs Hidden), deduplicate, and persist hiring signals."""
    identity = CompanyIdentityDTO(
        company_id=company.id,
        name=company.name,
        official_website=company.official_website,
        normalized_domain=company.normalized_domain,
        external_id=company.external_id,
        stage=company.stage,  # type: ignore[arg-type]
    )
    intel = provider.get_hiring_signals(identity)
    now = datetime.now(UTC)

    persisted_signals: list[HiringSignal] = []
    persisted_jobs: list[JobOpportunity] = []

    for dto in intel.signals:
        # Rule: funding alone is never treated as proof of hiring
        if dto.is_funding_only and not dto.has_confirmed_open_role:
            continue

        pub_date = ensure_utc(dto.publication_date)
        is_stale_by_date = pub_date is not None and (now - pub_date) > timedelta(days=STALE_JOB_DAYS)
        is_stale = dto.is_stale or is_stale_by_date
        has_evidence = len(dto.evidence) > 0

        if dto.has_confirmed_open_role and not is_stale and has_evidence:
            opportunity_category = "active"
            conclusion_type = "verified"
            verification_status = "verified"
            reason = "Confirmed active public job opening supported by recent source evidence."
        else:
            opportunity_category = "hidden"
            conclusion_type = "inferred"
            if not has_evidence or is_stale:
                verification_status = "requires_review" if is_stale else "unverified"
            else:
                verification_status = "verified"
            reason = (
                "No confirmed active public opening; classified as hidden opportunity based on "
                f"{dto.signal_type.replace('_', ' ')} evidence."
            )

        dedup_key = _compute_signal_dedup_key(dto)
        existing_sig = db.scalar(
            select(HiringSignal).where(
                HiringSignal.company_id == company.id,
                HiringSignal.dedup_key == dedup_key,
            )
        )
        if existing_sig is not None:
            persist_and_link_evidence(
                db,
                entity_type="hiring_signal",
                entity_id=existing_sig.id,
                evidence_items=dto.evidence,
            )
            persisted_signals.append(existing_sig)
            continue

        sig = HiringSignal(
            company_id=company.id,
            dedup_key=dedup_key,
            signal_type=dto.signal_type,
            opportunity_category=opportunity_category,
            title=dto.title.strip()[:500],
            description=dto.description,
            role_titles=list(dict.fromkeys(dto.role_titles)),
            department=dto.department,
            location=dto.location,
            job_posting_url=validate_http_url(dto.job_posting_url),
            publication_date=pub_date,
            retrieved_at=now,
            observed_fact=dto.observed_fact,
            classification_reason=reason,
            conclusion_type=conclusion_type,
            uncertainties=dto.uncertainties or ("Listing may be stale." if is_stale else None),
            verification_status=verification_status,
            confidence=dto.confidence,
            data_origin=dto.data_origin,
        )
        db.add(sig)
        db.flush()
        persist_and_link_evidence(
            db,
            entity_type="hiring_signal",
            entity_id=sig.id,
            evidence_items=dto.evidence,
        )
        persisted_signals.append(sig)

    first_active_sig_id = next((s.id for s in persisted_signals if s.opportunity_category == "active"), None)

    for job_dto in intel.job_postings:
        valid_url = validate_http_url(job_dto.job_url)
        if valid_url is None:
            continue

        posting_date = ensure_utc(job_dto.posting_date)
        is_stale = posting_date is not None and (now - posting_date) > timedelta(days=STALE_JOB_DAYS)
        has_evidence = len(job_dto.evidence) > 0
        is_active = bool(job_dto.is_currently_confirmed and not is_stale and has_evidence)
        verification_status = "verified" if is_active else ("requires_review" if is_stale else "unverified")

        existing_job = db.scalar(
            select(JobOpportunity).where(
                JobOpportunity.company_id == company.id,
                JobOpportunity.job_url == valid_url,
            )
        )
        if existing_job is not None:
            existing_job.is_active = is_active
            existing_job.verification_status = verification_status
            existing_job.last_verified_at = now
            persist_and_link_evidence(
                db,
                entity_type="job_opportunity",
                entity_id=existing_job.id,
                evidence_items=job_dto.evidence,
            )
            persisted_jobs.append(existing_job)
            continue

        job = JobOpportunity(
            company_id=company.id,
            hiring_signal_id=first_active_sig_id,
            title=job_dto.title.strip()[:255],
            job_url=valid_url,
            location=job_dto.location,
            employment_type=job_dto.employment_type,
            posting_date=posting_date,
            last_verified_at=now,
            verification_status=verification_status,
            is_active=is_active,
            data_origin=job_dto.data_origin,
        )
        db.add(job)
        db.flush()
        persist_and_link_evidence(
            db,
            entity_type="job_opportunity",
            entity_id=job.id,
            evidence_items=job_dto.evidence,
        )
        persisted_jobs.append(job)

    has_active = any(j.is_active for j in persisted_jobs) or any(
        s.opportunity_category == "active" for s in persisted_signals
    )
    has_hidden = any(s.opportunity_category == "hidden" for s in persisted_signals)

    if has_active:
        company.opportunity_type = "active"
    elif has_hidden:
        company.opportunity_type = "hidden"
    elif company.opportunity_type not in {"active", "hidden"}:
        company.opportunity_type = "unknown"

    db.flush()
    return persisted_signals, persisted_jobs
