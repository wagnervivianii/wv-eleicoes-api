"""Minimal logging configuration with request correlation."""

import logging

from wv_eleicoes_api.core.request_context import current_request_id


class RequestIdFilter(logging.Filter):
    """Attach the current request ID to every application log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = current_request_id()
        return True


def configure_logging(level: str) -> None:
    """Configure deterministic process logging without serializing settings or secrets."""

    handler = logging.StreamHandler()
    handler.addFilter(RequestIdFilter())
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s %(levelname)s %(name)s request_id=%(request_id)s %(message)s"
        )
    )

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)
