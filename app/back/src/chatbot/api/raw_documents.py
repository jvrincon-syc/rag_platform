"""Serve raw source documents for citation links.

Single shared implementation included by the pipeline app (``api.app.create_app``), so it inherits
that app's bearer-auth dependency — the endpoint is NOT public. The dedicated chatbot runtime mounts
the same pipeline app, so it gets this route too without a second copy.

Markdown files are rendered to a minimal, self-contained HTML page so citations open readable inline
(not a download); PDFs stream as-is for the browser's built-in viewer.
"""
from __future__ import annotations

import os
from pathlib import Path

from fastapi import APIRouter, Response, status
from fastapi.responses import FileResponse, HTMLResponse
from markdown_it import MarkdownIt

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


@router.get("/api/documents/raw/{file_path:path}")
def serve_raw_document(file_path: str) -> Response:
    """Return a raw document by its path under ``SST_RAW_DOCS_ROOT``.

    Bearer auth is enforced by the app-level dependency. Path traversal is blocked by resolving the
    target and confirming it stays inside the raw docs root. ``.md`` is rendered to HTML; other
    files stream by media type.
    """
    raw_root = Path(os.environ.get("SST_RAW_DOCS_ROOT", "data/docs_raw")).resolve()
    target = (raw_root / file_path).resolve()
    if not target.is_relative_to(raw_root):
        return Response(status_code=status.HTTP_403_FORBIDDEN)
    if not target.is_file():
        return Response(status_code=status.HTTP_404_NOT_FOUND)

    if target.suffix.lower() in (".md", ".markdown"):
        body = _MD.render(target.read_text(encoding="utf-8"))
        page = _HTML_SHELL.replace("__TITLE__", target.name).replace("__BODY__", body)
        return HTMLResponse(page)

    media_type = "application/pdf" if target.suffix.lower() == ".pdf" else "application/octet-stream"
    return FileResponse(target, media_type=media_type, filename=target.name)


if __name__ == "__main__":  # ponytail self-check
    html = _MD.render("# Título\n\n- uno\n- dos\n\n**negrita** y `code`.")
    assert "<h1>" in html and "<li>uno</li>" in html and "<strong>negrita</strong>" in html, html
    print("markdown render OK")
