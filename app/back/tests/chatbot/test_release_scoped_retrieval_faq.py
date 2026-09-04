"""PostgresReleaseScopedRetrievalPort FAQ shortcut: release-membership gate (PR-3 3.3).

Before this gate, ``_faq_result`` answered unconditionally from any FAQ hit via a synthetic
``faq`` lane that never touched Postgres — a curated FAQ entry citing a document that was later
removed, unapproved, or that never belonged to the queried release could still "answer" as if it
were release evidence. Now the citation must be indexed, approved, and a member of
``rag_release_id`` (``_faq_reference_in_release``); otherwise ``_faq_result`` returns ``None`` and
``search`` falls through to real, release-scoped retrieval instead.
"""

from __future__ import annotations

import pytest

from chatbot.application.ports import ChatbotReleaseLane
from chatbot.infrastructure.release_scoped_retrieval import (
    PostgresReleaseScopedRetrievalPort,
)
from retrieval.infrastructure.faq_resolver import FaqMatch

_LANE_ROW = ("ep_local", "it_default", "cv_2026")


class _FakeCursor:
    """Returns the next queued row-list per ``execute()`` call; ``[]`` once exhausted."""

    def __init__(self, connection: "_FakeConnection") -> None:
        self._connection = connection

    def __enter__(self) -> "_FakeCursor":
        return self

    def __exit__(self, *_exc: object) -> None:
        return None

    def execute(self, sql: str, params: tuple) -> None:
        self._connection.executed.append((sql, params))
        self._connection.pending_rows = (
            self._connection.queue.pop(0) if self._connection.queue else []
        )

    def fetchall(self) -> list[tuple]:
        return self._connection.pending_rows


class _FakeConnection:
    def __init__(self, queue: list[list[tuple]]) -> None:
        self.queue = list(queue)
        self.executed: list[tuple[str, tuple]] = []
        self.pending_rows: list[tuple] = []

    def cursor(self) -> _FakeCursor:
        return _FakeCursor(self)


class _FakeFaqResolver:
    def __init__(self, match: FaqMatch | None) -> None:
        self._match = match

    def match(self, question: str) -> FaqMatch | None:
        return self._match


class _FakeFaqRegistry:
    def __init__(self, resolver: _FakeFaqResolver | None) -> None:
        self._resolver = resolver

    def resolver_for(self, project_id: str) -> _FakeFaqResolver | None:
        return self._resolver


def _port(connection: _FakeConnection, registry: _FakeFaqRegistry) -> PostgresReleaseScopedRetrievalPort:
    return PostgresReleaseScopedRetrievalPort(
        connection=connection,
        profiles=object(),  # not touched: these tests never reach real retrieval
        targets=object(),
        retrieval_profiles=object(),
        query_embedding=object(),
        faq_resolver_registry=registry,
    )


def _match(source_relpath: str | None = "manuals/comite.pdf") -> FaqMatch:
    reference = {"normalized_path": source_relpath, "document_title": "Manual Comite"} if source_relpath else {}
    return FaqMatch(
        faq_id="FAQ-1",
        question="Que es el comite?",
        answer="Es un organo consultivo.",
        status="supported",
        score=0.95,
        reference=reference,
    )


def test_faq_reference_in_release_true_cuando_hay_fila() -> None:
    connection = _FakeConnection(queue=[[(1,)]])
    port = _port(connection, registry=_FakeFaqRegistry(None))

    assert (
        port._faq_reference_in_release(
            project_id="proj_demo", rag_release_id="ragr_demo", source_relpath="manuals/x.pdf"
        )
        is True
    )


def test_faq_reference_in_release_false_cuando_no_hay_fila() -> None:
    connection = _FakeConnection(queue=[[]])
    port = _port(connection, registry=_FakeFaqRegistry(None))

    assert (
        port._faq_reference_in_release(
            project_id="proj_demo", rag_release_id="ragr_demo", source_relpath="manuals/x.pdf"
        )
        is False
    )


def test_faq_result_none_cuando_referencia_no_tiene_ruta() -> None:
    connection = _FakeConnection(queue=[])
    port = _port(connection, registry=_FakeFaqRegistry(None))

    result = port._faq_result(
        _match(source_relpath=None), project_id="proj_demo", rag_release_id="ragr_demo"
    )

    assert result is None
    assert connection.executed == []  # fail-closed before ever touching the DB


def test_faq_result_none_cuando_no_pertenece_a_release() -> None:
    connection = _FakeConnection(queue=[[]])  # membership check: no rows
    port = _port(connection, registry=_FakeFaqRegistry(None))

    result = port._faq_result(_match(), project_id="proj_demo", rag_release_id="ragr_demo")

    assert result is None


def test_faq_result_devuelve_evidencia_cuando_pertenece_a_release() -> None:
    connection = _FakeConnection(queue=[[(1,)]])  # membership check: hit
    port = _port(connection, registry=_FakeFaqRegistry(None))

    result = port._faq_result(_match(), project_id="proj_demo", rag_release_id="ragr_demo")

    assert result is not None
    assert result.evidence[0].text == "Es un organo consultivo."
    assert result.lane == ChatbotReleaseLane(
        embedding_profile_id="faq", indexing_target_id="faq", corpus_version="faq"
    )


def test_search_responde_desde_faq_sin_tocar_retrieval_real_cuando_pertenece_a_release() -> None:
    connection = _FakeConnection(queue=[[_LANE_ROW], [(1,)]])  # lane, then membership hit
    port = _port(connection, registry=_FakeFaqRegistry(_FakeFaqResolver(_match())))

    result = port.search(
        project_id="proj_demo",
        rag_variant_id="ignored",
        rag_release_id="ragr_demo",
        question="Que es el comite?",
        top_k=5,
    )

    assert result.evidence[0].text == "Es un organo consultivo."
    # Only the lane resolution + membership check ran; vector/lexical/rerank never did.
    assert len(connection.executed) == 2


def test_search_cae_a_retrieval_real_cuando_faq_no_pertenece_a_release() -> None:
    """A FAQ hit whose citation fails the release-membership gate must not answer.

    ``query_embedding``/``retrieval_profiles`` are bare ``object()`` sentinels here (this test's
    fakes never model the real hybrid-retrieval path), so reaching them raises ``AttributeError``
    — that is the proof ``search`` moved past the rejected FAQ shortcut into the real-retrieval
    branch instead of returning the FAQ evidence. Driving the full downstream
    ``RetrievalSearchService`` (embeddings, vector/lexical fusion, rerank) end to end needs a much
    larger Postgres-fake harness with no existing coverage for this class (no prior test file
    imported ``PostgresReleaseScopedRetrievalPort`` before this one) — out of scope for the FAQ
    isolation fix.
    """
    connection = _FakeConnection(queue=[[_LANE_ROW], []])  # lane, then membership miss
    port = _port(connection, registry=_FakeFaqRegistry(_FakeFaqResolver(_match())))

    with pytest.raises(AttributeError):
        port.search(
            project_id="proj_demo",
            rag_variant_id="ignored",
            rag_release_id="ragr_demo",
            question="Que es el comite?",
            top_k=5,
        )
