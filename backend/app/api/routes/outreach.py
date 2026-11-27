from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.schemas.m6 import (
    OutreachDraftCreateRequest,
    OutreachDraftEvidenceListResponse,
    OutreachDraftListResponse,
    OutreachDraftResponse,
    OutreachDraftStatus,
    OutreachDraftUpdateRequest,
    OutreachDraftVersionListResponse,
)
from app.schemas.run import ErrorResponse
from app.services.outreach_service import (
    approve_outreach_draft,
    archive_outreach_draft,
    generate_outreach_draft,
    get_outreach_draft,
    get_outreach_draft_evidence,
    get_outreach_draft_versions,
    list_outreach_drafts,
    review_outreach_draft,
    update_outreach_draft,
)

router = APIRouter(tags=["outreach"])


@router.post(
    "/outreach-drafts",
    response_model=OutreachDraftResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        404: {"model": ErrorResponse},
        409: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
        502: {"model": ErrorResponse},
        503: {"model": ErrorResponse},
        504: {"model": ErrorResponse},
    },
)
def create_outreach_draft(
    payload: OutreachDraftCreateRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> OutreachDraftResponse:
    """Generate an evidence-grounded founder outreach draft."""
    return generate_outreach_draft(db, settings, payload)


@router.get(
    "/outreach-drafts",
    response_model=OutreachDraftListResponse,
)
def get_outreach_drafts(
    candidate_id: str | None = Query(default=None),
    company_id: str | None = Query(default=None),
    matching_run_id: str | None = Query(default=None),
    status_filter: OutreachDraftStatus | None = Query(default=None, alias="status"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> OutreachDraftListResponse:
    """List persisted outreach drafts with optional filters and pagination."""
    return list_outreach_drafts(
        db,
        candidate_id=candidate_id,
        company_id=company_id,
        matching_run_id=matching_run_id,
        status_filter=status_filter,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/outreach-drafts/{draft_id}",
    response_model=OutreachDraftResponse,
    responses={404: {"model": ErrorResponse}},
)
def retrieve_outreach_draft(
    draft_id: str,
    db: Session = Depends(get_db),
) -> OutreachDraftResponse:
    """Retrieve a single outreach draft by ID."""
    return get_outreach_draft(db, draft_id)


@router.patch(
    "/outreach-drafts/{draft_id}",
    response_model=OutreachDraftResponse,
    responses={404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
)
def patch_outreach_draft(
    draft_id: str,
    payload: OutreachDraftUpdateRequest,
    db: Session = Depends(get_db),
) -> OutreachDraftResponse:
    """Edit subject and/or body of an outreach draft without altering provenance."""
    return update_outreach_draft(db, draft_id, payload)


@router.post(
    "/outreach-drafts/{draft_id}/review",
    response_model=OutreachDraftResponse,
    responses={404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
)
def mark_outreach_draft_reviewed(
    draft_id: str,
    db: Session = Depends(get_db),
) -> OutreachDraftResponse:
    """Mark an outreach draft as reviewed."""
    return review_outreach_draft(db, draft_id)


@router.post(
    "/outreach-drafts/{draft_id}/approve",
    response_model=OutreachDraftResponse,
    responses={404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
)
def mark_outreach_draft_approved(
    draft_id: str,
    db: Session = Depends(get_db),
) -> OutreachDraftResponse:
    """Approve an outreach draft for manual candidate use (never sends email)."""
    return approve_outreach_draft(db, draft_id)


@router.post(
    "/outreach-drafts/{draft_id}/archive",
    response_model=OutreachDraftResponse,
    responses={404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
)
def mark_outreach_draft_archived(
    draft_id: str,
    db: Session = Depends(get_db),
) -> OutreachDraftResponse:
    """Archive an unwanted outreach draft."""
    return archive_outreach_draft(db, draft_id)


@router.get(
    "/outreach-drafts/{draft_id}/evidence",
    response_model=OutreachDraftEvidenceListResponse,
    responses={404: {"model": ErrorResponse}},
)
def retrieve_outreach_draft_evidence(
    draft_id: str,
    db: Session = Depends(get_db),
) -> OutreachDraftEvidenceListResponse:
    """Retrieve claim-level evidence grounding and SourceEvidence provenance for a draft."""
    return get_outreach_draft_evidence(db, draft_id)


@router.get(
    "/outreach-drafts/{draft_id}/versions",
    response_model=OutreachDraftVersionListResponse,
    responses={404: {"model": ErrorResponse}},
)
def retrieve_outreach_draft_versions(
    draft_id: str,
    db: Session = Depends(get_db),
) -> OutreachDraftVersionListResponse:
    """Retrieve version history for an outreach draft."""
    return get_outreach_draft_versions(db, draft_id)
