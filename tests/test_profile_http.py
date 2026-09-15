from datetime import date

from fastapi.testclient import TestClient
from pytest import MonkeyPatch

from wv_eleicoes_api.api.v1.profiles import router as profile_router_module
from wv_eleicoes_api.api.v1.profiles.schemas import (
    CandidacySummary,
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


def sample_profile() -> PersonProfileResponse:
    return PersonProfileResponse(
        person=PersonSummary(
            id=42,
            legal_name="Pessoa Exemplo",
            display_name="Pessoa Exemplo",
            social_name=None,
            birth_date=date(1980, 1, 2),
            birth_uf="SP",
        ),
        external_identifiers=[
            ExternalIdentifierSummary(
                source_system="TSE",
                identifier_type="candidacy_sequence",
                identifier_value="123456",
                scope_key="election:2026:999",
            )
        ],
        candidacies=[
            CandidacySummary(
                election_year=2026,
                election_code="999",
                election_round=1,
                uf="SP",
                electoral_unit="SP",
                electoral_unit_name="SÃO PAULO",
                candidacy_sequence="123456",
                ballot_number="1234",
                ballot_name="PESSOA EXEMPLO",
                office=OfficeSummary(code="6", name="DEPUTADO FEDERAL"),
                party=PartySummary(
                    number="99",
                    acronym="PXX",
                    name="PARTIDO EXEMPLO",
                ),
                status_code="12",
                status_name="APTO",
            )
        ],
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
    assert response.json()["candidacies"][0]["party"]["acronym"] == "PXX"
    assert response.json()["candidacies"][0]["office"]["name"] == "DEPUTADO FEDERAL"


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
