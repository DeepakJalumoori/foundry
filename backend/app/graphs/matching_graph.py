from datetime import UTC, datetime
import logging
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.candidate import Candidate
from app.models.m4 import (
    Company,
    CompanyResearch,
    DiscoveryRun,
    Founder,
    FundingEvent,
    HiringSignal,
    JobOpportunity,
)
from app.models.m5 import CompanyAssessment, MatchingRun, MatchResult, RetrievalRecord
from app.providers.llm import LLMProvider, LLMProviderError
from app.repositories.profile_repository import ProfileRepository
from app.schemas.m5 import (
    EvidenceQualityReport,
    FitScoreResult,
    OpportunityAssessment,
    RetrievedEvidenceItem,
    StructuredCompanyAssessment,
)
from app.services.company_assessment_service import validate_company_assessment
from app.services.evidence_documents import EvidenceDocumentNormalizer
from app.services.fit_scoring import FIT_SCORING_VERSION, calculate_fit_score
from app.services.fts_retriever import EvidenceRetriever
from app.services.opportunity_classifier import classify_opportunity_evidence
from app.services.ranking import RANKING_POLICY_VERSION, compute_ranking_priority, rank_companies

logger = logging.getLogger(__name__)


class MatchingState(TypedDict):
    """Serializable typed state for the M5 LangGraph matching workflow."""

    matching_run_id: str
    candidate_id: str
    discovery_run_id: str | None
    company_ids: list[str]
    retrieval_config: dict[str, Any]
    scoring_version: str
    ranking_version: str

    candidate_profile_snapshot: dict[str, Any]
    company_context: dict[str, dict[str, Any]]

    retrieval_queries: dict[str, str]
    retrieved_evidence: dict[str, list[dict[str, Any]]]

    evidence_quality: dict[str, dict[str, Any]]
    company_assessments: dict[str, dict[str, Any]]
    assessment_metadata: dict[str, dict[str, Any]]

    match_scores: dict[str, dict[str, Any]]
    opportunity_assessments: dict[str, dict[str, Any]]
    explanations: dict[str, str]
    ranked_results: list[dict[str, Any]]

    warnings: list[str]
    errors: list[str]
    fatal_error_code: str | None
    fatal_error_message: str | None
    requires_review: bool
    persisted: bool
    final_status: str


def _sanitize_profile_snapshot(profile_data: dict[str, Any]) -> dict[str, Any]:
    """Build a sanitized candidate profile snapshot without raw resume text."""
    return {
        "basic_info": dict(profile_data.get("basic_info") or {}),
        "skills": list(profile_data.get("skills") or []),
        "work_experience": list(profile_data.get("work_experience") or []),
        "education": list(profile_data.get("education") or []),
        "projects": list(profile_data.get("projects") or []),
        "certifications_and_achievements": list(profile_data.get("certifications_and_achievements") or []),
        "additional_info": dict(profile_data.get("additional_info") or {}),
    }


