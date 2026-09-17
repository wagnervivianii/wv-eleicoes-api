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

## Profile 360 v1

`GET /api/v1/people/{person_id}/profile` exposes the first public person-centered read model.

The endpoint reads:

- `core.person` for the stable internal political-person identity;
- public rows from `core.person_external_identifier`;
- `analytics.candidate` for published candidacy data linked through the scoped
  TSE `candidacy_sequence`.

The API never reads CPF, voter-registration data, `raw.*` or `audit.*` for this endpoint.
The TSE candidacy sequence remains a candidacy identifier, not the identity of the person.

## Electoral history v1

`GET /api/v1/people/{person_id}/electoral-history` exposes the candidacy timeline for one
stable political person without requiring the frontend to consume the complete Profile 360.

The contract returns `person_id` plus published candidacies ordered from the newest election
to the oldest. Each candidacy preserves election, round, UF, electoral unit, office, ballot,
party and candidacy status fields from the approved longitudinal `analytics.candidate` read
model.

A person that exists but has no published candidacies receives `200` with an empty
`candidacies` list. A nonexistent person receives `404`, and non-positive identifiers receive
`422` from the path contract.

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
- `GET /api/v1/people/{person_id}/profile` — public Profile 360 v1.
- `GET /api/v1/people/{person_id}/electoral-history` — public longitudinal candidacy history.

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

The API must use the existing least-privilege role `wv_eleicoes_api`.
In addition to PostgreSQL ACLs,
the connection requests `default_transaction_read_only=on` and a bounded
`statement_timeout`.
Application code in this repository must not run migrations or write to RAW/audit layers.

## Declared assets v1

The declared-assets module exposes only TSE-declared values already published through the
approved CORE/ANALYTICS contracts. Monetary fields use Python `Decimal`; source signs are
preserved without `ABS`, zero clamps or API-side normalization.

Endpoints:

- `GET /api/v1/people/{person_id}/assets` — candidacy-scoped declaration history;
- `GET /api/v1/people/{person_id}/assets/evolution` — direct projection of
  `analytics.person_asset_evolution`;
- `GET /api/v1/people/{person_id}/assets/declarations/{election_year}/{election_code}/{candidacy_sequence}`
  — one declaration with summary, type composition and individual items.

The declaration-detail key intentionally includes election year, TSE election code and
candidacy sequence because a stable person can have multiple candidacy-scoped snapshots in
the same year. The assets module reads only `core.person`, `core.candidate_asset`,
`analytics.candidate_asset_summary`, `analytics.candidate_asset_type` and
`analytics.person_asset_evolution`.
