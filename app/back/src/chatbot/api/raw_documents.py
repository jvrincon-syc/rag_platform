"""Serve raw source documents for citation links.

Single shared implementation included by the pipeline app (``api.app.create_app``), so it inherits
that app's bearer-auth dependency — the endpoint is NOT public. The dedicated chatbot runtime mounts
the same pipeline app, so it gets this route too without a second copy.

Markdown files are rendered to a minimal, self-contained HTML page so citations open readable inline
(not a download); PDFs stream as-is for the browser's built-in viewer.

PR-1 1.7 (citas project-aware): la ruta legacy ``/api/documents/raw/{file_path}``
sirve desde una raíz global (``SST_RAW_DOCS_ROOT``) sin ``project_id`` — dos
proyectos con el mismo ``source_relpath`` colisionan en la misma URL y no hay
verificación de pertenencia. La ruta nueva
``/api/projects/{project_id}/document-revisions/{revision_id}/raw`` resuelve por
revisión (``GetProjectDocumentRevisionRawLocationUseCase``): exige scope de
proyecto y rechaza una revisión de otro proyecto. La ruta legacy se mantiene
temporalmente (deprecada) hasta que el emisor de citas emita la URL nueva.
"""
from __future__ import annotations

import os
from pathlib import Path

from fastapi import APIRouter, Depends, Response, status
from fastapi.responses import FileResponse, HTMLResponse
from markdown_it import MarkdownIt

from rag_platform.api.dependencies import (
    get_actor_provider,
    get_platform_services,
    require_rag_platform_enabled,
)
from rag_platform.application.actor_provider import TrustedPlatformActorProvider
from rag_platform.application.platform_access import PlatformActor
from rag_platform.application.services import RagPlatformServices
from rag_platform.domain.identity import IdentityKind, PlatformId

router = APIRouter()

# html=False: raw HTML embedded in a doc is escaped, not executed — no XSS from corpus content.
_MD = MarkdownIt("commonmark", {"html": False})

_HTML_SHELL = """<!doctype html>
<html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<style>
 body{max-width:820px;margin:2rem auto;padding:0 1rem;
   font:16px/1.6 system-ui,"Segoe UI",Arial,sans-serif;color:#1a1a1a}
 h1,h2,h3{line-height:1.25} pre{background:#f5f5f5;padding:.75rem;overflow:auto;border-radius:6px}
 code{background:#f0f0f0;padding:.1rem .3rem;border-radius:4px}
 table{border-collapse:collapse} td,th{border:1px solid #ddd;padding:.4rem .6rem} a{color:#0b5cad}
</style></head><body>__BODY__</body></html>"""


def _resolve_contained(raw_root: Path, relpath: str) -> Path | None:
    """Resolve ``relpath`` under ``raw_root``; ``None`` if it escapes (traversal)."""

    raw_root = raw_root.resolve()
    target = (raw_root / relpath).resolve()
    if not target.is_relative_to(raw_root):
        return None
    return target


def _serve_file(target: Path) -> Response:
    """Render ``.md`` inline as HTML; stream everything else by media type."""

    if not target.is_file():
        return Response(status_code=status.HTTP_404_NOT_FOUND)
    if target.suffix.lower() in (".md", ".markdown"):
        body = _MD.render(target.read_text(encoding="utf-8"))
        page = _HTML_SHELL.replace("__TITLE__", target.name).replace("__BODY__", body)
        return HTMLResponse(page)
    media_type = "application/pdf" if target.suffix.lower() == ".pdf" else "application/octet-stream"
    return FileResponse(target, media_type=media_type, filename=target.name)


@router.get("/api/documents/raw/{file_path:path}")
def serve_raw_document(file_path: str) -> Response:
    """Return a raw document by its path under ``SST_RAW_DOCS_ROOT`` (deprecated).

    Bearer auth is enforced by the app-level dependency. Path traversal is blocked by resolving the
    target and confirming it stays inside the raw docs root. ``.md`` is rendered to HTML; other
    files stream by media type.

    Deprecated (PR-1 1.7): global root, no ``project_id``, no ownership check. Kept temporarily for
    compatibility; prefer ``GET /api/projects/{project_id}/document-revisions/{revision_id}/raw``.
    """
    raw_root = Path(os.environ.get("SST_RAW_DOCS_ROOT", "data/docs_raw"))
    target = _resolve_contained(raw_root, file_path)
    if target is None:
        return Response(status_code=status.HTTP_403_FORBIDDEN)
    return _serve_file(target)


def _get_actor(
    provider: TrustedPlatformActorProvider = Depends(get_actor_provider),
) -> PlatformActor:
    return provider.current_actor()


@router.get(
    "/api/projects/{project_id}/document-revisions/{revision_id}/raw",
    dependencies=[Depends(require_rag_platform_enabled)],
)
def serve_project_document_revision_raw(
    project_id: str,
    revision_id: str,
    services: RagPlatformServices = Depends(get_platform_services),
    actor: PlatformActor = Depends(_get_actor),
) -> Response:
    """Return a raw document by project + revision id (PR-1 1.7 — project-aware citations).

    Authorization and ownership are enforced by
    ``GetProjectDocumentRevisionRawLocationUseCase`` (project scope +
    ``RevisionProjectMismatch``, both translated to the shared error envelope by
    ``api/app.py``) before any filesystem access. Path traversal is blocked the
    same way as the legacy route: resolve and confirm containment under the
    resolved raw root.
    """
    location = services.get_document_revision_raw_location.execute(
        project_id=PlatformId.parse(IdentityKind.PROJECT, project_id),
        source_document_revision_id=PlatformId.parse(
            IdentityKind.SOURCE_DOCUMENT_REVISION, revision_id
        ),
        actor=actor,
    )
    target = _resolve_contained(location.raw_root, location.source_relpath)
    if target is None:
        return Response(status_code=status.HTTP_403_FORBIDDEN)
    return _serve_file(target)


if __name__ == "__main__":  # ponytail self-check
    html = _MD.render("# Título\n\n- uno\n- dos\n\n**negrita** y `code`.")
    assert "<h1>" in html and "<li>uno</li>" in html and "<strong>negrita</strong>" in html, html
    print("markdown render OK")
