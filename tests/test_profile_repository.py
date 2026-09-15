from wv_eleicoes_api.api.v1.profiles.repository import (
    CANDIDACIES_QUERY,
    PERSON_QUERY,
    PUBLIC_IDENTIFIERS_QUERY,
)


def normalized(statement: object) -> str:
    return " ".join(str(statement).split()).lower()


def test_profile_queries_use_only_public_read_models() -> None:
    sql = " ".join(
        normalized(statement)
        for statement in (
            PERSON_QUERY,
            PUBLIC_IDENTIFIERS_QUERY,
            CANDIDACIES_QUERY,
        )
    )

    assert "core.person" in sql
    assert "core.person_external_identifier" in sql
    assert "analytics.candidate" in sql
    assert "raw." not in sql
    assert "audit." not in sql
    assert "nr_cpf_candidato" not in sql
    assert "nr_titulo_eleitoral_candidato" not in sql


def test_external_identifiers_are_public_only() -> None:
    assert "is_public = true" in normalized(PUBLIC_IDENTIFIERS_QUERY)
    assert "identifier.is_public = true" in normalized(CANDIDACIES_QUERY)


def test_tse_candidacy_identifier_is_scoped_by_election() -> None:
    sql = normalized(CANDIDACIES_QUERY)

    assert "identifier.source_system = 'tse'" in sql
    assert "identifier.identifier_type = 'candidacy_sequence'" in sql
    assert "identifier.identifier_value = candidate.candidacy_sequence" in sql
    assert "'election:' || candidate.election_year::text" in sql
    assert "|| ':' || candidate.election_code" in sql
