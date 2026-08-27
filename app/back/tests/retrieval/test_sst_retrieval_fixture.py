from __future__ import annotations

import json

from sst_retrieval_fixture import (
    load_cached_query_embeddings,
    load_sst_hybrid_questions,
    query_embedding_cache_path,
    save_cached_query_embeddings,
    sst_reusable_derived_state_exists,
)


def test_sst_hybrid_question_bank_expands_beyond_original_53() -> None:
    questions = load_sst_hybrid_questions()

    assert len(questions) >= 60
    assert "Cual es el objetivo general del manual de convivencia laboral?" in questions
    assert "En cuanto tiempo debe el Comite de Convivencia dar tramite a una queja?" in questions
    assert "Que programa incluye el PESV para proteger actores viales vulnerables?" in questions


def test_sst_reusable_derived_state_requires_non_empty_chunks_and_embeddings(
    tmp_path,
) -> None:
    assert sst_reusable_derived_state_exists(tmp_path) is False

    chunks = tmp_path / "chunks"
    embeddings = tmp_path / "embeddings"
    chunks.mkdir()
    embeddings.mkdir()
    (chunks / "bundle.chunking_metadata.json").write_text("{}", encoding="utf-8")

    assert sst_reusable_derived_state_exists(tmp_path) is False

    (embeddings / "bundle.json").write_text("{}", encoding="utf-8")

    assert sst_reusable_derived_state_exists(tmp_path) is True


def test_query_embedding_cache_round_trip(tmp_path) -> None:
    questions = load_sst_hybrid_questions()[:2]
    vectors = [[0.1, 0.2], [0.3, 0.4]]

    save_cached_query_embeddings(
        project_root=tmp_path,
        embedding_profile_id="local-bge-m3-v1",
        questions=questions,
        vectors=vectors,
    )

    restored = load_cached_query_embeddings(
        project_root=tmp_path,
        embedding_profile_id="local-bge-m3-v1",
        questions=questions,
    )

    assert restored == vectors


def test_query_embedding_cache_rejects_question_mismatch(tmp_path) -> None:
    questions = load_sst_hybrid_questions()[:2]
    cache_path = query_embedding_cache_path(
        tmp_path,
        embedding_profile_id="local-bge-m3-v1",
        questions=questions,
    )
    cache_path.write_text(
        json.dumps(
            {
                "embedding_profile_id": "local-bge-m3-v1",
                "questions": ["otra pregunta"],
                "vectors": [[0.1, 0.2]],
            }
        ),
        encoding="utf-8",
    )

    restored = load_cached_query_embeddings(
        project_root=tmp_path,
        embedding_profile_id="local-bge-m3-v1",
        questions=questions,
    )

    assert restored is None
