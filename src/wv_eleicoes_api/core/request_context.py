"""Request-scoped correlation identifier support."""

from contextvars import ContextVar, Token
from uuid import UUID, uuid4

REQUEST_ID_HEADER = "X-Request-ID"
_MAX_REQUEST_ID_LENGTH = 128
_request_id: ContextVar[str] = ContextVar("request_id", default="-")


def current_request_id() -> str:
    """Return the request ID visible to the current execution context."""

    return _request_id.get()


def bind_request_id(value: str) -> Token[str]:
    """Bind a request ID and return the token required to restore the context."""

    return _request_id.set(value)


def reset_request_id(token: Token[str]) -> None:
    """Restore the previous request ID context."""

    _request_id.reset(token)


def resolve_request_id(candidate: str | None) -> str:
    """Preserve a safe incoming ID or generate a canonical UUID4."""

    if candidate:
        stripped = candidate.strip()
        if stripped and len(stripped) <= _MAX_REQUEST_ID_LENGTH and _is_safe_request_id(stripped):
            return stripped
    return str(uuid4())


def _is_safe_request_id(value: str) -> bool:
    if any(ord(character) < 33 or ord(character) > 126 for character in value):
        return False
    try:
        UUID(value)
    except ValueError:
        return all(character.isalnum() or character in "-_.:/" for character in value)
    return True
