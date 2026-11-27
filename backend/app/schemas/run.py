from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


InputSource = Literal["linkedin_url", "resume_pdf"]
RunStatus = Literal["pending", "processing", "completed", "failed"]


class CandidateResponse(BaseModel):
    """Public representation of a candidate input record."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    input_source: InputSource
    linkedin_url: str | None = None
    resume_filename: str | None = None
    resume_size_bytes: int | None = None
    created_at: datetime


class RunErrorResponse(BaseModel):
    """Structured error information on a failed research run."""

    code: str | None = None
    message: str | None = None


class RunResponse(BaseModel):
    """Public representation of a research run."""

    run_id: str
    status: RunStatus
    candidate: CandidateResponse
    profile_extraction_status: str | None = None
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error: RunErrorResponse | None = None


class ErrorResponse(BaseModel):
    """Standard API error envelope."""

    code: str
    detail: str
