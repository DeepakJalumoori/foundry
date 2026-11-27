from typing import Any

from app.schemas.m5 import (
    DimensionScore,
    FitScoreResult,
    RetrievedEvidenceItem,
    StructuredCompanyAssessment,
)

FIT_SCORING_VERSION = "fit_v1"

FIT_V1_WEIGHTS: dict[str, float] = {
    "technical_skill_overlap": 40.0,
    "relevant_experience": 25.0,
    "project_domain_relevance": 15.0,
    "industry_product_relevance": 10.0,
    "role_seniority_compatibility": 10.0,
}


def _collect_candidate_skills(profile: dict[str, Any]) -> set[str]:
    skills: set[str] = set()
    for item in profile.get("skills") or []:
        if isinstance(item, dict) and item.get("name"):
            skills.add(str(item["name"]).strip().lower())
    for exp in profile.get("work_experience") or []:
        if isinstance(exp, dict):
            for t in exp.get("technologies") or []:
                if str(t).strip():
                    skills.add(str(t).strip().lower())
    for proj in profile.get("projects") or []:
        if isinstance(proj, dict):
            for t in proj.get("technologies") or []:
                if str(t).strip():
                    skills.add(str(t).strip().lower())
    return skills


def _collect_company_skills(
    company_context: dict[str, Any],
) -> set[str]:
    """Collect authoritative company technical skills strictly from validated company context."""
    skills: set[str] = set()
    for t in company_context.get("tech_stack") or []:
        if str(t).strip():
            skills.add(str(t).strip().lower())
    return skills


def _validate_raw_score(raw: float | None) -> float | None:
    if raw is None:
        return None
    if raw < 0.0 or raw > 100.0:
        raise ValueError(f"Dimension raw_score {raw} is outside allowed [0, 100] bounds.")
    return round(raw, 2)


