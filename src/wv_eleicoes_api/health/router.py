"""Liveness and readiness routes."""

from typing import Literal

from fastapi import APIRouter, Response, status
from pydantic import BaseModel

from wv_eleicoes_api.db.engine import database_is_ready

router = APIRouter(prefix="/health", tags=["health"])


class HealthResponse(BaseModel):
    status: Literal["ok", "not_ready"]


@router.get("/live", response_model=HealthResponse)
def liveness() -> HealthResponse:
    """Report process liveness without depending on external services."""

    return HealthResponse(status="ok")


@router.get("/ready", response_model=HealthResponse)
def readiness(response: Response) -> HealthResponse:
    """Report whether the API can reach PostgreSQL through its read-only connection."""

    if database_is_ready():
        return HealthResponse(status="ok")
    response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return HealthResponse(status="not_ready")
