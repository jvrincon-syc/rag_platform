"""Dedicated ASGI entrypoint for the RAG Platform chatbot dispatch runtime."""

from __future__ import annotations

import os
from collections.abc import Mapping

from chatbot_runtime.app import build_chatbot_runtime_from_env
from chatbot_runtime.settings import RuntimeSettings


def load_runtime_settings(environ: Mapping[str, str]) -> RuntimeSettings:
    return RuntimeSettings.from_env(environ)


def main() -> None:
    """Warm BGE before serving RAG Platform dispatch traffic through Uvicorn."""

    settings = load_runtime_settings(os.environ)
    runtime = build_chatbot_runtime_from_env(environ=os.environ)
    snapshot = runtime.warmup.warm()
    if not snapshot.ready:
        runtime.services.close()
        raise RuntimeError(
            f"BGE warmup failed before serving traffic ({snapshot.last_error})"
        )

    try:
        import uvicorn
    except ImportError as error:
        runtime.services.close()
        raise RuntimeError(
            "uvicorn is required to run the chatbot ASGI runtime"
        ) from error

    uvicorn.run(
        runtime.app,
        host=settings.api_bind_host,
        port=settings.api_port,
    )


if __name__ == "__main__":
    main()
