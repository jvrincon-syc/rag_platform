"""Fundación del build asíncrono durable (Fase 8 §D-3b, Task 1 del rework).

Cubre las lecturas/escrituras del job durable (repo in-memory) y los casos de uso
de encolado y consulta de estado, con scope fail-closed. El worker que corre el
motor (Task 2) NO se ejerce aquí: esta capa solo persiste y autoriza.

PENDIENTE DE EJECUCIÓN por el operador.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

import pytest

from rag_platform.application.platform_access import PlatformActor
from rag_platform.application.release_build_job_service import (
    EnqueueReleaseBuildUseCase,
    GetReleaseBuildStatusUseCase,
)
from rag_platform.domain.build_jobs import ReleaseBuildJob, ReleaseBuildJobState
from rag_platform.domain.errors import (
    PlatformAccessDenied,
    ReleaseBuildJobNotFound,
)
from rag_platform.application.release_build_service import RagReleaseBuildReport
from rag_platform.domain.errors import RagPlatformError
from rag_platform.domain.identity import IdentityKind, PlatformId
from rag_platform.infrastructure.in_memory.repositories import (
    AllowAllAccessPolicy,
    InMemoryReleaseBuildJobRepository,
)
from rag_platform.infrastructure.release_build_runner import run_one_build


def _pid(kind: IdentityKind, value: str) -> PlatformId:
    return PlatformId(kind=kind, value=value)


_RELEASE = _pid(IdentityKind.RAG_RELEASE, "ragr_demo")
_PROJECT = _pid(IdentityKind.PROJECT, "proj_demo")
_T0 = datetime(2026, 8, 24, 12, 0, 0, tzinfo=timezone.utc)
_T1 = datetime(2026, 8, 24, 12, 5, 0, tzinfo=timezone.utc)


@dataclass(frozen=True)
class _StubRelease:
    rag_release_id: PlatformId
    project_id: PlatformId


class _StubReleases:
    def __init__(self, release: _StubRelease) -> None:
        self._release = release

    def get(self, rag_release_id: PlatformId) -> _StubRelease:
        return self._release


def _job(build_job_id: str, *, state: ReleaseBuildJobState = ReleaseBuildJobState.QUEUED) -> ReleaseBuildJob:
    return ReleaseBuildJob(
        build_job_id=build_job_id,
        rag_release_id=_RELEASE,
        project_id=_PROJECT,
        state=state,
        created_at=_T0,
        updated_at=_T0,
    )


# --------------------------------------------------------------------------- #
# Repo in-memory                                                              #
# --------------------------------------------------------------------------- #


def test_repo_create_get_y_latest_devuelven_el_job() -> None:
    repo = InMemoryReleaseBuildJobRepository()
    repo.create(_job("bjob_1"))

    assert repo.get("bjob_1").state is ReleaseBuildJobState.QUEUED
    assert repo.latest_for_release(_RELEASE).build_job_id == "bjob_1"


def test_repo_latest_devuelve_el_mas_reciente() -> None:
    repo = InMemoryReleaseBuildJobRepository()
    repo.create(_job("bjob_old"))
    newer = _job("bjob_new").model_copy(update={"created_at": _T1, "updated_at": _T1})
    repo.create(newer)

    assert repo.latest_for_release(_RELEASE).build_job_id == "bjob_new"


def test_repo_update_transiciona_estado() -> None:
    repo = InMemoryReleaseBuildJobRepository()
    repo.create(_job("bjob_1"))
    running = repo.get("bjob_1").model_copy(
        update={"state": ReleaseBuildJobState.RUNNING, "updated_at": _T1}
    )
    repo.update(running)

    assert repo.get("bjob_1").state is ReleaseBuildJobState.RUNNING


def test_repo_get_y_update_de_job_inexistente_fallan_cerrado() -> None:
    repo = InMemoryReleaseBuildJobRepository()
    with pytest.raises(ReleaseBuildJobNotFound):
        repo.get("bjob_missing")
    with pytest.raises(ReleaseBuildJobNotFound):
        repo.update(_job("bjob_missing"))


def test_repo_latest_sin_jobs_devuelve_none() -> None:
    assert InMemoryReleaseBuildJobRepository().latest_for_release(_RELEASE) is None


# --------------------------------------------------------------------------- #
# Casos de uso                                                                #
# --------------------------------------------------------------------------- #


def _enqueue_use_case(repo: InMemoryReleaseBuildJobRepository) -> EnqueueReleaseBuildUseCase:
    return EnqueueReleaseBuildUseCase(
        releases=_StubReleases(_StubRelease(rag_release_id=_RELEASE, project_id=_PROJECT)),
        jobs=repo,
        access_policy=AllowAllAccessPolicy(),
    )


def test_enqueue_crea_job_queued_autorizado() -> None:
    repo = InMemoryReleaseBuildJobRepository()
    actor = PlatformActor(actor_id="op", project_scope=None)

    job = _enqueue_use_case(repo).execute(
        rag_release_id=_RELEASE, build_job_id="bjob_1", actor=actor, now=_T0
    )

    assert job.state is ReleaseBuildJobState.QUEUED
    assert job.project_id == _PROJECT
    assert repo.latest_for_release(_RELEASE).build_job_id == "bjob_1"


def test_enqueue_fuera_de_scope_falla_cerrado_sin_crear_job() -> None:
    repo = InMemoryReleaseBuildJobRepository()
    scoped = PlatformActor(actor_id="op", project_scope=("proj_otro",))

    with pytest.raises(PlatformAccessDenied):
        _enqueue_use_case(repo).execute(
            rag_release_id=_RELEASE, build_job_id="bjob_1", actor=scoped, now=_T0
        )
    assert repo.latest_for_release(_RELEASE) is None


def test_get_status_devuelve_none_y_luego_el_ultimo_job() -> None:
    repo = InMemoryReleaseBuildJobRepository()
    releases = _StubReleases(_StubRelease(rag_release_id=_RELEASE, project_id=_PROJECT))
    status = GetReleaseBuildStatusUseCase(
        releases=releases, jobs=repo, access_policy=AllowAllAccessPolicy()
    )
    actor = PlatformActor(actor_id="op", project_scope=None)

    assert status.execute(rag_release_id=_RELEASE, actor=actor) is None

    repo.create(_job("bjob_1"))
    assert status.execute(rag_release_id=_RELEASE, actor=actor).build_job_id == "bjob_1"


def test_get_status_fuera_de_scope_falla_cerrado() -> None:
    repo = InMemoryReleaseBuildJobRepository()
    releases = _StubReleases(_StubRelease(rag_release_id=_RELEASE, project_id=_PROJECT))
    status = GetReleaseBuildStatusUseCase(
        releases=releases, jobs=repo, access_policy=AllowAllAccessPolicy()
    )
    scoped = PlatformActor(actor_id="op", project_scope=("proj_otro",))

    with pytest.raises(PlatformAccessDenied):
        status.execute(rag_release_id=_RELEASE, actor=scoped)


# --------------------------------------------------------------------------- #
# Runner (transición durable queued → running → terminal)                     #
# --------------------------------------------------------------------------- #


class _StubBuildRelease:
    def __init__(self, *, report=None, error=None):
        self._report = report
        self._error = error

    def execute(self, *, rag_release_id, actor):
        if self._error is not None:
            raise self._error
        return self._report


class _BuildBlocked(RagPlatformError):
    code = "RELEASE_BUILD_TOO_LARGE"
    http_status = 422


def test_runner_marca_succeeded_con_el_reporte() -> None:
    repo = InMemoryReleaseBuildJobRepository()
    repo.create(_job("bjob_1"))
    report = RagReleaseBuildReport(
        rag_release_id=_RELEASE.value, revisions_built=3, reused_stages=2, built_stages=1
    )
    actor = PlatformActor(actor_id="op", project_scope=None)

    run_one_build(
        jobs=repo,
        build_release=_StubBuildRelease(report=report),
        build_job_id="bjob_1",
        rag_release_id=_RELEASE,
        actor=actor,
        now=lambda: _T1,
    )

    done = repo.get("bjob_1")
    assert done.state is ReleaseBuildJobState.SUCCEEDED
    assert (done.revisions_built, done.reused_stages, done.built_stages) == (3, 2, 1)


def test_runner_marca_failed_sin_dejar_el_job_colgado() -> None:
    repo = InMemoryReleaseBuildJobRepository()
    repo.create(_job("bjob_1"))
    actor = PlatformActor(actor_id="op", project_scope=None)

    run_one_build(
        jobs=repo,
        build_release=_StubBuildRelease(error=_BuildBlocked("snapshot demasiado grande")),
        build_job_id="bjob_1",
        rag_release_id=_RELEASE,
        actor=actor,
        now=lambda: _T1,
    )

    failed = repo.get("bjob_1")
    assert failed.state is ReleaseBuildJobState.FAILED
    assert failed.error_code == "RELEASE_BUILD_TOO_LARGE"
    assert failed.error_message


def test_runner_excepcion_inesperada_no_filtra_detalle_al_cliente() -> None:
    # Fase 7: una excepción inesperada (no de dominio) no puede exponer rutas
    # físicas ni secretos por el build-status. Se traduce a un código estable y un
    # id opaco; el texto crudo queda solo en el log del servidor.
    repo = InMemoryReleaseBuildJobRepository()
    repo.create(_job("bjob_1"))
    actor = PlatformActor(actor_id="op", project_scope=None)
    secreto = r"C:\venvs\rag_platform\secrets.env password=hunter2"

    run_one_build(
        jobs=repo,
        build_release=_StubBuildRelease(error=RuntimeError(secreto)),
        build_job_id="bjob_1",
        rag_release_id=_RELEASE,
        actor=actor,
        now=lambda: _T1,
    )

    failed = repo.get("bjob_1")
    assert failed.state is ReleaseBuildJobState.FAILED
    assert failed.error_code == "RELEASE_BUILD_INTERNAL_ERROR"
    assert secreto not in (failed.error_message or "")
    assert "password" not in (failed.error_message or "")
