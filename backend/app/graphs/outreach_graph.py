from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.candidate import Candidate
from app.models.m4 import Company, Founder, SourceEvidence
from app.models.m5 import MatchingRun, MatchResult
from app.models.m6 import OutreachDraft, OutreachDraftEvidence, OutreachDraftVersion
from app.providers.llm import LLMProvider, LLMProviderError
from app.repositories.profile_repository import ProfileRepository
from app.schemas.m5 import RetrievedEvidenceItem
from app.schemas.m6 import (
    OutreachIntent,
    OutreachStrategy,
    StructuredOutreachClaim,
    StructuredOutreachEmail,
)
from app.services.evidence_documents import EvidenceDocumentNormalizer
from app.services.fts_retriever import EvidenceRetriever
from app.services.outreach_grounding import (
    assemble_candidate_context,
    assemble_company_context,
    assemble_founder_context,
    collect_company_evidence_for_outreach,
    validate_outreach_generation,
)


class OutreachState(TypedDict):
    """Serializable typed state for the M6 LangGraph outreach generation workflow."""

    candidate_id: str
    matching_run_id: str
    match_result_id: str
    company_id: str
    founder_id: str
    outreach_intent: OutreachIntent

    candidate_context: dict[str, Any]
    company_context: dict[str, Any]
    founder_context: dict[str, Any]
    founder_evidence_ids: list[str]

    retrieved_evidence: list[dict[str, Any]]
    strategy: dict[str, Any]
    generated_draft: dict[str, Any]
    validated_claims: list[dict[str, Any]]

    generation_provider: str
    generation_model: str | None
    data_origin: str
    warnings: list[str]
    requires_review: bool

    draft_id: str | None
    fatal_error_code: str | None
    fatal_error_message: str | None
    fatal_status_code: int
    persisted: bool
    final_status: str


