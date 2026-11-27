from datetime import UTC, datetime, timedelta
from typing import Any

from app.schemas.m5 import (
    EvidenceStrength,
    M5OpportunityType,
    OpportunityAssessment,
    RetrievedEvidenceItem,
)
from app.services.hiring_service import STALE_JOB_DAYS


def _parse_dt(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo is not None else value.replace(tzinfo=UTC)
    if isinstance(value, str):
        try:
            dt = datetime.fromisoformat(value)
            return dt if dt.tzinfo is not None else dt.replace(tzinfo=UTC)
        except ValueError:
            return None
    return None


def classify_opportunity_evidence(
    *,
    company_context: dict[str, Any],
    retrieved_evidence: list[RetrievedEvidenceItem],
    reference_now: datetime | None = None,
) -> OpportunityAssessment:
    """Deterministically classify company opportunity type and evidence strength.

    Completely independent from candidate-company fit score.
    Never treats funding alone as proof of hiring.
    Never confuses retrieval timestamp with publication/posting date.
    """
    now = reference_now or datetime.now(UTC)
    stale_cutoff = now - timedelta(days=STALE_JOB_DAYS)

    jobs: list[dict[str, Any]] = list(company_context.get("job_opportunities") or [])
    signals: list[dict[str, Any]] = list(company_context.get("hiring_signals") or [])
    funding_events: list[dict[str, Any]] = list(company_context.get("funding_events") or [])

    ev_by_type: dict[str, list[RetrievedEvidenceItem]] = {}
    for ev in retrieved_evidence:
        ev_by_type.setdefault(ev.entity_type, []).append(ev)

    job_ev_ids = [ev.source_evidence_id for ev in ev_by_type.get("job_opportunity", [])]
    hiring_ev_ids = [ev.source_evidence_id for ev in ev_by_type.get("hiring_signal", [])]
    all_hiring_ev_ids = list(dict.fromkeys(job_ev_ids + hiring_ev_ids))

    observed_facts: list[str] = []
    uncertainties: list[str] = []
    missing_evidence: list[str] = []

    confirmed_recent_jobs: list[dict[str, Any]] = []
    stale_or_unverified_jobs: list[dict[str, Any]] = []

    for job in jobs:
        posting_dt = _parse_dt(job.get("posting_date"))
        is_stale = posting_dt is not None and posting_dt < stale_cutoff
        is_verified = job.get("verification_status") == "verified"
        if job.get("is_active") and is_verified and not is_stale:
            confirmed_recent_jobs.append(job)
        else:
            stale_or_unverified_jobs.append(job)
            if is_stale:
                uncertainties.append(f"Job listing '{job.get('title')}' is older than {STALE_JOB_DAYS} days (stale).")
            elif not is_verified:
                uncertainties.append(
                    f"Job listing '{job.get('title')}' has verification_status='{job.get('verification_status')}'."
                )
            if posting_dt is None:
                uncertainties.append(f"Job listing '{job.get('title')}' has an unknown posting date.")

    active_signals: list[dict[str, Any]] = []
    hidden_signals: list[dict[str, Any]] = []
    stale_or_weak_signals: list[dict[str, Any]] = []

    for sig in signals:
        sig_type = sig.get("signal_type", "")
        if sig_type == "funding_only":
            continue
        pub_dt = _parse_dt(sig.get("publication_date"))
        is_stale = pub_dt is not None and pub_dt < stale_cutoff
        is_verified = sig.get("verification_status") == "verified"
        category = sig.get("opportunity_category")

        if category == "active" and is_verified and not is_stale:
            active_signals.append(sig)
        elif category == "hidden" and is_verified and not is_stale:
            hidden_signals.append(sig)
        else:
            stale_or_weak_signals.append(sig)
            if pub_dt is None:
                uncertainties.append(f"Hiring signal '{sig.get('title')}' is missing a publication date.")
            elif is_stale:
                uncertainties.append(f"Hiring signal '{sig.get('title')}' is older than {STALE_JOB_DAYS} days.")
            if not is_verified:
                uncertainties.append(
                    f"Hiring signal '{sig.get('title')}' has verification_status='{sig.get('verification_status')}'."
                )

    # Check for conflicting signals (e.g. active job vs stale/requires_review)
    if confirmed_recent_jobs and stale_or_unverified_jobs:
        uncertainties.append("Company has both confirmed recent openings and stale/unverified job listings.")

    # Decision tree
    opportunity_type: M5OpportunityType
    evidence_strength: EvidenceStrength
    requires_review = False

    if confirmed_recent_jobs or active_signals:
        opportunity_type = "active"
        for job in confirmed_recent_jobs:
            observed_facts.append(
                f"Confirmed active public job: {job.get('title')} (posted: {job.get('posting_date') or 'unknown'})."
            )
        for sig in active_signals:
            observed_facts.append(str(sig.get("observed_fact") or sig.get("title")))

        supporting_ids = all_hiring_ev_ids
        if not supporting_ids:
            # Fallback to any retrieved evidence if job/signal evidence wasn't indexed separately
            supporting_ids = list(dict.fromkeys(ev.source_evidence_id for ev in retrieved_evidence))
            uncertainties.append("Active role record exists, but dedicated job evidence document was not retrieved.")
            requires_review = True

        verified_ev_count = sum(
            1
            for ev in retrieved_evidence
            if ev.source_evidence_id in supporting_ids and ev.verification_status == "verified"
        )
        if confirmed_recent_jobs and active_signals and verified_ev_count >= 1:
            evidence_strength = "strong"
        elif verified_ev_count >= 2:
            evidence_strength = "strong"
        elif verified_ev_count >= 1:
            evidence_strength = "moderate"
        else:
            evidence_strength = "weak"
            requires_review = True

        classification_reason = (
            "Confirmed recent public job opening(s) supported by verified source evidence."
            if not requires_review
            else "Active job opening record present, but supporting evidence requires manual verification."
        )

    elif hidden_signals:
        opportunity_type = "hidden"
        for sig in hidden_signals:
            observed_facts.append(str(sig.get("observed_fact") or sig.get("title")))
        supporting_ids = all_hiring_ev_ids or list(
            dict.fromkeys(ev.source_evidence_id for ev in retrieved_evidence if ev.entity_type != "funding_event")
        )
        verified_ev_count = sum(
            1
            for ev in retrieved_evidence
            if ev.source_evidence_id in supporting_ids and ev.verification_status == "verified"
        )
        if verified_ev_count >= 2:
            evidence_strength = "moderate"
        elif verified_ev_count >= 1:
            evidence_strength = "moderate"
        else:
            evidence_strength = "weak"
            requires_review = True

        missing_evidence.append("No confirmed public job posting URL found.")
        classification_reason = (
            "No confirmed public job opening; credible non-funding hiring/expansion evidence supports considering an approach."
        )

    elif stale_or_weak_signals or stale_or_unverified_jobs:
        # Stale or unverified evidence cannot be marked as confirmed active
        has_any_non_funding_signal = len(stale_or_weak_signals) > 0
        if has_any_non_funding_signal:
            opportunity_type = "hidden"
            evidence_strength = "weak"
            requires_review = True
            for sig in stale_or_weak_signals:
                observed_facts.append(str(sig.get("observed_fact") or sig.get("title")))
            supporting_ids = all_hiring_ev_ids
            missing_evidence.append("Recent, verified hiring signal or active public job posting.")
            classification_reason = (
                "Only unverified, undated, or stale hiring evidence found; flagged as weak hidden opportunity requiring review."
            )
        else:
            opportunity_type = "insufficient_evidence"
            evidence_strength = "weak" if stale_or_unverified_jobs else "insufficient"
            requires_review = True
            for job in stale_or_unverified_jobs:
                observed_facts.append(f"Unverified or stale job record: {job.get('title')}.")
            supporting_ids = all_hiring_ev_ids
            missing_evidence.append("Recent, verified public job posting or credible expansion signal.")
            classification_reason = (
                "Existing job listing(s) are stale or unverified; insufficient credible evidence of an active opportunity."
            )

    else:
        opportunity_type = "insufficient_evidence"
        evidence_strength = "insufficient"
        supporting_ids = []
        if funding_events:
            observed_facts.append(
                f"Company has {len(funding_events)} funding event(s), but funding alone is never proof of hiring."
            )
        missing_evidence.append("Confirmed public job postings or credible hiring/expansion signals.")
        classification_reason = (
            "No credible active job openings or hiring-related expansion signals found; funding alone does not establish hiring."
        )

    return OpportunityAssessment(
        opportunity_type=opportunity_type,
        evidence_strength=evidence_strength,
        observed_facts=observed_facts,
        supporting_evidence_ids=list(dict.fromkeys(supporting_ids)),
        classification_reason=classification_reason,
        uncertainties=list(dict.fromkeys(uncertainties)),
        missing_evidence=list(dict.fromkeys(missing_evidence)),
        requires_review=requires_review,
    )
