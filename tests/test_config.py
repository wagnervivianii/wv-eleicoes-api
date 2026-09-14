import pytest
from pydantic import ValidationError

from wv_eleicoes_api.config import Settings


def test_settings_use_api_prefix_and_defaults() -> None:
    settings = Settings(_env_file=None)
    assert settings.api_prefix == "/api/v1"
    assert settings.database_url is None


def test_invalid_api_prefix_is_rejected() -> None:
    with pytest.raises(ValidationError):
        Settings(api_prefix="api/v1", _env_file=None)
