from dataclasses import dataclass
from datetime import date
import re

from app.schemas.candidate_profile import (
    ProfileExtractionStatus,
    SkillItem,
    StructuredCandidateProfile,
)
from app.services.resume_extractor import ResumeExtractionResult

_MONTH_NAMES = {
    "jan": 1, "january": 1,
    "feb": 2, "february": 2,
    "mar": 3, "march": 3,
    "apr": 4, "april": 4,
    "may": 5,
    "jun": 6, "june": 6,
    "jul": 7, "july": 7,
    "aug": 8, "august": 8,
    "sep": 9, "sept": 9, "september": 9,
    "oct": 10, "october": 10,
    "nov": 11, "november": 11,
    "dec": 12, "december": 12,
}

_CURRENT_MARKERS = {"present", "current", "now", "ongoing"}


@dataclass(frozen=True, slots=True)
class ProfileValidationOutcome:
    """Validated and grounded candidate profile with review status and warnings."""

    profile: StructuredCandidateProfile
    extraction_status: ProfileExtractionStatus
    warnings: list[str]


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def _parse_date_value(raw: str | None) -> tuple[date | None, bool]:
    """Parse common resume date strings into (comparable_date, is_valid_format).

    Returns (None, True) for 'Present'/'Current' or None.
    """
    if raw is None:
        return None, True

    cleaned = raw.strip()
    if not cleaned:
        return None, True

    if cleaned.lower() in _CURRENT_MARKERS:
        return None, True

    if re.fullmatch(r"\d{4}", cleaned):
        year = int(cleaned)
        if 1950 <= year <= 2100:
            return date(year, 1, 1), True
        return None, False

    ym_match = re.fullmatch(r"(\d{4})-(\d{1,2})", cleaned)
    if ym_match:
        year, month = int(ym_match.group(1)), int(ym_match.group(2))
        if 1950 <= year <= 2100 and 1 <= month <= 12:
            return date(year, month, 1), True
        return None, False

    ymd_match = re.fullmatch(r"(\d{4})-(\d{1,2})-(\d{1,2})", cleaned)
    if ymd_match:
        year, month, day = int(ymd_match.group(1)), int(ymd_match.group(2)), int(ymd_match.group(3))
        try:
            return date(year, month, day), True
        except ValueError:
            return None, False

    month_year_match = re.fullmatch(r"([A-Za-z]+)\s+(\d{4})", cleaned)
    if month_year_match:
        month_str = month_year_match.group(1).lower()
        year = int(month_year_match.group(2))
        month = _MONTH_NAMES.get(month_str)
        if month is not None and 1950 <= year <= 2100:
            return date(year, month, 1), True
        return None, False

    return None, False


def _deduplicate_skills(skills: list[SkillItem], warnings: list[str]) -> list[SkillItem]:
    seen: dict[str, SkillItem] = {}
    for skill in skills:
        key = re.sub(r"\s+", " ", skill.name).strip().lower()
        if not key:
            continue
        if key in seen:
            warnings.append(f"Duplicate skill '{skill.name}' removed after case-insensitive normalization.")
            continue
        seen[key] = skill
    return list(seen.values())


def _snippet_matches_text(norm_snippet: str, norm_text: str) -> bool:
    if len(norm_snippet) <= 6 or " " not in norm_snippet:
        pattern = rf"(?<![a-z0-9_]){re.escape(norm_snippet)}(?![a-z0-9_])"
        return re.search(pattern, norm_text) is not None
    return norm_snippet in norm_text


def _is_snippet_grounded(
    snippet: str | None,
    page_number: int | None,
    extraction: ResumeExtractionResult,
) -> bool:
    if not snippet or not snippet.strip():
        return False

    norm_snippet = _normalize_text(snippet)
    if not norm_snippet:
        return False

    if page_number is not None:
        if page_number < 1 or page_number > extraction.page_count:
            return False
        page_text = _normalize_text(extraction.pages[page_number - 1].text)
        if _snippet_matches_text(norm_snippet, page_text):
            return True

    full_text = _normalize_text(extraction.extracted_text)
    return _snippet_matches_text(norm_snippet, full_text)


