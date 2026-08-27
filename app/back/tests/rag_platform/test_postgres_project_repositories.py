"""Regresiones de contrato para adapters Postgres del catalogo Platform."""

from __future__ import annotations

from datetime import datetime, timezone

from rag_platform.domain.identity import IdentityKind, PlatformId
from rag_platform.infrastructure.postgres.project_repositories import (
    PostgresChunkingProfileRepository,
    PostgresProcessingProfileRepository,
)


class FakeCursor:
    def __init__(self, rows: list[tuple[object, ...]]) -> None:
        self._rows = rows
        self.executed: list[tuple[str, tuple[object, ...]]] = []

    def __enter__(self) -> "FakeCursor":
        return self

    def __exit__(self, *_exc: object) -> None:
        return None

    def execute(self, sql: str, params: tuple[object, ...]) -> None:
        self.executed.append((sql, params))

    def fetchall(self) -> list[tuple[object, ...]]:
        return self._rows


class FakeConnection:
    def __init__(self, rows: list[tuple[object, ...]]) -> None:
        self.cursor_instance = FakeCursor(rows)

    def cursor(self) -> FakeCursor:
        return self.cursor_instance


def _project_id() -> PlatformId:
    return PlatformId(kind=IdentityKind.PROJECT, value="proj_sst-general")


def test_postgres_processing_profiles_list_for_project_cumple_puerto() -> None:
    created_at = datetime(2026, 8, 25, tzinfo=timezone.utc)
    connection = FakeConnection(
        [
            (
                "pp_local",
                "proj_sst-general",
                "local",
                "pdf-ocr-v1",
                "rev-1",
                "local",
                {"ocr": "tesseract"},
                "a" * 64,
                "verified",
                created_at,
            )
        ]
    )

    profiles = PostgresProcessingProfileRepository(connection).list_for_project(
        _project_id()
    )

    assert [profile.processing_profile_id.value for profile in profiles] == [
        "pp_local"
    ]
    sql, params = connection.cursor_instance.executed[0]
    assert "WHERE project_id = %s" in sql
    assert "ORDER BY processing_profile_id" in sql
    assert params == ("proj_sst-general",)


def test_postgres_chunking_profiles_list_for_project_cumple_puerto() -> None:
    created_at = datetime(2026, 8, 25, tzinfo=timezone.utc)
    connection = FakeConnection(
        [
            (
                "cp_structural",
                "proj_sst-general",
                "structural",
                {"chunk_size": 800},
                "b" * 64,
                "verified",
                created_at,
            )
        ]
    )

    profiles = PostgresChunkingProfileRepository(connection).list_for_project(
        _project_id()
    )

    assert [profile.chunking_profile_id.value for profile in profiles] == [
        "cp_structural"
    ]
    sql, params = connection.cursor_instance.executed[0]
    assert "WHERE project_id = %s" in sql
    assert "ORDER BY chunking_profile_id" in sql
    assert params == ("proj_sst-general",)
