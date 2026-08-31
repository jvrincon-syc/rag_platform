"""Explicit BGE warmup state used by runtime health and readiness checks."""

from __future__ import annotations

from dataclasses import dataclass
from threading import Lock
from typing import Callable


@dataclass(frozen=True)
class WarmupStatusSnapshot:
    ready: bool
    warmed_embedding: bool
    warmed_reranker: bool
    last_error: str | None


class BgeWarmupService:
    """Run both BGE probes and expose a fail-closed readiness snapshot."""

    def __init__(
        self,
        *,
        embed_probe: Callable[[], object],
        rerank_probe: Callable[[], object],
    ) -> None:
        self._embed_probe = embed_probe
        self._rerank_probe = rerank_probe
        self._lock = Lock()
        self._status = WarmupStatusSnapshot(
            ready=False,
            warmed_embedding=False,
            warmed_reranker=False,
            last_error=None,
        )

    def warm(self) -> WarmupStatusSnapshot:
        """Warm embedding first, then reranking, and retain partial failure state."""

        with self._lock:
            warmed_embedding = False
            warmed_reranker = False
            try:
                self._embed_probe()
                warmed_embedding = True
                self._rerank_probe()
                warmed_reranker = True
            except Exception as error:
                self._status = WarmupStatusSnapshot(
                    ready=False,
                    warmed_embedding=warmed_embedding,
                    warmed_reranker=warmed_reranker,
                    last_error=type(error).__name__,
                )
                return self._status

            self._status = WarmupStatusSnapshot(
                ready=True,
                warmed_embedding=True,
                warmed_reranker=True,
                last_error=None,
            )
            return self._status

    def status(self) -> WarmupStatusSnapshot:
        """Return the latest immutable warmup result."""

        with self._lock:
            return self._status

    def ready(self) -> bool:
        """Return true only after both BGE capabilities warmed successfully."""

        return self.status().ready
