"""Read-only PostgreSQL queries for public political profiles."""

from sqlalchemy import text
from sqlalchemy.engine import RowMapping

from wv_eleicoes_api.api.v1.profiles.schemas import (
    CandidacySummary,
    ElectoralHistoryResponse,
    ExternalIdentifierSummary,
    OfficeSummary,
    PartySummary,
    PersonProfileResponse,
    PersonSummary,
)
from wv_eleicoes_api.db.engine import get_engine

PERSON_QUERY = text(
    """
    SELECT
        id,
        legal_name,
        display_name,
        social_name,
        birth_date,
        birth_uf
    FROM core.person
    WHERE id = :person_id
    """
)

PERSON_EXISTS_QUERY = text(
    """
    SELECT id
    FROM core.person
    WHERE id = :person_id
    """
)

PUBLIC_IDENTIFIERS_QUERY = text(
    """
    SELECT
        source_system,
        identifier_type,
        identifier_value,
        scope_key
    FROM core.person_external_identifier
    WHERE person_id = :person_id
      AND is_public = true
    ORDER BY source_system, identifier_type, scope_key, identifier_value
    """
)

CANDIDACIES_QUERY = text(
    """
    SELECT
        candidate.election_year,
        candidate.election_code,
        candidate.election_round,
        candidate.uf,
        candidate.electoral_unit,
        candidate.electoral_unit_name,
        candidate.office_code,
        candidate.office_name,
        candidate.candidacy_sequence,
        candidate.ballot_number,
        candidate.ballot_name,
        candidate.party_number,
        candidate.party_acronym,
        candidate.party_name,
        candidate.status_code,
        candidate.status_name
    FROM core.person_external_identifier AS identifier
    JOIN analytics.candidate AS candidate
      ON identifier.source_system = 'TSE'
     AND identifier.identifier_type = 'candidacy_sequence'
     AND identifier.identifier_value = candidate.candidacy_sequence
     AND identifier.scope_key =
         'election:' || candidate.election_year::text || ':' || candidate.election_code
    WHERE identifier.person_id = :person_id
      AND identifier.is_public = true
    ORDER BY
        candidate.election_year DESC,
        candidate.election_round DESC NULLS LAST,
        candidate.office_name,
        candidate.uf,
        candidate.candidacy_sequence
    """
)


def _person_from_row(row: RowMapping) -> PersonSummary:
    return PersonSummary.model_validate(dict(row))


def _identifier_from_row(row: RowMapping) -> ExternalIdentifierSummary:
    return ExternalIdentifierSummary.model_validate(dict(row))


def _candidacy_from_row(row: RowMapping) -> CandidacySummary:
    return CandidacySummary(
        election_year=row["election_year"],
        election_code=row["election_code"],
        election_round=row["election_round"],
        uf=row["uf"],
        electoral_unit=row["electoral_unit"],
        electoral_unit_name=row["electoral_unit_name"],
        candidacy_sequence=row["candidacy_sequence"],
        ballot_number=row["ballot_number"],
        ballot_name=row["ballot_name"],
        office=OfficeSummary(
            code=row["office_code"],
            name=row["office_name"],
        ),
        party=PartySummary(
            number=row["party_number"],
            acronym=row["party_acronym"],
            name=row["party_name"],
        ),
        status_code=row["status_code"],
        status_name=row["status_name"],
    )


def fetch_person_profile(person_id: int) -> PersonProfileResponse | None:
    """Fetch one public Profile 360 using only approved read models."""

    with get_engine().connect() as connection:
        person_row = (
            connection.execute(PERSON_QUERY, {"person_id": person_id})
            .mappings()
            .one_or_none()
        )
        if person_row is None:
            return None

        identifier_rows = connection.execute(
            PUBLIC_IDENTIFIERS_QUERY,
            {"person_id": person_id},
        ).mappings()
        candidacy_rows = connection.execute(
            CANDIDACIES_QUERY,
            {"person_id": person_id},
        ).mappings()

        return PersonProfileResponse(
            person=_person_from_row(person_row),
            external_identifiers=[
                _identifier_from_row(row)
                for row in identifier_rows
            ],
            candidacies=[
                _candidacy_from_row(row)
                for row in candidacy_rows
            ],
        )


def fetch_electoral_history(person_id: int) -> ElectoralHistoryResponse | None:
    """Fetch the published candidacy timeline for one stable political person."""

    with get_engine().connect() as connection:
        existing_person_id = connection.scalar(
            PERSON_EXISTS_QUERY,
            {"person_id": person_id},
        )
        if existing_person_id is None:
            return None

        candidacy_rows = connection.execute(
            CANDIDACIES_QUERY,
            {"person_id": person_id},
        ).mappings()

        return ElectoralHistoryResponse(
            person_id=int(existing_person_id),
            candidacies=[
                _candidacy_from_row(row)
                for row in candidacy_rows
            ],
        )
