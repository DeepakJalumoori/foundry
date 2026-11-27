from datetime import UTC, datetime
import logging

from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.graphs.outreach_graph import OutreachState, build_outreach_graph
from app.models.m4 import Company, Founder, SourceEvidence
from app.models.m6 import OutreachDraft, OutreachDraftEvidence, OutreachDraftVersion
from app.providers.llm import LLMProvider, get_llm_provider
from app.schemas.m6 import (
    FounderSummaryResponse,
    OutreachDraftCreateRequest,
    OutreachDraftEvidenceItemResponse,
    OutreachDraftEvidenceListResponse,
    OutreachDraftListResponse,
    OutreachDraftResponse,
    OutreachDraftStatus,
    OutreachDraftUpdateRequest,
    OutreachDraftVersionListResponse,
    OutreachDraftVersionResponse,
    OutreachStrategy,
)
from app.services.fts_retriever import EvidenceRetriever, SQLiteFTSRetriever

logger = logging.getLogger(__name__)

_ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "draft": {"reviewed", "approved", "archived"},
    "reviewed": {"approved", "archived"},
    "approved": {"archived"},
    "archived": set(),
}


class OutreachDraftNotFoundError(Exception):
    status_code: int = 404
    code: str = "OUTREACH_DRAFT_NOT_FOUND"
    detail: str = "Outreach draft not found."


class OutreachValidationError(Exception):
    def __init__(self, code: str, detail: str, status_code: int = 422) -> None:
        super().__init__(detail)
        self.code = code
        self.detail = detail
        self.status_code = status_code


class OutreachConflictError(Exception):
    def __init__(self, code: str, detail: str, status_code: int = 409) -> None:
        super().__init__(detail)
        self.code = code
        self.detail = detail
        self.status_code = status_code


class OutreachExecutionError(Exception):
    def __init__(self, code: str = "OUTREACH_WORKFLOW_ERROR", detail: str = "Outreach generation failed.", status_code: int = 500) -> None:
        super().__init__(detail)
        self.code = code
        self.detail = detail
        self.status_code = status_code


def _to_draft_response(db: Session, draft: OutreachDraft) -> OutreachDraftResponse:
    company = db.get(Company, draft.company_id)
    founder = db.get(Founder, draft.founder_id)
    evidence_count = db.scalar(
        select(func.count())
        .select_from(OutreachDraftEvidence)
        .where(OutreachDraftEvidence.outreach_draft_id == draft.id)
    ) or 0

    founder_summary = FounderSummaryResponse(
        founder_id=draft.founder_id,
        full_name=founder.full_name if founder else "Unknown Founder",
        role_title=founder.role_title if founder else None,
        public_profile_url=founder.public_profile_url if founder else None,
        email=None,
        verification_status=(founder.verification_status if founder else "requires_review"),  # type: ignore[arg-type]
        data_origin=(founder.data_origin if founder else draft.data_origin),  # type: ignore[arg-type]
        conflict_notes=founder.conflict_notes if founder else None,
    )

    strategy = OutreachStrategy.model_validate(draft.strategy_json)

    return OutreachDraftResponse(
        id=draft.id,
        candidate_id=draft.candidate_id,
        matching_run_id=draft.matching_run_id,
        match_result_id=draft.match_result_id,
        company_id=draft.company_id,
        company_name=company.name if company else "Unknown Company",
        founder_id=draft.founder_id,
        founder=founder_summary,
        outreach_intent=draft.outreach_intent,  # type: ignore[arg-type]
        status=draft.status,  # type: ignore[arg-type]
        subject=draft.subject,
        body=draft.body,
        original_subject=draft.original_subject,
        original_body=draft.original_body,
        personalization_rationale=draft.personalization_rationale,
        strategy=strategy,
        structured_sections=dict(draft.structured_sections_json or {}),
        candidate_strengths_used=list(draft.candidate_strengths_used or []),
        company_facts_used=list(draft.company_facts_used or []),
        unsupported_claims=list(draft.unsupported_claims or []),
        review_warnings=list(draft.review_warnings or []),
        requires_review=draft.requires_review,
        generation_provider=draft.generation_provider,
        generation_model=draft.generation_model,
        data_origin=draft.data_origin,  # type: ignore[arg-type]
        version=draft.version,
        evidence_count=int(evidence_count),
        created_at=draft.created_at,
        updated_at=draft.updated_at,
        reviewed_at=draft.reviewed_at,
        approved_at=draft.approved_at,
        archived_at=draft.archived_at,
    )


