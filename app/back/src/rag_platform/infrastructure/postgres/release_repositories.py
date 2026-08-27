"""PostgreSQL adapters for releases and memberships (Fase 5).

Reflects the schema frozen by migration ``20260810_07`` and never issues DDL,
mirroring the pattern of ``project_repositories.py``. Every statement is
parameterized. Credentials are never read from or written to the database.
"""

from __future__ import annotations

from datetime import datetime

from rag_platform.domain.build_jobs import ReleaseBuildJob, ReleaseBuildJobState
from rag_platform.domain.errors import RagReleaseNotFound, ReleaseBuildJobNotFound
from rag_platform.domain.identity import IdentityKind, PlatformId
from rag_platform.domain.lifecycle import (
    RagRelease,
    RagReleaseMembership,
    ReleaseState,
)

_RELEASE_COLUMNS = (
    "rag_release_id",
    "project_id",
    "rag_variant_id",
    "corpus_snapshot_id",
    "target_binding_key",
    "configuration_version",
    "release_number",
    "state",
    "release_manifest_hash",
    "created_by",
    "created_at",
    "validated_at",
    "reason",
)


def _pid(kind: IdentityKind, value: str) -> PlatformId:
    return PlatformId(kind=kind, value=value)


class PostgresRagReleaseRepository:
    """Reads and writes ``rag_releases``."""

    def __init__(self, connection: object) -> None:
        self._connection = connection

    def add(self, release: RagRelease) -> RagRelease:
        with self._connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO rag_releases ("
                " rag_release_id, project_id, rag_variant_id, corpus_snapshot_id,"
                " target_binding_key, configuration_version, release_number, state,"
                " release_manifest_hash, created_by, created_at, validated_at, reason)"
                " VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (
                    release.rag_release_id.value,
                    release.project_id.value,
                    release.rag_variant_id.value,
                    release.corpus_snapshot_id.value,
                    release.target_binding_key,
                    release.configuration_version,
                    release.release_number,
                    release.state.value,
                    release.release_manifest_hash,
                    release.created_by,
                    release.created_at,
                    release.validated_at,
                    release.reason,
                ),
            )
        return release

    def get(self, rag_release_id: PlatformId) -> RagRelease:
        with self._connection.cursor() as cursor:
            cursor.execute(
                f"SELECT {', '.join(_RELEASE_COLUMNS)} FROM rag_releases"
                " WHERE rag_release_id = %s",
                (rag_release_id.value,),
            )
            row = cursor.fetchone()
        if row is None:
            raise RagReleaseNotFound(rag_release_id.value)
        return _row_to_release(row)

    def list_for_project(self, project_id: PlatformId) -> list[RagRelease]:
        with self._connection.cursor() as cursor:
            cursor.execute(
                f"SELECT {', '.join(_RELEASE_COLUMNS)} FROM rag_releases"
                " WHERE project_id = %s ORDER BY rag_release_id",
                (project_id.value,),
            )
            rows = cursor.fetchall()
        return [_row_to_release(row) for row in rows]

    def list_release_numbers(self, rag_variant_id: PlatformId) -> list[int]:
        with self._connection.cursor() as cursor:
            cursor.execute(
                "SELECT release_number FROM rag_releases WHERE rag_variant_id = %s",
                (rag_variant_id.value,),
            )
            return [int(row[0]) for row in cursor.fetchall()]

    def update_state(
        self,
        *,
        rag_release_id: PlatformId,
        state: ReleaseState,
        release_manifest_hash: str | None = None,
        validated_at: datetime | None = None,
        reason: str | None = None,
    ) -> RagRelease:
        # COALESCE preserva el valor actual cuando el parámetro es NULL (no borra el
        # manifiesto ni la fecha ya congelados en una transición posterior).
        with self._connection.cursor() as cursor:
            cursor.execute(
                "UPDATE rag_releases SET state = %s,"
                " release_manifest_hash = COALESCE(%s, release_manifest_hash),"
                " validated_at = COALESCE(%s, validated_at),"
                " reason = COALESCE(%s, reason)"
                " WHERE rag_release_id = %s",
                (
                    state.value,
                    release_manifest_hash,
                    validated_at,
                    reason,
                    rag_release_id.value,
                ),
            )
        return self.get(rag_release_id)


class PostgresRagReleaseMembershipRepository:
    """Reads and writes ``rag_release_memberships``."""

    def __init__(self, connection: object) -> None:
        self._connection = connection

    def add(self, membership: RagReleaseMembership) -> RagReleaseMembership:
        with self._connection.cursor() as cursor:
            # INSERT plano a propósito: un duplicado (misma release+revision u
            # ordinal) es una anomalía que debe explotar ruidosamente, nunca
            # silenciarse. El E2E limpia el estado derivado entre intentos y
            # una futura reanudación de builds debe comparar artefactos y
            # fallar cerrado ante drift, no tragarse el conflicto.
            cursor.execute(
                "INSERT INTO rag_release_memberships ("
                " rag_release_id, project_id, ordinal, source_document_revision_id,"
                " normalized_document_id, chunk_bundle_id, embedding_bundle_id,"
                " materialization_id)"
                " VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                (
                    membership.rag_release_id.value,
                    membership.project_id.value,
                    membership.ordinal,
                    membership.source_document_revision_id.value,
                    membership.normalized_document_id,
                    membership.chunk_bundle_id,
                    membership.embedding_bundle_id,
                    membership.materialization_id,
                ),
            )
        return membership

    def list_for_release(
        self, rag_release_id: PlatformId
    ) -> list[RagReleaseMembership]:
        with self._connection.cursor() as cursor:
            cursor.execute(
                "SELECT rag_release_id, project_id, ordinal,"
                " source_document_revision_id, normalized_document_id,"
                " chunk_bundle_id, embedding_bundle_id, materialization_id"
                " FROM rag_release_memberships"
                " WHERE rag_release_id = %s ORDER BY ordinal",
                (rag_release_id.value,),
            )
            rows = cursor.fetchall()
        return [_row_to_membership(row) for row in rows]


