from __future__ import annotations

from retrieval.infrastructure.postgres.repositories import (
    _FTS_BASENAME_A,
    _FTS_DIR_C,
    _FTS_GENERIC_DIRECTORY_TOKENS,
    _fts_query_modes,
    _normalize_fts_query,
    _tsvector_sql,
)


def test_normalize_fts_query_colapsa_puntuacion_y_preserva_siglas() -> None:
    normalized = _normalize_fts_query("  ARL,   responsabilidades!!! SG-SST?  ")

    assert normalized == "arl responsabilidades sg-sst"


def test_fts_query_modes_escalan_y_expanden_siglas_del_dominio() -> None:
    modes = _fts_query_modes("ARL responsabilidades")

    assert [mode.mode_name for mode in modes] == [
        "spanish_strict",
        "spanish_relaxed",
        "simple_relaxed",
        "spanish_relaxed_expanded",
        "simple_relaxed_expanded",
    ]
    assert [mode.query_text for mode in modes[:3]] == [
        "arl responsabilidades",
        "arl responsabilidades",
        "arl responsabilidades",
    ]
    assert all(
        mode.query_text == "arl responsabilidades administradora riesgos laborales"
        for mode in modes[3:]
    )


def test_weighted_fts_sql_usa_regexp_split_to_array_en_lugar_de_regexp_to_array() -> None:
    assert "regexp_split_to_array" in _FTS_DIR_C
    assert "regexp_to_array" not in _FTS_DIR_C
    assert "regexp_split_to_array" in _FTS_BASENAME_A
    assert "regexp_to_array" not in _FTS_BASENAME_A


def test_weighted_fts_sql_dir_builder_balancea_parentesis_y_regex() -> None:
    formatted = _FTS_DIR_C.format(t="n", c="source_relpath")

    assert formatted.count("regexp_replace(") == 1 + len(_FTS_GENERIC_DIRECTORY_TOKENS)
    assert formatted.count("(") == formatted.count(")")


def test_tsvector_sql_usa_simple_para_el_modo_simple_relaxed() -> None:
    assert "to_tsvector('simple'" in _tsvector_sql("node", config="simple")
    assert "to_tsvector('spanish'" in _tsvector_sql("node", config="spanish")