def build_outreach_graph(
    *,
    db: Session,
    llm_provider: LLMProvider,
    retriever: EvidenceRetriever,
    normalizer: EvidenceDocumentNormalizer | None = None,
):
    """Construct and compile the M6 LangGraph StateGraph for outreach draft generation."""
    doc_normalizer = normalizer or EvidenceDocumentNormalizer()

    def load_outreach_context(state: OutreachState) -> dict[str, Any]:
        candidate = db.get(Candidate, state["candidate_id"])
        if candidate is None:
            return {
                "fatal_error_code": "CANDIDATE_NOT_FOUND",
                "fatal_error_message": f"Candidate '{state['candidate_id']}' not found.",
                "fatal_status_code": 404,
            }

        profile = ProfileRepository.get_by_candidate_id(db, candidate.id)
        if profile is None or not profile.profile_data:
            return {
                "fatal_error_code": "PROFILE_NOT_FOUND",
                "fatal_error_message": f"Candidate '{candidate.id}' does not have an extracted profile.",
                "fatal_status_code": 404,
            }

        matching_run = db.get(MatchingRun, state["matching_run_id"])
        if matching_run is None:
            return {
                "fatal_error_code": "MATCHING_RUN_NOT_FOUND",
                "fatal_error_message": f"Matching run '{state['matching_run_id']}' not found.",
                "fatal_status_code": 404,
            }
        if matching_run.candidate_id != candidate.id:
            return {
                "fatal_error_code": "MATCHING_RUN_CANDIDATE_MISMATCH",
                "fatal_error_message": "Matching run does not belong to the specified candidate.",
                "fatal_status_code": 422,
            }
        if matching_run.status not in ("completed", "completed_with_warnings"):
            return {
                "fatal_error_code": "MATCHING_RUN_INCOMPLETE",
                "fatal_error_message": (
                    f"Matching run '{matching_run.id}' has status '{matching_run.status}' "
                    "and must be completed before generating outreach."
                ),
                "fatal_status_code": 409,
            }

        company = db.get(Company, state["company_id"])
        if company is None:
            return {
                "fatal_error_code": "COMPANY_NOT_FOUND",
                "fatal_error_message": f"Company '{state['company_id']}' not found.",
                "fatal_status_code": 404,
            }

        match_result = db.get(MatchResult, state["match_result_id"])
        if match_result is None:
            return {
                "fatal_error_code": "MATCH_RESULT_NOT_FOUND",
                "fatal_error_message": f"Match result '{state['match_result_id']}' not found.",
                "fatal_status_code": 404,
            }
        if match_result.matching_run_id != matching_run.id or match_result.company_id != company.id:
            return {
                "fatal_error_code": "MATCH_RESULT_MISMATCH",
                "fatal_error_message": "Match result does not belong to the selected matching run and company.",
                "fatal_status_code": 422,
            }

        # Check duplicate active (non-archived) draft for same run, company, founder, intent
        existing_draft = db.scalar(
            select(OutreachDraft).where(
                OutreachDraft.matching_run_id == matching_run.id,
                OutreachDraft.company_id == company.id,
                OutreachDraft.founder_id == state["founder_id"],
                OutreachDraft.outreach_intent == state["outreach_intent"],
                OutreachDraft.status != "archived",
            )
        )
        if existing_draft is not None:
            return {
                "fatal_error_code": "DUPLICATE_OUTREACH_DRAFT",
                "fatal_error_message": (
                    "An active outreach draft already exists for this matching run, company, founder, and intent."
                ),
                "fatal_status_code": 409,
            }

        doc_normalizer.index_company(db, company)
        candidate_ctx = assemble_candidate_context(profile.profile_data)
        company_ctx = assemble_company_context(db, company, match_result)

        if state["outreach_intent"] == "job_interest" and (
            company_ctx.get("opportunity_type") != "active" or not company_ctx.get("active_jobs")
        ):
            return {
                "fatal_error_code": "JOB_INTEREST_REQUIRES_ACTIVE_JOB",
                "fatal_error_message": (
                    "Cannot generate 'job_interest' outreach without an 'active' match classification "
                    "and at least one verified, non-stale active public job opportunity."
                ),
                "fatal_status_code": 422,
            }

        return {
            "candidate_context": candidate_ctx,
            "company_context": company_ctx,
        }

    def validate_selected_founder(state: OutreachState) -> dict[str, Any]:
        if state.get("fatal_error_code"):
            return {}

        founder = db.get(Founder, state["founder_id"])
        if founder is None:
            return {
                "fatal_error_code": "FOUNDER_NOT_FOUND",
                "fatal_error_message": f"Founder '{state['founder_id']}' not found.",
                "fatal_status_code": 404,
            }
        if founder.company_id != state["company_id"]:
            return {
                "fatal_error_code": "FOUNDER_COMPANY_MISMATCH",
                "fatal_error_message": "Selected founder does not belong to the selected company.",
                "fatal_status_code": 422,
            }

        founder_ctx, founder_evidence, founder_warnings = assemble_founder_context(db, founder)
        return {
            "founder_context": founder_ctx,
            "founder_evidence_ids": [ev.id for ev in founder_evidence],
            "warnings": [*state["warnings"], *founder_warnings],
        }

    def retrieve_personalization_evidence(state: OutreachState) -> dict[str, Any]:
        if state.get("fatal_error_code"):
            return {}

        company_ctx = state["company_context"]
        candidate_ctx = state["candidate_context"]
        query_parts = [
            str(company_ctx.get("name") or ""),
            str(company_ctx.get("product_or_service") or ""),
            " ".join(str(t) for t in (company_ctx.get("tech_stack") or [])[:5]),
            " ".join(str(s) for s in (candidate_ctx.get("skills") or [])[:5]),
        ]
        query = " ".join(p for p in query_parts if p).strip() or str(company_ctx.get("name") or "startup")

        fts_items = retriever.retrieve(
            query=query,
            company_id=state["company_id"],
            limit=12,
        )

        founder_ev_ids = list(state.get("founder_evidence_ids") or [])
        founder_evidence: list[SourceEvidence] = []
        if founder_ev_ids:
            founder_evidence = list(
                db.scalars(select(SourceEvidence).where(SourceEvidence.id.in_(founder_ev_ids))).all()
            )

        merged = collect_company_evidence_for_outreach(
            db,
            company_id=state["company_id"],
            matching_run_id=state["matching_run_id"],
            retrieved_items=fts_items,
            founder_evidence=founder_evidence,
        )

        if not merged:
            return {
                "fatal_error_code": "INSUFFICIENT_COMPANY_EVIDENCE",
                "fatal_error_message": "No company-specific evidence is available to ground outreach.",
                "fatal_status_code": 422,
            }

        return {
            "retrieved_evidence": [item.model_dump(mode="json") for item in merged],
        }

    def build_outreach_strategy_node(state: OutreachState) -> dict[str, Any]:
        if state.get("fatal_error_code"):
            return {}

        evidence_items = [RetrievedEvidenceItem.model_validate(item) for item in state["retrieved_evidence"]]
        try:
            result = llm_provider.build_outreach_strategy(
                outreach_intent=state["outreach_intent"],
                candidate_context=state["candidate_context"],
                company_context=state["company_context"],
                founder_context=state["founder_context"],
                retrieved_evidence=evidence_items,
            )
        except LLMProviderError as exc:
            return {
                "fatal_error_code": exc.code,
                "fatal_error_message": exc.detail,
                "fatal_status_code": exc.status_code,
            }

        return {
            "strategy": result.strategy.model_dump(mode="json"),
            "generation_provider": result.provider_name,
            "generation_model": result.model_name,
            "data_origin": result.data_origin,
            "warnings": [*state["warnings"], *result.warnings],
        }

    def generate_outreach_draft_node(state: OutreachState) -> dict[str, Any]:
        if state.get("fatal_error_code"):
            return {}

        evidence_items = [RetrievedEvidenceItem.model_validate(item) for item in state["retrieved_evidence"]]
        strategy = OutreachStrategy.model_validate(state["strategy"])
        try:
            result = llm_provider.generate_outreach_draft(
                outreach_intent=state["outreach_intent"],
                strategy=strategy,
                candidate_context=state["candidate_context"],
                company_context=state["company_context"],
                founder_context=state["founder_context"],
                retrieved_evidence=evidence_items,
            )
        except LLMProviderError as exc:
            return {
                "fatal_error_code": exc.code,
                "fatal_error_message": exc.detail,
                "fatal_status_code": exc.status_code,
            }

        return {
            "generated_draft": result.draft.model_dump(mode="json"),
            "generation_provider": result.provider_name,
            "generation_model": result.model_name,
            "data_origin": result.data_origin,
            "warnings": [*state["warnings"], *result.warnings],
        }

    def validate_outreach_claims_node(state: OutreachState) -> dict[str, Any]:
        if state.get("fatal_error_code"):
            return {}

        draft = StructuredOutreachEmail.model_validate(state["generated_draft"])
        strategy = OutreachStrategy.model_validate(state["strategy"])
        evidence_items = [RetrievedEvidenceItem.model_validate(item) for item in state["retrieved_evidence"]]

        try:
            cleaned_draft, cleaned_strategy, validated_claims, warnings, requires_review = validate_outreach_generation(
                draft=draft,
                strategy=strategy,
                company_id=state["company_id"],
                intent=state["outreach_intent"],
                candidate_context=state["candidate_context"],
                company_context=state["company_context"],
                founder_context=state["founder_context"],
                company_evidence=evidence_items,
                initial_warnings=state["warnings"],
            )
        except ValueError as exc:
            return {
                "fatal_error_code": "OUTREACH_GROUNDING_FAILED",
                "fatal_error_message": str(exc),
                "fatal_status_code": 422,
            }

        return {
            "generated_draft": cleaned_draft.model_dump(mode="json"),
            "strategy": cleaned_strategy.model_dump(mode="json"),
            "validated_claims": [c.model_dump(mode="json") for c in validated_claims],
            "warnings": warnings,
            "requires_review": requires_review,
        }

    def persist_outreach_draft(state: OutreachState) -> dict[str, Any]:
        if state.get("fatal_error_code"):
            return {"persisted": False}

        company_ctx = state["company_context"]
        if state["outreach_intent"] == "job_interest" and (
            company_ctx.get("opportunity_type") != "active" or not company_ctx.get("active_jobs")
        ):
            return {
                "fatal_error_code": "JOB_INTEREST_REQUIRES_ACTIVE_JOB",
                "fatal_error_message": (
                    "Cannot persist 'job_interest' outreach without an 'active' match classification "
                    "and a verified, non-stale active job opportunity."
                ),
                "fatal_status_code": 422,
                "persisted": False,
            }

        draft_model = StructuredOutreachEmail.model_validate(state["generated_draft"])
        sections = {
            "greeting": draft_model.greeting,
            "opening_personalization": draft_model.opening_personalization,
            "candidate_introduction": draft_model.candidate_introduction,
            "relevant_skills_experience": draft_model.relevant_skills_experience,
            "reason_for_contacting": draft_model.reason_for_contacting,
            "value_proposition": draft_model.value_proposition,
            "call_to_action": draft_model.call_to_action,
            "closing": draft_model.closing,
        }

        try:
            db_draft = OutreachDraft(
                candidate_id=state["candidate_id"],
                matching_run_id=state["matching_run_id"],
                match_result_id=state["match_result_id"],
                company_id=state["company_id"],
                founder_id=state["founder_id"],
                outreach_intent=state["outreach_intent"],
                status="draft",
                subject=draft_model.subject,
                body=draft_model.body,
                original_subject=draft_model.subject,
                original_body=draft_model.body,
                personalization_rationale=draft_model.personalization_rationale,
                strategy_json=state["strategy"],
                structured_sections_json=sections,
                candidate_strengths_used=draft_model.candidate_strengths_used,
                company_facts_used=draft_model.company_facts_used,
                unsupported_claims=draft_model.unsupported_or_uncertain_claims,
                review_warnings=state["warnings"],
                requires_review=state["requires_review"],
                generation_provider=state["generation_provider"] or "demo",
                generation_model=state["generation_model"],
                data_origin=state["data_origin"] or "demo",
                version=1,
            )
            db.add(db_draft)
            db.flush()

            for claim_raw in state["validated_claims"]:
                claim = StructuredOutreachClaim.model_validate(claim_raw)
                if claim.claim_category == "candidate_profile":
                    db.add(
                        OutreachDraftEvidence(
                            outreach_draft_id=db_draft.id,
                            source_evidence_id=None,
                            company_id=None,
                            claim_category=claim.claim_category,
                            claim_text=claim.claim_text,
                            verification_status=claim.verification_status,
                            support_status=claim.support_status,
                            requires_review=claim.requires_review,
                        )
                    )
                elif claim.evidence_ids:
                    for eid in claim.evidence_ids:
                        db.add(
                            OutreachDraftEvidence(
                                outreach_draft_id=db_draft.id,
                                source_evidence_id=eid,
                                company_id=state["company_id"],
                                claim_category=claim.claim_category,
                                claim_text=claim.claim_text,
                                verification_status=claim.verification_status,
                                support_status=claim.support_status,
                                requires_review=claim.requires_review,
                            )
                        )
                else:
                    db.add(
                        OutreachDraftEvidence(
                            outreach_draft_id=db_draft.id,
                            source_evidence_id=None,
                            company_id=state["company_id"],
                            claim_category=claim.claim_category,
                            claim_text=claim.claim_text,
                            verification_status=claim.verification_status,
                            support_status=claim.support_status,
                            requires_review=claim.requires_review,
                        )
                    )

            db.add(
                OutreachDraftVersion(
                    outreach_draft_id=db_draft.id,
                    version=1,
                    subject=db_draft.subject,
                    body=db_draft.body,
                    change_type="generated",
                    status_at_version="draft",
                )
            )
            db.commit()
            db.refresh(db_draft)
        except IntegrityError:
            db.rollback()
            return {
                "fatal_error_code": "DUPLICATE_OUTREACH_DRAFT",
                "fatal_error_message": (
                    "An active outreach draft already exists for this matching run, company, founder, and intent."
                ),
                "fatal_status_code": 409,
                "persisted": False,
            }
        except Exception as exc:
            db.rollback()
            return {
                "fatal_error_code": "OUTREACH_PERSISTENCE_FAILED",
                "fatal_error_message": f"Failed to persist outreach draft: {type(exc).__name__}",
                "fatal_status_code": 500,
                "persisted": False,
            }

        return {
            "draft_id": db_draft.id,
            "persisted": True,
        }

    def complete_outreach_generation(state: OutreachState) -> dict[str, Any]:
        if state.get("fatal_error_code"):
            return {"final_status": "failed"}
        return {"final_status": "completed"}

    graph = StateGraph(OutreachState)
    graph.add_node("load_outreach_context", load_outreach_context)
    graph.add_node("validate_selected_founder", validate_selected_founder)
    graph.add_node("retrieve_personalization_evidence", retrieve_personalization_evidence)
    graph.add_node("build_outreach_strategy", build_outreach_strategy_node)
    graph.add_node("generate_outreach_draft", generate_outreach_draft_node)
    graph.add_node("validate_outreach_claims", validate_outreach_claims_node)
    graph.add_node("persist_outreach_draft", persist_outreach_draft)
    graph.add_node("complete_outreach_generation", complete_outreach_generation)

    graph.add_edge(START, "load_outreach_context")
    graph.add_edge("load_outreach_context", "validate_selected_founder")
    graph.add_edge("validate_selected_founder", "retrieve_personalization_evidence")
    graph.add_edge("retrieve_personalization_evidence", "build_outreach_strategy")
    graph.add_edge("build_outreach_strategy", "generate_outreach_draft")
    graph.add_edge("generate_outreach_draft", "validate_outreach_claims")
    graph.add_edge("validate_outreach_claims", "persist_outreach_draft")
    graph.add_edge("persist_outreach_draft", "complete_outreach_generation")
    graph.add_edge("complete_outreach_generation", END)

    return graph.compile()
