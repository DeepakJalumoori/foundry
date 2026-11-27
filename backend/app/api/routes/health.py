from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.schemas.health import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health_check(
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> HealthResponse | JSONResponse:
    """Check service and SQLite database connectivity."""
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError:
        payload = HealthResponse(
            status="degraded",
            service="foundry-backend",
            version=settings.app_version,
            database="unavailable",
        )
        return JSONResponse(status_code=503, content=payload.model_dump())

    return HealthResponse(
        status="ok",
        service="foundry-backend",
        version=settings.app_version,
        database="ok",
    )