def build_matching_graph(
    *,
    db: Session,
    llm_provider: LLMProvider,
    retriever: EvidenceRetriever,
    normalizer: EvidenceDocumentNormalizer | None = None,
):
    """Construct and compile the single M5 LangGraph StateGraph."""
    doc_normalizer = normalizer or EvidenceDocumentNormalizer()

    def load_candidate_context(state: MatchingState) -> dict[str, Any]:
        candidate = db.get(Candidate, state["candidate_id"])
        if candidate is None:
            return {
                "fatal_error_code": "CANDIDATE_NOT_FOUND",
                "fatal_error_message": f"Candidate '{state['candidate_id']}' not found.",
                "errors": [*state["errors"], "Candidate not found."],
            }

        profile = ProfileRepository.get_by_candidate_id(db, candidate.id)
        if profile is None or not profile.profile_data:
            return {
                "fatal_error_code": "PROFILE_NOT_FOUND",
                "fatal_error_message": f"Candidate '{candidate.id}' does not have an extracted profile.",
                "errors": [*state["errors"], "Candidate profile not found."],
            }

        snapshot = _sanitize_profile_snapshot(profile.profile_data)
        return {"candidate_profile_snapshot": snapshot}

    def load_selected_companies(state: MatchingState) -> dict[str, Any]:
        target_ids = list(state.get("company_ids") or [])
        discovery_run_id = state.get("discovery_run_id")

        if discovery_run_id:
            d_run = db.get(DiscoveryRun, discovery_run_id)
            if d_run is None:
                return {
                    "fatal_error_code": "DISCOVERY_RUN_NOT_FOUND",
                    "fatal_error_message": f"Discovery run '{discovery_run_id}' not found.",
                    "errors": [*state["errors"], "Discovery run not found."],
                }
            if not target_ids:
                target_ids = list(d_run.company_ids or [])

        target_ids = list(dict.fromkeys(cid for cid in target_ids if cid))
        if not target_ids:
            return {
                "fatal_error_code": "NO_COMPANIES_SELECTED",
                "fatal_error_message": "No companies available for matching.",
                "errors": [*state["errors"], "No companies selected."],
            }

        companies = list(db.scalars(select(Company).where(Company.id.in_(target_ids))).all())
        found_map = {c.id: c for c in companies}
        missing = [cid for cid in target_ids if cid not in found_map]
        if missing:
            return {
                "fatal_error_code": "COMPANY_NOT_FOUND",
                "fatal_error_message": f"Company not found: {missing[0]}.",
                "errors": [*state["errors"], f"Missing company IDs: {', '.join(missing)}"],
            }

        context_map: dict[str, dict[str, Any]] = {}
        for cid in target_ids:
            comp = found_map[cid]
            # Ensure M4 records are normalized & indexed into EvidenceDocument + FTS5
            doc_normalizer.index_company(db, comp)

            research = list(
                db.scalars(select(CompanyResearch).where(CompanyResearch.company_id == comp.id)).all()
            )
            funding = list(
                db.scalars(select(FundingEvent).where(FundingEvent.company_id == comp.id)).all()
            )
            signals = list(
                db.scalars(select(HiringSignal).where(HiringSignal.company_id == comp.id)).all()
            )
            jobs = list(
                db.scalars(select(JobOpportunity).where(JobOpportunity.company_id == comp.id)).all()
            )
            founders = list(
                db.scalars(select(Founder).where(Founder.company_id == comp.id)).all()
            )

            context_map[cid] = {
                "id": comp.id,
                "name": comp.name,
                "normalized_domain": comp.normalized_domain,
                "official_website": comp.official_website,
                "description": comp.description,
                "industry": comp.industry,
                "product_or_service": comp.product_or_service,
                "headquarters": comp.headquarters,
                "stage": comp.stage,
                "tech_stack": list(comp.tech_stack or []),
                "data_origin": comp.data_origin,
                "research_summaries": [r.summary for r in research if r.summary],
                "funding_events": [
                    {
                        "id": f.id,
                        "round_type": f.round_type,
                        "amount": f.amount,
                        "currency": f.currency,
                        "announced_date": f.announced_date.isoformat() if f.announced_date else None,
                        "verification_status": f.verification_status,
                        "is_recent": f.is_recent,
                    }
                    for f in funding
                ],
                "hiring_signals": [
                    {
                        "id": s.id,
                        "signal_type": s.signal_type,
                        "opportunity_category": s.opportunity_category,
                        "title": s.title,
                        "observed_fact": s.observed_fact,
                        "publication_date": s.publication_date.isoformat() if s.publication_date else None,
                        "verification_status": s.verification_status,
                    }
                    for s in signals
                ],
                "job_opportunities": [
                    {
                        "id": j.id,
                        "title": j.title,
                        "job_url": j.job_url,
                        "posting_date": j.posting_date.isoformat() if j.posting_date else None,
                        "verification_status": j.verification_status,
                        "is_active": j.is_active,
                    }
                    for j in jobs
                ],
                "job_titles": [j.title for j in jobs],
                "founders": [
                    {"id": fnd.id, "full_name": fnd.full_name, "role_title": fnd.role_title}
                    for fnd in founders
                ],
            }

        return {
            "company_ids": target_ids,
            "company_context": context_map,
        }

    def prepare_retrieval_queries(state: MatchingState) -> dict[str, Any]:
        profile = state["candidate_profile_snapshot"]
        skill_names = [
            str(s.get("name", "")).strip()
            for s in (profile.get("skills") or [])
            if isinstance(s, dict) and s.get("name")
        ]
        headline = str((profile.get("basic_info") or {}).get("headline") or "").strip()

        queries: dict[str, str] = {}
        for cid, ctx in state["company_context"].items():
            terms = list(skill_names[:10])
            if headline:
                terms.append(headline)
            for tech in (ctx.get("tech_stack") or [])[:6]:
                terms.append(str(tech))
            if ctx.get("industry"):
                terms.append(str(ctx["industry"]))
            # Add hiring/job keywords so opportunity evidence is also retrieved
            terms.extend(["hiring", "engineer", "job", "team", "funding"])
            queries[cid] = " ".join(dict.fromkeys(t for t in terms if t))

        return {"retrieval_queries": queries}

    def retrieve_company_evidence(state: MatchingState) -> dict[str, Any]:
        cfg = state.get("retrieval_config") or {}
        limit = int(cfg.get("limit_per_company", 12))
        include_unverified = bool(cfg.get("include_unverified", True))
        data_origin = cfg.get("data_origin")
        verification_filter = None if include_unverified else "verified"

        retrieved: dict[str, list[dict[str, Any]]] = {}
        warnings = list(state["warnings"])

        for cid in state["company_ids"]:
            query = state["retrieval_queries"].get(cid, "")
            items = retriever.retrieve(
                query=query,
                company_id=cid,
                verification_status=verification_filter,  # type: ignore[arg-type]
                data_origin=data_origin,
                limit=limit,
            )
            if not items:
                warnings.append(f"No FTS5 evidence retrieved for company '{cid}'.")
            retrieved[cid] = [item.model_dump(mode="json") for item in items]

        return {"retrieved_evidence": retrieved, "warnings": warnings}

    def evaluate_evidence_quality(state: MatchingState) -> dict[str, Any]:
        quality_map: dict[str, dict[str, Any]] = {}
        warnings = list(state["warnings"])
        requires_review = state["requires_review"]

        for cid in state["company_ids"]:
            raw_items = state["retrieved_evidence"].get(cid, [])
            items = [RetrievedEvidenceItem.model_validate(r) for r in raw_items]
            verified_count = sum(1 for i in items if i.verification_status == "verified")
            has_research = any(i.entity_type in {"company", "company_research"} for i in items)
            has_funding = any(i.entity_type == "funding_event" for i in items)
            has_hiring = any(i.entity_type == "hiring_signal" for i in items)
            has_job = any(i.entity_type == "job_opportunity" for i in items)

            item_warnings: list[str] = []
            if not items:
                item_warnings.append("No evidence documents retrieved.")
                requires_review = True
            elif verified_count == 0:
                item_warnings.append("Retrieved evidence has no verified documents.")
                requires_review = True

            report = EvidenceQualityReport(
                company_id=cid,
                total_documents=len(items),
                verified_documents=verified_count,
                has_research_evidence=has_research,
                has_funding_evidence=has_funding,
                has_hiring_evidence=has_hiring,
                has_job_evidence=has_job,
                sufficient_for_fit=len(items) > 0,
                warnings=item_warnings,
            )
            quality_map[cid] = report.model_dump(mode="json")
            warnings.extend(f"[{cid}] {w}" for w in item_warnings)

        return {
            "evidence_quality": quality_map,
            "warnings": warnings,
            "requires_review": requires_review,
        }

    def analyze_candidate_company_fit(state: MatchingState) -> dict[str, Any]:
        profile = state["candidate_profile_snapshot"]
        assessments: dict[str, dict[str, Any]] = {}
        metadata_map: dict[str, dict[str, Any]] = {}
        warnings = list(state["warnings"])
        requires_review = state["requires_review"]

        for cid in state["company_ids"]:
            ctx = state["company_context"][cid]
            items = [
                RetrievedEvidenceItem.model_validate(r)
                for r in state["retrieved_evidence"].get(cid, [])
            ]
            try:
                res = llm_provider.assess_candidate_company_fit(
                    candidate_profile=profile,
                    company_context=ctx,
                    retrieved_evidence=items,
                )
                cleaned, val_warnings = validate_company_assessment(
                    res.assessment,
                    company_id=cid,
                    candidate_profile=profile,
                    retrieved_evidence=items,
                    company_context=ctx,
                )
                warnings.extend(res.warnings)
                warnings.extend(val_warnings)
                if cleaned.requires_review:
                    requires_review = True
                assessments[cid] = cleaned.model_dump(mode="json")
                metadata_map[cid] = {
                    "provider_name": res.provider_name,
                    "model_name": res.model_name,
                    "data_origin": res.data_origin,
                }
            except LLMProviderError as exc:
                logger.warning("LLM assessment failed for company %s: %s", cid, exc.code)
                warnings.append(f"LLM assessment failed for company '{cid}' ({exc.code}); marked for review.")
                requires_review = True
                fallback = StructuredCompanyAssessment(
                    required_technical_skills=list(ctx.get("tech_stack") or []),
                    evidence_references=[i.source_evidence_id for i in items[:5]],
                    explanation=(
                        f"Automated qualitative LLM analysis unavailable ({exc.code}); "
                        "deterministic scoring applied and flagged for manual review."
                    ),
                    uncertainties=[f"LLM provider error: {exc.code}"],
                    requires_review=True,
                )
                assessments[cid] = fallback.model_dump(mode="json")
                provider_name = getattr(llm_provider, "provider_name", "unknown")
                data_origin = getattr(
                    llm_provider,
                    "data_origin",
                    "demo" if provider_name == "demo" else "real",
                )
                metadata_map[cid] = {
                    "provider_name": provider_name,
                    "model_name": getattr(llm_provider, "model_name", None),
                    "data_origin": data_origin,
                }

        return {
            "company_assessments": assessments,
            "assessment_metadata": metadata_map,
            "warnings": warnings,
            "requires_review": requires_review,
        }

    def calculate_fit_scores(state: MatchingState) -> dict[str, Any]:
        profile = state["candidate_profile_snapshot"]
        scoring_version = state.get("scoring_version") or FIT_SCORING_VERSION
        scores: dict[str, dict[str, Any]] = {}
        requires_review = state["requires_review"]

        for cid in state["company_ids"]:
            ctx = state["company_context"][cid]
            items = [
                RetrievedEvidenceItem.model_validate(r)
                for r in state["retrieved_evidence"].get(cid, [])
            ]
            assessment = StructuredCompanyAssessment.model_validate(
                state["company_assessments"][cid]
            )
            fit_result = calculate_fit_score(
                candidate_profile=profile,
                company_context=ctx,
                retrieved_evidence=items,
                assessment=assessment,
                scoring_version=scoring_version,
            )
            if fit_result.requires_review:
                requires_review = True
            scores[cid] = fit_result.model_dump(mode="json")

        return {"match_scores": scores, "requires_review": requires_review}

    def classify_opportunity_evidence_node(state: MatchingState) -> dict[str, Any]:
        opps: dict[str, dict[str, Any]] = {}
        requires_review = state["requires_review"]

        for cid in state["company_ids"]:
            ctx = state["company_context"][cid]
            items = [
                RetrievedEvidenceItem.model_validate(r)
                for r in state["retrieved_evidence"].get(cid, [])
            ]
            opp = classify_opportunity_evidence(
                company_context=ctx,
                retrieved_evidence=items,
            )
            if opp.requires_review:
                requires_review = True
            opps[cid] = opp.model_dump(mode="json")

        return {"opportunity_assessments": opps, "requires_review": requires_review}

    def generate_explanations(state: MatchingState) -> dict[str, Any]:
        ranking_version = state.get("ranking_version") or RANKING_POLICY_VERSION
        explanations: dict[str, str] = {}
        prioritized = []

        for cid in state["company_ids"]:
            ctx = state["company_context"][cid]
            fit_res = FitScoreResult.model_validate(state["match_scores"][cid])
            opp_res = OpportunityAssessment.model_validate(state["opportunity_assessments"][cid])
            qual_res = StructuredCompanyAssessment.model_validate(state["company_assessments"][cid])

            explanations[cid] = (
                f"{ctx['name']} — Fit: {fit_res.fit_score}/100 (coverage {fit_res.fit_coverage}%). "
                f"Opportunity: {opp_res.opportunity_type} ({opp_res.evidence_strength} evidence). "
                f"{qual_res.explanation} {opp_res.classification_reason}"
            ).strip()

            prioritized.append(
                compute_ranking_priority(
                    company_id=cid,
                    fit_result=fit_res,
                    opportunity=opp_res,
                    ranking_version=ranking_version,
                )
            )

        sorted_items = rank_companies(prioritized)
        ranked_payload = []
        for idx, item in enumerate(sorted_items, start=1):
            ranked_payload.append(
                {
                    "company_id": item.company_id,
                    "ranking_position": idx,
                    "ranking_score": item.ranking_score,
                    "ranking_explanation": item.ranking_explanation,
                    "ranking_factors": item.ranking_factors,
                }
            )

        return {"explanations": explanations, "ranked_results": ranked_payload}

    def persist_results(state: MatchingState) -> dict[str, Any]:
        run = db.get(MatchingRun, state["matching_run_id"])
        if run is None:
            return {
                "fatal_error_code": "MATCHING_RUN_NOT_FOUND",
                "fatal_error_message": f"Matching run '{state['matching_run_id']}' not found.",
                "errors": [*state["errors"], "MatchingRun record missing during persistence."],
            }

        try:
            run.company_ids = list(state["company_ids"])
            run.candidate_profile_snapshot = state["candidate_profile_snapshot"]
            run.warnings = list(dict.fromkeys(state["warnings"]))
            run.requires_review = bool(state["requires_review"])

            for ranked in state["ranked_results"]:
                cid = ranked["company_id"]
                ctx = state["company_context"][cid]
                qual_dict = state["company_assessments"][cid]
                qual = StructuredCompanyAssessment.model_validate(qual_dict)
                meta = state["assessment_metadata"][cid]
                fit_res = FitScoreResult.model_validate(state["match_scores"][cid])
                opp_res = OpportunityAssessment.model_validate(state["opportunity_assessments"][cid])

                ca = CompanyAssessment(
                    matching_run_id=run.id,
                    company_id=cid,
                    provider_name=meta["provider_name"],
                    model_name=meta.get("model_name"),
                    assessment_data=qual_dict,
                    evidence_ids=qual.evidence_references,
                    uncertainties=qual.uncertainties,
                    requires_review=qual.requires_review,
                )
                db.add(ca)
                db.flush()

                mr = MatchResult(
                    matching_run_id=run.id,
                    company_id=cid,
                    company_assessment_id=ca.id,
                    fit_score=fit_res.fit_score,
                    fit_coverage=fit_res.fit_coverage,
                    scoring_version=fit_res.scoring_version,
                    dimension_breakdown=[d.model_dump(mode="json") for d in fit_res.dimensions],
                    opportunity_type=opp_res.opportunity_type,
                    evidence_strength=opp_res.evidence_strength,
                    opportunity_assessment=opp_res.model_dump(mode="json"),
                    ranking_position=ranked["ranking_position"],
                    ranking_version=state["ranking_version"],
                    ranking_score=ranked["ranking_score"],
                    ranking_explanation=ranked["ranking_explanation"],
                    ranking_factors=ranked["ranking_factors"],
                    explanation=state["explanations"][cid],
                    company_snapshot={
                        "id": ctx["id"],
                        "name": ctx["name"],
                        "stage": ctx["stage"],
                        "industry": ctx.get("industry"),
                        "normalized_domain": ctx.get("normalized_domain"),
                        "data_origin": ctx.get("data_origin", "demo"),
                    },
                    requires_review=bool(fit_res.requires_review or opp_res.requires_review),
                    data_origin=ctx.get("data_origin", "demo"),
                )
                db.add(mr)

                query_text = state["retrieval_queries"].get(cid, "")
                for order_idx, raw_ev in enumerate(state["retrieved_evidence"].get(cid, []), start=1):
                    ev_item = RetrievedEvidenceItem.model_validate(raw_ev)
                    rec = RetrievalRecord(
                        matching_run_id=run.id,
                        company_id=cid,
                        query_text=query_text,
                        filters_json=state["retrieval_config"],
                        evidence_document_id=ev_item.evidence_document_id,
                        source_evidence_id=ev_item.source_evidence_id,
                        rank_order=order_idx,
                        bm25_score=ev_item.bm25_score,
                        retrieved_snapshot={
                            "entity_type": ev_item.entity_type,
                            "document_title": ev_item.document_title,
                            "content": ev_item.content,
                            "source_url": ev_item.source_url,
                            "source_title": ev_item.source_title,
                            "publication_date": ev_item.publication_date.isoformat() if ev_item.publication_date else None,
                            "retrieved_at": ev_item.retrieved_at.isoformat(),
                            "verification_status": ev_item.verification_status,
                            "data_origin": ev_item.data_origin,
                        },
                    )
                    db.add(rec)

            db.commit()
            return {"persisted": True}
        except Exception as exc:
            db.rollback()
            logger.exception("Failed persisting M5 matching results for run %s", run.id)
            return {
                "persisted": False,
                "fatal_error_code": "PERSISTENCE_ERROR",
                "fatal_error_message": f"Failed to persist matching results ({type(exc).__name__}).",
                "errors": [*state["errors"], f"Persistence failure: {type(exc).__name__}"],
            }

    def complete_matching_run(state: MatchingState) -> dict[str, Any]:
        run = db.get(MatchingRun, state["matching_run_id"])
        now = datetime.now(UTC)
        if state.get("fatal_error_code"):
            status = "failed"
        elif state.get("warnings"):
            status = "completed_with_warnings"
        else:
            status = "completed"

        if run is not None:
            run.status = status
            run.error_code = state.get("fatal_error_code")
            run.error_message = state.get("fatal_error_message")
            run.warnings = list(dict.fromkeys(state["warnings"]))
            run.requires_review = bool(state.get("requires_review", False))
            run.completed_at = now
            db.commit()

        return {"final_status": status}

    def _route_after_candidate(state: MatchingState) -> str:
        return "complete_matching_run" if state.get("fatal_error_code") else "load_selected_companies"

    def _route_after_companies(state: MatchingState) -> str:
        return "complete_matching_run" if state.get("fatal_error_code") else "prepare_retrieval_queries"

    graph = StateGraph(MatchingState)
    graph.add_node("load_candidate_context", load_candidate_context)
    graph.add_node("load_selected_companies", load_selected_companies)
    graph.add_node("prepare_retrieval_queries", prepare_retrieval_queries)
    graph.add_node("retrieve_company_evidence", retrieve_company_evidence)
    graph.add_node("evaluate_evidence_quality", evaluate_evidence_quality)
    graph.add_node("analyze_candidate_company_fit", analyze_candidate_company_fit)
    graph.add_node("calculate_fit_scores", calculate_fit_scores)
    graph.add_node("classify_opportunity_evidence", classify_opportunity_evidence_node)
    graph.add_node("generate_explanations", generate_explanations)
    graph.add_node("persist_results", persist_results)
    graph.add_node("complete_matching_run", complete_matching_run)

    graph.add_edge(START, "load_candidate_context")
    graph.add_conditional_edges(
        "load_candidate_context",
        _route_after_candidate,
        {
            "complete_matching_run": "complete_matching_run",
            "load_selected_companies": "load_selected_companies",
        },
    )
    graph.add_conditional_edges(
        "load_selected_companies",
        _route_after_companies,
        {
            "complete_matching_run": "complete_matching_run",
            "prepare_retrieval_queries": "prepare_retrieval_queries",
        },
    )
    graph.add_edge("prepare_retrieval_queries", "retrieve_company_evidence")
    graph.add_edge("retrieve_company_evidence", "evaluate_evidence_quality")
    graph.add_edge("evaluate_evidence_quality", "analyze_candidate_company_fit")
    graph.add_edge("analyze_candidate_company_fit", "calculate_fit_scores")
    graph.add_edge("calculate_fit_scores", "classify_opportunity_evidence")
    graph.add_edge("classify_opportunity_evidence", "generate_explanations")
    graph.add_edge("generate_explanations", "persist_results")
    graph.add_edge("persist_results", "complete_matching_run")
    graph.add_edge("complete_matching_run", END)

    return graph.compile()
