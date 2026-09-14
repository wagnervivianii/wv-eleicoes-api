"""FastAPI application factory."""

from fastapi import FastAPI

from wv_eleicoes_api import __version__
from wv_eleicoes_api.api.v1.router import router as api_v1_router
from wv_eleicoes_api.config import Settings, get_settings
from wv_eleicoes_api.core.logging import configure_logging
from wv_eleicoes_api.core.middleware import RequestContextMiddleware
from wv_eleicoes_api.health.router import router as health_router


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create the WV Eleicoes API application."""

    resolved = settings or get_settings()
    configure_logging(resolved.log_level)

    app = FastAPI(
        title=resolved.app_name,
        version=__version__,
        docs_url="/docs" if resolved.environment != "production" else None,
        redoc_url=None,
    )
    app.add_middleware(RequestContextMiddleware)
    app.include_router(health_router)
    app.include_router(api_v1_router, prefix=resolved.api_prefix)
    return app