def calculate_fit_score(
    *,
    candidate_profile: dict[str, Any],
    company_context: dict[str, Any],
    retrieved_evidence: list[RetrievedEvidenceItem],
    assessment: StructuredCompanyAssessment | None,
    scoring_version: str = FIT_SCORING_VERSION,
) -> FitScoreResult:
    """Deterministically calculate candidate-company fit score and assessment coverage.

    Never delegates arithmetic to an LLM. Distinguishes missing information
    (assessable=False) from genuine mismatch (assessable=True, low raw_score)
    and normalizes the final score across assessable dimensions only.
    """
    if scoring_version != FIT_SCORING_VERSION:
        raise ValueError(f"Unsupported scoring_version: {scoring_version}")

    ev_ids = list(dict.fromkeys(ev.source_evidence_id for ev in retrieved_evidence))
    candidate_skills = _collect_candidate_skills(candidate_profile)
    company_skills = _collect_company_skills(company_context)
    work_exp = candidate_profile.get("work_experience") or []
    projects = candidate_profile.get("projects") or []
    basic_info = candidate_profile.get("basic_info") or {}

    dimensions: list[DimensionScore] = []

    # 1. Technical skill overlap (weight 40)
    w_skills = FIT_V1_WEIGHTS["technical_skill_overlap"]
    if not candidate_skills or not company_skills:
        missing_side = "candidate skills" if not candidate_skills else "company tech stack"
        dimensions.append(
            DimensionScore(
                dimension="technical_skill_overlap",
                raw_score=None,
                weight=w_skills,
                weighted_contribution=0.0,
                assessable=False,
                supporting_evidence_ids=[],
                explanation=f"Not assessable: missing {missing_side}.",
            )
        )
    else:
        matched = sorted(candidate_skills & company_skills)
        raw = _validate_raw_score((len(matched) / len(company_skills)) * 100.0)
        assert raw is not None
        dimensions.append(
            DimensionScore(
                dimension="technical_skill_overlap",
                raw_score=raw,
                weight=w_skills,
                weighted_contribution=round(raw * w_skills / 100.0, 2),
                assessable=True,
                supporting_evidence_ids=ev_ids[:5],
                explanation=f"Matched {len(matched)}/{len(company_skills)} company technical skills ({', '.join(matched) or 'none'}).",
            )
        )

    # 2. Relevant experience (weight 25)
    w_exp = FIT_V1_WEIGHTS["relevant_experience"]
    years = basic_info.get("years_of_experience")
    if not work_exp and years is None:
        dimensions.append(
            DimensionScore(
                dimension="relevant_experience",
                raw_score=None,
                weight=w_exp,
                weighted_contribution=0.0,
                assessable=False,
                supporting_evidence_ids=[],
                explanation="Not assessable: candidate work experience and years of experience are missing.",
            )
        )
    else:
        exp_text = " ".join(
            f"{e.get('job_title', '')} {e.get('description', '')} {' '.join(e.get('technologies') or [])}"
            for e in work_exp
            if isinstance(e, dict)
        ).lower()
        tech_hits = sum(1 for skill in company_skills if skill in exp_text)
        base_exp = 40.0 if work_exp else 25.0
        if years is not None:
            base_exp = max(base_exp, min(70.0, float(years) * 15.0))
        tech_bonus = min(30.0, tech_hits * 15.0)
        raw = _validate_raw_score(min(100.0, base_exp + tech_bonus))
        assert raw is not None
        dimensions.append(
            DimensionScore(
                dimension="relevant_experience",
                raw_score=raw,
                weight=w_exp,
                weighted_contribution=round(raw * w_exp / 100.0, 2),
                assessable=True,
                supporting_evidence_ids=ev_ids[:3],
                explanation=f"Evaluated {len(work_exp)} work experience entries with {tech_hits} company stack overlap(s).",
            )
        )

    # 3. Project and domain relevance (weight 15)
    w_proj = FIT_V1_WEIGHTS["project_domain_relevance"]
    if not projects:
        dimensions.append(
            DimensionScore(
                dimension="project_domain_relevance",
                raw_score=None,
                weight=w_proj,
                weighted_contribution=0.0,
                assessable=False,
                supporting_evidence_ids=[],
                explanation="Not assessable: candidate projects are not present in profile.",
            )
        )
    else:
        proj_text = " ".join(
            f"{p.get('name', '')} {p.get('description', '')} {' '.join(p.get('technologies') or [])}"
            for p in projects
            if isinstance(p, dict)
        ).lower()
        proj_hits = sum(1 for skill in company_skills if skill in proj_text)
        raw = _validate_raw_score(min(100.0, 35.0 + proj_hits * 25.0))
        assert raw is not None
        dimensions.append(
            DimensionScore(
                dimension="project_domain_relevance",
                raw_score=raw,
                weight=w_proj,
                weighted_contribution=round(raw * w_proj / 100.0, 2),
                assessable=True,
                supporting_evidence_ids=ev_ids[:3],
                explanation=f"Evaluated {len(projects)} project(s) with {proj_hits} relevant technology match(es).",
            )
        )

    # 4. Industry / product relevance (weight 10)
    w_ind = FIT_V1_WEIGHTS["industry_product_relevance"]
    industry = (company_context.get("industry") or "").strip().lower()
    product = (company_context.get("product_or_service") or company_context.get("description") or "").strip().lower()
    if not industry and not product:
        dimensions.append(
            DimensionScore(
                dimension="industry_product_relevance",
                raw_score=None,
                weight=w_ind,
                weighted_contribution=0.0,
                assessable=False,
                supporting_evidence_ids=[],
                explanation="Not assessable: company industry and product description are missing.",
            )
        )
    else:
        cand_blob = " ".join(
            [
                str(basic_info.get("headline") or ""),
                str((candidate_profile.get("additional_info") or {}).get("summary") or ""),
                " ".join(
                    f"{e.get('job_title', '')} {e.get('description', '')}"
                    for e in work_exp
                    if isinstance(e, dict)
                ),
                " ".join(
                    f"{p.get('name', '')} {p.get('description', '')}"
                    for p in projects
                    if isinstance(p, dict)
                ),
            ]
        ).lower()
        keywords = [w for w in (industry + " " + product).replace(",", " ").split() if len(w) >= 4]
        unique_kw = list(dict.fromkeys(keywords))
        hits = sum(1 for kw in unique_kw if kw in cand_blob)
        raw = _validate_raw_score(min(100.0, 25.0 + hits * 20.0)) if unique_kw else 25.0
        assert raw is not None
        dimensions.append(
            DimensionScore(
                dimension="industry_product_relevance",
                raw_score=raw,
                weight=w_ind,
                weighted_contribution=round(raw * w_ind / 100.0, 2),
                assessable=True,
                supporting_evidence_ids=ev_ids[:2],
                explanation=f"Matched {hits} industry/product keyword(s) against candidate background.",
            )
        )

    # 5. Role and seniority compatibility (weight 10)
    w_role = FIT_V1_WEIGHTS["role_seniority_compatibility"]
    headline = str(basic_info.get("headline") or basic_info.get("current_role") or "").strip().lower()
    stage = str(company_context.get("stage") or "").strip().lower()
    job_titles = [str(t).lower() for t in (company_context.get("job_titles") or [])]
    if not headline and not work_exp:
        dimensions.append(
            DimensionScore(
                dimension="role_seniority_compatibility",
                raw_score=None,
                weight=w_role,
                weighted_contribution=0.0,
                assessable=False,
                supporting_evidence_ids=[],
                explanation="Not assessable: candidate headline and role history are missing.",
            )
        )
    else:
        role_score = 50.0
        if job_titles:
            headline_words = {w for w in headline.split() if len(w) >= 4}
            if any(any(w in jt for w in headline_words) for jt in job_titles):
                role_score = 90.0
        elif stage in {"pre_seed", "seed", "series_a", "series_b", "series_c"}:
            role_score = 65.0
        raw = _validate_raw_score(role_score)
        assert raw is not None
        dimensions.append(
            DimensionScore(
                dimension="role_seniority_compatibility",
                raw_score=raw,
                weight=w_role,
                weighted_contribution=round(raw * w_role / 100.0, 2),
                assessable=True,
                supporting_evidence_ids=ev_ids[:2],
                explanation=f"Evaluated role compatibility for stage '{stage or 'unknown'}'.",
            )
        )

    total_weight = sum(FIT_V1_WEIGHTS.values())
    assessable_weight = sum(d.weight for d in dimensions if d.assessable)
    weighted_sum = sum(d.weighted_contribution for d in dimensions if d.assessable)

    fit_coverage = round((assessable_weight / total_weight) * 100.0, 2) if total_weight > 0 else 0.0
    fit_score = round((weighted_sum / assessable_weight) * 100.0, 2) if assessable_weight > 0 else 0.0
    fit_score = max(0.0, min(100.0, fit_score))

    requires_review = bool(
        fit_coverage < 60.0
        or (assessment is not None and assessment.requires_review)
        or not retrieved_evidence
    )

    return FitScoreResult(
        scoring_version=scoring_version,
        fit_score=fit_score,
        fit_coverage=fit_coverage,
        assessable_weight=assessable_weight,
        total_weight=total_weight,
        dimensions=dimensions,
        requires_review=requires_review,
    )
