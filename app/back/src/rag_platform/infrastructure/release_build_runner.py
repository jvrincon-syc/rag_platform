"""Runner del build asíncrono de release (Fase 8 §D-3b, Task 2 del rework).

El build corre el motor pesado fuera del hilo del request para no colgar el
socket. En modo Postgres cada build usa su PROPIA conexión (bundle fresco), de
modo que NO comparte la conexión del request (que no es thread-safe) y no bloquea
las lecturas; el estado se persiste en la misma tabla durable, visible por polling.
En modo memoria se reutilizan los repos compartidos (thread-safe por lock).

El runner nunca deja un job colgado en ``running``: toda excepción del motor se
traduce a estado ``failed`` con su causa.
"""

from __future__ import annotations

import threading
from datetime import datetime, timezone
from typing import Callable, Protocol

from rag_platform.application.platform_access import PlatformActor
from rag_platform.application.release_build_job_service import ReleaseBuildJobRepository
from rag_platform.domain.build_jobs import ReleaseBuildJobState
from rag_platform.domain.errors import RagPlatformError
from rag_platform.domain.identity import PlatformId


class _BuildReleaseUseCase(Protocol):
    def execute(self, *, rag_release_id: PlatformId, actor: PlatformActor): ...


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def run_one_build(
    *,
    jobs: ReleaseBuildJobRepository,
    build_release: _BuildReleaseUseCase,
    build_job_id: str,
    rag_release_id: PlatformId,
    actor: PlatformActor,
    now: Callable[[], datetime] = _utcnow,
) -> None:
    """Corre UN build: transiciona ``queued → running → succeeded|failed`` durable."""

    job = jobs.get(build_job_id)
    jobs.update(job.model_copy(update={"state": ReleaseBuildJobState.RUNNING, "updated_at": now()}))
    try:
        report = build_release.execute(rag_release_id=rag_release_id, actor=actor)
        jobs.update(
            job.model_copy(
                update={
                    "state": ReleaseBuildJobState.SUCCEEDED,
                    "revisions_built": report.revisions_built,
                    "reused_stages": report.reused_stages,
                    "built_stages": report.built_stages,
                    "updated_at": now(),
                }
            )
        )
    except RagPlatformError as exc:
        jobs.update(
            job.model_copy(
                update={
                    "state": ReleaseBuildJobState.FAILED,
                    "error_code": exc.code,
                    "error_message": str(exc),
                    "updated_at": now(),
                }
            )
        )
    except Exception as exc:  # noqa: BLE001 — el job nunca queda colgado en running
        jobs.update(
            job.model_copy(
                update={
                    "state": ReleaseBuildJobState.FAILED,
                    "error_code": "RELEASE_BUILD_FAILED",
                    "error_message": f"{type(exc).__name__}: {exc}",
                    "updated_at": now(),
                }
            )
        )


class ReleaseBuildRunner:
    """Encola la ejecución de un build en un hilo daemon.

    ``execute_build`` encapsula la diferencia por modo de persistencia: en Postgres
    abre un bundle fresco (conexión propia) y lo cierra al terminar; en memoria usa
    los repos compartidos. El runner solo lanza el hilo; no conoce la conexión.
    """

    def __init__(
        self,
        *,
        execute_build: Callable[[str, PlatformId, PlatformActor], None],
    ) -> None:
        self._execute_build = execute_build

    def submit(
        self, *, build_job_id: str, rag_release_id: PlatformId, actor: PlatformActor
    ) -> None:
        thread = threading.Thread(
            target=self._execute_build,
            args=(build_job_id, rag_release_id, actor),
            name=f"release-build-{build_job_id}",
            daemon=True,
        )
        thread.start()
