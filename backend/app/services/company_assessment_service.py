import re
from typing import Any

from app.schemas.m5 import RetrievedEvidenceItem, StructuredCompanyAssessment

_INJECTION_PATTERNS = (
    re.compile(r"</?\s*untrusted_evidence\s*>", re.IGNORECASE),
    re.compile(r"ignore\s+(all\s+)?previous\s+instructions", re.IGNORECASE),
    re.compile(r"system\s+prompt", re.IGNORECASE),
    re.compile(r"override\s+scoring", re.IGNORECASE),
)


def _contains_injection_marker(text: str) -> bool:
    return any(p.search(text) for p in _INJECTION_PATTERNS)


def validate_company_assessment(
    assessment: StructuredCompanyAssessment,
    *,
    company_id: str,
    candidate_profile: dict[str, Any],
    retrieved_evidence: list[RetrievedEvidenceItem],
    company_context: dict[str, Any] | None = None,
) -> tuple[StructuredCompanyAssessment, list[str]]:
    """Validate LLM assessment against retrieved company evidence, company context, and candidate profile.

    - Strips cross-company or non-existent evidence references.
    - Strips unsupported candidate_matching_skills not in CandidateProfile.
    - Strips unsupported required_technical_skills not in company_context['tech_stack']
      or retrieved_evidence text.
    - Validates experience, project, domain, role notes and explanation against
      stored profile/evidence and strips prompt-injection artifacts.
    """
    warnings: list[str] = []
    valid_evidence_ids = {
        ev.source_evidence_id
        for ev in retrieved_evidence
        if ev.company_id == company_id
    }

    validated_refs: list[str] = []
    invalid_refs: list[str] = []
    for ref in assessment.evidence_references:
        if ref in valid_evidence_ids:
            if ref not in validated_refs:
                validated_refs.append(ref)
        else:
            invalid_refs.append(ref)

    uncertainties = list(assessment.uncertainties)
    requires_review = assessment.requires_review

    if invalid_refs:
        warnings.append(
            f"Stripped {len(invalid_refs)} invalid or cross-company evidence reference(s)."
        )
        uncertainties.append("Some cited evidence references were not present in this company's retrieved evidence.")
        requires_review = True

    # 1. Verify candidate_matching_skills against CandidateProfile
    profile_skill_tokens: set[str] = set()
    for s in candidate_profile.get("skills") or []:
        if isinstance(s, dict) and s.get("name"):
            profile_skill_tokens.add(str(s["name"]).strip().lower())
    for exp in candidate_profile.get("work_experience") or []:
        if isinstance(exp, dict):
            for tech in exp.get("technologies") or []:
                profile_skill_tokens.add(str(tech).strip().lower())
    for proj in candidate_profile.get("projects") or []:
        if isinstance(proj, dict):
            for tech in proj.get("technologies") or []:
                profile_skill_tokens.add(str(tech).strip().lower())

    verified_matching: list[str] = []
    unsupported_matching: list[str] = []
    for skill in assessment.candidate_matching_skills:
        if skill.strip().lower() in profile_skill_tokens:
            verified_matching.append(skill)
        else:
            unsupported_matching.append(skill)

    if unsupported_matching:
        warnings.append(
            f"Removed {len(unsupported_matching)} unsupported candidate skill claim(s): "
            + ", ".join(unsupported_matching[:5])
        )
        uncertainties.append("LLM listed candidate skills not found in stored CandidateProfile.")
        requires_review = True

    # 2. Verify required_technical_skills against authoritative company tech_stack & retrieved evidence
    authoritative_tech = {
        str(t).strip().lower()
        for t in ((company_context or {}).get("tech_stack") or [])
        if str(t).strip()
    }
    evidence_blob = " ".join(
        f"{ev.document_title} {ev.content}" for ev in retrieved_evidence if ev.company_id == company_id
    ).lower()

    verified_required: list[str] = []
    unsupported_required: list[str] = []
    for req_skill in assessment.required_technical_skills:
        norm = req_skill.strip().lower()
        if not norm:
            continue
        if norm in authoritative_tech or re.search(rf"\b{re.escape(norm)}\b", evidence_blob):
            verified_required.append(req_skill)
        else:
            unsupported_required.append(req_skill)

    if unsupported_required:
        warnings.append(
            f"Removed {len(unsupported_required)} unsupported company required skill claim(s): "
            + ", ".join(unsupported_required[:5])
        )
        uncertainties.append("LLM listed required company skills not grounded in company context or retrieved evidence.")
        requires_review = True

    # 3. Validate relevant_experience_notes against CandidateProfile.work_experience
    work_exp = candidate_profile.get("work_experience") or []
    exp_tokens = {
        str(val).strip().lower()
        for e in work_exp
        if isinstance(e, dict)
        for val in (e.get("organization"), e.get("job_title"))
        if val and str(val).strip()
    }
    verified_exp_notes: list[str] = []
    for note in assessment.relevant_experience_notes:
        if _contains_injection_marker(note):
            warnings.append("Removed prompt-injection artifact from relevant_experience_notes.")
            requires_review = True
            continue
        if not work_exp:
            warnings.append("Removed unsupported experience note when candidate work_experience is empty.")
            requires_review = True
            continue
        if any(tok in note.lower() for tok in exp_tokens):
            verified_exp_notes.append(note)
        else:
            warnings.append("Removed ungrounded experience note not matching stored work_experience.")
            requires_review = True

    # 4. Validate project_relevance_notes against CandidateProfile.projects
    projects = candidate_profile.get("projects") or []
    proj_tokens = {
        str(p.get("name")).strip().lower()
        for p in projects
        if isinstance(p, dict) and p.get("name")
    }
    verified_proj_notes: list[str] = []
    for note in assessment.project_relevance_notes:
        if _contains_injection_marker(note):
            warnings.append("Removed prompt-injection artifact from project_relevance_notes.")
            requires_review = True
            continue
        if not projects:
            warnings.append("Removed unsupported project note when candidate projects list is empty.")
            requires_review = True
            continue
        if any(tok in note.lower() for tok in proj_tokens):
            verified_proj_notes.append(note)
        else:
            warnings.append("Removed ungrounded project note not matching stored projects.")
            requires_review = True

    # 5. Sanitize domain & role notes
    verified_domain_notes: list[str] = []
    for note in assessment.domain_relevance_notes:
        if _contains_injection_marker(note):
            warnings.append("Removed prompt-injection artifact from domain_relevance_notes.")
            requires_review = True
            continue
        if not retrieved_evidence and not (company_context or {}).get("industry"):
            requires_review = True
            continue
        verified_domain_notes.append(note[:300])

    verified_role_notes: list[str] = []
    for note in assessment.role_compatibility_notes:
        if _contains_injection_marker(note):
            warnings.append("Removed prompt-injection artifact from role_compatibility_notes.")
            requires_review = True
            continue
        verified_role_notes.append(note[:300])

    # 6. Validate & sanitize explanation
    explanation = assessment.explanation.strip()
    if _contains_injection_marker(explanation):
        warnings.append("Sanitized prompt-injection pattern in LLM explanation.")
        uncertainties.append("LLM explanation contained untrusted instruction-like text and was replaced.")
        requires_review = True
        explanation = (
            f"Automated assessment for {(company_context or {}).get('name', 'company')} "
            f"flagged for manual review due to untrusted evidence text."
        )
    elif not validated_refs and retrieved_evidence:
        requires_review = True
        uncertainties.append("Assessment explanation has no validated evidence references.")

    cleaned = assessment.model_copy(
        update={
            "required_technical_skills": verified_required,
            "candidate_matching_skills": verified_matching,
            "relevant_experience_notes": verified_exp_notes,
            "project_relevance_notes": verified_proj_notes,
            "domain_relevance_notes": verified_domain_notes,
            "role_compatibility_notes": verified_role_notes,
            "evidence_references": validated_refs,
            "explanation": explanation[:1000],
            "uncertainties": list(dict.fromkeys(uncertainties)),
            "requires_review": requires_review,
        }
    )
    return cleaned, list(dict.fromkeys(warnings))
