"""Repository-level identity must be RAG Platform, not the old repo slug."""

from __future__ import annotations

import json
import re
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]


def _read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_repo_package_identity_is_rag_platform() -> None:
    package = _read_json(ROOT / "package.json")
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    front_package = _read_json(ROOT / "app/front/package.json")

    assert package["name"] == "rag_platform"
    assert (
        package["description"]
        == "RAG Platform multiproyecto con ingesta, versionado, indexacion y retrieval trazable."
    )
    assert pyproject["project"]["name"] == "rag-platform"
    assert front_package["name"] == "rag-platform-operator-ui"


def test_versioned_config_does_not_point_to_legacy_repo_or_venv_paths() -> None:
    blocked_patterns = {
        "legacy work venv": re.compile(r"venv_windows_trabajo", re.IGNORECASE),
        "legacy named venv": re.compile(r"C:[/\\]venvs[/\\]chatbot-sst", re.IGNORECASE),
        "legacy db identity": re.compile(r"(?<!LEGACY_)POSTGRES_DB=chatbot_sst"),
        "legacy repo url": re.compile(r"github\.com/jvrincon-syc/chatbot-sst"),
        "legacy absolute repo path": re.compile(
            r"C:[/\\]Users[/\\]jvrincon[/\\]Documents[/\\]chatbot_sst[/\\]chatbot-sst",
            re.IGNORECASE,
        ),
    }
    scanned_roots = (
        ROOT / "README.md",
        ROOT / "AGENTS.md",
        ROOT / "CLAUDE.md",
        ROOT / "README_REGLAS.md",
        ROOT / "package.json",
        ROOT / "pyproject.toml",
        ROOT / "secrets.example.env",
        ROOT / "docs",
        ROOT / "scripts",
        ROOT / "app",
    )
    suffixes = {".md", ".py", ".ts", ".tsx", ".mjs", ".json", ".toml", ".yml", ".yaml", ".env", ".txt"}
    violations: list[str] = []

    def candidate_files(path: Path) -> list[Path]:
        if path.is_file():
            return [path]
        return [
            item
            for item in path.rglob("*")
            if item.is_file()
            and item.suffix in suffixes
            and "node_modules" not in item.parts
            and "__pycache__" not in item.parts
        ]

    for root in scanned_roots:
        for file_path in candidate_files(root):
            if file_path == Path(__file__):
                continue
            text = file_path.read_text(encoding="utf-8", errors="ignore")
            for label, pattern in blocked_patterns.items():
                if pattern.search(text):
                    violations.append(f"{label}: {file_path.relative_to(ROOT)}")

    assert violations == []
