from dataclasses import dataclass
from typing import Any

from app.schemas.m5 import EvidenceStrength, FitScoreResult, M5OpportunityType, OpportunityAssessment

RANKING_POLICY_VERSION = "rank_v2"

# Fit-dominant prioritization policy (rank_v2):
# - Candidate suitability (fit_score * coverage + coverage) accounts for up to 80 points.
# - Opportunity type + evidence strength act as secondary prioritization signals (up to 20 points).
# - Thus, a near-zero fit company with an active opening (max 30 pts) cannot outrank a
#   high-fit company even with insufficient hiring evidence (e.g., 100% fit = 80 pts).
_OPPORTUNITY_TIER_BONUS: dict[M5OpportunityType, float] = {
    "active": 12.0,
    "hidden": 7.0,
    "insufficient_evidence": 0.0,
}

_EVIDENCE_STRENGTH_BONUS: dict[EvidenceStrength, float] = {
    "strong": 8.0,
    "moderate": 5.0,
    "weak": 2.0,
    "insufficient": 0.0,
}


@dataclass(frozen=True, slots=True)
class RankedCandidateCompany:
    """Intermediate ranking record before assigning 1-based positions."""

    company_id: str
    fit_result: FitScoreResult
    opportunity: OpportunityAssessment
    ranking_score: float
    ranking_explanation: str
    ranking_factors: dict[str, Any]


def compute_ranking_priority(
    *,
    company_id: str,
    fit_result: FitScoreResult,
    opportunity: OpportunityAssessment,
    ranking_version: str = RANKING_POLICY_VERSION,
) -> RankedCandidateCompany:
    """Compute fit-dominant deterministic ranking priority while keeping fit & opportunity separate."""
    if ranking_version != RANKING_POLICY_VERSION:
        raise ValueError(f"Unsupported ranking_version: {ranking_version}")

    opp_bonus = _OPPORTUNITY_TIER_BONUS[opportunity.opportunity_type]
    strength_bonus = _EVIDENCE_STRENGTH_BONUS[opportunity.evidence_strength]
    coverage_ratio = fit_result.fit_coverage / 100.0
    fit_component = round(fit_result.fit_score * 0.70 * coverage_ratio, 2)
    coverage_component = round(coverage_ratio * 10.0, 2)
    needs_review = fit_result.requires_review or opportunity.requires_review
    review_penalty = -4.0 if needs_review else 0.0

    ranking_score = round(
        fit_component + coverage_component + opp_bonus + strength_bonus + review_penalty,
        2,
    )

    factors = {
        "ranking_version": ranking_version,
        "fit_score": fit_result.fit_score,
        "fit_coverage": fit_result.fit_coverage,
        "fit_component": fit_component,
        "coverage_component": coverage_component,
        "opportunity_type": opportunity.opportunity_type,
        "opportunity_tier_bonus": opp_bonus,
        "evidence_strength": opportunity.evidence_strength,
        "evidence_strength_bonus": strength_bonus,
        "requires_review": needs_review,
        "review_penalty": review_penalty,
        "ranking_score": ranking_score,
    }

    explanation = (
        f"Policy {ranking_version} (fit-dominant): fit={fit_result.fit_score} at {fit_result.fit_coverage}% "
        f"coverage (+{fit_component + coverage_component:.2f}), "
        f"opportunity={opportunity.opportunity_type} (+{opp_bonus}), "
        f"evidence_strength={opportunity.evidence_strength} (+{strength_bonus})"
        + (f", manual_review_penalty ({review_penalty})" if review_penalty else "")
        + f" => priority={ranking_score}."
    )

    return RankedCandidateCompany(
        company_id=company_id,
        fit_result=fit_result,
        opportunity=opportunity,
        ranking_score=ranking_score,
        ranking_explanation=explanation,
        ranking_factors=factors,
    )


def rank_companies(items: list[RankedCandidateCompany]) -> list[RankedCandidateCompany]:
    """Deterministically sort ranked companies with explicit tie-breakers."""
    return sorted(
        items,
        key=lambda item: (
            -item.ranking_score,
            -item.fit_result.fit_score,
            -item.fit_result.fit_coverage,
            item.company_id,
        ),
    )
