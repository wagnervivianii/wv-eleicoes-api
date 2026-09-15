from datetime import date

from fastapi.testclient import TestClient
from pytest import MonkeyPatch

from wv_eleicoes_api.api.v1.profiles import router as profile_router_module
from wv_eleicoes_api.api.v1.profiles.schemas import (
    CandidacySummary,
    ElectoralHistoryResponse,
    ExternalIdentifierSummary,
    OfficeSummary,
    PartySummary,
    PersonProfileResponse,
    PersonSummary,
)
from wv_eleicoes_api.app import create_app
from wv_eleicoes_api.config import Settings


def client() -> TestClient:
    return TestClient(create_app(Settings(environment="test", _env_file=None)))


def candidacy(year: int) -> CandidacySummary:
    if year == 2026:
        return CandidacySummary(
            election_year=2026,
            election_code="6259",
            election_round=1,
            uf="RS",
            electoral_unit="RS",
            electoral_unit_name="RIO GRANDE DO SUL",
            candidacy_sequence="202600001",
            ballot_number="22114",
            ballot_name="PESSOA EXEMPLO",
            office=OfficeSummary(code="7", name="DEPUTADO ESTADUAL"),
            party=PartySummary(number="22", acronym="PL", name="PARTIDO LIBERAL"),
            status_code=None,
            status_name=None,
        )
    return CandidacySummary(
        election_year=2022,
        election_code="546",
        election_round=1,
        uf="RS",
        electoral_unit="RS",
        electoral_unit_name="RIO GRANDE DO SUL",
        candidacy_sequence="202200001",
        ballot_number="2220",
        ballot_name="PESSOA EXEMPLO",
        office=OfficeSummary(code="6", name="DEPUTADO FEDERAL"),
        party=PartySummary(number="22", acronym="PL", name="PARTIDO LIBERAL"),
        status_code="12",
        status_name="APTO",
    )


def sample_profile() -> PersonProfileResponse:
    return PersonProfileResponse(
        person=PersonSummary(
            id=42,
            legal_name="Pessoa Exemplo",
            display_name="Pessoa Exemplo",
            social_name=None,
            birth_date=date(1980, 1, 2),
            birth_uf="RS",
        ),
        external_identifiers=[
            ExternalIdentifierSummary(
                source_system="TSE",
                identifier_type="candidacy_sequence",
                identifier_value="202600001",
                scope_key="election:2026:6259",
            )
        ],
        candidacies=[candidacy(2026), candidacy(2022)],
    )


def sample_history() -> ElectoralHistoryResponse:
    return ElectoralHistoryResponse(
        person_id=42,
        candidacies=[candidacy(2026), candidacy(2022)],
    )


def test_profile_360_contract(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(
        profile_router_module,
        "fetch_person_profile",
        lambda person_id: sample_profile() if person_id == 42 else None,
    )

    response = client().get("/api/v1/people/42/profile")

    assert response.status_code == 200
    assert response.json()["person"]["id"] == 42
    assert response.json()["external_identifiers"][0]["source_system"] == "TSE"
    assert response.json()["candidacies"][0]["party"]["acronym"] == "PL"
    assert response.json()["candidacies"][0]["office"]["name"] == "DEPUTADO ESTADUAL"


def test_profile_360_returns_404_when_person_does_not_exist(
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        profile_router_module,
        "fetch_person_profile",
        lambda person_id: None,
    )

    response = client().get("/api/v1/people/999/profile")

    assert response.status_code == 404
    assert response.json() == {"detail": "Person not found"}


def test_profile_360_rejects_non_positive_person_id() -> None:
    response = client().get("/api/v1/people/0/profile")

    assert response.status_code == 422


def test_electoral_history_contract(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(
        profile_router_module,
        "fetch_electoral_history",
        lambda person_id: sample_history() if person_id == 42 else None,
    )

    response = client().get("/api/v1/people/42/electoral-history")

    assert response.status_code == 200
    payload = response.json()
    assert payload["person_id"] == 42
    assert [item["election_year"] for item in payload["candidacies"]] == [2026, 2022]
    assert payload["candidacies"][0]["office"]["name"] == "DEPUTADO ESTADUAL"
    assert payload["candidacies"][1]["office"]["name"] == "DEPUTADO FEDERAL"


def test_electoral_history_returns_404_when_person_does_not_exist(
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        profile_router_module,
        "fetch_electoral_history",
        lambda person_id: None,
    )

    response = client().get("/api/v1/people/999/electoral-history")

    assert response.status_code == 404
    assert response.json() == {"detail": "Person not found"}


def test_electoral_history_rejects_non_positive_person_id() -> None:
    response = client().get("/api/v1/people/0/electoral-history")

    assert response.status_code == 422
