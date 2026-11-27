from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.candidate_profile import CandidateProfileResponse
from app.schemas.run import ErrorResponse
from app.services.candidate_profile_service import get_candidate_profile

router = APIRouter(prefix="/candidates", tags=["candidates"])


@router.get(
    "/{candidate_id}/profile",
    response_model=CandidateProfileResponse,
    responses={404: {"model": ErrorResponse}},
)
def retrieve_candidate_profile(
    candidate_id: str,
    db: Session = Depends(get_db),
) -> CandidateProfileResponse:
    """Retrieve the structured, evidence-backed profile for a candidate."""
    return get_candidate_profile(db, candidate_id)
