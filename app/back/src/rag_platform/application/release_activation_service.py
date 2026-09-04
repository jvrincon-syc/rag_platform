"""Retire ``/activate`` from the public lifecycle (G2, PR-2 2.2, ADR-011).

Publishing (``publication_service``) is a pure state transition; the legacy
``activate_rag_release`` (``infrastructure/release_activation.py``) is a
separate, explicit, Postgres-only action that flips ``is_active`` and creates a
legacy retrieval profile via a multi-transaction bundle loop (not atomic today
-- a residual PR-2 2.2 gap, real risk without a live Postgres connection to
verify a rewrite against). Neither the in-memory nor the Postgres
release-scoped retrieval adapter reads ``is_active`` or that legacy profile
(PR-2 2.1, ``test_release_search_no_depende_de_is_active``): under
``release_serving_only`` the legacy activation stops mattering to what the
chatbot can answer, so this use case never runs it -- it fails closed instead
of running the unverifiable non-atomic path.

G2: rather than a 200 "no-op" response that simulates success (the original
PR-2 2.2 shape), this raises ``ReleaseActivateNotPublic`` (410) -- the route is
actually retired from the public contract, not just neutered. It keeps the
SAME authorization contract as the real activation
(``require_project_operator`` over the release's project) so gating
``/activate`` behind the flag never becomes an authorization bypass: an
out-of-scope actor still gets ``PlatformAccessDenied`` first.
"""

from __future__ import annotations

from rag_platform.application.context import PlatformAccessPolicy
from rag_platform.application.platform_access import (
    PlatformActor,
    require_project_operator,
)
from rag_platform.application.release_service import RagReleaseRepository
from rag_platform.domain.errors import ReleaseActivateNotPublic
from rag_platform.domain.identity import PlatformId


class NoOpActivateReleaseUseCase:
    """Retire ``/activate`` under the release-scoped serving model (G2)."""

    def __init__(
        self, *, releases: RagReleaseRepository, access_policy: PlatformAccessPolicy
    ) -> None:
        self._releases = releases
        self._access_policy = access_policy

    def execute(
        self, *, rag_release_id: PlatformId, actor: PlatformActor
    ) -> dict[str, object]:
        """Authorize the actor, then fail closed: activation is not public.

        Raises:
            PlatformAccessDenied: If the actor is not an operator in scope of
                the release's project.
            ReleaseActivateNotPublic: Always, once authorized -- ``/activate``
                is retired from the public lifecycle under this flag.
        """

        release = self._releases.get(rag_release_id)
        require_project_operator(
            policy=self._access_policy, actor=actor, project_id=release.project_id
        )
        raise ReleaseActivateNotPublic(
            "activation is retired from the public release lifecycle; "
            "publish the release and serve from PUBLISHED + memberships"
        )
