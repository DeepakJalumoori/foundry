from datetime import UTC, datetime, timedelta
import re
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.m4 import (
    Company,
    CompanyResearch,
    EvidenceLink,
    Founder,
    FundingEvent,
    HiringSignal,
    JobOpportunity,
    SourceEvidence,
)
from app.models.m5 import MatchResult, RetrievalRecord
from app.schemas.m5 import RetrievedEvidenceItem
from app.schemas.m6 import (
    OutreachIntent,
    OutreachStrategy,
    StructuredOutreachClaim,
    StructuredOutreachEmail,
)
from app.services.hiring_service import STALE_JOB_DAYS
from app.services.source_validation import ensure_utc

_UNTRUSTED_TAG_SPAN_PATTERN = re.compile(
    r"<\s*untrusted_evidence\s*>.*?<\s*/\s*untrusted_evidence\s*>",
    re.IGNORECASE | re.DOTALL,
)

_INJECTION_PATTERNS = (
    re.compile(r"</?\s*untrusted_evidence\s*>", re.IGNORECASE),
    re.compile(r"(ignore|disregard|forget)\s+(all\s+)?(previous|prior|system)\s+(rules|instructions|prompts?)", re.IGNORECASE),
    re.compile(r"system\s+prompt", re.IGNORECASE),
    re.compile(r"invent\s+(a\s+)?(founder\s+)?email", re.IGNORECASE),
    re.compile(r"override\s+(all\s+)?(rules|instructions|scoring)", re.IGNORECASE),
    re.compile(r"\byou\s+are\s+now\b|\bact\s+as\b", re.IGNORECASE),
)

_BANNED_GENERIC_PHRASES = (
    "i hope this email finds you well",
    "i am extremely passionate about your company",
    "i would love to be a part of your journey",
)

_EMAIL_REGEX = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")

_HIRING_CLAIM_PATTERNS = (
    re.compile(r"\bapply(ing)?\s+(for|to)\s+(the|your)\s+(open\s+)?(role|position)\b", re.IGNORECASE),
    re.compile(r"\bopen\s+(role|position|job\s+opening)s?\b", re.IGNORECASE),
    re.compile(r"\b(job\s+posting|job\s+listing|formal\s+listing)\b", re.IGNORECASE),
    re.compile(r"\bsaw\s+your\s+.*\b(role|posting|opening)\b", re.IGNORECASE),
    re.compile(r"\bactively\s+hiring\b|\blooking\s+to\s+hire\b|\bhiring\s+for\b", re.IGNORECASE),
)

_NUMBER_OR_QUANTIFIER_PATTERN = re.compile(
    r"(\$?\b\d[\d,]*(?:\.\d+)?(?:\s*[mkb]|%|x|-person)?\b)",
    re.IGNORECASE,
)

_ROLE_TITLE_PATTERN = re.compile(
    r"\b(?:As\s+(?:the\s+)?|who\s+is\s+(?:the\s+)?|your\s+role\s+as\s+)"
    r"([A-Z][A-Za-z&/\- ]{2,40}?(?:Founder|CEO|CTO|COO|CFO|CPO|VP|Head\s+of\s+[A-Z][A-Za-z]+|Director\s+of\s+[A-Z][A-Za-z]+))",
)

_COMMON_SENTENCE_STARTERS = {
    "i", "we", "you", "your", "the", "this", "that", "while", "given", "if",
    "would", "hi", "hello", "dear", "best", "regards", "sincerely", "my", "our",
    "having", "with", "for", "in", "at", "on", "as", "it", "they", "their",
}

_EXPANSION_OR_MARKET_PATTERN = re.compile(
    r"\b(expanded|expanding|expansion|entered|entering|market-entry|launched\s+in|"
    r"opened\s+a\s+.*office|european|apac|latam|emea|london|berlin|tokyo|singapore)\b",
    re.IGNORECASE,
)

_CUSTOMER_OR_REVENUE_PATTERN = re.compile(
    r"\b(serves?|serving|customers?|users?|clients?|arr|mrr|revenue|funding|raised|valuation|series\s+[a-c]|seed\s+round)\b",
    re.IGNORECASE,
)

_CANDIDATE_ACHIEVEMENT_PATTERN = re.compile(
    r"\b(built|created|architected|led|managed|scaled|reduced|improved|increased|designed|launched)\b",
    re.IGNORECASE,
)


def is_qualifying_active_job(job: JobOpportunity, *, now: datetime | None = None) -> bool:
    """Return True only if a JobOpportunity is active, verified, and within STALE_JOB_DAYS (inclusive)."""
    if not job.is_active or job.verification_status != "verified":
        return False
    ref_now = ensure_utc(now) or datetime.now(UTC)
    ref_date = ensure_utc(job.posting_date) or ensure_utc(job.last_verified_at)
    if ref_date is None:
        return False
    return (ref_now - ref_date) <= timedelta(days=STALE_JOB_DAYS)


