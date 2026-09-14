# WV Eleicoes API

FastAPI read-only service for the public WV Eleicoes platform.

This repository is intentionally separated from `wv-eleicoes-data` and `wv-eleicoes-web`.
The data repository owns ingestion, migrations and analytical publication. This API consumes
only approved read models through the PostgreSQL role `wv_eleicoes_api`.

## Foundation scope

- FastAPI application factory;
- environment configuration with the `WV_ELEICOES_API_` prefix;
- PostgreSQL connection configured as read-only at the session level;
- liveness and readiness endpoints;
- versioned `/api/v1` root contract;
- request ID propagation/generation;
- basic request logging without secrets;
- pytest, Ruff and MyPy configuration.

No candidate/person business endpoint is implemented in this first unit. Identity (`core.person`)
and Profile 360 belong to the next functional units in the same chat contract.

## Python

Python 3.12+.

Create and activate a virtual environment, then install the project with development dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -e '.[dev]'
```

Copy `.env.example` to `.env` and provide the real read-only database URL. Never commit `.env`.

## Run locally

```bash
uvicorn wv_eleicoes_api.main:app --reload --host 127.0.0.1 --port 8000
```

## Endpoints

- `GET /health/live` — process liveness; does not require PostgreSQL.
- `GET /health/ready` — readiness; checks a read-only PostgreSQL connection with `SELECT 1`.
- `GET /api/v1` — versioned API root.

Every HTTP response receives `X-Request-ID`. A valid incoming `X-Request-ID` is preserved; otherwise
the API generates a UUID4 request ID.

## Quality gates

```bash
python -m compileall -q src tests
python -m ruff check .
python -m mypy src/wv_eleicoes_api
python -m pytest
```

## Database safety

The API must use the existing least-privilege role `wv_eleicoes_api`. In addition to PostgreSQL ACLs,
the connection requests `default_transaction_read_only=on` and a bounded `statement_timeout`.
Application code in this repository must not run migrations or write to RAW/audit layers.
