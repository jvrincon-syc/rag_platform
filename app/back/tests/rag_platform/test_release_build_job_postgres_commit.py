"""Regression: PostgresReleaseBuildJobRepository must commit its own writes.

The build worker runs in a background thread with its OWN fresh connection
(release_build_runner.py), separate from the request connection that enqueued
the job. Without an explicit commit, that write is invisible to the other
connection under MVCC -- live symptom: the worker thread died on its first
``jobs.get(build_job_id)`` with ``ReleaseBuildJobNotFound`` even though the
row had just been inserted by the request handler moments earlier.
"""

from __future__ import annotations

from datetime import datetime, timezone

from rag_platform.domain.build_jobs import ReleaseBuildJob, ReleaseBuildJobState
from rag_platform.domain.identity import IdentityKind, PlatformId
from rag_platform.infrastructure.postgres.release_repositories import (
    PostgresReleaseBuildJobRepository,
)


class _FakeCursor:
    def __init__(self, *, fetchone_result: tuple | None = None, rowcount: int = 1) -> None:
        self.executed: list[tuple[str, tuple]] = []
        self._fetchone_result = fetchone_result
        self.rowcount = rowcount

    def __enter__(self) -> "_FakeCursor":
        return self

    def __exit__(self, *_exc: object) -> None:
        return None

    def execute(self, sql: str, params: tuple) -> None:
        self.executed.append((sql, params))

    def fetchone(self):
        return self._fetchone_result


class _FakeConnection:
    def __init__(self, cursor: _FakeCursor) -> None:
        self._cursor = cursor
        self.commit_calls = 0

    def cursor(self) -> _FakeCursor:
        return self._cursor

    def commit(self) -> None:
        self.commit_calls += 1


def _job() -> ReleaseBuildJob:
    return ReleaseBuildJob(
        build_job_id="bjob_demo",
        rag_release_id=PlatformId(kind=IdentityKind.RAG_RELEASE, value="ragr_demo"),
        project_id=PlatformId(kind=IdentityKind.PROJECT, value="proj_demo"),
        state=ReleaseBuildJobState.QUEUED,
        created_at=datetime(2026, 8, 27, tzinfo=timezone.utc),
        updated_at=datetime(2026, 8, 27, tzinfo=timezone.utc),
    )


def test_create_commits_so_a_fresh_connection_can_see_the_job() -> None:
    connection = _FakeConnection(_FakeCursor())

    PostgresReleaseBuildJobRepository(connection).create(_job())

    assert connection.commit_calls == 1


def test_update_commits_so_polling_on_another_connection_sees_the_transition() -> None:
    connection = _FakeConnection(_FakeCursor(rowcount=1))

    PostgresReleaseBuildJobRepository(connection).update(
        _job().model_copy(update={"state": ReleaseBuildJobState.RUNNING})
    )

    assert connection.commit_calls == 1