def contains_injection_marker(text: str) -> bool:
    if _UNTRUSTED_TAG_SPAN_PATTERN.search(text):
        return True
    return any(p.search(text) for p in _INJECTION_PATTERNS)


def strip_injection_markers(text: str) -> tuple[str, bool]:
    cleaned = text
    had_marker = False
    if _UNTRUSTED_TAG_SPAN_PATTERN.search(cleaned):
        had_marker = True
        cleaned = _UNTRUSTED_TAG_SPAN_PATTERN.sub("", cleaned)

    # Remove any entire sentence containing an injection instruction
    paragraphs = cleaned.split("\n\n")
    safe_paragraphs: list[str] = []
    for para in paragraphs:
        if "\n" in para and not any(p.search(para) for p in _INJECTION_PATTERNS):
            safe_paragraphs.append(para)
            continue
        sentences = re.split(r"(?<=[.!?])\s+", para.strip())
        kept: list[str] = []
        for sent in sentences:
            if any(p.search(sent) for p in _INJECTION_PATTERNS):
                had_marker = True
                continue
            if sent.strip():
                kept.append(sent.strip())
        if kept:
            safe_paragraphs.append(" ".join(kept))

    result = "\n\n".join(safe_paragraphs)
    result = re.sub(r"[ \t]{2,}", " ", result)
    result = re.sub(r"\n{3,}", "\n\n", result).strip()
    return result, had_marker


def assemble_candidate_context(profile_data: dict[str, Any]) -> dict[str, Any]:
    """Assemble sanitized candidate context from M3 CandidateProfile without raw resume text."""
    basic = profile_data.get("basic_info") or {}
    additional = profile_data.get("additional_info") or {}

    skills: list[str] = []
    for item in profile_data.get("skills") or []:
        if isinstance(item, dict) and item.get("name"):
            name = str(item["name"]).strip()
            if name and name not in skills:
                skills.append(name)

    work_experience: list[dict[str, Any]] = []
    for exp in profile_data.get("work_experience") or []:
        if isinstance(exp, dict):
            work_experience.append(
                {
                    "job_title": exp.get("job_title"),
                    "organization": exp.get("organization"),
                    "start_date": exp.get("start_date"),
                    "end_date": exp.get("end_date"),
                    "is_current": exp.get("is_current"),
                    "technologies": list(exp.get("technologies") or []),
                    "highlights": list(exp.get("highlights") or []),
                }
            )

    projects: list[dict[str, Any]] = []
    for proj in profile_data.get("projects") or []:
        if isinstance(proj, dict):
            projects.append(
                {
                    "name": proj.get("name"),
                    "description": proj.get("description"),
                    "technologies": list(proj.get("technologies") or []),
                    "outcomes": list(proj.get("outcomes") or []),
                }
            )

    education: list[dict[str, Any]] = []
    for edu in profile_data.get("education") or []:
        if isinstance(edu, dict):
            education.append(
                {
                    "institution": edu.get("institution"),
                    "degree": edu.get("degree"),
                    "field_of_study": edu.get("field_of_study"),
                }
            )

    achievements: list[str] = []
    for cert in profile_data.get("certifications_and_achievements") or []:
        if isinstance(cert, dict) and cert.get("title"):
            achievements.append(str(cert["title"]).strip())
        elif isinstance(cert, str) and cert.strip():
            achievements.append(cert.strip())

    return {
        "full_name": basic.get("full_name"),
        "email": basic.get("email"),
        "headline": basic.get("headline"),
        "current_role": basic.get("current_role"),
        "years_of_experience": basic.get("years_of_experience"),
        "skills": skills,
        "work_experience": work_experience,
        "projects": projects,
        "education": education,
        "achievements": achievements,
        "summary": additional.get("summary"),
        "interests": list(additional.get("interests") or []),
    }


