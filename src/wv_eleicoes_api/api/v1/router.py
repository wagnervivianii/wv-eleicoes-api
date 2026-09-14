"""Root contract for API version 1."""

from fastapi import APIRouter
from pydantic import BaseModel

from wv_eleicoes_api import __version__

router = APIRouter(tags=["api"])


class ApiRootResponse(BaseModel):
    name: str
    version: str
    status: str


@router.get("", response_model=ApiRootResponse)
def api_root() -> ApiRootResponse:
    """Expose the stable versioned API entry point."""

    return ApiRootResponse(name="wv-eleicoes-api", version=__version__, status="ok")
