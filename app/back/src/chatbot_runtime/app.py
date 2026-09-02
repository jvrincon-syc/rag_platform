"""ASGI application factory for dedicated SST chatbot traffic."""

from __future__ import annotations

from collections.abc import Mapping
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from chatbot_runtime.dependencies import build_warmup_service
from chatbot_runtime.warmup import BgeWarmupService
from fastapi import FastAPI, Response, status

if TYPE_CHECKING:
    from api.dependencies import PipelineServices


@dataclass(frozen=True)
class ChatbotRuntime:
    """The persistent application services owned by one ASGI worker."""

    app: FastAPI
    services: PipelineServices
    warmup: BgeWarmupService


def create_chatbot_runtime_app(
    *,
    pipeline_app: FastAPI,
    warmup_service: BgeWarmupService,
) -> FastAPI:
    """Expose unauthenticated process probes and mount the authenticated API."""

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        # Mounted applications do not run their lifespan automatically.
        async with pipeline_app.router.lifespan_context(pipeline_app):
            yield

    app = FastAPI(
        title="Chatbot SST Runtime",
        version="0.1.0",
        lifespan=lifespan,
    )

    @app.get("/healthz")
    def healthz() -> dict[str, object]:
        return {"healthy": True}

    @app.get("/readyz")
    def readyz(response: Response) -> dict[str, object]:
        snapshot = warmup_service.status()
        if not snapshot.ready:
            response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {
            "ready": snapshot.ready,
            "warmed_embedding": snapshot.warmed_embedding,
            "warmed_reranker": snapshot.warmed_reranker,
            "last_error": snapshot.last_error,
        }

    # Probes stay outside bearer auth. The raw-document endpoint now lives inside the mounted
    # pipeline app (bearer-protected via chatbot.api.raw_documents), so it is not re-declared here.
    app.mount("/", pipeline_app)
    return app


def build_chatbot_runtime(
    *,
    chunks_root: Path,
    embeddings_root: Path,
    environ: Mapping[str, str],
    warmup_service: BgeWarmupService | None = None,
) -> ChatbotRuntime:
    """Compose the dedicated chatbot process without GUI HTTP adapters."""

    from api.dependencies import build_pipeline_services_from_env

    services = build_pipeline_services_from_env(
        chunks_root=chunks_root,
        embeddings_root=embeddings_root,
        environ=environ,
    )
    warmup = warmup_service or build_warmup_service(services=services)

    # Imported here so runtime unit tests can inject warmup without hard-coupling
    # module import to the full pipeline application graph.
    from api.app import create_app

    pipeline_app = create_app(services=services)
    app = create_chatbot_runtime_app(
        pipeline_app=pipeline_app,
        warmup_service=warmup,
    )
    app.state.chatbot_runtime = ChatbotRuntime(
        app=app,
        services=services,
        warmup=warmup,
    )
    return app.state.chatbot_runtime


def build_chatbot_runtime_from_env(
    *,
    environ: Mapping[str, str],
) -> ChatbotRuntime:
    """Resolve settings from env vars and build the dedicated chatbot runtime."""

    from chatbot_runtime.settings import RuntimeSettings

    settings = RuntimeSettings.from_env(environ)
    return build_chatbot_runtime(
        chunks_root=settings.chunks_root,
        embeddings_root=settings.embeddings_root,
        environ=environ,
    )