def assemble_company_context(
    db: Session,
    company: Company,
    match_result: MatchResult,
    *,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Assemble structured company and M5 match context using M4 job freshness/verification rules."""
    research_records = list(
        db.scalars(
            select(CompanyResearch)
            .where(CompanyResearch.company_id == company.id)
            .order_by(CompanyResearch.researched_at.desc())
        ).all()
    )
    funding_events = list(
        db.scalars(select(FundingEvent).where(FundingEvent.company_id == company.id)).all()
    )
    hiring_signals = list(
        db.scalars(select(HiringSignal).where(HiringSignal.company_id == company.id)).all()
    )
    job_opportunities = list(
        db.scalars(select(JobOpportunity).where(JobOpportunity.company_id == company.id)).all()
    )

    ref_now = ensure_utc(now) or datetime.now(UTC)
    active_jobs = [
        {
            "id": job.id,
            "title": job.title,
            "job_url": job.job_url,
            "location": job.location,
            "employment_type": job.employment_type,
            "posting_date": job.posting_date.isoformat() if job.posting_date else None,
            "last_verified_at": job.last_verified_at.isoformat() if job.last_verified_at else None,
            "verification_status": job.verification_status,
            "is_active": job.is_active,
        }
        for job in job_opportunities
        if is_qualifying_active_job(job, now=ref_now)
    ]

    return {
        "company_id": company.id,
        "name": company.name,
        "description": company.description,
        "industry": company.industry,
        "product_or_service": company.product_or_service,
        "stage": company.stage,
        "tech_stack": list(company.tech_stack or []),
        "official_website": company.official_website,
        "data_origin": company.data_origin,
        "research_summaries": [r.summary for r in research_records if r.summary],
        "funding_events": [
            {
                "round_type": f.round_type,
                "amount": f.amount,
                "currency": f.currency,
                "normalized_summary": f.normalized_summary,
                "verification_status": f.verification_status,
            }
            for f in funding_events
        ],
        "hiring_signals": [
            {
                "signal_type": s.signal_type,
                "opportunity_category": s.opportunity_category,
                "title": s.title,
                "observed_fact": s.observed_fact,
                "role_titles": list(s.role_titles or []),
                "verification_status": s.verification_status,
            }
            for s in hiring_signals
        ],
        "active_jobs": active_jobs,
        "match_fit_score": match_result.fit_score,
        "match_fit_coverage": match_result.fit_coverage,
        "opportunity_type": match_result.opportunity_type,
        "evidence_strength": match_result.evidence_strength,
        "match_explanation": match_result.explanation,
    }


def assemble_founder_context(
    db: Session,
    founder: Founder,
) -> tuple[dict[str, Any], list[SourceEvidence], list[str]]:
    """Assemble conservative founder context without fabricating email or role."""
    links = list(
        db.scalars(
            select(EvidenceLink).where(
                EvidenceLink.entity_type == "founder",
                EvidenceLink.entity_id == founder.id,
            )
        ).all()
    )
    evidence_ids = [link.evidence_id for link in links]
    founder_evidence: list[SourceEvidence] = []
    if evidence_ids:
        founder_evidence = list(
            db.scalars(select(SourceEvidence).where(SourceEvidence.id.in_(evidence_ids))).all()
        )

    warnings: list[str] = []
    if founder.verification_status != "verified":
        warnings.append(
            f"Founder identity verification status is '{founder.verification_status}'; review before outreach."
        )
    if founder.conflict_notes:
        warnings.append(f"Founder record has conflict notes: {founder.conflict_notes}")
    if not founder.role_title:
        warnings.append("Founder role/title is missing; avoid assuming a specific title.")
    if not founder.public_profile_url:
        warnings.append("Founder public profile URL is unavailable.")
    warnings.append(
        "Founder email address is unavailable in stored records; outreach draft generated without fabricated email."
    )

    context = {
        "founder_id": founder.id,
        "company_id": founder.company_id,
        "full_name": founder.full_name,
        "role_title": founder.role_title,
        "public_profile_url": founder.public_profile_url,
        "email": None,
        "biography": founder.biography,
        "verification_status": founder.verification_status,
        "conflict_notes": founder.conflict_notes,
        "data_origin": founder.data_origin,
        "evidence_ids": [ev.id for ev in founder_evidence],
    }
    return context, founder_evidence, warnings


def collect_company_evidence_for_outreach(
    db: Session,
    *,
    company_id: str,
    matching_run_id: str,
    retrieved_items: list[RetrievedEvidenceItem],
    founder_evidence: list[SourceEvidence],
) -> list[RetrievedEvidenceItem]:
    """Merge company-specific FTS5 evidence, match retrieval records, and founder evidence safely."""
    by_source_id: dict[str, RetrievedEvidenceItem] = {}

    for item in retrieved_items:
        if item.company_id == company_id:
            by_source_id[item.source_evidence_id] = item

    prior_records = list(
        db.scalars(
            select(RetrievalRecord)
            .where(
                RetrievalRecord.matching_run_id == matching_run_id,
                RetrievalRecord.company_id == company_id,
            )
            .order_by(RetrievalRecord.rank_order.asc())
        ).all()
    )
    for rec in prior_records:
        if rec.source_evidence_id and rec.source_evidence_id not in by_source_id:
            snap = rec.retrieved_snapshot or {}
            src = db.get(SourceEvidence, rec.source_evidence_id)
            if src is not None:
                by_source_id[src.id] = RetrievedEvidenceItem(
                    evidence_document_id=rec.evidence_document_id or src.id,
                    source_evidence_id=src.id,
                    company_id=company_id,
                    entity_type=str(snap.get("entity_type") or "company"),
                    document_title=str(snap.get("document_title") or src.source_title),
                    content=str(snap.get("content") or src.excerpt or src.source_title),
                    source_url=src.source_url,
                    source_title=src.source_title,
                    publication_date=src.publication_date,
                    retrieved_at=src.retrieved_at,
                    verification_status=src.verification_status,  # type: ignore[arg-type]
                    data_origin=src.data_origin,  # type: ignore[arg-type]
                    bm25_score=rec.bm25_score,
                )

    for src in founder_evidence:
        if src.id not in by_source_id:
            by_source_id[src.id] = RetrievedEvidenceItem(
                evidence_document_id=src.id,
                source_evidence_id=src.id,
                company_id=company_id,
                entity_type="founder",
                document_title=src.source_title,
                content=src.excerpt or src.source_title,
                source_url=src.source_url,
                source_title=src.source_title,
                publication_date=src.publication_date,
                retrieved_at=src.retrieved_at,
                verification_status=src.verification_status,  # type: ignore[arg-type]
                data_origin=src.data_origin,  # type: ignore[arg-type]
                bm25_score=None,
            )

    return list(by_source_id.values())


def _candidate_grounding_corpus(candidate_context: dict[str, Any]) -> str:
    parts: list[str] = [
        str(candidate_context.get("full_name") or ""),
        str(candidate_context.get("headline") or ""),
        str(candidate_context.get("current_role") or ""),
        str(candidate_context.get("summary") or ""),
    ]
    for skill in candidate_context.get("skills") or []:
        parts.append(str(skill))
    for exp in candidate_context.get("work_experience") or []:
        if isinstance(exp, dict):
            parts.extend(
                [
                    str(exp.get("job_title") or ""),
                    str(exp.get("organization") or ""),
                    " ".join(str(t) for t in (exp.get("technologies") or [])),
                    " ".join(str(h) for h in (exp.get("highlights") or [])),
                ]
            )
    for proj in candidate_context.get("projects") or []:
        if isinstance(proj, dict):
            parts.extend(
                [
                    str(proj.get("name") or ""),
                    str(proj.get("description") or ""),
                    " ".join(str(t) for t in (proj.get("technologies") or [])),
                    " ".join(str(o) for o in (proj.get("outcomes") or [])),
                ]
            )
    for edu in candidate_context.get("education") or []:
        if isinstance(edu, dict):
            parts.extend(
                [
                    str(edu.get("institution") or ""),
                    str(edu.get("degree") or ""),
                    str(edu.get("field_of_study") or ""),
                ]
            )
    for ach in candidate_context.get("achievements") or []:
        parts.append(str(ach))
    for interest in candidate_context.get("interests") or []:
        parts.append(str(interest))
    return " ".join(p for p in parts if p).lower()


def _candidate_token_set(candidate_context: dict[str, Any]) -> set[str]:
    tokens: set[str] = set()
    for skill in candidate_context.get("skills") or []:
        if str(skill).strip():
            tokens.add(str(skill).strip().lower())
    for exp in candidate_context.get("work_experience") or []:
        if isinstance(exp, dict):
            for field_name in ("job_title", "organization"):
                val = exp.get(field_name)
                if val:
                    tokens.add(str(val).strip().lower())
            for tech in exp.get("technologies") or []:
                tokens.add(str(tech).strip().lower())
            for h in exp.get("highlights") or []:
                tokens.add(str(h).strip().lower())
    for proj in candidate_context.get("projects") or []:
        if isinstance(proj, dict):
            if proj.get("name"):
                tokens.add(str(proj["name"]).strip().lower())
            for tech in proj.get("technologies") or []:
                tokens.add(str(tech).strip().lower())
            for out in proj.get("outcomes") or []:
                tokens.add(str(out).strip().lower())
    for edu in candidate_context.get("education") or []:
        if isinstance(edu, dict):
            for f in ("institution", "degree", "field_of_study"):
                if edu.get(f):
                    tokens.add(str(edu[f]).strip().lower())
    for ach in candidate_context.get("achievements") or []:
        tokens.add(str(ach).strip().lower())
    return tokens


def _all_numbers_present(text: str, corpus_lower: str) -> bool:
    for num in _NUMBER_OR_QUANTIFIER_PATTERN.findall(text):
        n = num.strip().lower()
        # Allow standard polite call-to-action duration ("15-minute" / "15 minutes")
        if n in ("15",):
            continue
        if n not in corpus_lower:
            return False
    return True


def _is_candidate_claim_supported(claim_text: str, candidate_context: dict[str, Any]) -> bool:
    norm = claim_text.strip().lower()
    if not norm:
        return False
    corpus_lower = _candidate_grounding_corpus(candidate_context)
    if not _all_numbers_present(claim_text, corpus_lower):
        return False
    tokens = _candidate_token_set(candidate_context)
    for tok in tokens:
        if len(tok) >= 2 and (tok in norm or norm in tok):
            return True
    return False


def _build_company_grounding_corpus(
    company_context: dict[str, Any],
    company_evidence: list[RetrievedEvidenceItem],
    cited_evidence_only: list[RetrievedEvidenceItem] | None = None,
) -> str:
    parts: list[str] = [
        str(company_context.get("name") or ""),
        str(company_context.get("description") or ""),
        str(company_context.get("industry") or ""),
        str(company_context.get("product_or_service") or ""),
        str(company_context.get("stage") or ""),
        " ".join(str(t) for t in (company_context.get("tech_stack") or [])),
    ]
    for s in company_context.get("research_summaries") or []:
        parts.append(str(s))
    for f in company_context.get("funding_events") or []:
        if isinstance(f, dict):
            parts.append(str(f.get("normalized_summary") or ""))
            parts.append(str(f.get("round_type") or ""))
            if f.get("amount") is not None:
                parts.append(str(f["amount"]))
    for h in company_context.get("hiring_signals") or []:
        if isinstance(h, dict):
            parts.append(str(h.get("observed_fact") or ""))
            parts.append(str(h.get("title") or ""))
    for j in company_context.get("active_jobs") or []:
        if isinstance(j, dict):
            parts.append(str(j.get("title") or ""))
    ev_list = cited_evidence_only if cited_evidence_only is not None else company_evidence
    for ev in ev_list:
        if not contains_injection_marker(ev.content):
            parts.append(ev.document_title)
            parts.append(ev.content)
    return " ".join(parts).lower()


def _is_company_claim_supported(
    claim_text: str,
    *,
    cited_evidence: list[RetrievedEvidenceItem],
    company_context: dict[str, Any],
    founder_context: dict[str, Any],
    claim_category: str,
) -> bool:
    if not cited_evidence:
        return False
    ev_corpus = " ".join(
        f"{ev.document_title} {ev.content}"
        for ev in cited_evidence
        if not contains_injection_marker(ev.content)
    ).lower()
    full_corpus = _build_company_grounding_corpus(company_context, cited_evidence, cited_evidence)
    combined = f"{ev_corpus} {full_corpus}"

    if not _all_numbers_present(claim_text, combined):
        return False

    if claim_category == "founder":
        founder_role = str(founder_context.get("role_title") or "").strip().lower()
        for match in _ROLE_TITLE_PATTERN.findall(claim_text):
            if not founder_role or match.strip().lower() not in founder_role:
                return False

    return True


def _is_neutral_connective_sentence(
    sentence: str,
    *,
    company_name: str,
    candidate_context: dict[str, Any],
) -> bool:
    """Return True only if the sentence contains no ungrounded factual claims."""
    if any(p.search(sentence) for p in _HIRING_CLAIM_PATTERNS):
        return False
    if _EXPANSION_OR_MARKET_PATTERN.search(sentence):
        return False
    if _CUSTOMER_OR_REVENUE_PATTERN.search(sentence):
        return False
    if _ROLE_TITLE_PATTERN.search(sentence):
        return False
    if _CANDIDATE_ACHIEVEMENT_PATTERN.search(sentence):
        return False
    if _NUMBER_OR_QUANTIFIER_PATTERN.search(sentence):
        # Only allow standard 15-minute CTA
        nums = [n.strip().lower() for n in _NUMBER_OR_QUANTIFIER_PATTERN.findall(sentence)]
        if any(n != "15" for n in nums):
            return False

    # Reject unexpected capitalized org/geography names not in company/candidate context
    cand_corpus = _candidate_grounding_corpus(candidate_context)
    comp_lower = company_name.lower()
    for match in re.finditer(r"\b([A-Z][A-Za-z0-9.&-]{2,})\b", sentence):
        if match.start() == 0:
            continue
        word = match.group(1).lower()
        if word in _COMMON_SENTENCE_STARTERS:
            continue
        if word in comp_lower or word in cand_corpus:
            continue
        return False

    return True


def _sentence_matches_validated_grounding(
    sentence: str,
    *,
    intent: OutreachIntent,
    company_context: dict[str, Any],
    candidate_context: dict[str, Any],
    founder_context: dict[str, Any],
    validated_claims: list[StructuredOutreachClaim],
    company_evidence: list[RetrievedEvidenceItem],
) -> tuple[bool, str | None]:
    """Verify a sentence against validated claims, candidate profile, founder data, or neutral allowlist."""
    company_name = str(company_context.get("name") or "")
    has_qualifying_active_job = (
        intent == "job_interest"
        and company_context.get("opportunity_type") == "active"
        and bool(company_context.get("active_jobs"))
    )

    is_negative_disclaimer = bool(
        re.search(r"\b(did not|didn't|no)\s+(see\s+)?(a\s+)?formal\s+listing\b", sentence, re.IGNORECASE)
        or re.search(r"\bwithout\s+assuming\s+any\s+current\s+hiring\b", sentence, re.IGNORECASE)
    )
    if not is_negative_disclaimer and any(p.search(sentence) for p in _HIRING_CLAIM_PATTERNS):
        if not has_qualifying_active_job:
            return False, "Removed unsupported hiring/job-opening claim from outreach text."
        job_titles = [str(j.get("title") or "").lower() for j in (company_context.get("active_jobs") or [])]
        if not any(jt and jt in sentence.lower() for jt in job_titles):
            return False, "Removed ungrounded job-title claim from outreach text."

    # Check founder role titles against verified founder_context
    founder_role = str(founder_context.get("role_title") or "").strip().lower()
    for role_match in _ROLE_TITLE_PATTERN.findall(sentence):
        if not founder_role or role_match.strip().lower() not in founder_role:
            return False, "Removed unsupported founder role/title claim from outreach text."

    if _is_neutral_connective_sentence(
        sentence, company_name=company_name, candidate_context=candidate_context
    ):
        return True, None

    # Otherwise, sentence contains factual assertions: must be grounded in validated claims or profile/company corpus
    supported_company_claims = [
        c.claim_text.lower()
        for c in validated_claims
        if c.claim_category != "candidate_profile" and c.support_status == "supported"
    ]
    company_corpus = _build_company_grounding_corpus(company_context, company_evidence)
    candidate_corpus = _candidate_grounding_corpus(candidate_context)
    combined_corpus = f"{company_corpus} {candidate_corpus} {' '.join(supported_company_claims)}"

    # Every numerical quantifier/currency/count must appear in combined_corpus
    if not _all_numbers_present(sentence, combined_corpus):
        return False, "Removed ungrounded numerical or metric claim from outreach text."

    # Expansion/market-entry assertions must be explicitly supported in company_corpus
    if _EXPANSION_OR_MARKET_PATTERN.search(sentence):
        exp_terms = [t.lower() for t in _EXPANSION_OR_MARKET_PATTERN.findall(sentence)]
        if not all(t in company_corpus for t in exp_terms):
            return False, "Removed unsupported expansion or market-entry claim from outreach text."

    # Customer/revenue/funding assertions must be explicitly supported in company_corpus
    if _CUSTOMER_OR_REVENUE_PATTERN.search(sentence):
        cust_terms = [t.lower() for t in _CUSTOMER_OR_REVENUE_PATTERN.findall(sentence)]
        if not all(t in company_corpus for t in cust_terms):
            return False, "Removed unsupported customer or revenue claim from outreach text."

    # Candidate achievement assertions must be supported in candidate_corpus (not merely company_corpus)
    if _CANDIDATE_ACHIEVEMENT_PATTERN.search(sentence) and re.search(r"\b(i|my)\b", sentence, re.IGNORECASE):
        if not _all_numbers_present(sentence, candidate_corpus):
            return False, "Removed unverified candidate metric claim from outreach text."
        # Check capitalized orgs/technologies or key achievement nouns in candidate_corpus
        content_words = [
            w.lower()
            for w in re.findall(r"\b[a-zA-Z][a-zA-Z0-9._+-]{3,}\b", sentence)
            if w.lower() not in {
                "built", "created", "architected", "led", "managed", "scaled", "reduced",
                "improved", "increased", "designed", "launched", "that", "with", "from",
                "into", "have", "been", "experience", "background", "production", "systems",
            }
        ]
        if content_words and not any(w in candidate_corpus for w in content_words):
            return False, "Removed unverified candidate achievement claim from outreach text."

    # Any capitalized proper nouns/geographies/orgs must exist in company/candidate/founder context
    founder_name_lower = str(founder_context.get("full_name") or "").lower()
    allowed_prop_corpus = f"{combined_corpus} {founder_name_lower}"
    for match in re.finditer(r"\b([A-Z][A-Za-z0-9.&-]{2,})\b", sentence):
        if match.start() == 0:
            continue
        word = match.group(1).lower()
        if word in _COMMON_SENTENCE_STARTERS:
            continue
        if word not in allowed_prop_corpus:
            return False, f"Removed ungrounded entity/organization claim ('{match.group(1)}') from outreach text."

    return True, None


def _sanitize_and_ground_body(
    body: str,
    *,
    intent: OutreachIntent,
    company_context: dict[str, Any],
    candidate_context: dict[str, Any],
    founder_context: dict[str, Any],
    validated_claims: list[StructuredOutreachClaim],
    company_evidence: list[RetrievedEvidenceItem],
    allowed_emails: set[str],
) -> tuple[str, list[str], bool]:
    warnings: list[str] = []
    requires_review = False

    cleaned_body, had_injection = strip_injection_markers(body)
    if had_injection:
        warnings.append("Removed prompt-injection instruction span from generated body.")
        requires_review = True

    for em in _EMAIL_REGEX.findall(cleaned_body):
        if em.lower() not in allowed_emails:
            cleaned_body = cleaned_body.replace(em, "[redacted-unverified-email]")
            warnings.append("Redacted unverified email address in body; founder email is unavailable.")
            requires_review = True

    kept_paragraphs: list[str] = []
    substantive_sentences = 0

    for para in cleaned_body.split("\n\n"):
        stripped_para = para.strip()
        if not stripped_para:
            continue

        # Preserve greeting ("Hi X,") and closing ("Best regards,\nName")
        if re.fullmatch(r"(Hi|Hello|Dear)\s+[^,\n]+,", stripped_para, re.IGNORECASE):
            kept_paragraphs.append(stripped_para)
            continue
        if "\n" in stripped_para and re.match(r"^(Best|Regards|Sincerely|Thanks)", stripped_para, re.IGNORECASE):
            kept_paragraphs.append(stripped_para)
            continue

        sentences = re.split(r"(?<=[.!?])\s+", stripped_para)
        kept_sentences: list[str] = []
        for sent in sentences:
            s = sent.strip()
            if not s:
                continue
            ok, reason = _sentence_matches_validated_grounding(
                s,
                intent=intent,
                company_context=company_context,
                candidate_context=candidate_context,
                founder_context=founder_context,
                validated_claims=validated_claims,
                company_evidence=company_evidence,
            )
            if not ok:
                warnings.append(reason or "Removed ungrounded factual sentence from outreach body.")
                requires_review = True
                continue
            kept_sentences.append(s)
            substantive_sentences += 1

        if kept_sentences:
            kept_paragraphs.append(" ".join(kept_sentences))

    if substantive_sentences == 0:
        raise ValueError(
            "Generated outreach body has no coherent grounded content remaining after sanitization."
        )

    final_body = "\n\n".join(kept_paragraphs).strip()
    return final_body, warnings, requires_review


def validate_outreach_generation(
    *,
    draft: StructuredOutreachEmail,
    strategy: OutreachStrategy,
    company_id: str,
    intent: OutreachIntent,
    candidate_context: dict[str, Any],
    company_context: dict[str, Any],
    founder_context: dict[str, Any],
    company_evidence: list[RetrievedEvidenceItem],
    initial_warnings: list[str],
) -> tuple[StructuredOutreachEmail, OutreachStrategy, list[StructuredOutreachClaim], list[str], bool]:
    """Deterministically validate generated outreach claims, evidence IDs, and final subject/body."""
    warnings = list(initial_warnings)
    requires_review = bool(
        founder_context.get("verification_status") != "verified" or founder_context.get("conflict_notes")
    )
    evidence_by_id = {ev.source_evidence_id: ev for ev in company_evidence if ev.company_id == company_id}

    # 1. Validate evidence_references (strip cross-company or unknown IDs)
    valid_refs: list[str] = []
    invalid_refs: list[str] = []
    for ref in draft.evidence_references:
        if ref in evidence_by_id:
            if ref not in valid_refs:
                valid_refs.append(ref)
        else:
            invalid_refs.append(ref)

    if invalid_refs:
        warnings.append(
            f"Stripped {len(invalid_refs)} invalid or cross-company evidence reference(s)."
        )
        requires_review = True

    # 2. Independently validate claim-level evidence grounding
    validated_claims: list[StructuredOutreachClaim] = []
    unsupported_claims = list(draft.unsupported_or_uncertain_claims)

    for claim in draft.claims:
        if contains_injection_marker(claim.claim_text):
            warnings.append("Removed claim containing prompt-injection marker.")
            requires_review = True
            continue

        if claim.claim_category == "candidate_profile":
            if claim.evidence_ids:
                warnings.append("Removed company evidence IDs from candidate_profile claim.")
            supported = _is_candidate_claim_supported(claim.claim_text, candidate_context)
            if not supported:
                unsupported_claims.append(claim.claim_text)
                warnings.append(f"Flagged unsupported candidate claim: {claim.claim_text[:100]}")
                requires_review = True
            validated_claims.append(
                StructuredOutreachClaim(
                    claim_text=claim.claim_text,
                    claim_category="candidate_profile",
                    evidence_ids=[],
                    verification_status="verified" if supported else "requires_review",
                    support_status="supported" if supported else "unsupported",
                    requires_review=not supported,
                )
            )
        else:
            claim_ev_ids = [eid for eid in claim.evidence_ids if eid in evidence_by_id]
            dropped_ids = [eid for eid in claim.evidence_ids if eid not in evidence_by_id]
            if dropped_ids:
                warnings.append("Stripped invalid or cross-company evidence ID(s) from company claim.")
                requires_review = True

            cited_items = [evidence_by_id[eid] for eid in claim_ev_ids]
            claim_supported = _is_company_claim_supported(
                claim.claim_text,
                cited_evidence=cited_items,
                company_context=company_context,
                founder_context=founder_context,
                claim_category=claim.claim_category,
            )

            if claim_ev_ids and claim_supported:
                all_verified = all(
                    evidence_by_id[eid].verification_status == "verified" for eid in claim_ev_ids
                )
                v_status = "verified" if all_verified else "unverified"
                s_status = "supported"
                c_review = claim.requires_review or not all_verified
            else:
                v_status = "requires_review"
                s_status = "unsupported"
                c_review = True
                unsupported_claims.append(claim.claim_text)
                warnings.append(f"Flagged ungrounded company claim: {claim.claim_text[:100]}")
                requires_review = True

            validated_claims.append(
                StructuredOutreachClaim(
                    claim_text=claim.claim_text,
                    claim_category=claim.claim_category,
                    evidence_ids=claim_ev_ids,
                    verification_status=v_status,  # type: ignore[arg-type]
                    support_status=s_status,  # type: ignore[arg-type]
                    requires_review=c_review,
                )
            )

    # 3. Validate candidate_strengths_used against CandidateProfile
    verified_strengths: list[str] = []
    for strength in draft.candidate_strengths_used:
        if _is_candidate_claim_supported(strength, candidate_context):
            verified_strengths.append(strength)
        else:
            unsupported_claims.append(f"Candidate strength not in profile: {strength}")
            warnings.append(f"Removed unsupported candidate strength: {strength}")
            requires_review = True

    # 4. Validate and sanitize final subject and body
    allowed_emails: set[str] = set()
    if candidate_context.get("email"):
        allowed_emails.add(str(candidate_context["email"]).strip().lower())
    if founder_context.get("email"):
        allowed_emails.add(str(founder_context["email"]).strip().lower())

    company_name = str(company_context.get("name") or "your team")

    clean_subject, subj_injection = strip_injection_markers(draft.subject)
    if subj_injection:
        warnings.append("Removed prompt-injection instruction from subject.")
        requires_review = True
    for em in _EMAIL_REGEX.findall(clean_subject):
        if em.lower() not in allowed_emails:
            clean_subject = clean_subject.replace(em, "").strip()
            warnings.append("Removed unverified email address from subject; founder email is unavailable.")
            requires_review = True

    subj_ok, subj_reason = _sentence_matches_validated_grounding(
        clean_subject,
        intent=intent,
        company_context=company_context,
        candidate_context=candidate_context,
        founder_context=founder_context,
        validated_claims=validated_claims,
        company_evidence=company_evidence,
    )
    if not clean_subject or not subj_ok:
        clean_subject = f"Connecting regarding {company_name}"
        warnings.append(subj_reason or "Replaced ungrounded or empty subject with neutral fallback.")
        requires_review = True

    clean_body, body_warnings, body_review = _sanitize_and_ground_body(
        draft.body,
        intent=intent,
        company_context=company_context,
        candidate_context=candidate_context,
        founder_context=founder_context,
        validated_claims=validated_claims,
        company_evidence=company_evidence,
        allowed_emails=allowed_emails,
    )
    warnings.extend(body_warnings)
    if body_review:
        requires_review = True

    # 5. Post-transformation validation check
    lower_body = clean_body.lower()
    for phrase in _BANNED_GENERIC_PHRASES:
        if phrase in lower_body:
            warnings.append(f"Draft contains generic cliché phrase: '{phrase}'.")
            requires_review = True

    if not valid_refs:
        warnings.append("No company SourceEvidence IDs were cited; manual review required.")
        requires_review = True

    if not clean_body or contains_injection_marker(clean_body) or contains_injection_marker(clean_subject):
        raise ValueError("Generated outreach draft failed post-sanitization safety validation.")

    cleaned_draft = draft.model_copy(
        update={
            "subject": clean_subject,
            "body": clean_body,
            "outreach_intent": intent,
            "candidate_strengths_used": verified_strengths,
            "evidence_references": valid_refs,
            "claims": validated_claims,
            "unsupported_or_uncertain_claims": list(dict.fromkeys(unsupported_claims)),
            "review_warnings": list(dict.fromkeys(warnings)),
        }
    )

    return cleaned_draft, strategy, validated_claims, list(dict.fromkeys(warnings)), requires_review
