from datetime import UTC, datetime
from decimal import Decimal

from fastapi.testclient import TestClient
from pytest import MonkeyPatch

from wv_eleicoes_api.api.v1.assets import router as asset_router_module
from wv_eleicoes_api.api.v1.assets.schemas import (
    AssetDeclarationDetailResponse,
    AssetDeclarationSummary,
    AssetEvolutionPoint,
    AssetEvolutionResponse,
    AssetHistoryResponse,
    AssetItem,
    AssetTypeComposition,
)
from wv_eleicoes_api.app import create_app
from wv_eleicoes_api.config import Settings


def client() -> TestClient:
    return TestClient(create_app(Settings(environment="test", _env_file=None)))


def summary() -> AssetDeclarationSummary:
    return AssetDeclarationSummary(
        election_year=2026,
        election_code="6259",
        candidacy_sequence="202600001",
        asset_count=3,
        declared_value_count=3,
        missing_value_count=0,
        positive_value_count=2,
        zero_value_count=0,
        negative_value_count=1,
        declared_value_signed_total=Decimal("899.75"),
        declared_value_positive_total=Decimal("1000.00"),
        declared_value_negative_total=Decimal("-100.25"),
        has_negative_values=True,
        largest_declared_value=Decimal("750.00"),
        largest_asset_order=2,
        largest_asset_type_code="13",
        largest_asset_type_name="VEICULO",
        largest_asset_description="AUTOMOVEL",
        latest_asset_updated_at=datetime(2026, 8, 20, 15, 0, tzinfo=UTC),
        source_snapshot_at=datetime(2026, 9, 16, 12, 0, tzinfo=UTC),
    )


def evolution() -> AssetEvolutionResponse:
    return AssetEvolutionResponse(
        person_id=42,
        evolution=[
            AssetEvolutionPoint(
                election_year=2022,
                candidacy_snapshot_count=1,
                election_count=1,
                election_code="546",
                candidacy_sequence="202200001",
                asset_count=2,
                declared_value_signed_total=Decimal("500.00"),
                has_negative_values=False,
                snapshot_status="single_snapshot",
                previous_election_year=None,
                previous_candidacy_snapshot_count=None,
                previous_election_count=None,
                previous_election_code=None,
                previous_candidacy_sequence=None,
                previous_asset_count=None,
                previous_declared_value_signed_total=None,
                previous_has_negative_values=None,
                previous_snapshot_status=None,
                declared_value_nominal_change=None,
                comparison_status="first_snapshot",
                declared_value_change_pct=None,
            ),
            AssetEvolutionPoint(
                election_year=2026,
                candidacy_snapshot_count=1,
                election_count=1,
                election_code="6259",
                candidacy_sequence="202600001",
                asset_count=3,
                declared_value_signed_total=Decimal("899.75"),
                has_negative_values=True,
                snapshot_status="single_snapshot",
                previous_election_year=2022,
                previous_candidacy_snapshot_count=1,
                previous_election_count=1,
                previous_election_code="546",
                previous_candidacy_sequence="202200001",
                previous_asset_count=2,
                previous_declared_value_signed_total=Decimal("500.00"),
                previous_has_negative_values=False,
                previous_snapshot_status="single_snapshot",
                declared_value_nominal_change=Decimal("399.75"),
                comparison_status="contains_negative_values",
                declared_value_change_pct=None,
            ),
        ],
    )


def detail() -> AssetDeclarationDetailResponse:
    return AssetDeclarationDetailResponse(
        summary=summary(),
        composition=[
            AssetTypeComposition(
                asset_type_code="13",
                asset_type_name="VEICULO",
                asset_count=2,
                declared_value_count=2,
                negative_value_count=1,
                declared_value_signed_total=Decimal("649.75"),
                declared_value_positive_total=Decimal("750.00"),
                declared_value_negative_total=Decimal("-100.25"),
                largest_declared_value=Decimal("750.00"),
                item_share_pct=Decimal("66.6667"),
                positive_value_share_pct=Decimal("75.0000"),
            )
        ],
        items=[
            AssetItem(
                asset_order=1,
                asset_type_code="13",
                asset_type_name="VEICULO",
                asset_description="AJUSTE DECLARADO",
                declared_value=Decimal("-100.25"),
                declared_value_status="parsed",
                asset_updated_at=None,
            )
        ],
    )


