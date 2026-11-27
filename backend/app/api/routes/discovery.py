from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.schemas.m4 import DiscoveryCriteriaRequest, DiscoveryRunResponse
from app.schemas.run import ErrorResponse
from app.services.discovery_orchestrator import get_discovery_run, run_startup_discovery_pipeline

router = APIRouter(prefix="/discovery", tags=["discovery"])


@router.post(
    "",
    response_model=DiscoveryRunResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        404: {"model": ErrorResponse},
        502: {"model": ErrorResponse},
        503: {"model": ErrorResponse},
    },
)
def start_discovery(
    payload: DiscoveryCriteriaRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> DiscoveryRunResponse:
    """Discover and research startups for a candidate with an extracted profile."""
    return run_startup_discovery_pipeline(db, settings, payload)


@router.get(
    "/{run_id}",
    response_model=DiscoveryRunResponse,
    responses={404: {"model": ErrorResponse}},
)
def retrieve_discovery_run(
    run_id: str,
    db: Session = Depends(get_db),
) -> DiscoveryRunResponse:
    """Retrieve the status and summary of a startup discovery run."""
    return get_discovery_run(db, run_id)
