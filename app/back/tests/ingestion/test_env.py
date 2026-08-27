from __future__ import annotations

import os

from ingestion.config.env import load_runtime_llama_settings, load_secrets_env


def test_load_secrets_env_returns_values_without_mutating_process_environment(
    tmp_path,
    monkeypatch,
) -> None:
    monkeypatch.delenv("LLAMA_CLOUD_API_KEY", raising=False)
    secrets_path = tmp_path / "secrets.env"
    secrets_path.write_text(
        "LLAMA_CLOUD_API_KEY=test-key\nLLAMA_CLOUD_ENABLED=true\n",
        encoding="utf-8",
    )

    loaded = load_secrets_env(secrets_path)

    assert loaded == {
        "LLAMA_CLOUD_API_KEY": "test-key",
        "LLAMA_CLOUD_ENABLED": "true",
    }
    assert "LLAMA_CLOUD_API_KEY" not in os.environ


def test_load_runtime_llama_settings_reads_secret_file_without_global_env_side_effects(
    tmp_path,
    monkeypatch,
) -> None:
    monkeypatch.delenv("LLAMA_CLOUD_API_KEY", raising=False)
    monkeypatch.delenv("LLAMA_CLOUD_ENABLED", raising=False)
    secrets_path = tmp_path / "secrets.env"
    secrets_path.write_text(
        "LLAMA_CLOUD_API_KEY=test-key\nLLAMA_CLOUD_ENABLED=true\n",
        encoding="utf-8",
    )

    settings = load_runtime_llama_settings(secrets_path)

    assert settings.cloud_enabled is True
    assert settings.api_key is not None
    assert settings.api_key.get_secret_value() == "test-key"
    assert "LLAMA_CLOUD_API_KEY" not in os.environ
