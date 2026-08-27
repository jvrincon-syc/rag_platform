from __future__ import annotations

import pytest

from retrieval.postgres_fts_retriever import PostgresFtsRetriever


def test_postgres_fts_retriever_builds_parameterized_spanish_fts_query() -> None:
    query = PostgresFtsRetriever.build_query(
        filters={"document_type": "manual", "topic": "SST"}
    )

    assert "to_tsvector('spanish', text)" in query.sql
    assert "plainto_tsquery('spanish', %(query)s)" in query.sql
    assert "metadata->>'document_type' = %(document_type)s" in query.sql
    assert query.params["document_type"] == "manual"
    assert query.params["topic"] == "SST"


def test_postgres_fts_retriever_rejects_unsafe_filter_keys() -> None:
    with pytest.raises(ValueError, match="unsafe filter key"):
        PostgresFtsRetriever.build_query(filters={"topic') OR 1=1 --": "SST"})
