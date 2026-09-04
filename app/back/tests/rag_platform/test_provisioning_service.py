"""PR-1.2 — el auto-provisioning autoriza al actor real por scope de proyecto.

Antes, el router llamaba a la infraestructura directo (AllowAllAccessPolicy +
actor fijo ``ui-provisioner``), saltándose ``require_project_operator``. Estos
tests fijan el contrato del caso de uso sin tocar la BD: la delegación física
(INSERTs/variante) se reemplaza por un doble que solo registra la llamada.
"""

from __future__ import annotations

import pytest

from rag_platform.application.platform_access import PlatformActor
from rag_platform.application.provisioning_service import (
    ProvisionCustomChunkingVariantUseCase,
    ProvisionDefaultVariantUseCase,
)
from rag_platform.domain.errors import PlatformAccessDenied
from rag_platform.domain.identity import IdentityKind, PlatformId


class _AllowOperatorPolicy:
    """Operador siempre autorizado; el scope de proyecto lo aplica el caso de uso."""

    def require_operator(self, *, actor_id: str) -> None:
        del actor_id


def _pid(slug: str) -> PlatformId:
    return PlatformId(kind=IdentityKind.PROJECT, value=f"proj_{slug}")


class _RecordingDefaultDelegate:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def __call__(self, *, project_slug: str, embedding_backend: str, actor_id: str) -> dict:
        self.calls.append(
            {"project_slug": project_slug, "embedding_backend": embedding_backend, "actor_id": actor_id}
        )
        return {"status": "provisioned"}


class _RecordingCustomDelegate:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def __call__(
        self, *, project_slug: str, embedding_backend: str, chunking_params: dict, actor_id: str
    ) -> dict:
        self.calls.append(
            {
                "project_slug": project_slug,
                "embedding_backend": embedding_backend,
                "chunking_params": chunking_params,
                "actor_id": actor_id,
            }
        )
        return {"status": "provisioned"}


def test_provision_default_variant_rechaza_actor_fuera_de_scope():
    delegate = _RecordingDefaultDelegate()
    use_case = ProvisionDefaultVariantUseCase(policy=_AllowOperatorPolicy(), provision=delegate)
    actor = PlatformActor(actor_id="op-a", project_scope=("proj_a",))

    with pytest.raises(PlatformAccessDenied):
        use_case.execute(project_id=_pid("b"), embedding_backend="local", actor=actor)

    assert delegate.calls == []  # nunca delega si el actor no está en scope


def test_provision_default_variant_usa_actor_y_slug_del_request():
    delegate = _RecordingDefaultDelegate()
    use_case = ProvisionDefaultVariantUseCase(policy=_AllowOperatorPolicy(), provision=delegate)
    actor = PlatformActor(actor_id="op-a", project_scope=("proj_a",))

    result = use_case.execute(project_id=_pid("a"), embedding_backend="local", actor=actor)

    assert result == {"status": "provisioned"}
    assert delegate.calls == [
        {"project_slug": "a", "embedding_backend": "local", "actor_id": "op-a"}
    ]


def test_provision_default_variant_permite_operador_global():
    delegate = _RecordingDefaultDelegate()
    use_case = ProvisionDefaultVariantUseCase(policy=_AllowOperatorPolicy(), provision=delegate)
    actor = PlatformActor(actor_id="root", project_scope=None)  # global

    use_case.execute(project_id=_pid("cualquiera"), embedding_backend="voyage", actor=actor)

    assert delegate.calls[0]["project_slug"] == "cualquiera"


def test_provision_custom_rechaza_fuera_de_scope_y_pasa_params_en_scope():
    delegate = _RecordingCustomDelegate()
    use_case = ProvisionCustomChunkingVariantUseCase(
        policy=_AllowOperatorPolicy(), provision=delegate
    )
    scoped = PlatformActor(actor_id="op-a", project_scope=("proj_a",))

    with pytest.raises(PlatformAccessDenied):
        use_case.execute(
            project_id=_pid("b"), embedding_backend="local", chunking_params={}, actor=scoped
        )
    assert delegate.calls == []

    use_case.execute(
        project_id=_pid("a"),
        embedding_backend="local",
        chunking_params={"child_target_tokens": 320},
        actor=scoped,
    )
    assert delegate.calls == [
        {
            "project_slug": "a",
            "embedding_backend": "local",
            "chunking_params": {"child_target_tokens": 320},
            "actor_id": "op-a",
        }
    ]
