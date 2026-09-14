import pytest

from wv_eleicoes_api.config import Settings
from wv_eleicoes_api.db import engine as engine_module
from wv_eleicoes_api.db.engine import (
    build_postgres_options,
    database_is_ready,
    validate_database_url,
)


def test_postgres_options_enforce_read_only_and_timeout() -> None:
    settings = Settings(database_statement_timeout_ms=3210, _env_file=None)
    options = build_postgres_options(settings)
    assert "default_transaction_read_only=on" in options
    assert "statement_timeout=3210" in options


def test_non_postgresql_url_is_rejected() -> None:
    with pytest.raises(ValueError, match="PostgreSQL"):
        validate_database_url("sqlite:///test.db")


class _FakeConnection:
    def __init__(self, value: object) -> None:
        self.value = value

    def __enter__(self) -> "_FakeConnection":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def scalar(self, statement: object) -> object:
        del statement
        return self.value


class _FakeEngine:
    def __init__(self, value: object) -> None:
        self.value = value

    def connect(self) -> _FakeConnection:
        return _FakeConnection(self.value)


def test_database_is_ready_returns_true_for_select_one(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(engine_module, "get_engine", lambda: _FakeEngine(1))
    assert database_is_ready() is True


def test_database_is_ready_returns_false_for_unexpected_scalar(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(engine_module, "get_engine", lambda: _FakeEngine(0))
    assert database_is_ready() is False
