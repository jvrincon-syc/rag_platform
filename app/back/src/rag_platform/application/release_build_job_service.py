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

from datetime import datetime
from typing import Protocol, runtime_checkable

from rag_platform.application.context import PlatformAccessPolicy
from rag_platform.application.platform_access import (
    PlatformActor,
    require_project_operator,
)
from rag_platform.application.release_service import RagReleaseRepository
from rag_platform.domain.build_jobs import ReleaseBuildJob, ReleaseBuildJobState
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
