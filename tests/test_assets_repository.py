from wv_eleicoes_api.api.v1.assets.repository import (
    ASSET_DECLARATION_SUMMARY_QUERY,
    ASSET_DECLARATION_TYPES_QUERY,
    ASSET_DECLARATIONS_QUERY,
    ASSET_EVOLUTION_QUERY,
    ASSET_ITEMS_QUERY,
    PERSON_EXISTS_QUERY,
)


def normalized(statement: object) -> str:
    return " ".join(str(statement).split()).lower()


def all_asset_sql() -> str:
    return " ".join(
        normalized(statement)
        for statement in (
            PERSON_EXISTS_QUERY,
            ASSET_DECLARATIONS_QUERY,
            ASSET_EVOLUTION_QUERY,
            ASSET_DECLARATION_SUMMARY_QUERY,
            ASSET_DECLARATION_TYPES_QUERY,
            ASSET_ITEMS_QUERY,
        )
    )


def test_asset_queries_use_only_approved_relations() -> None:
    sql = all_asset_sql()

    assert "core.person" in sql
    assert "analytics.candidate_asset_item" in sql
    assert "core.candidate_asset" not in sql
    assert "analytics.candidate_asset_summary" in sql
    assert "analytics.candidate_asset_type" in sql
    assert "analytics.person_asset_evolution" in sql
    assert "core.person_external_identifier" not in sql
    assert "analytics.candidate " not in sql
    assert "raw." not in sql
    assert "audit." not in sql
    assert "nr_cpf_candidato" not in sql
    assert "nr_titulo_eleitoral_candidato" not in sql


def test_asset_queries_are_select_only_and_do_not_hide_negative_values() -> None:
    statements = (
        PERSON_EXISTS_QUERY,
        ASSET_DECLARATIONS_QUERY,
        ASSET_EVOLUTION_QUERY,
        ASSET_DECLARATION_SUMMARY_QUERY,
        ASSET_DECLARATION_TYPES_QUERY,
        ASSET_ITEMS_QUERY,
    )

    for statement in statements:
        sql = normalized(statement)
        assert sql.startswith("select ")
        assert " insert " not in f" {sql} "
        assert " update " not in f" {sql} "
        assert " delete " not in f" {sql} "
        assert "abs(" not in sql
        assert "greatest(" not in sql
        assert "least(" not in sql


def test_evolution_is_consumed_directly_without_recalculation() -> None:
    sql = normalized(ASSET_EVOLUTION_QUERY)

    assert "from analytics.person_asset_evolution" in sql
    assert "lag(" not in sql
    assert "round(" not in sql
    assert "declared_value_signed_total - previous_declared_value_signed_total" not in sql
    assert "* 100" not in sql
    assert "comparison_status" in sql
    assert "snapshot_status" in sql
    assert "previous_declared_value_signed_total" in sql
    assert "declared_value_nominal_change" in sql
    assert "declared_value_change_pct" in sql


def test_asset_items_use_published_serving_relation() -> None:
    sql = normalized(ASSET_ITEMS_QUERY)

    assert "from analytics.candidate_asset_item" in sql
    assert "core.candidate_asset" not in sql
    assert "raw." not in sql
    assert "audit." not in sql


def test_declaration_detail_uses_complete_candidacy_scope_key() -> None:
    for statement in (
        ASSET_DECLARATION_SUMMARY_QUERY,
        ASSET_DECLARATION_TYPES_QUERY,
        ASSET_ITEMS_QUERY,
    ):
        sql = normalized(statement)
        assert "person_id = :person_id" in sql
        assert "election_year = :election_year" in sql
        assert "election_code = :election_code" in sql
        assert "candidacy_sequence = :candidacy_sequence" in sql


def test_history_and_evolution_have_explicit_temporal_order() -> None:
    assert "election_year desc" in normalized(ASSET_DECLARATIONS_QUERY)
    assert "election_year asc" in normalized(ASSET_EVOLUTION_QUERY)
