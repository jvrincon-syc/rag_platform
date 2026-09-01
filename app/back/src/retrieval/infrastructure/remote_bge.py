"""Remote BGE-M3 embed + rerank clients that call a Lightning AI GPU studio.

Offloads the two heavy retrieval operations off the local 8GB box entirely: the query is embedded
and the candidate pool is reranked on the studio's GPU (same BGE-M3 weights, so vectors and scores
match the locally indexed corpus). Only pgvector search + orchestration stay local. Opt-in via
``RETRIEVAL_QUERY_EMBED=remote`` and ``RETRIEVAL_RERANKER=remote``; the endpoint + bearer come from
``REMOTE_BGE_URL`` and ``REMOTE_BGE_KEY``.

Same ``EmbeddingEngine`` / ``RerankerPort`` contracts as the local adapters, so nothing downstream
changes. Network failures surface as domain-agnostic runtime errors; the dispatch path already
fails closed on retrieval errors.
"""

from __future__ import annotations

import json
import os
import urllib.request
from collections.abc import Sequence
from dataclasses import dataclass, field

from embedding.domain.models import Normalization
from retrieval.domain.models import RetrievedEvidence


def _endpoint() -> tuple[str, str | None]:
    url = os.environ.get("REMOTE_BGE_URL", "").rstrip("/")
    if not url:
        raise RuntimeError("REMOTE_BGE_URL is not set; the remote BGE client needs the studio URL")
    return url, os.environ.get("REMOTE_BGE_KEY") or None


def _post(path: str, payload: dict, timeout: float = 60.0) -> dict:
    url, key = _endpoint()
    data = json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if key:
        headers["Authorization"] = f"Bearer {key}"
    request = urllib.request.Request(url + path, data=data, headers=headers)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read())


class RemoteBgeQueryEngine:
    """Embeds queries by calling the studio's /embed; matches the durable bge profile."""

    def __init__(self, *, model_name: str, dimension: int) -> None:
        self._model_name = model_name
        self._dimension = dimension

    @property
    def provider_name(self) -> str:
        return "bge"

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def dimension(self) -> int:
        return self._dimension

    @property
    def normalization(self) -> Normalization:
        return "l2"

    @property
    def supports_queries(self) -> bool:
        return True

    def observe_revision(self) -> str:
        return "remote-bge-m3"

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        raise NotImplementedError("RemoteBgeQueryEngine is query-only; document embedding stays local")

    def embed_queries(self, texts: Sequence[str]) -> list[list[float]]:
        vectors = _post("/embed", {"texts": list(texts)}).get("vectors", [])
        return [[float(x) for x in vector] for vector in vectors]


@dataclass
class RemoteBgeReranker:
    """Reorders the deduped pool by scores from the studio's /rerank (colbert+sparse+dense)."""

    _unused: bool = field(default=False, repr=False)

    def rerank(
        self, *, query: str, candidates: list[RetrievedEvidence], top_n: int
    ) -> list[RetrievedEvidence]:
        if not candidates:
            return []
        scores = _post(
            "/rerank",
            {"query": query, "passages": [candidate.text for candidate in candidates]},
        ).get("scores", [])
        if len(scores) != len(candidates):
            # Fail closed rather than mis-pair scores to candidates.
            raise RuntimeError("remote rerank returned a score count that does not match the pool")
        ranked = sorted(zip(candidates, scores), key=lambda pair: pair[1], reverse=True)
        return [
            candidate.model_copy(
                update={
                    "score": float(score),
                    "metadata": {
                        **candidate.metadata,
                        "rerank_score": float(score),
                        "pre_rerank_score": candidate.score,
                    },
                }
            )
            for candidate, score in ranked[:top_n]
        ]

    def warm(self) -> None:
        """No local model to warm; the studio holds the weights."""
