"""G2 (PR-2 2.2): ``/activate`` is retired from the public lifecycle under

``release_serving_only``. ``NoOpActivateReleaseUseCase`` keeps the same
project-scope authorization as the real, Postgres-only ``activate_rag_release``
(never touched here -- fake repos only, no DB), but never runs the legacy
multi-transaction bundle activation that flips ``is_active``: once authorized,
it fails closed with ``ReleaseActivateNotPublic`` (410) instead of returning a
200 that simulates success.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from rag_platform.application.platform_access import PlatformActor
from rag_platform.application.release_activation_service import (
    NoOpActivateReleaseUseCase,
)
from rag_platform.domain.errors import PlatformAccessDenied, ReleaseActivateNotPublic
from rag_platform.domain.identity import IdentityKind, PlatformId
from rag_platform.domain.lifecycle import RagRelease, ReleaseState
from rag_platform.infrastructure.in_memory.release_repositories import (
    InMemoryRagReleaseRepository,
)
from rag_platform.infrastructure.in_memory.repositories import AllowAllAccessPolicy

_PROJECT = PlatformId(IdentityKind.PROJECT, "proj_alpha")
_VARIANT = PlatformId(IdentityKind.RAG_VARIANT, "ragv_bge")
_SNAPSHOT = PlatformId(IdentityKind.CORPUS_SNAPSHOT, "corpus_s1")
_RELEASE = PlatformId(IdentityKind.RAG_RELEASE, "ragr_r1")
_NOW = datetime(2026, 8, 11, tzinfo=timezone.utc)


class _DenyAll:
    def require_operator(self, *, actor_id: str) -> None:
        raise PlatformAccessDenied("denied")


def _release() -> RagRelease:
    return RagRelease(
        rag_release_id=_RELEASE,
        project_id=_PROJECT,
        rag_variant_id=_VARIANT,
        corpus_snapshot_id=_SNAPSHOT,
        target_binding_key="primary",
        configuration_version=1,
        release_number=1,
        state=ReleaseState.PUBLISHED,
        release_manifest_hash="a" * 64,
        created_by="op-1",
        created_at=_NOW,
    )


def test_no_op_autoriza_y_luego_falla_cerrado_como_no_publica() -> None:
    releases = InMemoryRagReleaseRepository()
    releases.add(_release())
    use_case = NoOpActivateReleaseUseCase(
        releases=releases, access_policy=AllowAllAccessPolicy()
    )

    with pytest.raises(ReleaseActivateNotPublic):
        use_case.execute(rag_release_id=_RELEASE, actor=PlatformActor(actor_id="op-1"))


def test_no_op_sigue_fallando_cerrado_sin_permiso() -> None:
    """The no-op skips legacy activation, never authorization."""

    releases = InMemoryRagReleaseRepository()
    releases.add(_release())
    use_case = NoOpActivateReleaseUseCase(releases=releases, access_policy=_DenyAll())

    with pytest.raises(PlatformAccessDenied):
        use_case.execute(rag_release_id=_RELEASE, actor=PlatformActor(actor_id="op-1"))


def test_no_op_falla_cerrado_cuando_actor_fuera_de_scope() -> None:
    releases = InMemoryRagReleaseRepository()
    releases.add(_release())
    use_case = NoOpActivateReleaseUseCase(
        releases=releases, access_policy=AllowAllAccessPolicy()
    )

    with pytest.raises(PlatformAccessDenied):
        use_case.execute(
            rag_release_id=_RELEASE,
            actor=PlatformActor(actor_id="op-1", project_scope=("proj_beta",)),
        )