def test_asset_history_contract(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(
        asset_router_module,
        "fetch_asset_history",
        lambda person_id: AssetHistoryResponse(person_id=42, declarations=[summary()])
        if person_id == 42
        else None,
    )

    response = client().get("/api/v1/people/42/assets")

    assert response.status_code == 200
    payload = response.json()
    assert payload["person_id"] == 42
    assert payload["declarations"][0]["election_year"] == 2026
    assert payload["declarations"][0]["declared_value_negative_total"] == "-100.25"


def test_asset_history_returns_empty_list_for_existing_person_without_assets(
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        asset_router_module,
        "fetch_asset_history",
        lambda person_id: AssetHistoryResponse(person_id=person_id, declarations=[]),
    )

    response = client().get("/api/v1/people/42/assets")

    assert response.status_code == 200
    assert response.json() == {"person_id": 42, "declarations": []}


def test_asset_history_returns_404_for_missing_person(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(asset_router_module, "fetch_asset_history", lambda person_id: None)

    response = client().get("/api/v1/people/999/assets")

    assert response.status_code == 404
    assert response.json() == {"detail": "Person not found"}


def test_asset_history_rejects_non_positive_person_id() -> None:
    assert client().get("/api/v1/people/0/assets").status_code == 422


def test_asset_evolution_preserves_published_semantics(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(
        asset_router_module,
        "fetch_asset_evolution",
        lambda person_id: evolution() if person_id == 42 else None,
    )

    response = client().get("/api/v1/people/42/assets/evolution")

    assert response.status_code == 200
    payload = response.json()["evolution"]
    assert [row["election_year"] for row in payload] == [2022, 2026]
    assert payload[1]["comparison_status"] == "contains_negative_values"
    assert payload[1]["previous_declared_value_signed_total"] == "500.00"
    assert payload[1]["declared_value_nominal_change"] == "399.75"
    assert payload[1]["declared_value_change_pct"] is None


def test_asset_evolution_returns_404_for_missing_person(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(asset_router_module, "fetch_asset_evolution", lambda person_id: None)

    response = client().get("/api/v1/people/999/assets/evolution")

    assert response.status_code == 404


def test_asset_declaration_detail_contract(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(
        asset_router_module,
        "fetch_asset_declaration_detail",
        lambda person_id, election_year, election_code, candidacy_sequence: (True, detail()),
    )

    response = client().get(
        "/api/v1/people/42/assets/declarations/2026/6259/202600001"
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["summary"]["candidacy_sequence"] == "202600001"
    assert payload["composition"][0]["item_share_pct"] == "66.6667"
    assert payload["items"][0]["declared_value"] == "-100.25"


def test_asset_declaration_detail_distinguishes_missing_person(
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        asset_router_module,
        "fetch_asset_declaration_detail",
        lambda person_id, election_year, election_code, candidacy_sequence: (False, None),
    )

    response = client().get(
        "/api/v1/people/999/assets/declarations/2026/6259/202600001"
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Person not found"}


def test_asset_declaration_detail_returns_404_for_missing_declaration(
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        asset_router_module,
        "fetch_asset_declaration_detail",
        lambda person_id, election_year, election_code, candidacy_sequence: (True, None),
    )

    response = client().get(
        "/api/v1/people/42/assets/declarations/2026/6259/202699999"
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Asset declaration not found"}


def test_asset_declaration_detail_rejects_invalid_scope() -> None:
    invalid_year = client().get(
        "/api/v1/people/42/assets/declarations/0/6259/202600001"
    )
    invalid_code = client().get(
        "/api/v1/people/42/assets/declarations/2026/not-a-code/202600001"
    )

    assert invalid_year.status_code == 422
    assert invalid_code.status_code == 422
