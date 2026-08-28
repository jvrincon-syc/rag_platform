"""``RunPipelineProjectNormalizer`` registra el normalizado en el read-model.

``run_pipeline`` solo devuelve conteos agregados (``processed``/``failed``/...),
sin detalle por documento. Antes de este fix, el adaptador nunca escribía en
``NormalizedArtifactRepository``/``project_normalized_documents``: esa tabla
solo se poblaba después, en el build de una release (``artifact_reuse_service``/
``release_build_resolver``). Efecto observado: tras un normalize exitoso desde
Platform, el read-model de Documentos seguía mostrando todo como ``pending``.

La señal de éxito por revisión es la existencia del markdown promovido en
``normalized_root`` (las revisiones fallidas nunca llegan a escribirse).
"""

from __future__ import annotations

from rag_platform.domain.identity import IdentityKind, PlatformId
from rag_platform.infrastructure.normalization.run_pipeline_normalizer import (
    RunPipelineProjectNormalizer,
)
from rag_platform.infrastructure.storage.project_storage import ProjectStorageResolver


class _FakeProject:
    def __init__(self, project_id: PlatformId) -> None:
        self.project_id = project_id


class _FakeRevision:
    def __init__(self, revision_id: PlatformId, source_relpath: str) -> None:
        self.source_document_revision_id = revision_id
        self.source_relpath = source_relpath


class _FakeNormalizedArtifactRepository:
    def __init__(self) -> None:
        self.added: list = []

    def add(self, artifact):
        self.added.append(artifact)
        return artifact

    def find(self, **kwargs):
        return None

    def list_normalized_revision_ids(self, project_id):
        return frozenset()


def _pid(kind: IdentityKind, value: str) -> PlatformId:
    return PlatformId(kind=kind, value=value)


def test_register_normalized_solo_para_revisiones_con_markdown_en_disco(tmp_path) -> None:
    storage = ProjectStorageResolver(tmp_path)
    project_id = _pid(IdentityKind.PROJECT, "proj_demo")
    project = _FakeProject(project_id)
    repo = _FakeNormalizedArtifactRepository()
    normalizer = RunPipelineProjectNormalizer(storage, normalized_artifacts=repo)

    ok_id = _pid(IdentityKind.SOURCE_DOCUMENT_REVISION, "srev_ok")
    failed_id = _pid(IdentityKind.SOURCE_DOCUMENT_REVISION, "srev_failed")
    revisions = (
        _FakeRevision(ok_id, "docs/ok.pdf"),
        _FakeRevision(failed_id, "docs/failed.pdf"),
    )

    normalized_root = storage.resolve_root(project_id, "normalized")
    (normalized_root / "docs").mkdir(parents=True)
    (normalized_root / "docs" / "ok.md").write_text("# ok", encoding="utf-8")
    # "failed.md" deliberadamente ausente: simula el documento que run_pipeline
    # contó en summary["failed"] y nunca escribió a disco.

    normalizer.register_normalized(
        project=project,
        revisions=revisions,
        normalized_root=normalized_root,
        processing_profile_fingerprint="f" * 64,
    )

    assert [a.source_document_revision_id.value for a in repo.added] == ["srev_ok"]
    assert repo.added[0].artifact_relpath == "normalized/docs/ok.md"
    assert repo.added[0].project_id == project_id


def test_register_normalized_no_op_sin_repositorio(tmp_path) -> None:
    storage = ProjectStorageResolver(tmp_path)
    normalizer = RunPipelineProjectNormalizer(storage)

    # Sin repo inyectado: no debe explotar (lo llama el CLI incluso cuando el
    # caller no wireó persistencia, p. ej. pruebas del wrapper).
    normalizer.register_normalized(
        project=_FakeProject(_pid(IdentityKind.PROJECT, "proj_demo")),
        revisions=(),
        normalized_root=tmp_path,
        processing_profile_fingerprint="f" * 64,
    )
