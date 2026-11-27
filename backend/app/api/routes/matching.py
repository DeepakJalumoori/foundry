from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.schemas.m5 import (
    MatchDetailResponse,
    MatchEvidenceListResponse,
    MatchingRunCreateRequest,
    MatchingRunResponse,
    MatchResultsListResponse,
)
from app.schemas.run import ErrorResponse
from app.services.matching_service import (
    get_match_detail,
    get_match_evidence,
    get_matching_run,
    list_matching_run_results,
    start_matching_run,
)

router = APIRouter(tags=["matching"])


@router.post(
    "/matching-runs",
    response_model=MatchingRunResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        404: {"model": ErrorResponse},
        409: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
        502: {"model": ErrorResponse},
        503: {"model": ErrorResponse},
    },
)
def create_matching_run(
    payload: MatchingRunCreateRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> MatchingRunResponse:
    """Start and execute an M5 candidate-company matching workflow."""
    return start_matching_run(db, settings, payload)


@router.get(
    "/matching-runs/{run_id}",
    response_model=MatchingRunResponse,
    responses={404: {"model": ErrorResponse}},
)
def retrieve_matching_run(
    run_id: str,
    db: Session = Depends(get_db),
) -> MatchingRunResponse:
    """Retrieve matching run status and summary."""
    return get_matching_run(db, run_id)


@router.get(
    "/matching-runs/{run_id}/results",
    response_model=MatchResultsListResponse,
    responses={404: {"model": ErrorResponse}},
)
def retrieve_matching_run_results(
    run_id: str,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> MatchResultsListResponse:
    """Retrieve paginated ranked match results for a matching run."""
    return list_matching_run_results(db, run_id, limit=limit, offset=offset)


@router.get(
    "/matches/{match_id}",
    response_model=MatchDetailResponse,
    responses={404: {"model": ErrorResponse}},
)
def retrieve_match_detail(
    match_id: str,
    db: Session = Depends(get_db),
) -> MatchDetailResponse:
    """Retrieve a complete individual candidate-company match assessment."""
    return get_match_detail(db, match_id)


@router.get(
    "/matches/{match_id}/evidence",
    response_model=MatchEvidenceListResponse,
    responses={404: {"model": ErrorResponse}},
)
def retrieve_match_evidence(
    match_id: str,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> MatchEvidenceListResponse:
    """Retrieve supporting retrieved evidence and source references for a match."""
    return get_match_evidence(db, match_id, limit=limit, offset=offset)
