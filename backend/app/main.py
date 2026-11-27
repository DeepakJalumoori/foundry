from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import candidates_router, health_router, runs_router
from app.core.config import get_settings
from app.providers.llm import LLMProviderError
from app.schemas.run import ErrorResponse
from app.services.candidate_profile_service import (
    CandidateNotFoundError,
    DuplicateProcessingError,
    ProfileNotFoundError,
    UnsupportedInputSourceError,
)
from app.services.file_storage import ResumeValidationError
from app.services.resume_extractor import ResumeExtractionError
from app.services.run_service import InputValidationError, RunNotFoundError


def create_app() -> FastAPI:
    """Construct and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    @app.exception_handler(InputValidationError)
    async def _handle_input_validation(_request: Request, exc: InputValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(code=exc.code, detail=exc.detail).model_dump(),
        )

    @app.exception_handler(ResumeValidationError)
    async def _handle_resume_validation(_request: Request, exc: ResumeValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(code=exc.code, detail=exc.detail).model_dump(),
        )

    @app.exception_handler(RunNotFoundError)
    async def _handle_run_not_found(_request: Request, exc: RunNotFoundError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(code=exc.code, detail=exc.detail).model_dump(),
        )

    @app.exception_handler(CandidateNotFoundError)
    async def _handle_candidate_not_found(_request: Request, exc: CandidateNotFoundError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(code=exc.code, detail=exc.detail).model_dump(),
        )

    @app.exception_handler(ProfileNotFoundError)
    async def _handle_profile_not_found(_request: Request, exc: ProfileNotFoundError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(code=exc.code, detail=exc.detail).model_dump(),
        )

    @app.exception_handler(UnsupportedInputSourceError)
    async def _handle_unsupported_input_source(
        _request: Request,
        exc: UnsupportedInputSourceError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(code=exc.code, detail=exc.detail).model_dump(),
        )

    @app.exception_handler(DuplicateProcessingError)
    async def _handle_duplicate_processing(
        _request: Request,
        exc: DuplicateProcessingError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(code=exc.code, detail=exc.detail).model_dump(),
        )

    @app.exception_handler(ResumeExtractionError)
    async def _handle_resume_extraction(_request: Request, exc: ResumeExtractionError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(code=exc.code, detail=exc.detail).model_dump(),
        )

    @app.exception_handler(LLMProviderError)
    async def _handle_llm_provider(_request: Request, exc: LLMProviderError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(code=exc.code, detail=exc.detail).model_dump(),
        )

    app.include_router(health_router, prefix="/api")
    app.include_router(runs_router, prefix="/api")
    app.include_router(candidates_router, prefix="/api")

    return app


app = create_app()
