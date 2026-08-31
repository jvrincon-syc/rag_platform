"""Runtime-specific composition helpers for the chatbot ASGI process."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from chatbot_runtime.warmup import BgeWarmupService

if TYPE_CHECKING:
    from api.dependencies import PipelineServices


def _resolve_warm_probe(*, services: "PipelineServices") -> Callable[[], object]:
    warmup = getattr(services, "warmup", None)
    if callable(warmup):
        return warmup
    raise RuntimeError("PipelineServices must expose a callable warmup() hook")


def build_warmup_service(*, services: PipelineServices) -> BgeWarmupService:
    """Build readiness probes around the pipeline's shared BGE runtime.

    ``PipelineServices.warmup`` loads the reranker through the same injected
    ``BgeModelCache`` used by query embeddings. Calling it for each capability
    preserves an explicit readiness contract while the cache guarantees one
    process-resident model instance.
    """

    warm_probe = _resolve_warm_probe(services=services)
    return BgeWarmupService(
        embed_probe=warm_probe,
        rerank_probe=warm_probe,
    )