def _row_to_release(row) -> RagRelease:
    return RagRelease(
        rag_release_id=_pid(IdentityKind.RAG_RELEASE, str(row[0])),
        project_id=_pid(IdentityKind.PROJECT, str(row[1])),
        rag_variant_id=_pid(IdentityKind.RAG_VARIANT, str(row[2])),
        corpus_snapshot_id=_pid(IdentityKind.CORPUS_SNAPSHOT, str(row[3])),
        target_binding_key=str(row[4]),
        configuration_version=int(row[5]),
        release_number=int(row[6]),
        state=ReleaseState(str(row[7])),
        release_manifest_hash=row[8],
        created_by=str(row[9]),
        created_at=row[10],
        validated_at=row[11],
        reason=row[12],
    )


def _row_to_membership(row) -> RagReleaseMembership:
    return RagReleaseMembership(
        rag_release_id=_pid(IdentityKind.RAG_RELEASE, str(row[0])),
        project_id=_pid(IdentityKind.PROJECT, str(row[1])),
        ordinal=int(row[2]),
        source_document_revision_id=_pid(
            IdentityKind.SOURCE_DOCUMENT_REVISION, str(row[3])
        ),
        normalized_document_id=str(row[4]),
        chunk_bundle_id=str(row[5]),
        embedding_bundle_id=str(row[6]),
        materialization_id=str(row[7]),
    )


_BUILD_JOB_COLUMNS = (
    "build_job_id",
    "rag_release_id",
    "project_id",
    "state",
    "revisions_built",
    "reused_stages",
    "built_stages",
    "error_code",
    "error_message",
    "created_at",
    "updated_at",
)


class PostgresReleaseBuildJobRepository:
    """Estado durable de los intentos de build asíncrono (Fase 8 §D-3b).

    Refleja el esquema de la migración ``20260824_01``; nunca emite DDL. Todo
    statement es parametrizado.
    """

    def __init__(self, connection: object) -> None:
        self._connection = connection

    def create(self, job: ReleaseBuildJob) -> ReleaseBuildJob:
        with self._connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO release_build_jobs ("
                " build_job_id, rag_release_id, project_id, state, revisions_built,"
                " reused_stages, built_stages, error_code, error_message,"
                " created_at, updated_at)"
                " VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (
                    job.build_job_id,
                    job.rag_release_id.value,
                    job.project_id.value,
                    job.state.value,
                    job.revisions_built,
                    job.reused_stages,
                    job.built_stages,
                    job.error_code,
                    job.error_message,
                    job.created_at,
                    job.updated_at,
                ),
            )
        return job

    def update(self, job: ReleaseBuildJob) -> ReleaseBuildJob:
        with self._connection.cursor() as cursor:
            cursor.execute(
                "UPDATE release_build_jobs SET state = %s, revisions_built = %s,"
                " reused_stages = %s, built_stages = %s, error_code = %s,"
                " error_message = %s, updated_at = %s WHERE build_job_id = %s",
                (
                    job.state.value,
                    job.revisions_built,
                    job.reused_stages,
                    job.built_stages,
                    job.error_code,
                    job.error_message,
                    job.updated_at,
                    job.build_job_id,
                ),
            )
            if cursor.rowcount == 0:
                raise ReleaseBuildJobNotFound(job.build_job_id)
        return job

    def get(self, build_job_id: str) -> ReleaseBuildJob:
        with self._connection.cursor() as cursor:
            cursor.execute(
                f"SELECT {', '.join(_BUILD_JOB_COLUMNS)} FROM release_build_jobs"
                " WHERE build_job_id = %s",
                (build_job_id,),
            )
            row = cursor.fetchone()
        if row is None:
            raise ReleaseBuildJobNotFound(build_job_id)
        return _row_to_build_job(row)

    def latest_for_release(self, rag_release_id: PlatformId) -> ReleaseBuildJob | None:
        with self._connection.cursor() as cursor:
            cursor.execute(
                f"SELECT {', '.join(_BUILD_JOB_COLUMNS)} FROM release_build_jobs"
                " WHERE rag_release_id = %s"
                " ORDER BY created_at DESC, build_job_id DESC LIMIT 1",
                (rag_release_id.value,),
            )
            row = cursor.fetchone()
        return None if row is None else _row_to_build_job(row)


def _row_to_build_job(row) -> ReleaseBuildJob:
    return ReleaseBuildJob(
        build_job_id=str(row[0]),
        rag_release_id=_pid(IdentityKind.RAG_RELEASE, str(row[1])),
        project_id=_pid(IdentityKind.PROJECT, str(row[2])),
        state=ReleaseBuildJobState(str(row[3])),
        revisions_built=None if row[4] is None else int(row[4]),
        reused_stages=None if row[5] is None else int(row[5]),
        built_stages=None if row[6] is None else int(row[6]),
        error_code=row[7],
        error_message=row[8],
        created_at=row[9],
        updated_at=row[10],
    )
