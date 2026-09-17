"""Public response contracts for TSE declared assets."""

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel

SnapshotStatus = Literal["single_snapshot", "multiple_candidacy_snapshots"]
ComparisonStatus = Literal[
    "first_snapshot",
    "current_ambiguous",
    "previous_ambiguous",
    "contains_negative_values",
    "zero_baseline",
    "missing_value",
    "comparable",
]
DeclaredValueStatus = Literal["missing", "parsed", "unrecognized"]


class AssetDeclarationSummary(BaseModel):
    """Published summary for one person/candidacy declared-assets snapshot."""

    election_year: int
    election_code: str
    candidacy_sequence: str
    asset_count: int
    declared_value_count: int
    missing_value_count: int
    positive_value_count: int
    zero_value_count: int
    negative_value_count: int
    declared_value_signed_total: Decimal | None
    declared_value_positive_total: Decimal
    declared_value_negative_total: Decimal
    has_negative_values: bool | None
    largest_declared_value: Decimal | None
    largest_asset_order: int | None
    largest_asset_type_code: str | None
    largest_asset_type_name: str | None
    largest_asset_description: str | None
    latest_asset_updated_at: datetime | None
    source_snapshot_at: datetime | None


class AssetHistoryResponse(BaseModel):
    """Declared-assets snapshots for one stable political person."""

    person_id: int
    declarations: list[AssetDeclarationSummary]


class AssetEvolutionPoint(BaseModel):
    """One annual row published by analytics.person_asset_evolution."""

    election_year: int
    candidacy_snapshot_count: int
    election_count: int
    election_code: str | None
    candidacy_sequence: str | None
    asset_count: int | None
    declared_value_signed_total: Decimal | None
    has_negative_values: bool | None
    snapshot_status: SnapshotStatus
    previous_election_year: int | None
    previous_candidacy_snapshot_count: int | None
    previous_election_count: int | None
    previous_election_code: str | None
    previous_candidacy_sequence: str | None
    previous_asset_count: int | None
    previous_declared_value_signed_total: Decimal | None
    previous_has_negative_values: bool | None
    previous_snapshot_status: SnapshotStatus | None
    declared_value_nominal_change: Decimal | None
    comparison_status: ComparisonStatus
    declared_value_change_pct: Decimal | None


class AssetEvolutionResponse(BaseModel):
    """Annual declared-assets evolution for one stable political person."""

    person_id: int
    evolution: list[AssetEvolutionPoint]


class AssetTypeComposition(BaseModel):
    """Declared-assets composition for one candidacy and asset type."""

    asset_type_code: str | None
    asset_type_name: str | None
    asset_count: int
    declared_value_count: int
    negative_value_count: int
    declared_value_signed_total: Decimal | None
    declared_value_positive_total: Decimal
    declared_value_negative_total: Decimal
    largest_declared_value: Decimal | None
    item_share_pct: Decimal
    positive_value_share_pct: Decimal | None


class AssetItem(BaseModel):
    """One individual item declared by a candidate to the TSE."""

    asset_order: int
    asset_type_code: str | None
    asset_type_name: str | None
    asset_description: str | None
    declared_value: Decimal | None
    declared_value_status: DeclaredValueStatus
    asset_updated_at: datetime | None


class AssetDeclarationDetailResponse(BaseModel):
    """Summary, type composition and individual items for one declaration."""

    summary: AssetDeclarationSummary
    composition: list[AssetTypeComposition]
    items: list[AssetItem]
