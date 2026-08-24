"""Job de build asíncrono de una release (Fase 8 rework, plan 2026-08-21 §D-3b).

El build de una release corre el motor pesado; hacerlo síncrono dentro del
request HTTP bloquea el handler (socket hang up). Este agregado modela el estado
de ciclo de vida de un intento de build asíncrono, observable por la GUI vía
polling y durable (sobrevive refresh y reinicio del proceso).

Dominio puro: sin SDK ni SQL. Reusa ``StrictModel`` y las identidades tipadas.
El worker que corre el motor vive en infraestructura; aquí solo el estado.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import Field

from ingestion.schemas.common import StrictModel
from rag_platform.domain.models import ProjectId, RagReleaseId


class ReleaseBuildJobState(str, Enum):
    """Ciclo de vida observable de un intento de build asíncrono.

    ``succeeded``/``failed`` son terminales: un build que no completa deja el job
    observable como fallido con su causa, nunca colgado en ``running``.
    """

    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


_TERMINAL_STATES = frozenset({ReleaseBuildJobState.SUCCEEDED, ReleaseBuildJobState.FAILED})


class ReleaseBuildJob(StrictModel):
    """Estado durable de un intento de build asíncrono de una release.

    Los tres enteros del reporte se llenan solo al terminar con éxito; los campos
    de error solo al fallar. El job nunca guarda texto de documento, vectores,
    secretos ni rutas físicas.
    """

    build_job_id: str = Field(min_length=1)
    rag_release_id: RagReleaseId
    project_id: ProjectId
    state: ReleaseBuildJobState = ReleaseBuildJobState.QUEUED
    revisions_built: int | None = Field(default=None, ge=0)
    reused_stages: int | None = Field(default=None, ge=0)
    built_stages: int | None = Field(default=None, ge=0)
    error_code: str | None = None
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime

    @property
    def is_terminal(self) -> bool:
        return self.state in _TERMINAL_STATES
