"""Environment-backed settings for the dedicated chatbot runtime."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Literal


WorkerMode = Literal["warm"]


@dataclass(frozen=True)
class RuntimeSettings:
    """Operational settings shared by the API and warm worker processes."""

    api_bind_host: str = "0.0.0.0"
    api_port: int = 8780
    worker_mode: WorkerMode = "warm"
    bge_model_name: str = "BAAI/bge-m3"
    hf_hub_cache: Path | None = None
    chunks_root: Path = Path("data/docs_normalized")
    embeddings_root: Path = Path("data/embeddings")

    @classmethod
    def from_env(cls, environ: Mapping[str, str]) -> "RuntimeSettings":
        """Build settings from explicit environment data without reading globals."""

        raw_worker_mode = environ.get("CHATBOT_RUNTIME_WORKER_MODE", "warm")
        if raw_worker_mode != "warm":
            raise ValueError("CHATBOT_RUNTIME_WORKER_MODE must be 'warm'")

        raw_cache = environ.get("HF_HUB_CACHE", "").strip()
        return cls(
            api_bind_host=environ.get("CHATBOT_RUNTIME_API_BIND_HOST", "0.0.0.0"),
            api_port=int(environ.get("CHATBOT_RUNTIME_API_PORT", "8780")),
            worker_mode="warm",
            bge_model_name=environ.get("BGE_MODEL_NAME", "BAAI/bge-m3"),
            hf_hub_cache=Path(raw_cache) if raw_cache else None,
            chunks_root=Path(
                environ.get("CHATBOT_RUNTIME_CHUNKS_ROOT", "data/docs_normalized")
            ),
            embeddings_root=Path(
                environ.get("CHATBOT_RUNTIME_EMBEDDINGS_ROOT", "data/embeddings")
            ),
        )
