"""Adaptador que normaliza reutilizando el motor de ingesta ``run_pipeline``.

Implementa el puerto ``ProjectDocumentNormalizer`` sin reimplementar el pipeline:
escanea los bytes raw del proyecto, corre el preflight de identidad fail-closed
(``resolve_platform_contexts_or_raise``) y delega en el mismo ``run_pipeline`` que
usa la lane legacy, con swap atómico staging → normalized. La función pura
``execute_normalize_pipeline`` es la orquestación física compartida por este
adaptador HTTP y por el CLI ``run_project_ingestion.py`` (única fuente de la
lógica de staging/promote/cloud-gating).

Por defecto es on-prem: fuerza ``LLAMA_CLOUD_ENABLED=false`` para que los PDFs
corporativos se parseen localmente (pdfium + tesseract) y nunca se envíen a un
servicio externo sin autorización registrada (SECURITY_AND_DATA §3).
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path, PurePosixPath
from typing import Callable

from ingestion.application.platform_metadata import (
    PlatformContextResolutionError,
    resolve_platform_contexts_or_raise,
)
from ingestion.inventory.scanner import scan_docs_raw
from ingestion.paths import canonical_relpath
from rag_platform.application.context import NormalizedArtifactRepository
from rag_platform.application.project_normalization_service import (
    ProjectNormalizeOutcome,
)
from rag_platform.domain.errors import ProjectNormalizationIncomplete
from rag_platform.domain.models import (
    NormalizedDocumentArtifact,
    RagProject,
    SourceDocumentRevision,
)
from rag_platform.infrastructure.storage.project_storage import ProjectStorageResolver

#: Etiquetas del escaneo raw (identidad la lleva la revisión lógica, no el scan).
_RAW_CORPUS_VERSION = "platform-raw"
_RAW_PIPELINE_VERSION = "platform-raw-v1"
#: Versiones por defecto del normalizado de plataforma (mismas que el CLI).
_CORPUS_VERSION = "platform-normalized"
_PIPELINE_VERSION = "2.0.0"


def execute_normalize_pipeline(
    *,
    raw_root: Path,
    normalized_root: Path,
    resolver: Callable[[object], object],
    only_sources: tuple[str, ...],
    force: bool,
    corpus_version: str,
    pipeline_version: str,
    request_id: str,
    allow_cloud: bool,
    env_file: str | Path | None = None,
) -> dict:
    """Corre ``run_pipeline`` raw→normalized con promote atómico y devuelve el resumen.

    ``env_file`` carga secrets como el CLI legacy; en HTTP se pasa ``None`` porque
    el proceso servidor ya trae el entorno cargado. Fuerza on-prem salvo
    ``allow_cloud``.
    """

    # run_pipeline arrastra LlamaSettings/pdfium/tesseract: import perezoso para no
    # encarecer el import del módulo (lo cargan el router y la composición).
    from ingestion.pipeline import run_pipeline

    if env_file is not None:
        from ingestion.config.env import load_secrets_env

        load_secrets_env(Path(env_file), apply=True)
    if not allow_cloud:
        os.environ["LLAMA_CLOUD_ENABLED"] = "false"

    # promote=True exige un staging DISTINTO del root live: el pipeline escribe/valida
    # en staging y luego hace el swap atómico staging → normalized.
    staging_root = normalized_root.parent / f".{normalized_root.name}.staging"
    if staging_root.exists():
        shutil.rmtree(staging_root)
    try:
        return run_pipeline(
            docs_raw=raw_root,
            docs_normalized=normalized_root,
            staging_root=staging_root,
            promote=True,
            force=force,
            only_sources=list(only_sources) or None,
            corpus_version=corpus_version,
            pipeline_version=pipeline_version,
            platform_context_resolver=resolver,
            request_id=request_id,
        )
    finally:
        if staging_root.exists():
            shutil.rmtree(staging_root)


class RunPipelineProjectNormalizer:
    """Adaptador infra del puerto ``ProjectDocumentNormalizer``."""

    def __init__(
        self,
        storage: ProjectStorageResolver,
        *,
        normalized_artifacts: NormalizedArtifactRepository | None = None,
        env_file: str | Path | None = None,
        allow_cloud: bool = False,
    ) -> None:
        self._storage = storage
        self._normalized_artifacts = normalized_artifacts
        self._env_file = env_file
        self._allow_cloud = allow_cloud

    def normalize(
        self,
        *,
        project: RagProject,
        revisions: tuple[SourceDocumentRevision, ...],
        processing_profile_id: str,
        processing_profile_fingerprint: str,
        rag_variant_id: str | None,
        semantic_recipe_fingerprint: str | None,
        force: bool,
    ) -> ProjectNormalizeOutcome:
        raw_root = self._storage.resolve_declared_root(project, "raw")
        normalized_root = self._storage.resolve_declared_root(project, "normalized")

        records = scan_docs_raw(
            raw_root,
            corpus_version=_RAW_CORPUS_VERSION,
            pipeline_version=_RAW_PIPELINE_VERSION,
        )
        wanted = {canonical_relpath(r.source_relpath) for r in revisions}
        by_relpath = {canonical_relpath(r.source_relpath): r for r in revisions}
        # Fail-closed: cada revisión pedida debe tener sus bytes raw en disco.
        on_disk = {canonical_relpath(rec.source_relpath) for rec in records}
        missing = sorted(wanted - on_disk)
        if missing:
            raise ProjectNormalizationIncomplete(
                f"raw bytes missing for selected documents: {missing}"
            )
        selected = [
            rec for rec in records if canonical_relpath(rec.source_relpath) in wanted
        ]

        try:
            contexts = resolve_platform_contexts_or_raise(
                records=selected,
                revisions_by_relpath=by_relpath,
                project_id=project.project_id.value,
                processing_profile_id=processing_profile_id,
                processing_profile_fingerprint=processing_profile_fingerprint,
                rag_variant_id=rag_variant_id,
                semantic_recipe_fingerprint=semantic_recipe_fingerprint,
            )
        except PlatformContextResolutionError as exc:
            raise ProjectNormalizationIncomplete(str(exc)) from exc

        summary = execute_normalize_pipeline(
            raw_root=raw_root,
            normalized_root=normalized_root,
            resolver=lambda record: contexts.get(
                canonical_relpath(record.source_relpath)
            ),
            only_sources=tuple(r.source_relpath for r in revisions),
            force=force,
            corpus_version=_CORPUS_VERSION,
            pipeline_version=_PIPELINE_VERSION,
            request_id=f"platform_normalize_{project.project_id.value}",
            allow_cloud=self._allow_cloud,
            env_file=self._env_file,
        )
        if self._normalized_artifacts is not None:
            self.register_normalized(
                project=project,
                revisions=revisions,
                normalized_root=normalized_root,
                processing_profile_fingerprint=processing_profile_fingerprint,
            )
        return ProjectNormalizeOutcome(
            rag_variant_id=rag_variant_id or "",
            processed=int(summary.get("processed", 0)),
            needs_review=int(summary.get("needs_review", 0)),
            skipped=int(summary.get("skipped", 0)),
            failed=int(summary.get("failed", 0)),
            revision_ids=tuple(r.source_document_revision_id.value for r in revisions),
        )

    def register_normalized(
        self,
        *,
        project: RagProject,
        revisions: tuple[SourceDocumentRevision, ...],
        normalized_root: Path,
        processing_profile_fingerprint: str,
    ) -> None:
        """Registra en el read-model cada revisión cuyo markdown quedó en disco.

        ``run_pipeline`` solo devuelve conteos agregados (no detalle por
        documento), así que la señal de éxito por revisión es la existencia del
        archivo promovido: las que fallaron nunca llegan a escribirse. El
        ``artifact_relpath`` replica la convención de
        ``Schema2FilesystemNormalizedArtifactBuilder`` (release_build_resolver.py)
        para que el reuso de build encuentre el mismo artefacto. Público: lo
        llaman tanto ``normalize()`` (endpoint HTTP) como el CLI
        ``run_project_ingestion.py``, que ejecuta ``execute_normalize_pipeline``
        fuera de la conexión y reabre una después solo para este registro.
        """
        if self._normalized_artifacts is None:
            return
        for revision in revisions:
            # Normaliza separadores Windows a POSIX: en intérprete POSIX `Path` no
            # parte por `\`, así un source_relpath Windows quedaría como un único
            # componente con backslash (ni el artifact_relpath ni el existencial
            # coincidirían con el archivo real en disco).
            source_posix = revision.source_relpath.replace("\\", "/")
            artifact_relpath = (
                f"normalized/{PurePosixPath(source_posix).with_suffix('.md').as_posix()}"
            )
            if not (normalized_root / PurePosixPath(source_posix).with_suffix(".md")).exists():
                continue
            self._normalized_artifacts.add(
                NormalizedDocumentArtifact(
                    project_id=project.project_id,
                    source_document_revision_id=revision.source_document_revision_id,
                    processing_profile_fingerprint=processing_profile_fingerprint,
                    schema_version="2.0",
                    artifact_relpath=artifact_relpath,
                )
            )
