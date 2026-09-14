"""HTTP middleware used by the API foundation."""

import logging
import time
from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from wv_eleicoes_api.core.request_context import (
    REQUEST_ID_HEADER,
    bind_request_id,
    reset_request_id,
    resolve_request_id,
)

logger = logging.getLogger("wv_eleicoes_api.http")


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Correlate requests and emit one bounded access log entry per request."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        request_id = resolve_request_id(request.headers.get(REQUEST_ID_HEADER))
        token = bind_request_id(request_id)
        started = time.perf_counter()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            response.headers[REQUEST_ID_HEADER] = request_id
            return response
        finally:
            elapsed_ms = (time.perf_counter() - started) * 1000
            logger.info(
                "request method=%s path=%s status=%d duration_ms=%.2f",
                request.method,
                request.url.path,
                status_code,
                elapsed_ms,
            )
            reset_request_id(token)
