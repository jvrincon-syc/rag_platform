"""PR-1 1.7 — citas project-aware: HTTP contract of the raw-by-revision route.

``GET /api/projects/{project_id}/document-revisions/{revision_id}/raw`` replaces
the global, project-unaware ``GET /api/documents/raw/{file_path}`` (kept
temporarily, deprecated) for citation links. Covers: resolves by revision,
rejects a revision that belongs to another project, and out-of-scope actors.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterator

import pytest
from fastapi.testclient import TestClient

from api.app import create_app
from api.dependencies import build_pipeline_services
from core.feature_flags import FeatureFlags
from core.http_auth import AUTH_CREDENTIALS_JSON_KEY, ConfiguredBearerAuth

GLOBAL_TOKEN = "token-global-op"
ALPHA_TOKEN = "token-alpha-op"


def _authenticator() -> ConfiguredBearerAuth:
    return ConfiguredBearerAuth(
        {
            AUTH_CREDENTIALS_JSON_KEY: (
                "["
                '{"principal_id":"op-1","token":"' + GLOBAL_TOKEN + '"},'
                '{"principal_id":"jose","token":"'
                + ALPHA_TOKEN
                + '","project_scope":["proj_alpha"]}'
                "]"
            )
        }
    )


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def env(tmp_path: Path) -> Iterator[tuple[TestClient, Path]]:
    services = build_pipeline_services(
        chunks_root=tmp_path / "chunks",
        embeddings_root=tmp_path / "embeddings",
        feature_flags=FeatureFlags(rag_platform_v1=True),
        allow_mock_engine=True,
        http_authenticator=_authenticator(),
    )
    with TestClient(create_app(services=services)) as client:
        client.headers.update(_auth_headers(GLOBAL_TOKEN))
        yield client, tmp_path


def _create_project(client: TestClient, slug: str) -> None:
    assert (
        client.post(
            "/api/platform/projects",
            json={"project_slug": slug, "display_name": slug.title()},
        ).status_code
        == 201
    )


def _upload(
    client: TestClient,
    slug: str,
    *,
    source_relpath: str,
    content: bytes,
    headers: dict[str, str] | None = None,
) -> dict:
    response = client.post(
        f"/api/platform/projects/proj_{slug}/documents",
        files={"file": (source_relpath.split("/")[-1], content, "text/markdown")},
        data={"source_relpath": source_relpath},
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_citation_resuelve_por_revision(env: tuple[TestClient, Path]) -> None:
    client, _ = env
    _create_project(client, "demo")
    revision = _upload(
        client, "demo", source_relpath="manuals/guia.md", content=b"# Hola\n"
    )
    revision_id = revision["source_document_revision_id"]

    response = client.get(
        f"/api/projects/proj_demo/document-revisions/{revision_id}/raw"
    )

    assert response.status_code == 200, response.text
    assert "<h1>Hola</h1>" in response.text


def test_citation_rechaza_revision_de_otro_proyecto(
    env: tuple[TestClient, Path],
) -> None:
    client, _ = env
    _create_project(client, "alpha")
    _create_project(client, "beta")
    revision = _upload(
        client, "alpha", source_relpath="manuals/guia.md", content=b"# Hola\n"
    )
    revision_id = revision["source_document_revision_id"]

    # La revisión pertenece a alpha; se pide por beta.
    response = client.get(
        f"/api/projects/proj_beta/document-revisions/{revision_id}/raw"
    )

    assert response.status_code == 409, response.text
    assert response.json()["error"]["code"] == "REVISION_PROJECT_MISMATCH"


def test_citation_fuera_de_scope_403(env: tuple[TestClient, Path]) -> None:
    client, _ = env
    _create_project(client, "beta")
    revision = _upload(
        client, "beta", source_relpath="manuals/guia.md", content=b"# Hola\n"
    )
    revision_id = revision["source_document_revision_id"]

    response = client.get(
        f"/api/projects/proj_beta/document-revisions/{revision_id}/raw",
        headers=_auth_headers(ALPHA_TOKEN),
    )

    assert response.status_code == 403, response.text
    assert response.json()["error"]["code"] == "PLATFORM_ACCESS_DENIED"


def test_citation_revision_inexistente_404(env: tuple[TestClient, Path]) -> None:
    client, _ = env
    _create_project(client, "demo")

    response = client.get(
        "/api/projects/proj_demo/document-revisions/srev_nope/raw"
    )

    assert response.status_code == 404, response.text
    assert response.json()["error"]["code"] == "SOURCE_DOCUMENT_REVISION_NOT_FOUND"


def test_legacy_route_sigue_disponible(env: tuple[TestClient, Path]) -> None:
    """The deprecated global route stays up until every citation emitter moves off it."""
    client, _ = env
    response = client.get("/api/documents/raw/does-not-exist.md")
    assert response.status_code == 404
