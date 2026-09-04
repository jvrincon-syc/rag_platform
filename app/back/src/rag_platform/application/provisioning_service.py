"""Autorización project-scoped del auto-provisioning (PR-1.2).

El provisioning físico (INSERTs de receta + variante) vive en
``infrastructure.default_provisioning``. Estos casos de uso ponen la guarda de
autorización que faltaba: exigen operador y scope de proyecto **antes** de
delegar, igual que el resto de la plataforma (``require_project_operator``).

Antes, el router HTTP importaba la infraestructura directo y esta corría con
``AllowAllAccessPolicy`` + un actor fijo ``ui-provisioner``: el ``actor``
autenticado del request nunca autorizaba la operación, así que un operador con
scope al proyecto A podía provisionar el proyecto B. Aquí se cierra ese hueco y
se atribuye la operación al actor real.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from rag_platform.application.context import PlatformAccessPolicy
from rag_platform.application.platform_access import (
    PlatformActor,
    require_project_operator,
)
from rag_platform.domain.identity import PlatformId


def _project_slug(project_id: PlatformId) -> str:
    """``proj_<slug>`` -> ``<slug>`` (la infraestructura trabaja con el slug)."""

    value = project_id.value
    return value[len("proj_") :] if value.startswith("proj_") else value


class _ProvisionDefaultDelegate(Protocol):
    def __call__(
        self, *, project_slug: str, embedding_backend: str, actor_id: str
    ) -> dict: ...


class _ProvisionCustomDelegate(Protocol):
    def __call__(
        self,
        *,
        project_slug: str,
        embedding_backend: str,
        chunking_params: dict,
        actor_id: str,
    ) -> dict: ...


@dataclass(frozen=True)
class ProvisionDefaultVariantUseCase:
    """Autoriza y ejecuta el provisioning del preset por defecto de un proyecto."""

    policy: PlatformAccessPolicy
    provision: _ProvisionDefaultDelegate

    def execute(
        self, *, project_id: PlatformId, embedding_backend: str, actor: PlatformActor
    ) -> dict:
        require_project_operator(
            policy=self.policy, actor=actor, project_id=project_id
        )
        return self.provision(
            project_slug=_project_slug(project_id),
            embedding_backend=embedding_backend,
            actor_id=actor.actor_id,
        )


@dataclass(frozen=True)
class ProvisionCustomChunkingVariantUseCase:
    """Autoriza y ejecuta el provisioning de una variante con chunking a medida."""

    policy: PlatformAccessPolicy
    provision: _ProvisionCustomDelegate

    def execute(
        self,
        *,
        project_id: PlatformId,
        embedding_backend: str,
        chunking_params: dict,
        actor: PlatformActor,
    ) -> dict:
        require_project_operator(
            policy=self.policy, actor=actor, project_id=project_id
        )
        return self.provision(
            project_slug=_project_slug(project_id),
            embedding_backend=embedding_backend,
            chunking_params=chunking_params,
            actor_id=actor.actor_id,
        )
