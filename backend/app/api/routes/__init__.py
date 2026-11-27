from app.api.routes.candidates import router as candidates_router
from app.api.routes.companies import router as companies_router
from app.api.routes.discovery import router as discovery_router
from app.api.routes.health import router as health_router
from app.api.routes.matching import router as matching_router
from app.api.routes.runs import router as runs_router

__all__ = [
    "candidates_router",
    "companies_router",
    "discovery_router",
    "health_router",
    "matching_router",
    "runs_router",
]