def validate_and_ground_profile(
    profile: StructuredCandidateProfile,
    extraction: ResumeExtractionResult,
    initial_warnings: list[str] | None = None,
) -> ProfileValidationOutcome:
    """Validate dates, deduplicate skills, and verify evidence snippets against extracted PDF text."""
    warnings: list[str] = list(extraction.warnings)
    if initial_warnings:
        warnings.extend(initial_warnings)

    data = profile.model_copy(deep=True)
    data.skills = _deduplicate_skills(data.skills, warnings)

    total_items = 0
    review_items = 0

    for skill in data.skills:
        total_items += 1
        if not _is_snippet_grounded(skill.evidence_snippet, skill.page_number, extraction):
            skill.evidence_status = "requires_review"
            review_items += 1
            warnings.append(f"Skill '{skill.name}' lacks verified resume evidence and requires review.")

    for exp in data.work_experience:
        total_items += 1
        start_dt, start_ok = _parse_date_value(exp.start_date)
        end_dt, end_ok = _parse_date_value(exp.end_date)

        if not start_ok or not end_ok:
            exp.evidence_status = "requires_review"
            review_items += 1
            warnings.append(f"Work experience at '{exp.organization}' has an unrecognized date format.")
        elif start_dt and end_dt and start_dt > end_dt:
            exp.evidence_status = "requires_review"
            review_items += 1
            warnings.append(f"Work experience at '{exp.organization}' has start_date after end_date.")
        elif exp.is_current and exp.end_date and exp.end_date.strip().lower() not in _CURRENT_MARKERS:
            exp.evidence_status = "requires_review"
            review_items += 1
            warnings.append(f"Current role at '{exp.organization}' has an inconsistent end_date.")
        elif not _is_snippet_grounded(exp.evidence_snippet, exp.page_number, extraction):
            exp.evidence_status = "requires_review"
            review_items += 1
            warnings.append(f"Work experience at '{exp.organization}' lacks verified resume evidence.")

    for edu in data.education:
        total_items += 1
        start_dt, start_ok = _parse_date_value(edu.start_date)
        end_dt, end_ok = _parse_date_value(edu.end_date)

        if not start_ok or not end_ok:
            edu.evidence_status = "requires_review"
            review_items += 1
            warnings.append(f"Education at '{edu.institution}' has an unrecognized date format.")
        elif start_dt and end_dt and start_dt > end_dt:
            edu.evidence_status = "requires_review"
            review_items += 1
            warnings.append(f"Education at '{edu.institution}' has start_date after end_date.")
        elif not _is_snippet_grounded(edu.evidence_snippet, edu.page_number, extraction):
            edu.evidence_status = "requires_review"
            review_items += 1
            warnings.append(f"Education at '{edu.institution}' lacks verified resume evidence.")

    for proj in data.projects:
        total_items += 1
        if not _is_snippet_grounded(proj.evidence_snippet, proj.page_number, extraction):
            proj.evidence_status = "requires_review"
            review_items += 1
            warnings.append(f"Project '{proj.name}' lacks verified resume evidence.")

    for cert in data.certifications_and_achievements:
        total_items += 1
        if not _is_snippet_grounded(cert.evidence_snippet, cert.page_number, extraction):
            cert.evidence_status = "requires_review"
            review_items += 1
            warnings.append(
                f"Certification or achievement '{cert.title}' lacks verified resume evidence."
            )

    for item in data.evidence:
        total_items += 1
        if not _is_snippet_grounded(item.snippet, item.page_number, extraction):
            item.status = "requires_review"
            item.confidence = None
            review_items += 1
            warnings.append(f"Evidence claim '{item.claim}' could not be verified in resume text.")

    if total_items > 0 and review_items == total_items:
        extraction_status: ProfileExtractionStatus = "requires_manual_review"
    elif warnings:
        extraction_status = "extracted_with_warnings"
    else:
        extraction_status = "extracted"

    return ProfileValidationOutcome(
        profile=data,
        extraction_status=extraction_status,
        warnings=warnings,
    )
