from __future__ import annotations

import os
from pathlib import Path

from ingestion.config.llama_settings import LlamaSettings, load_llama_settings


def load_secrets_env(path: Path, *, apply: bool = False) -> dict[str, str]:
    loaded: dict[str, str] = {}
    if not path.exists():
        return loaded
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        loaded[key.strip()] = value.strip()
    if apply:
        for key, value in loaded.items():
            os.environ.setdefault(key, value)
    return loaded


def load_runtime_llama_settings(
    secrets_path: Path | None = None,
    *,
    environ: dict[str, str] | None = None,
) -> LlamaSettings:
    env = dict(os.environ if environ is None else environ)
    if secrets_path is not None:
        for key, value in load_secrets_env(secrets_path).items():
            env.setdefault(key, value)
    return load_llama_settings(env)
