"""SQLAlchemy engine configured for read-only API access."""

from functools import lru_cache

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import SQLAlchemyError

from wv_eleicoes_api.config import Settings, get_settings


def build_postgres_options(settings: Settings) -> str:
    """Return libpq options enforcing read-only transactions and bounded statements."""

    return (
        "-c default_transaction_read_only=on "
        f"-c statement_timeout={settings.database_statement_timeout_ms}"
    )


def validate_database_url(database_url: str) -> None:
    """Reject non-PostgreSQL database URLs for this service."""

    backend = make_url(database_url).get_backend_name()
    if backend != "postgresql":
        raise ValueError("WV Eleicoes API requires a PostgreSQL database URL")


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    """Build the process-wide SQLAlchemy engine lazily."""

    settings = get_settings()
    if not settings.database_url:
        raise RuntimeError("WV_ELEICOES_API_DATABASE_URL is not configured")

    validate_database_url(settings.database_url)
    return create_engine(
        settings.database_url,
        pool_pre_ping=True,
        pool_size=settings.database_pool_size,
        max_overflow=settings.database_max_overflow,
        pool_timeout=settings.database_pool_timeout_seconds,
        connect_args={"options": build_postgres_options(settings)},
    )


def database_is_ready() -> bool:
    """Return True only when a read-only PostgreSQL connection can execute SELECT 1."""

    try:
        with get_engine().connect() as connection:
            result: object = connection.scalar(text("SELECT 1"))
            return result == 1
    except (RuntimeError, ValueError, SQLAlchemyError):
        return False
