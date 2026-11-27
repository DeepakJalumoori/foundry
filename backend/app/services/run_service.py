from urllib.parse import urlsplit

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.research_run import ResearchRun
from app.repositories.run_repository import RunRepository
from app.schemas.run import CandidateResponse, RunErrorResponse, RunResponse
from app.services.file_storage import delete_stored_file, save_validated_pdf


class InputValidationError(Exception):
    """Raised when candidate input violates validation rules."""

    status_code: int = 422

    def __init__(self, code: str, detail: str) -> None:
        super().__init__(detail)
        self.code = code
        self.detail = detail


class RunNotFoundError(Exception):
    """Raised when a research run cannot be found."""

    status_code: int = 404
    code: str = "RUN_NOT_FOUND"
    detail: str = "Research run not found."


def validate_linkedin_url(raw_url: str) -> str:
    """Validate and normalize an HTTPS LinkedIn profile URL."""
    stripped = raw_url.strip()
    if not stripped:
        raise InputValidationError("EMPTY_LINKEDIN_URL", "LinkedIn URL cannot be empty.")

    try:
        parsed = urlsplit(stripped)
    except ValueError as exc:
        raise InputValidationError("INVALID_LINKEDIN_URL", "LinkedIn URL is malformed.") from exc

    if parsed.scheme.lower() != "https":
        raise InputValidationError(
            "INVALID_LINKEDIN_SCHEME",
            "LinkedIn URL must use https://.",
        )

    if parsed.username or parsed.password or parsed.port is not None:
        raise InputValidationError(
            "INVALID_LINKEDIN_URL",
            "LinkedIn URL must not include credentials or custom ports.",
        )

    hostname = (parsed.hostname or "").lower()
    if hostname != "linkedin.com" and not hostname.endswith(".linkedin.com"):
        raise InputValidationError(
            "INVALID_LINKEDIN_HOST",
            "URL host must be linkedin.com.",
        )

    path = parsed.path or ""
    if not path.startswith("/in/"):
        raise InputValidationError(
            "INVALID_LINKEDIN_PATH",
            "LinkedIn URL path must start with /in/.",
        )

    profile_slug = path[4:].strip("/")
    if not profile_slug:
        raise InputValidationError(
            "INVALID_LINKEDIN_PATH",
            "LinkedIn profile URL must include a non-empty profile identifier after /in/.",
        )

    normalized_path = f"/in/{profile_slug}"
    return f"https://{hostname}{normalized_path}"


async def create_research_run(
    db: Session,
    settings: Settings,
    *,
    linkedin_url: str | None,
    resume_file: UploadFile | None,
) -> ResearchRun:
    """Validate candidate input (XOR LinkedIn URL or PDF) and persist Candidate + ResearchRun."""
    has_url_field = linkedin_url is not None
    has_nonempty_url = bool(linkedin_url and linkedin_url.strip())
    has_file = resume_file is not None

    if has_nonempty_url and has_file:
        raise InputValidationError(
            "MULTIPLE_INPUT_METHODS",
            "Provide either a LinkedIn URL or a PDF resume, not both.",
        )

    if has_url_field and not has_nonempty_url and not has_file:
        raise InputValidationError(
            "EMPTY_LINKEDIN_URL",
            "LinkedIn URL cannot be empty.",
        )

    if has_url_field and not has_nonempty_url and has_file and linkedin_url != "":
        raise InputValidationError(
            "EMPTY_LINKEDIN_URL",
            "LinkedIn URL cannot be whitespace-only.",
        )

    if not has_nonempty_url and not has_file:
        raise InputValidationError(
            "MISSING_CANDIDATE_INPUT",
            "Provide either a LinkedIn URL or a PDF resume.",
        )

    if has_nonempty_url:
        assert linkedin_url is not None
        normalized_url = validate_linkedin_url(linkedin_url)
        return RunRepository.create_linkedin_candidate_and_run(db, normalized_url)

    assert resume_file is not None
    stored = await save_validated_pdf(
        resume_file,
        upload_dir=settings.upload_dir,
        max_size_bytes=settings.max_resume_size_bytes,
    )

    try:
        return RunRepository.create_resume_candidate_and_run(
            db,
            resume_filename=stored.original_filename,
            resume_content_type=stored.content_type,
            resume_size_bytes=stored.size_bytes,
            resume_storage_key=stored.storage_key,
        )
    except Exception:
        delete_stored_file(settings.upload_dir, stored.storage_key)
        raise


def get_research_run(db: Session, run_id: str) -> ResearchRun:
    """Fetch a ResearchRun by ID or raise RunNotFoundError."""
    run = RunRepository.get_run_by_id(db, run_id)
    if run is None:
        raise RunNotFoundError()
    return run


def to_run_response(run: ResearchRun) -> RunResponse:
    """Map ORM ResearchRun + Candidate to the public RunResponse schema."""
    error: RunErrorResponse | None = None
    if run.error_code is not None or run.error_message is not None:
        error = RunErrorResponse(code=run.error_code, message=run.error_message)

    return RunResponse(
        run_id=run.id,
        status=run.status,  # type: ignore[arg-type]
        candidate=CandidateResponse.model_validate(run.candidate),
        created_at=run.created_at,
        started_at=run.started_at,
        completed_at=run.completed_at,
        error=error,
    )
