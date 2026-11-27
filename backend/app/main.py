from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import health_router, runs_router
from app.core.config import get_settings
from app.schemas.run import ErrorResponse
from app.services.file_storage import ResumeValidationError
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

    app.include_router(health_router, prefix="/api")
    app.include_router(runs_router, prefix="/api")

    return app


app = create_app()
