from datetime import UTC, datetime
import logging

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.graphs.matching_graph import MatchingState, build_matching_graph
from app.models.candidate import Candidate
from app.models.m4 import Company, DiscoveryRun
from app.models.m5 import CompanyAssessment, MatchingRun, MatchResult, RetrievalRecord
from app.providers.llm import LLMProvider, get_llm_provider
from app.repositories.profile_repository import ProfileRepository
from app.schemas.m5 import (
    DimensionScore,
    MatchDetailResponse,
    MatchEvidenceItemResponse,
    MatchEvidenceListResponse,
    MatchingRunCreateRequest,
    MatchingRunResponse,
    MatchResultsListResponse,
    MatchResultSummaryResponse,
    OpportunityAssessment,
    StructuredCompanyAssessment,
)
from app.services.fit_scoring import FIT_SCORING_VERSION
from app.services.fts_retriever import EvidenceRetriever, SQLiteFTSRetriever
from app.services.ranking import RANKING_POLICY_VERSION


class MatchingRunNotFoundError(Exception):
    status_code: int = 404
    code: str = "MATCHING_RUN_NOT_FOUND"
    detail: str = "Matching run not found."


class MatchResultNotFoundError(Exception):
    status_code: int = 404
    code: str = "MATCH_RESULT_NOT_FOUND"
    detail: str = "Match result not found."


class MatchingValidationError(Exception):
    def __init__(self, code: str, detail: str, status_code: int = 422) -> None:
        super().__init__(detail)
        self.code = code
        self.detail = detail
        self.status_code = status_code


class MatchingConflictError(Exception):
    def __init__(self, code: str = "DUPLICATE_MATCHING_RUN", detail: str = "A matching run for this candidate and company selection already exists or is in progress.", status_code: int = 409) -> None:
        super().__init__(detail)
        self.code = code
        self.detail = detail
        self.status_code = status_code


class MatchingExecutionError(Exception):
    def __init__(self, code: str = "MATCHING_WORKFLOW_ERROR", detail: str = "Matching workflow failed unexpectedly.", status_code: int = 500) -> None:
        super().__init__(detail)
        self.code = code
        self.detail = detail
        self.status_code = status_code


logger = logging.getLogger(__name__)


def _to_run_response(db: Session, run: MatchingRun) -> MatchingRunResponse:
    result_count = db.scalar(
        select(func.count()).select_from(MatchResult).where(MatchResult.matching_run_id == run.id)
    ) or 0
    return MatchingRunResponse(
        run_id=run.id,
        candidate_id=run.candidate_id,
        discovery_run_id=run.discovery_run_id,
        company_ids=list(run.company_ids or []),
        status=run.status,  # type: ignore[arg-type]
        scoring_version=run.scoring_version,
        ranking_version=run.ranking_version,
        retrieval_config=dict(run.retrieval_config or {}),
        warnings=list(run.warnings or []),
        error_code=run.error_code,
        error_message=run.error_message,
        requires_review=run.requires_review,
        result_count=int(result_count),
        created_at=run.created_at,
        started_at=run.started_at,
        completed_at=run.completed_at,
    )