def generate_outreach_draft(
    db: Session,
    settings: Settings,
    payload: OutreachDraftCreateRequest,
    *,
    llm_provider: LLMProvider | None = None,
    retriever: EvidenceRetriever | None = None,
) -> OutreachDraftResponse:
    """Execute the M6 LangGraph outreach workflow and return the persisted draft."""
    provider = llm_provider or get_llm_provider(settings)
    ev_retriever = retriever or SQLiteFTSRetriever(db)

    graph = build_outreach_graph(db=db, llm_provider=provider, retriever=ev_retriever)
    initial_state: OutreachState = {
        "candidate_id": payload.candidate_id,
        "matching_run_id": payload.matching_run_id,
        "match_result_id": payload.match_result_id,
        "company_id": payload.company_id,
        "founder_id": payload.founder_id,
        "outreach_intent": payload.outreach_intent,
        "candidate_context": {},
        "company_context": {},
        "founder_context": {},
        "founder_evidence_ids": [],
        "retrieved_evidence": [],
        "strategy": {},
        "generated_draft": {},
        "validated_claims": [],
        "generation_provider": "",
        "generation_model": None,
        "data_origin": "demo",
        "warnings": [],
        "requires_review": False,
        "draft_id": None,
        "fatal_error_code": None,
        "fatal_error_message": None,
        "fatal_status_code": 500,
        "persisted": False,
        "final_status": "pending",
    }

    try:
        final_state = graph.invoke(initial_state)
    except Exception as exc:
        logger.exception("Unhandled error in M6 outreach LangGraph workflow")
        db.rollback()
        raise OutreachExecutionError(
            code="OUTREACH_WORKFLOW_ERROR",
            detail=f"Outreach workflow failed unexpectedly: {type(exc).__name__}",
            status_code=500,
        ) from exc

    if final_state.get("fatal_error_code"):
        code = str(final_state["fatal_error_code"])
        detail = str(final_state.get("fatal_error_message") or "Outreach generation failed.")
        status_code = int(final_state.get("fatal_status_code") or 500)
        if status_code == 409:
            raise OutreachConflictError(code=code, detail=detail, status_code=409)
        if status_code in (404, 422):
            raise OutreachValidationError(code=code, detail=detail, status_code=status_code)
        raise OutreachExecutionError(code=code, detail=detail, status_code=status_code)

    draft_id = final_state.get("draft_id")
    if not draft_id:
        raise OutreachExecutionError()

    draft = db.get(OutreachDraft, draft_id)
    if draft is None:
        raise OutreachDraftNotFoundError()
    return _to_draft_response(db, draft)


