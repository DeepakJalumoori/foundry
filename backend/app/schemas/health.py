from typing import Literal

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Health check response contract."""

    status: Literal["ok", "degraded"]
    service: str
    version: str
    database: Literal["ok", "unavailable"]
