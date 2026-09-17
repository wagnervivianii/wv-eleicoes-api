"""Read-only PostgreSQL queries for public declared-assets endpoints."""

from sqlalchemy import text
from sqlalchemy.engine import Connection, RowMapping

from wv_eleicoes_api.api.v1.assets.schemas import (
    AssetDeclarationDetailResponse,
    AssetDeclarationSummary,
    AssetEvolutionPoint,
    AssetEvolutionResponse,
    AssetHistoryResponse,
    AssetItem,
    AssetTypeComposition,
)
from wv_eleicoes_api.db.engine import get_engine

PERSON_EXISTS_QUERY = text(
    """
    SELECT id
    FROM core.person
    WHERE id = :person_id
    """
)

ASSET_DECLARATIONS_QUERY = text(
    """
    SELECT
        election_year,
        election_code,
        candidacy_sequence,
        asset_count,
        declared_value_count,
        missing_value_count,
        positive_value_count,
        zero_value_count,
        negative_value_count,
        declared_value_signed_total,
        declared_value_positive_total,
        declared_value_negative_total,
        has_negative_values,
        largest_declared_value,
        largest_asset_order,
        largest_asset_type_code,
        largest_asset_type_name,
        largest_asset_description,
        latest_asset_updated_at,
        source_snapshot_at
    FROM analytics.candidate_asset_summary
    WHERE person_id = :person_id
    ORDER BY election_year DESC, election_code DESC, candidacy_sequence DESC
    """
)

ASSET_EVOLUTION_QUERY = text(
    """
    SELECT
        election_year,
        candidacy_snapshot_count,
        election_count,
        election_code,
        candidacy_sequence,
        asset_count,
        declared_value_signed_total,
        has_negative_values,
        snapshot_status,
        previous_election_year,
        previous_candidacy_snapshot_count,
        previous_election_count,
        previous_election_code,
        previous_candidacy_sequence,
        previous_asset_count,
        previous_declared_value_signed_total,
        previous_has_negative_values,
        previous_snapshot_status,
        declared_value_nominal_change,
        comparison_status,
        declared_value_change_pct
    FROM analytics.person_asset_evolution
    WHERE person_id = :person_id
    ORDER BY election_year ASC
    """
)

ASSET_DECLARATION_SUMMARY_QUERY = text(
    """
    SELECT
        election_year,
        election_code,
        candidacy_sequence,
        asset_count,
        declared_value_count,
        missing_value_count,
        positive_value_count,
        zero_value_count,
        negative_value_count,
        declared_value_signed_total,
        declared_value_positive_total,
        declared_value_negative_total,
        has_negative_values,
        largest_declared_value,
        largest_asset_order,
        largest_asset_type_code,
        largest_asset_type_name,
        largest_asset_description,
        latest_asset_updated_at,
        source_snapshot_at
    FROM analytics.candidate_asset_summary
    WHERE person_id = :person_id
      AND election_year = :election_year
      AND election_code = :election_code
      AND candidacy_sequence = :candidacy_sequence
    """
)

ASSET_DECLARATION_TYPES_QUERY = text(
    """
    SELECT
        asset_type_code,
        asset_type_name,
        asset_count,
        declared_value_count,
        negative_value_count,
        declared_value_signed_total,
        declared_value_positive_total,
        declared_value_negative_total,
        largest_declared_value,
        item_share_pct,
        positive_value_share_pct
    FROM analytics.candidate_asset_type
    WHERE person_id = :person_id
      AND election_year = :election_year
      AND election_code = :election_code
      AND candidacy_sequence = :candidacy_sequence
    ORDER BY asset_count DESC, asset_type_name NULLS LAST, asset_type_code NULLS LAST
    """
)

ASSET_ITEMS_QUERY = text(
    """
    SELECT
        asset_order,
        asset_type_code,
        asset_type_name,
        asset_description,
        declared_value,
        declared_value_status,
        asset_updated_at
    FROM analytics.candidate_asset_item
    WHERE person_id = :person_id
      AND election_year = :election_year
      AND election_code = :election_code
      AND candidacy_sequence = :candidacy_sequence
    ORDER BY asset_order ASC
    """
)


def _person_exists(connection: Connection, person_id: int) -> bool:
    return connection.scalar(PERSON_EXISTS_QUERY, {"person_id": person_id}) is not None


def _summary_from_row(row: RowMapping) -> AssetDeclarationSummary:
    return AssetDeclarationSummary.model_validate(dict(row))


def _evolution_from_row(row: RowMapping) -> AssetEvolutionPoint:
    return AssetEvolutionPoint.model_validate(dict(row))


def _type_from_row(row: RowMapping) -> AssetTypeComposition:
    return AssetTypeComposition.model_validate(dict(row))


def _item_from_row(row: RowMapping) -> AssetItem:
    return AssetItem.model_validate(dict(row))


def fetch_asset_history(person_id: int) -> AssetHistoryResponse | None:
    """Return candidacy-scoped declared-assets summaries for one existing person."""

    with get_engine().connect() as connection:
        if not _person_exists(connection, person_id):
            return None

        rows = connection.execute(
            ASSET_DECLARATIONS_QUERY,
            {"person_id": person_id},
        ).mappings()
        return AssetHistoryResponse(
            person_id=person_id,
            declarations=[_summary_from_row(row) for row in rows],
        )


def fetch_asset_evolution(person_id: int) -> AssetEvolutionResponse | None:
    """Return the published annual evolution without recalculating analytical values."""

    with get_engine().connect() as connection:
        if not _person_exists(connection, person_id):
            return None

        rows = connection.execute(
            ASSET_EVOLUTION_QUERY,
            {"person_id": person_id},
        ).mappings()
        return AssetEvolutionResponse(
            person_id=person_id,
            evolution=[_evolution_from_row(row) for row in rows],
        )


def fetch_asset_declaration_detail(
    person_id: int,
    election_year: int,
    election_code: str,
    candidacy_sequence: str,
) -> tuple[bool, AssetDeclarationDetailResponse | None]:
    """Return person existence plus one candidacy-scoped declared-assets detail."""

    params = {
        "person_id": person_id,
        "election_year": election_year,
        "election_code": election_code,
        "candidacy_sequence": candidacy_sequence,
    }
    with get_engine().connect() as connection:
        if not _person_exists(connection, person_id):
            return False, None

        summary_row = connection.execute(
            ASSET_DECLARATION_SUMMARY_QUERY,
            params,
        ).mappings().one_or_none()
        if summary_row is None:
            return True, None

        type_rows = connection.execute(
            ASSET_DECLARATION_TYPES_QUERY,
            params,
        ).mappings()
        item_rows = connection.execute(
            ASSET_ITEMS_QUERY,
            params,
        ).mappings()
        return True, AssetDeclarationDetailResponse(
            summary=_summary_from_row(summary_row),
            composition=[_type_from_row(row) for row in type_rows],
            items=[_item_from_row(row) for row in item_rows],
        )