def list_outreach_drafts(
    db: Session,
    *,
    candidate_id: str | None = None,
    company_id: str | None = None,
    matching_run_id: str | None = None,
    status_filter: OutreachDraftStatus | None = None,
    limit: int = 20,
    offset: int = 0,
) -> OutreachDraftListResponse:
    stmt = select(OutreachDraft)
    count_stmt = select(func.count()).select_from(OutreachDraft)

    if candidate_id:
        stmt = stmt.where(OutreachDraft.candidate_id == candidate_id)
        count_stmt = count_stmt.where(OutreachDraft.candidate_id == candidate_id)
    if company_id:
        stmt = stmt.where(OutreachDraft.company_id == company_id)
        count_stmt = count_stmt.where(OutreachDraft.company_id == company_id)
    if matching_run_id:
        stmt = stmt.where(OutreachDraft.matching_run_id == matching_run_id)
        count_stmt = count_stmt.where(OutreachDraft.matching_run_id == matching_run_id)
    if status_filter:
        stmt = stmt.where(OutreachDraft.status == status_filter)
        count_stmt = count_stmt.where(OutreachDraft.status == status_filter)

    total = int(db.scalar(count_stmt) or 0)
    rows = list(
        db.scalars(
            stmt.order_by(OutreachDraft.created_at.desc()).offset(offset).limit(limit)
        ).all()
    )
    return OutreachDraftListResponse(
        items=[_to_draft_response(db, row) for row in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


def get_outreach_draft(db: Session, draft_id: str) -> OutreachDraftResponse:
    draft = db.get(OutreachDraft, draft_id)
    if draft is None:
        raise OutreachDraftNotFoundError()
    return _to_draft_response(db, draft)


def update_outreach_draft(
    db: Session,
    draft_id: str,
    payload: OutreachDraftUpdateRequest,
) -> OutreachDraftResponse:
    draft = db.get(OutreachDraft, draft_id)
    if draft is None:
        raise OutreachDraftNotFoundError()
    if draft.status in ("approved", "archived"):
        raise OutreachConflictError(
            code="DRAFT_IMMUTABLE_IN_STATUS",
            detail=f"Cannot edit an outreach draft in '{draft.status}' status.",
            status_code=409,
        )
    if draft.version != payload.expected_version:
        raise OutreachConflictError(
            code="STALE_DRAFT_VERSION",
            detail=(
                f"Expected draft version {payload.expected_version}, "
                f"but current persisted version is {draft.version}."
            ),
            status_code=409,
        )
    if payload.subject is None and payload.body is None:
        raise OutreachValidationError(
            code="EMPTY_DRAFT_UPDATE",
            detail="At least one of 'subject' or 'body' must be provided.",
            status_code=422,
        )

    new_subject = payload.subject if payload.subject is not None else draft.subject
    new_body = payload.body if payload.body is not None else draft.body

    if new_subject == draft.subject and new_body == draft.body:
        return _to_draft_response(db, draft)

    now = datetime.now(UTC)
    next_version = payload.expected_version + 1
    try:
        res = db.execute(
            update(OutreachDraft)
            .where(
                OutreachDraft.id == draft_id,
                OutreachDraft.version == payload.expected_version,
                OutreachDraft.status.in_(["draft", "reviewed"]),
            )
            .values(
                subject=new_subject,
                body=new_body,
                version=next_version,
                updated_at=now,
            )
        )
        if res.rowcount != 1:
            db.rollback()
            current = db.get(OutreachDraft, draft_id)
            if current is None:
                raise OutreachDraftNotFoundError()
            if current.status in ("approved", "archived"):
                raise OutreachConflictError(
                    code="DRAFT_IMMUTABLE_IN_STATUS",
                    detail=f"Cannot edit an outreach draft in '{current.status}' status.",
                    status_code=409,
                )
            raise OutreachConflictError(
                code="STALE_DRAFT_VERSION",
                detail=(
                    f"Expected draft version {payload.expected_version}, "
                    f"but current persisted version is {current.version}."
                ),
                status_code=409,
            )

        db.add(
            OutreachDraftVersion(
                outreach_draft_id=draft_id,
                version=next_version,
                subject=new_subject,
                body=new_body,
                change_type="edited",
                status_at_version=draft.status,
            )
        )
        db.commit()
    except OutreachConflictError:
        raise
    except OutreachDraftNotFoundError:
        raise
    except IntegrityError as exc:
        db.rollback()
        raise OutreachConflictError(
            code="CONCURRENT_DRAFT_CONFLICT",
            detail="Draft was modified concurrently; reload and retry with the latest version.",
            status_code=409,
        ) from exc

    db.expire_all()
    updated = db.get(OutreachDraft, draft_id)
    assert updated is not None
    return _to_draft_response(db, updated)


def _transition_draft_status(
    db: Session,
    draft_id: str,
    target_status: OutreachDraftStatus,
) -> OutreachDraftResponse:
    draft = db.get(OutreachDraft, draft_id)
    if draft is None:
        raise OutreachDraftNotFoundError()

    allowed = _ALLOWED_TRANSITIONS.get(draft.status, set())
    if target_status not in allowed:
        raise OutreachConflictError(
            code="INVALID_STATUS_TRANSITION",
            detail=f"Cannot transition outreach draft from '{draft.status}' to '{target_status}'.",
            status_code=409,
        )

    now = datetime.now(UTC)
    current_status = draft.status
    current_version = draft.version
    next_version = current_version + 1
    values: dict[str, object] = {
        "status": target_status,
        "version": next_version,
        "updated_at": now,
    }
    if target_status == "reviewed":
        values["reviewed_at"] = now
    elif target_status == "approved":
        if draft.reviewed_at is None:
            values["reviewed_at"] = now
        values["approved_at"] = now
    elif target_status == "archived":
        values["archived_at"] = now

    try:
        res = db.execute(
            update(OutreachDraft)
            .where(
                OutreachDraft.id == draft_id,
                OutreachDraft.status == current_status,
                OutreachDraft.version == current_version,
            )
            .values(**values)
        )
        if res.rowcount != 1:
            db.rollback()
            raise OutreachConflictError(
                code="CONCURRENT_DRAFT_CONFLICT",
                detail="Draft status or version changed concurrently; reload and retry.",
                status_code=409,
            )

        db.add(
            OutreachDraftVersion(
                outreach_draft_id=draft_id,
                version=next_version,
                subject=draft.subject,
                body=draft.body,
                change_type="status_change",
                status_at_version=target_status,
            )
        )
        db.commit()
    except OutreachConflictError:
        raise
    except IntegrityError as exc:
        db.rollback()
        raise OutreachConflictError(
            code="CONCURRENT_DRAFT_CONFLICT",
            detail="Draft status or version changed concurrently; reload and retry.",
            status_code=409,
        ) from exc

    db.expire_all()
    updated = db.get(OutreachDraft, draft_id)
    assert updated is not None
    return _to_draft_response(db, updated)


def review_outreach_draft(db: Session, draft_id: str) -> OutreachDraftResponse:
    return _transition_draft_status(db, draft_id, "reviewed")


def approve_outreach_draft(db: Session, draft_id: str) -> OutreachDraftResponse:
    return _transition_draft_status(db, draft_id, "approved")


def archive_outreach_draft(db: Session, draft_id: str) -> OutreachDraftResponse:
    return _transition_draft_status(db, draft_id, "archived")


def get_outreach_draft_evidence(db: Session, draft_id: str) -> OutreachDraftEvidenceListResponse:
    draft = db.get(OutreachDraft, draft_id)
    if draft is None:
        raise OutreachDraftNotFoundError()

    rows = list(
        db.scalars(
            select(OutreachDraftEvidence)
            .where(OutreachDraftEvidence.outreach_draft_id == draft_id)
            .order_by(OutreachDraftEvidence.created_at.asc())
        ).all()
    )
    items: list[OutreachDraftEvidenceItemResponse] = []
    for row in rows:
        src = db.get(SourceEvidence, row.source_evidence_id) if row.source_evidence_id else None
        items.append(
            OutreachDraftEvidenceItemResponse(
                id=row.id,
                outreach_draft_id=row.outreach_draft_id,
                source_evidence_id=row.source_evidence_id,
                company_id=row.company_id,
                claim_category=row.claim_category,  # type: ignore[arg-type]
                claim_text=row.claim_text,
                verification_status=row.verification_status,  # type: ignore[arg-type]
                support_status=row.support_status,  # type: ignore[arg-type]
                requires_review=row.requires_review,
                source_url=src.source_url if src else None,
                source_title=src.source_title if src else None,
                excerpt=src.excerpt if src else None,
                publication_date=src.publication_date if src else None,
                created_at=row.created_at,
            )
        )
    return OutreachDraftEvidenceListResponse(outreach_draft_id=draft_id, items=items)


def get_outreach_draft_versions(db: Session, draft_id: str) -> OutreachDraftVersionListResponse:
    draft = db.get(OutreachDraft, draft_id)
    if draft is None:
        raise OutreachDraftNotFoundError()

    rows = list(
        db.scalars(
            select(OutreachDraftVersion)
            .where(OutreachDraftVersion.outreach_draft_id == draft_id)
            .order_by(OutreachDraftVersion.version.asc())
        ).all()
    )
    return OutreachDraftVersionListResponse(
        outreach_draft_id=draft_id,
        current_version=draft.version,
        items=[
            OutreachDraftVersionResponse(
                id=row.id,
                outreach_draft_id=row.outreach_draft_id,
                version=row.version,
                subject=row.subject,
                body=row.body,
                change_type=row.change_type,  # type: ignore[arg-type]
                status_at_version=row.status_at_version,  # type: ignore[arg-type]
                created_at=row.created_at,
            )
            for row in rows
        ],
    )
