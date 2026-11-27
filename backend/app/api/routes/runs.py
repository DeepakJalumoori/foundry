from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.schemas.run import ErrorResponse, RunResponse
from app.services.run_service import create_research_run, get_research_run, to_run_response

router = APIRouter(prefix="/runs", tags=["runs"])


@router.post(
    "",
    response_model=RunResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        413: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
    },
)
async def create_run(
    linkedin_url: Annotated[str | None, Form()] = None,
    resume_file: Annotated[UploadFile | None, File()] = None,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> RunResponse:
    """Submit either a LinkedIn URL or a PDF resume to initialize a pending research run."""
    run = await create_research_run(
        db,
        settings,
        linkedin_url=linkedin_url,
        resume_file=resume_file,
    )
    return to_run_response(run)


@router.get(
    "/{run_id}",
    response_model=RunResponse,
    responses={404: {"model": ErrorResponse}},
)
def get_run(
    run_id: str,
    db: Session = Depends(get_db),
) -> RunResponse:
    """Retrieve a research run by its identifier."""
    run = get_research_run(db, run_id)
    return to_run_response(run)
