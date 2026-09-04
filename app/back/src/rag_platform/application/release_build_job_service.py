"""Casos de uso del build asíncrono durable de una release (Fase 8 §D-3b).

Separa el *encolado* (rápido, dentro del request) de la *ejecución* del motor
(lenta, en un worker fuera del hilo del request). El request encola un
``ReleaseBuildJob`` en estado ``queued`` y responde 202; el worker (infraestructura,
Task 2) transiciona ``running → succeeded|failed`` con su PROPIA conexión, sin
compartir la conexión del request. La GUI observa el estado por polling.

Fail-closed por scope: un actor fuera del scope del proyecto de la release no
encola ni consulta su build.
"""

from __future__ import annotations

from datetime import datetime, timezone
import logging
from typing import Protocol, runtime_checkable

from core.logging.observability import (
    EventStatus,
    JsonlEventSink,
    ObservabilityDomain,
    ObservabilityEvent,
    emit_observability_event,
)
from rag_platform.application.context import PlatformAccessPolicy
from rag_platform.application.platform_access import (
    PlatformActor,
    require_project_operator,
)
from rag_platform.application.release_service import RagReleaseRepository
from rag_platform.domain.build_jobs import ReleaseBuildJob, ReleaseBuildJobState
from rag_platform.domain.errors import ReleaseBuildAlreadyRunning
from rag_platform.domain.identity import PlatformId


@runtime_checkable
class ReleaseBuildJobRepository(Protocol):
    """Persistencia durable del estado de los intentos de build asíncrono."""

    def create(self, job: ReleaseBuildJob) -> ReleaseBuildJob:
        """Inserta un job nuevo (estado inicial ``queued``)."""

    def update(self, job: ReleaseBuildJob) -> ReleaseBuildJob:
        """Persiste una transición de estado del job (running/succeeded/failed)."""

    def get(self, build_job_id: str) -> ReleaseBuildJob:
        """Devuelve el job por id o lanza ``ReleaseBuildJobNotFound``."""

    def latest_for_release(self, rag_release_id: PlatformId) -> ReleaseBuildJob | None:
        """Devuelve el job más reciente de la release, o ``None`` si no hay ninguno."""

    def list_non_terminal(self) -> list[ReleaseBuildJob]:
        """Devuelve todos los jobs ``queued``/``running`` en todo el repo."""


class EnqueueReleaseBuildUseCase:
    """Encola un build asíncrono: crea el job ``queued`` tras autorizar por scope.

    NO corre el motor: eso es responsabilidad del worker (Task 2). La idempotencia
    HTTP la garantiza el guard del router (misma intención → mismo 202), así que
    aquí no se deduplica: cada intención lógica nueva es un job nuevo.
    """

    def __init__(
        self,
        *,
        releases: RagReleaseRepository,
        jobs: ReleaseBuildJobRepository,
        access_policy: PlatformAccessPolicy,
    ) -> None:
        self._releases = releases
        self._jobs = jobs
        self._access_policy = access_policy

    def execute(
        self,
        *,
        rag_release_id: PlatformId,
        build_job_id: str,
        actor: PlatformActor,
        now: datetime,
    ) -> ReleaseBuildJob:
        release = self._releases.get(rag_release_id)
        require_project_operator(
            policy=self._access_policy, actor=actor, project_id=release.project_id
        )
        # PR-1 1.4: fail-closed contra builds concurrentes de la MISMA release --
        # dos builds compiten por CPU/modelo y por el runtime de embedding
        # scoped-al-hilo (embedding.application.engine_registry). Un job
        # queued/running existente bloquea uno nuevo hasta que termina.
        active = self._jobs.latest_for_release(rag_release_id)
        if active is not None and not active.is_terminal:
            raise ReleaseBuildAlreadyRunning(
                f"release {rag_release_id.value} already has an active build "
                f"({active.build_job_id}, state={active.state.value})"
            )
        job = ReleaseBuildJob(
            build_job_id=build_job_id,
            rag_release_id=release.rag_release_id,
            project_id=release.project_id,
            state=ReleaseBuildJobState.QUEUED,
            created_at=now,
            updated_at=now,
        )
        return self._jobs.create(job)


class GetReleaseBuildStatusUseCase:
    """Lee el estado del build más reciente de una release (scope-aware)."""

    def __init__(
        self,
        *,
        releases: RagReleaseRepository,
        jobs: ReleaseBuildJobRepository,
        access_policy: PlatformAccessPolicy,
    ) -> None:
        self._releases = releases
        self._jobs = jobs
        self._access_policy = access_policy

    def execute(
        self, *, rag_release_id: PlatformId, actor: PlatformActor
    ) -> ReleaseBuildJob | None:
        release = self._releases.get(rag_release_id)
        require_project_operator(
            policy=self._access_policy, actor=actor, project_id=release.project_id
        )
        return self._jobs.latest_for_release(rag_release_id)


class ReleaseBuildJobReconciler:
    """Resolve build jobs left ``queued``/``running`` by a process that died (PR-1 1.6).

    The build worker runs on a daemon thread (``ReleaseBuildRunner``); if the
    process is killed or restarted mid-build, the job's last durable state stays
    ``queued``/``running`` forever -- indistinguishable from "still working" for
    both the polling GUI and ``EnqueueReleaseBuildUseCase``'s one-active-build
    guard (PR-1 1.4), which would then reject every future build for that
    release. Mirrors ``IndexingRunReconciler``: mark abandoned jobs ``failed``
    at startup, before the API starts serving requests.
    """

    def __init__(
        self,
        *,
        jobs: ReleaseBuildJobRepository,
        logger: logging.Logger | None = None,
        jsonl_sink: JsonlEventSink | None = None,
    ) -> None:
        self._jobs = jobs
        self._logger = logger or logging.getLogger(__name__)
        self._jsonl_sink = jsonl_sink

    def reconcile(self) -> list[ReleaseBuildJob]:
        """Mark every non-terminal job ``failed`` and return the reconciled jobs."""

        reconciled: list[ReleaseBuildJob] = []
        for job in self._jobs.list_non_terminal():
            updated = job.model_copy(
                update={
                    "state": ReleaseBuildJobState.FAILED,
                    "error_code": "RELEASE_BUILD_ABANDONED",
                    "error_message": "Proceso reiniciado; el build no completó.",
                    "updated_at": datetime.now(timezone.utc),
                }
            )
            reconciled.append(self._jobs.update(updated))
            emit_observability_event(
                logger=self._logger,
                event=ObservabilityEvent(
                    event="release_build_job_reconciled",
                    domain=ObservabilityDomain.BACKEND,
                    status=EventStatus.WARNING,
                    message=f"release_build_job_reconciled {job.build_job_id}",
                    attributes={
                        "build_job_id": job.build_job_id,
                        "rag_release_id": job.rag_release_id.value,
                        "project_id": job.project_id.value,
                        "previous_state": job.state.value,
                    },
                ),
                jsonl_sink=self._jsonl_sink,
            )
        return reconciled
