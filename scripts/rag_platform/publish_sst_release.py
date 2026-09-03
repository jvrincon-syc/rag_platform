"""Publica UNA release PUBLISHED para sst-general reusando el corpus ya construido.

Cadena de casos de uso in-process (sin HTTP/auth/idempotency), reusando el
contenedor `build_pipeline_services_from_env` ya cableado:

    corpus snapshot -> create_release_draft -> build (REUSA los 353 vectores
    existentes, crea 55 membresias) -> validate (congela manifest) -> publish.

NO borra derivados. El build reusa por identidad los artefactos materializados;
`BuildRagReleaseUseCase` crea una `rag_release_membership` por documento aunque
reuse (release_build_service.py:200), y el retrieval Postgres resuelve la lane por
`rag_release_memberships`, no por `rag_release_id` estampado en runs. Por eso
publicar sobre el corpus reusado deja el retrieval funcional sin re-embeber.

Uso:
    C:/venvs/rag_platform/Scripts/python.exe scripts/rag_platform/publish_sst_release.py
"""

from __future__ import annotations

import os
import sys
import uuid
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT / "app" / "back" / "src"))
sys.path.insert(0, str(_REPO_ROOT / "scripts" / "indexing"))

_PROJECT_SLUG = "sst-general"
_PROJECT_ID = "proj_sst-general"
_VARIANT_ID = "ragv_local-bge"
_BINDING_KEY = "primary"
_ACTOR_ID = "operator-publish-sst"


def _dsn() -> str:
    from prepare_postgres_indexing import build_dsn_from_env, load_env_file

    dsn = build_dsn_from_env(dict(load_env_file(_REPO_ROOT / "secrets.env")))
    assert dsn, "sin DSN de PostgreSQL en secrets.env"
    return dsn


def _all_revision_ids(dsn: str) -> list[str]:
    import psycopg2
    from psycopg2.extensions import parse_dsn

    conn = psycopg2.connect(**parse_dsn(dsn))
    try:
        with conn.cursor() as cur:
            # Orden estable por relpath para un snapshot determinista.
            cur.execute(
                "SELECT source_document_revision_id FROM source_document_revisions"
                " WHERE project_id = %s ORDER BY source_relpath",
                (_PROJECT_ID,),
            )
            return [str(r[0]) for r in cur.fetchall()]
    finally:
        conn.close()


def _verify(dsn: str, release_id: str) -> None:
    import psycopg2
    from psycopg2.extensions import parse_dsn

    conn = psycopg2.connect(**parse_dsn(dsn))
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT state FROM rag_releases WHERE rag_release_id = %s", (release_id,)
            )
            state = cur.fetchone()
            cur.execute(
                "SELECT count(*) FROM rag_release_memberships WHERE rag_release_id = %s",
                (release_id,),
            )
            memberships = cur.fetchone()[0]
            # Misma resolucion de lane que PostgresReleaseScopedRetrievalPort._resolve_lane.
            cur.execute(
                """
                SELECT count(DISTINCT (eb.embedding_profile_id, im.indexing_target_id,
                                       eb.corpus_version))
                FROM rag_release_memberships AS m
                JOIN embedding_bundles AS eb
                  ON eb.embedding_bundle_id = m.embedding_bundle_id
                 AND eb.project_id = m.project_id
                JOIN indexing_materializations AS im
                  ON im.materialization_id = m.materialization_id
                 AND im.project_id = m.project_id
                WHERE m.project_id = %s AND m.rag_release_id = %s
                """,
                (_PROJECT_ID, release_id),
            )
            lanes = cur.fetchone()[0]
    finally:
        conn.close()
    print(f"  state         = {state[0] if state else None}")
    print(f"  memberships   = {memberships}")
    print(f"  lanes_resolved= {lanes}  (retrieval exige exactamente 1)")
    assert state and state[0] == "published", "la release no quedo PUBLISHED"
    assert memberships > 0, "sin membresias -> retrieval vacio"
    assert lanes == 1, "la release no resuelve exactamente una lane"


def main() -> int:
    dsn = _dsn()
    os.environ["RAG_PLATFORM_POSTGRES_DSN"] = dsn
    os.environ["SST_POSTGRES_DSN"] = dsn
    os.environ["SST_PERSISTENCE_MODE"] = "postgres"
    os.environ["SST_FEATURE_RAG_PLATFORM_V1"] = "true"

    from api.dependencies import build_pipeline_services_from_env
    from rag_platform.application.platform_access import PlatformActor
    from rag_platform.domain.identity import IdentityKind, PlatformId

    actor = PlatformActor(actor_id=_ACTOR_ID)  # project_scope=None => operador sin restriccion
    revision_ids = _all_revision_ids(dsn)
    print(f"revisiones = {len(revision_ids)}")
    assert revision_ids, "no hay revisiones para el proyecto"

    chunks_root = _REPO_ROOT / "data" / "projects" / _PROJECT_SLUG / "chunks"
    embeddings_root = _REPO_ROOT / "data" / "projects" / _PROJECT_SLUG / "embeddings"
    services = build_pipeline_services_from_env(
        chunks_root=chunks_root, embeddings_root=embeddings_root
    )
    try:
        rp = services.rag_platform
        assert rp is not None, "rag_platform no cableado (flag rag_platform_v1?)"

        print("1) corpus snapshot ...")
        snapshot = rp.create_corpus_snapshot.execute(
            project_id=_PROJECT_SLUG,
            document_revision_ids=revision_ids,
            actor=actor,
        )
        print(f"   snapshot = {snapshot.corpus_snapshot_id.value}")

        print("2) create release draft ...")
        release = rp.create_release_draft.execute(
            rag_variant_id=PlatformId(kind=IdentityKind.RAG_VARIANT, value=_VARIANT_ID),
            corpus_snapshot_id=snapshot.corpus_snapshot_id,
            target_binding_key=_BINDING_KEY,
            actor=actor,
        )
        release_id = release.rag_release_id
        print(f"   release = {release_id.value}")

        print("3) build (reusa artefactos, crea membresias) ...")
        report = services.rag_platform_build.execute(
            rag_release_id=release_id, actor=actor
        )
        print(
            f"   revisions={report.revisions_built} reused_stages={report.reused_stages}"
            f" built_stages={report.built_stages}"
        )

        print("4) validate (congela manifest) ...")
        rp.validate_release.execute(rag_release_id=release_id, actor=actor)

        print("5) publish ...")
        rp.publish_release.execute(rag_release_id=release_id, actor=actor)
    finally:
        services.close()

    print("verificacion en BD:")
    _verify(dsn, release_id.value)
    print(f"\nPUBLISHED release_id = {release_id.value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