def start_matching_run(
    db: Session,
    settings: Settings,
    payload: MatchingRunCreateRequest,
    *,
    llm_provider: LLMProvider | None = None,
    retriever: EvidenceRetriever | None = None,
) -> MatchingRunResponse:
    """Validate inputs, create a MatchingRun, and execute the M5 LangGraph workflow."""
    candidate = db.get(Candidate, payload.candidate_id)
    if candidate is None:
        raise MatchingValidationError("CANDIDATE_NOT_FOUND", "Candidate not found.", status_code=404)

    profile = ProfileRepository.get_by_candidate_id(db, candidate.id)
    if profile is None or not profile.profile_data:
        raise MatchingValidationError(
            "PROFILE_NOT_EXTRACTED",
            "Candidate does not have an extracted profile yet.",
            status_code=422,
        )

    company_ids: list[str] = list(payload.company_ids or [])
    if payload.discovery_run_id is not None:
        d_run = db.get(DiscoveryRun, payload.discovery_run_id)
        if d_run is None:
            raise MatchingValidationError(
                "DISCOVERY_RUN_NOT_FOUND",
                "Discovery run not found.",
                status_code=404,
            )
        if d_run.candidate_id != candidate.id:
            raise MatchingValidationError(
                "DISCOVERY_CANDIDATE_MISMATCH",
                "Discovery run does not belong to the specified candidate.",
                status_code=422,
            )
        if not company_ids:
            company_ids = list(d_run.company_ids or [])

    if not company_ids:
        raise MatchingValidationError(
            "NO_COMPANIES_SELECTED",
            "No companies available for matching.",
            status_code=422,
        )

    found_companies = list(db.scalars(select(Company.id).where(Company.id.in_(company_ids))).all())
    if len(found_companies) != len(set(company_ids)):
        raise MatchingValidationError(
            "COMPANY_NOT_FOUND",
            "One or more specified companies were not found.",
            status_code=404,
        )

    # Deterministic normalization for duplicate/concurrent run detection
    normalized_company_ids = sorted(set(company_ids))
    existing_runs = list(
        db.scalars(
            select(MatchingRun).where(
                MatchingRun.candidate_id == candidate.id,
                MatchingRun.discovery_run_id == payload.discovery_run_id,
                MatchingRun.status.in_(["pending", "processing", "completed", "completed_with_warnings"]),
            )
        ).all()
    )
    for existing in existing_runs:
        if sorted(set(existing.company_ids or [])) == normalized_company_ids:
            if existing.status in {"pending", "processing"}:
                raise MatchingConflictError(
                    "MATCHING_RUN_IN_PROGRESS",
                    "A matching run for this candidate and company selection is already in progress.",
                )
            raise MatchingConflictError(
                "DUPLICATE_MATCHING_RUN",
                "A completed matching run for this exact candidate, discovery run, and company selection already exists.",
            )

    provider = llm_provider or get_llm_provider(settings)
    active_retriever = retriever or SQLiteFTSRetriever(db)

    now = datetime.now(UTC)
    run = MatchingRun(
        candidate_id=candidate.id,
        discovery_run_id=payload.discovery_run_id,
        company_ids=normalized_company_ids,
        status="processing",
        scoring_version=settings.matching_scoring_version or FIT_SCORING_VERSION,
        ranking_version=settings.matching_ranking_version or RANKING_POLICY_VERSION,
        retrieval_config=payload.retrieval_config.model_dump(mode="json"),
        started_at=now,
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    graph = build_matching_graph(
        db=db,
        llm_provider=provider,
        retriever=active_retriever,
    )
    initial_state: MatchingState = {
        "matching_run_id": run.id,
        "candidate_id": candidate.id,
        "discovery_run_id": payload.discovery_run_id,
        "company_ids": normalized_company_ids,
        "retrieval_config": run.retrieval_config,
        "scoring_version": run.scoring_version,
        "ranking_version": run.ranking_version,
        "candidate_profile_snapshot": {},
        "company_context": {},
        "retrieval_queries": {},
        "retrieved_evidence": {},
        "evidence_quality": {},
        "company_assessments": {},
        "assessment_metadata": {},
        "match_scores": {},
        "opportunity_assessments": {},
        "explanations": {},
        "ranked_results": [],
        "warnings": [],
        "errors": [],
        "fatal_error_code": None,
        "fatal_error_message": None,
        "requires_review": False,
        "persisted": False,
        "final_status": "processing",
    }

    try:
        graph.invoke(initial_state)
    except Exception as exc:
        logger.exception("Unhandled exception during matching graph execution for run %s", run.id)
        db.rollback()
        try:
            db.execute(delete(MatchResult).where(MatchResult.matching_run_id == run.id))
            db.execute(delete(CompanyAssessment).where(CompanyAssessment.matching_run_id == run.id))
            db.execute(delete(RetrievalRecord).where(RetrievalRecord.matching_run_id == run.id))
            failed_run = db.get(MatchingRun, run.id)
            if failed_run is not None:
                failed_run.status = "failed"
                failed_run.error_code = "MATCHING_WORKFLOW_ERROR"
                failed_run.error_message = f"Matching workflow failed ({type(exc).__name__})."
                failed_run.completed_at = datetime.now(UTC)
            db.commit()
        except Exception:
            db.rollback()
        raise MatchingExecutionError(
            "MATCHING_WORKFLOW_ERROR",
            f"Matching workflow failed ({type(exc).__name__}).",
            status_code=500,
        ) from exc

    db.refresh(run)
    return _to_run_response(db, run)


def get_matching_run(db: Session, run_id: str) -> MatchingRunResponse:
    run = db.get(MatchingRun, run_id)
    if run is None:
        raise MatchingRunNotFoundError()
    return _to_run_response(db, run)


def list_matching_run_results(
    db: Session,
    run_id: str,
    *,
    limit: int = 20,
    offset: int = 0,
) -> MatchResultsListResponse:
    run = db.get(MatchingRun, run_id)
    if run is None:
        raise MatchingRunNotFoundError()

    total = db.scalar(
        select(func.count()).select_from(MatchResult).where(MatchResult.matching_run_id == run_id)
    ) or 0

    rows = list(
        db.scalars(
            select(MatchResult)
            .where(MatchResult.matching_run_id == run_id)
            .order_by(MatchResult.ranking_position.asc())
            .limit(limit)
            .offset(offset)
        ).all()
    )

    items = [
        MatchResultSummaryResponse(
            match_id=row.id,
            matching_run_id=row.matching_run_id,
            company_id=row.company_id,
            company_name=str((row.company_snapshot or {}).get("name") or "Unknown"),
            company_stage=str((row.company_snapshot or {}).get("stage") or "unknown"),
            company_industry=(row.company_snapshot or {}).get("industry"),
            ranking_position=row.ranking_position,
            ranking_version=row.ranking_version,
            ranking_explanation=row.ranking_explanation,
            ranking_factors=dict(row.ranking_factors or {}),
            fit_score=row.fit_score,
            fit_coverage=row.fit_coverage,
            scoring_version=row.scoring_version,
            opportunity_type=row.opportunity_type,  # type: ignore[arg-type]
            evidence_strength=row.evidence_strength,  # type: ignore[arg-type]
            explanation=row.explanation,
            requires_review=row.requires_review,
            data_origin=row.data_origin,  # type: ignore[arg-type]
            created_at=row.created_at,
        )
        for row in rows
    ]

    return MatchResultsListResponse(
        matching_run_id=run_id,
        items=items,
        total=int(total),
        limit=limit,
        offset=offset,
    )


def get_match_detail(db: Session, match_id: str) -> MatchDetailResponse:
    mr = db.get(MatchResult, match_id)
    if mr is None:
        raise MatchResultNotFoundError()

    qual_assessment: StructuredCompanyAssessment | None = None
    if mr.company_assessment_id:
        ca = db.get(CompanyAssessment, mr.company_assessment_id)
        if ca is not None and ca.assessment_data:
            qual_assessment = StructuredCompanyAssessment.model_validate(ca.assessment_data)

    return MatchDetailResponse(
        match_id=mr.id,
        matching_run_id=mr.matching_run_id,
        company_id=mr.company_id,
        company_snapshot=dict(mr.company_snapshot or {}),
        ranking_position=mr.ranking_position,
        ranking_version=mr.ranking_version,
        ranking_explanation=mr.ranking_explanation,
        ranking_factors=dict(mr.ranking_factors or {}),
        fit_score=mr.fit_score,
        fit_coverage=mr.fit_coverage,
        scoring_version=mr.scoring_version,
        dimension_breakdown=[DimensionScore.model_validate(d) for d in (mr.dimension_breakdown or [])],
        opportunity_assessment=OpportunityAssessment.model_validate(mr.opportunity_assessment),
        qualitative_assessment=qual_assessment,
        explanation=mr.explanation,
        requires_review=mr.requires_review,
        data_origin=mr.data_origin,  # type: ignore[arg-type]
        created_at=mr.created_at,
    )


def get_match_evidence(
    db: Session,
    match_id: str,
    *,
    limit: int = 20,
    offset: int = 0,
) -> MatchEvidenceListResponse:
    mr = db.get(MatchResult, match_id)
    if mr is None:
        raise MatchResultNotFoundError()

    total = db.scalar(
        select(func.count())
        .select_from(RetrievalRecord)
        .where(
            RetrievalRecord.matching_run_id == mr.matching_run_id,
            RetrievalRecord.company_id == mr.company_id,
        )
    ) or 0

    rows = list(
        db.scalars(
            select(RetrievalRecord)
            .where(
                RetrievalRecord.matching_run_id == mr.matching_run_id,
                RetrievalRecord.company_id == mr.company_id,
            )
            .order_by(RetrievalRecord.rank_order.asc())
            .limit(limit)
            .offset(offset)
        ).all()
    )

    items = []
    for row in rows:
        snap = dict(row.retrieved_snapshot or {})
        items.append(
            MatchEvidenceItemResponse(
                retrieval_record_id=row.id,
                evidence_document_id=row.evidence_document_id,
                source_evidence_id=row.source_evidence_id,
                company_id=row.company_id,
                query_text=row.query_text,
                rank_order=row.rank_order,
                bm25_score=row.bm25_score,
                entity_type=str(snap.get("entity_type") or "unknown"),
                document_title=str(snap.get("document_title") or ""),
                content=str(snap.get("content") or ""),
                source_url=snap.get("source_url"),
                source_title=snap.get("source_title"),
                publication_date=snap.get("publication_date"),
                retrieved_at=snap.get("retrieved_at"),
                verification_status=str(snap.get("verification_status") or "unverified"),
                data_origin=str(snap.get("data_origin") or "demo"),
            )
        )

    return MatchEvidenceListResponse(
        match_id=mr.id,
        matching_run_id=mr.matching_run_id,
        company_id=mr.company_id,
        items=items,
        total=int(total),
        limit=limit,
        offset=offset,
    )
