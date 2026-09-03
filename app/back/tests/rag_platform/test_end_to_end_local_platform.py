
"""Live E2E: real sst-general corpus -> release build -> pgvector retrieval.

Purpose
-------
This test has one responsibility: prove that the real local RAG pipeline can take
the SST raw corpus all the way to release-scoped retrieval using the production
chunking / BGE-M3 / indexing stack.

It intentionally does NOT test crash recovery, resumable builds, retryable domain
jobs, or membership idempotency. Those behaviours belong in focused tests.

Flow
----
1. Hard-clean the local E2E project state.
2. Run the real project ingestion + normalization CLI.
3. Create a corpus snapshot from every source revision.
4. Create a fresh RAG release draft.
5. Run the real release build in a short-lived OS subprocess.
6. Verify release memberships and physical pgvector rows.
7. Embed the smoke-query set with the same BGE profile in another fresh process.
8. Execute release-scoped pgvector retrieval for every query.
9. Write ``e2e_retrieval_report.md`` for manual relevance inspection.
10. Hard-clean the E2E state in a finalizer.

Windows note
------------
BGE-M3/Torch runs in REAL OS subprocesses (``subprocess``, result via JSON
file) because this machine kills ANY ``multiprocessing``-created child
(pool or Process, spawn) with a deterministic 0xC0000005 on the first Torch
forward, while the same code launched as a plain script passes consistently.
If a build subprocess dies natively, the test DOES NOT try to resume the
partial release: it deletes the whole derived build attempt, creates a new
snapshot/release, and retries from a clean derived state. That keeps this test
focused on pipeline correctness instead of silently depending on resumability
semantics.

Usage
-----
    npm run python -- -m pytest \
      app/back/tests/rag_platform/test_end_to_end_local_platform.py::test_end_to_end_local_pipeline_and_retrieval \
      -v -s
"""

from __future__ import annotations

import hashlib
import importlib.util
import logging
import os
import shutil
import sys
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pytest

from sst_retrieval_fixture import (
    load_cached_query_embeddings,
    load_sst_hybrid_questions,
    save_cached_query_embeddings,
)


# ---------------------------------------------------------------------------
# Paths / identity / runtime configuration
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parents[4]
_PROJECT_SLUG = "sst-general"
_PROJECT_ID = f"proj_{_PROJECT_SLUG}"
_RAW_ROOT = _REPO_ROOT / "data" / "projects" / _PROJECT_SLUG / "raw"
_PROJECT_ROOT = _REPO_ROOT / "data" / "projects" / _PROJECT_SLUG

sys.path.insert(0, str(_REPO_ROOT / "app" / "back" / "src"))
sys.path.insert(0, str(_REPO_ROOT / "scripts" / "indexing"))

_VARIANT_ID = "ragv_local-bge"
_BINDING_KEY = "primary"
_ACTOR = "operator-retrieval-e2e"

_EMBEDDING_PROFILE_ID = "local-bge-m3-v1"
_VECTOR_TABLE = "idx_vec_local_bge_m3_v1"
_TOP_K = 8

# A native crash is operational noise in this specific Windows runtime. Each
# build retry starts from a CLEAN derived state and a fresh release. It never
# resumes a half-built release.
_MAX_BUILD_PROCESS_ATTEMPTS = 3
_MAX_QUERY_PROCESS_ATTEMPTS = 3

_RMTREE_RETRY_WINERRORS = {5, 32}
_MAX_RMTREE_ATTEMPTS = 6

_E2E_LOCK_PATH = _PROJECT_ROOT / ".e2e.lock"

_QUESTIONS = load_sst_hybrid_questions()


# ---------------------------------------------------------------------------
# Console progress / build logging
# ---------------------------------------------------------------------------

class _Progress:
    def __init__(self, capsys, *, total_steps: int) -> None:
        self._capsys = capsys
        self._total_steps = total_steps
        self._current_step = 0
        self._started = time.monotonic()

    def step(self, label: str) -> None:
        self._current_step += 1
        remaining = max(0, self._total_steps - self._current_step)
        self._emit(
            f"stage {self._current_step}/{self._total_steps} "
            f"({remaining} left): {label}"
        )

    def detail(self, label: str) -> None:
        self._emit(f"  {label}")

    def question(self, index: int, total: int, question: str) -> None:
        self._emit(f"retrieval {index}/{total} ({total - index} left): {question}")

    def _emit(self, label: str) -> None:
        elapsed = time.monotonic() - self._started
        with self._capsys.disabled():
            print(f"[rag-e2e] {label} | elapsed={elapsed:.1f}s", flush=True)


class _ElapsedLogHandler(logging.Handler):
    def __init__(self) -> None:
        super().__init__(level=logging.DEBUG)
        self._started_at = time.monotonic()

    def emit(self, record: logging.LogRecord) -> None:
        elapsed = time.monotonic() - self._started_at
        print(
            f"[rag-e2e][build-log] +{elapsed:.1f}s "
            f"{record.levelname} {record.name}: {record.getMessage()}",
            flush=True,
        )


_BUILD_LOG_NAMESPACES = (
    "chunking",
    "embedding.application",
    "indexing.application",
    "indexing.infrastructure.embeddings.bge",
    "rag_platform.infrastructure.release_build_runner",
)


def _attach_build_logging() -> tuple[_ElapsedLogHandler, int, dict[str, int]]:
    handler = _ElapsedLogHandler()
    root = logging.getLogger()
    previous_root_level = root.level
    previous_levels = {
        namespace: logging.getLogger(namespace).level
        for namespace in _BUILD_LOG_NAMESPACES
    }

    root.addHandler(handler)
    if root.level > logging.INFO or root.level == logging.NOTSET:
        root.setLevel(logging.INFO)

    for namespace in _BUILD_LOG_NAMESPACES:
        logging.getLogger(namespace).setLevel(logging.DEBUG)

    return handler, previous_root_level, previous_levels


def _detach_build_logging(
    state: tuple[_ElapsedLogHandler, int, dict[str, int]]
) -> None:
    handler, previous_root_level, previous_levels = state
    root = logging.getLogger()
    root.removeHandler(handler)
    root.setLevel(previous_root_level)

    for namespace, level in previous_levels.items():
        logging.getLogger(namespace).setLevel(level)


class _Heartbeat:
    def __init__(self, label: str, *, interval_seconds: float = 20.0) -> None:
        self._label = label
        self._interval = interval_seconds
        self._started_at = time.monotonic()
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def __enter__(self) -> "_Heartbeat":
        self._thread.start()
        return self

    def __exit__(self, *_exc_info) -> None:
        self._stop.set()
        self._thread.join(timeout=2.0)

    def _run(self) -> None:
        while not self._stop.wait(self._interval):
            elapsed = time.monotonic() - self._started_at
            print(
                f"[rag-e2e] {self._label} still running... {elapsed:.0f}s",
                flush=True,
            )


# ---------------------------------------------------------------------------
# Generic repo / DB helpers
# ---------------------------------------------------------------------------

def _load(module_name: str, relpath: str):
    spec = importlib.util.spec_from_file_location(module_name, _REPO_ROOT / relpath)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"no se pudo cargar modulo {module_name} desde {relpath}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _dsn() -> str | None:
    from prepare_postgres_indexing import build_dsn_from_env, load_env_file

    return build_dsn_from_env(dict(load_env_file(_REPO_ROOT / "secrets.env")))


def _connect(dsn: str):
    import psycopg2
    from psycopg2.extensions import parse_dsn

    return psycopg2.connect(**parse_dsn(dsn))


def _assert_local_e2e_dsn(dsn: str) -> None:
    """Fail closed before any destructive SQL.

    This test hard-deletes rows for ``proj_sst-general``. It must never be pointed
    at a remote or production PostgreSQL instance.
    """

    from psycopg2.extensions import parse_dsn

    parsed = parse_dsn(dsn)
    host = (parsed.get("host") or "").strip().lower()
    dbname = (parsed.get("dbname") or "").strip().lower()

    allowed_hosts = {"", "localhost", "127.0.0.1", "::1"}
    if host not in allowed_hosts:
        raise RuntimeError(
            "E2E destructivo bloqueado: RAG_PLATFORM_POSTGRES_DSN no apunta a localhost "
            f"(host={host!r})"
        )

    if "prod" in dbname or "production" in dbname:
        raise RuntimeError(
            "E2E destructivo bloqueado: el nombre de la DB parece productivo "
            f"(dbname={dbname!r})"
        )


def _raw_relpaths() -> tuple[str, ...]:
    return tuple(
        sorted(
            str(path.relative_to(_RAW_ROOT)).replace("\\", "/")
            for path in _RAW_ROOT.rglob("*")
            if path.is_file()
        )
    )


def _source_revisions_for_project(dsn: str) -> tuple[tuple[str, str], ...]:
    connection = _connect(dsn)
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT source_relpath, source_document_revision_id "
                "FROM source_document_revisions "
                "WHERE project_id = %s "
                "ORDER BY source_relpath, source_document_revision_id",
                (_PROJECT_ID,),
            )
            return tuple((str(row[0]), str(row[1])) for row in cursor.fetchall())
    finally:
        connection.close()


def _variant_seeded(dsn: str) -> bool:
    connection = _connect(dsn)
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT 1 FROM rag_variants WHERE rag_variant_id = %s",
                (_VARIANT_ID,),
            )
            return cursor.fetchone() is not None
    finally:
        connection.close()


def _table_exists(cursor, table: str) -> bool:
    cursor.execute("SELECT to_regclass(%s)", (f"public.{table}",))
    row = cursor.fetchone()
    return row is not None and row[0] is not None


def _column_exists(cursor, table: str, column: str) -> bool:
    cursor.execute(
        "SELECT 1 FROM information_schema.columns "
        "WHERE table_schema = 'public' "
        "AND table_name = %s AND column_name = %s",
        (table, column),
    )
    return cursor.fetchone() is not None


def _delete_optional(
    cursor,
    table: str,
    statement: str,
    params: tuple = (),
) -> int:
    if not _table_exists(cursor, table):
        return 0
    cursor.execute(statement, params)
    return int(cursor.rowcount)


def _delete_project_vector_rows(cursor) -> dict[str, int]:
    from psycopg2 import sql

    deleted: dict[str, int] = {}
    cursor.execute(
        "SELECT tablename FROM pg_tables "
        "WHERE schemaname = 'public' "
        "AND tablename LIKE 'idx_vec_%' "
        "ORDER BY tablename"
    )

    for (table_name,) in cursor.fetchall():
        table = str(table_name)

        if _column_exists(cursor, table, "project_id"):
            cursor.execute(
                sql.SQL("DELETE FROM {} WHERE project_id = %s").format(
                    sql.Identifier(table)
                ),
                (_PROJECT_ID,),
            )
            deleted[table] = int(cursor.rowcount)
            continue

        if (
            _column_exists(cursor, table, "node_id")
            and _table_exists(cursor, "indexing_nodes")
        ):
            cursor.execute(
                sql.SQL(
                    "DELETE FROM {} "
                    "WHERE node_id IN ("
                    " SELECT node_id FROM indexing_nodes WHERE project_id = %s"
                    ")"
                ).format(sql.Identifier(table)),
                (_PROJECT_ID,),
            )
            deleted[table] = int(cursor.rowcount)

    return deleted


# ---------------------------------------------------------------------------
# Safe local cleanup
# ---------------------------------------------------------------------------

def _rmtree_with_windows_retry(path: Path) -> None:
    if not path.exists():
        return

    for attempt in range(_MAX_RMTREE_ATTEMPTS):
        try:
            shutil.rmtree(path)
            return
        except PermissionError as exc:
            winerror = getattr(exc, "winerror", None)
            if os.name != "nt" or winerror not in _RMTREE_RETRY_WINERRORS:
                raise
            if attempt == _MAX_RMTREE_ATTEMPTS - 1:
                raise
            time.sleep(0.05 * (2**attempt))


def _clear_derived_filesystem() -> None:
    for name in ("chunks", "embeddings"):
        _rmtree_with_windows_retry(_PROJECT_ROOT / name)


def _clear_build_state(
    dsn: str,
    *,
    delete_snapshots_and_releases: bool,
) -> dict[str, int]:
    """Delete ONLY derived build state.

    Source revisions + normalized document ledgers/files are preserved so a native
    BGE crash can restart a completely fresh release without re-running OCR.
    """

    deleted: dict[str, int] = {}
    connection = _connect(dsn)
    connection.autocommit = False

    try:
        with connection.cursor() as cursor:
            deleted.update(_delete_project_vector_rows(cursor))

            deleted["release_build_jobs"] = _delete_optional(
                cursor,
                "release_build_jobs",
                "DELETE FROM release_build_jobs WHERE project_id = %s",
                (_PROJECT_ID,),
            )
            deleted["rag_release_memberships"] = _delete_optional(
                cursor,
                "rag_release_memberships",
                "DELETE FROM rag_release_memberships WHERE project_id = %s",
                (_PROJECT_ID,),
            )

            if _table_exists(cursor, "rag_release_documents"):
                if _column_exists(cursor, "rag_release_documents", "project_id"):
                    cursor.execute(
                        "DELETE FROM rag_release_documents WHERE project_id = %s",
                        (_PROJECT_ID,),
                    )
                else:
                    cursor.execute(
                        "DELETE FROM rag_release_documents "
                        "WHERE rag_release_id IN ("
                        " SELECT rag_release_id FROM rag_releases WHERE project_id = %s"
                        ")",
                        (_PROJECT_ID,),
                    )
                deleted["rag_release_documents"] = int(cursor.rowcount)

            deleted["rag_build_steps"] = _delete_optional(
                cursor,
                "rag_build_steps",
                "DELETE FROM rag_build_steps "
                "WHERE rag_build_run_id IN ("
                " SELECT rag_build_run_id FROM rag_build_runs WHERE project_id = %s"
                ")",
                (_PROJECT_ID,),
            )
            deleted["rag_build_runs"] = _delete_optional(
                cursor,
                "rag_build_runs",
                "DELETE FROM rag_build_runs WHERE project_id = %s",
                (_PROJECT_ID,),
            )

            deleted["readiness_checks"] = _delete_optional(
                cursor,
                "readiness_checks",
                "DELETE FROM readiness_checks "
                "WHERE subject_id IN ("
                " SELECT embedding_bundle_id FROM embedding_bundles WHERE project_id = %s"
                ") OR subject_id IN ("
                " SELECT materialization_id FROM indexing_materializations "
                " WHERE project_id = %s"
                ")",
                (_PROJECT_ID, _PROJECT_ID),
            )

            deleted["indexing_materializations"] = _delete_optional(
                cursor,
                "indexing_materializations",
                "DELETE FROM indexing_materializations WHERE project_id = %s",
                (_PROJECT_ID,),
            )
            deleted["indexing_run_documents"] = _delete_optional(
                cursor,
                "indexing_run_documents",
                "DELETE FROM indexing_run_documents "
                "WHERE run_id IN ("
                " SELECT run_id FROM indexing_runs WHERE project_id = %s"
                ")",
                (_PROJECT_ID,),
            )
            deleted["indexing_runs"] = _delete_optional(
                cursor,
                "indexing_runs",
                "DELETE FROM indexing_runs WHERE project_id = %s",
                (_PROJECT_ID,),
            )

            deleted["embedding_bundle_chunks"] = _delete_optional(
                cursor,
                "embedding_bundle_chunks",
                "DELETE FROM embedding_bundle_chunks "
                "WHERE embedding_bundle_id IN ("
                " SELECT embedding_bundle_id FROM embedding_bundles WHERE project_id = %s"
                ")",
                (_PROJECT_ID,),
            )
            deleted["embedding_runs"] = _delete_optional(
                cursor,
                "embedding_runs",
                "DELETE FROM embedding_runs WHERE project_id = %s",
                (_PROJECT_ID,),
            )
            deleted["embedding_bundles"] = _delete_optional(
                cursor,
                "embedding_bundles",
                "DELETE FROM embedding_bundles WHERE project_id = %s",
                (_PROJECT_ID,),
            )

            deleted["indexing_nodes"] = _delete_optional(
                cursor,
                "indexing_nodes",
                "DELETE FROM indexing_nodes WHERE project_id = %s",
                (_PROJECT_ID,),
            )
            deleted["chunk_bundles"] = _delete_optional(
                cursor,
                "chunk_bundles",
                "DELETE FROM chunk_bundles WHERE project_id = %s",
                (_PROJECT_ID,),
            )

            if delete_snapshots_and_releases:
                deleted["rag_releases"] = _delete_optional(
                    cursor,
                    "rag_releases",
                    "DELETE FROM rag_releases WHERE project_id = %s",
                    (_PROJECT_ID,),
                )
                deleted["corpus_snapshot_documents"] = _delete_optional(
                    cursor,
                    "corpus_snapshot_documents",
                    "DELETE FROM corpus_snapshot_documents "
                    "WHERE corpus_snapshot_id IN ("
                    " SELECT corpus_snapshot_id FROM corpus_snapshots WHERE project_id = %s"
                    ")",
                    (_PROJECT_ID,),
                )
                deleted["corpus_snapshots"] = _delete_optional(
                    cursor,
                    "corpus_snapshots",
                    "DELETE FROM corpus_snapshots WHERE project_id = %s",
                    (_PROJECT_ID,),
                )

        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

    _clear_derived_filesystem()
    return deleted


def _hard_delete_e2e_project_state(
    dsn: str,
    *,
    raw_relpaths: tuple[str, ...],
) -> dict[str, int]:
    """Return the local project to a clean E2E baseline."""

    deleted = _clear_build_state(
        dsn,
        delete_snapshots_and_releases=True,
    )

    connection = _connect(dsn)
    connection.autocommit = False
    try:
        with connection.cursor() as cursor:
            deleted["project_normalized_document_artifacts"] = _delete_optional(
                cursor,
                "project_normalized_document_artifacts",
                "DELETE FROM project_normalized_document_artifacts WHERE project_id = %s",
                (_PROJECT_ID,),
            )
            deleted["project_normalized_documents"] = _delete_optional(
                cursor,
                "project_normalized_documents",
                "DELETE FROM project_normalized_documents WHERE project_id = %s",
                (_PROJECT_ID,),
            )
            deleted["project_raw_document_artifacts"] = _delete_optional(
                cursor,
                "project_raw_document_artifacts",
                "DELETE FROM project_raw_document_artifacts WHERE project_id = %s",
                (_PROJECT_ID,),
            )
            deleted["source_document_revisions"] = _delete_optional(
                cursor,
                "source_document_revisions",
                "DELETE FROM source_document_revisions WHERE project_id = %s",
                (_PROJECT_ID,),
            )
            deleted["project_documents"] = _delete_optional(
                cursor,
                "project_documents",
                "DELETE FROM project_documents WHERE project_id = %s",
                (_PROJECT_ID,),
            )

            # Legacy indexing-normalized rows have no project_id in older schemas.
            # This cleanup is allowed only after _assert_local_e2e_dsn() succeeded.
            if raw_relpaths:
                deleted["indexing_normalized_documents"] = _delete_optional(
                    cursor,
                    "indexing_normalized_documents",
                    "DELETE FROM indexing_normalized_documents "
                    "WHERE source_relpath = ANY(%s)",
                    (list(raw_relpaths),),
                )

        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

    return deleted


def _format_deleted_counts(deleted: dict[str, int]) -> str:
    nonzero = [
        f"{table}={count}"
        for table, count in deleted.items()
        if int(count) > 0
    ]
    return ", ".join(nonzero) if nonzero else "no rows"


# ---------------------------------------------------------------------------
# Exclusive operator-run lock
# ---------------------------------------------------------------------------

def _acquire_e2e_lock() -> None:
    """Acquire a conservative filesystem lock.

    We intentionally DO NOT probe PIDs with ``os.kill(pid, 0)`` because that is
    unsafe on Windows. A stale lock requires an explicit operator override.
    """

    _E2E_LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)

    if os.environ.get("RAG_E2E_FORCE_UNLOCK") == "1":
        try:
            _E2E_LOCK_PATH.unlink()
        except FileNotFoundError:
            pass

    try:
        handle = os.open(
            str(_E2E_LOCK_PATH),
            os.O_CREAT | os.O_EXCL | os.O_WRONLY,
        )
    except FileExistsError as exc:
        owner = "unknown"
        try:
            owner = _E2E_LOCK_PATH.read_text(encoding="utf-8").strip() or "unknown"
        except OSError:
            pass
        raise RuntimeError(
            "otra corrida (o un lock huÃ©rfano) ya posee el E2E lock: "
            f"{_E2E_LOCK_PATH} owner={owner!r}. "
            "Si confirmaste que no hay otra corrida activa, usa "
            "RAG_E2E_FORCE_UNLOCK=1 una sola vez."
        ) from exc

    try:
        payload = (
            f"pid={os.getpid()}\n"
            f"created_at={datetime.now(timezone.utc).isoformat()}\n"
        )
        os.write(handle, payload.encode("utf-8"))
    finally:
        os.close(handle)


def _release_e2e_lock() -> None:
    try:
        _E2E_LOCK_PATH.unlink()
    except FileNotFoundError:
        pass


# ---------------------------------------------------------------------------
# BGE real-subprocess execution
# ---------------------------------------------------------------------------

#: En esta maquina, cualquier hijo creado por el modulo ``multiprocessing``
#: (pool o Process, spawn) muere con access violation (0xC0000005) en el
#: primer forward de Torch/BGE-M3, de forma deterministica; el mismo codigo
#: como proceso lanzado por linea de comandos pasa consistente. Por eso los
#: workloads BGE corren en procesos reales (``subprocess``) con resultado por
#: archivo JSON. Bonus: exitcode nativo real, stderr completo con el stack de
#: faulthandler, y timeout con kill del SO.
_BGE_WORKER_SCRIPT = (
    Path(__file__).resolve().parent / "workers" / "bge_runtime_worker.py"
)
_BGE_WORKER_TIMEOUT_SECONDS = {
    "preflight": 300,
    # batch=1 + 1 hilo en CPU: el build de 55 docs puede tardar horas.
    "build": 14400,
    # The shared SST benchmark question bank is large enough that per-question
    # forwards remain expensive without caching.
    "queries": 3600,
}


def _bge_worker_env() -> dict[str, str]:
    """Entorno nativo del worker: hilos OpenMP en 1 y HF offline."""

    env = os.environ.copy()
    env.update(
        {
            "OMP_NUM_THREADS": "1",
            "MKL_NUM_THREADS": "1",
            "OPENBLAS_NUM_THREADS": "1",
            "NUMEXPR_NUM_THREADS": "1",
            "TOKENIZERS_PARALLELISM": "false",
            # Diagnostico/estabilidad: un forward minimo por llamada.
            "EMBEDDING_BATCH_SIZE": "1",
            "HF_HUB_OFFLINE": "1",
            "TRANSFORMERS_OFFLINE": "1",
            # Ruta absoluta: la resolucion del snapshot no debe depender del CWD.
            "HF_HUB_CACHE": str(_REPO_ROOT / ".cache" / "huggingface"),
        }
    )
    return env


def _run_bge_worker(
    mode: str,
    args: list[str],
    *,
    label: str,
    progress: "_Progress | None" = None,
) -> dict[str, object]:
    """Lanza el worker como proceso real y devuelve su payload JSON.

    Una muerte nativa se detecta por exitcode != 0 (el SO reporta el codigo),
    un cuelgue por TimeoutExpired (con kill incluido); en ambos casos se
    incluye la cola de stderr, donde faulthandler deja el stack nativo.
    """

    import json as _json
    import subprocess

    out_path = _PROJECT_ROOT / f".worker_out_{mode}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    command = [
        sys.executable,
        str(_BGE_WORKER_SCRIPT),
        mode,
        str(out_path),
        *args,
    ]
    started_at = time.monotonic()
    try:
        completed = subprocess.run(
            command,
            cwd=str(_REPO_ROOT),
            env=_bge_worker_env(),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=_BGE_WORKER_TIMEOUT_SECONDS[mode],
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(
            f"BGE worker {label} excedio el timeout de "
            f"{_BGE_WORKER_TIMEOUT_SECONDS[mode]}s y fue terminado"
        ) from exc

    elapsed = time.monotonic() - started_at
    stderr_tail = "\n".join((completed.stderr or "").splitlines()[-25:])
    if completed.returncode != 0:
        # Exitcode 3 = error Python: el worker escribio el detalle en su JSON.
        worker_detail = ""
        try:
            failed = _json.loads(out_path.read_text(encoding="utf-8"))
            if not failed.get("ok"):
                worker_detail = (
                    f" error={failed.get('error')!r}; traceback:"
                    f"\n{str(failed.get('traceback', ''))[-1500:]}"
                )
        except (OSError, ValueError):
            pass
        raise RuntimeError(
            f"BGE worker {label} murio con exitcode={completed.returncode}"
            f" despues de {elapsed:.1f}s;"
            + (worker_detail if worker_detail else f" stderr:\n{stderr_tail}")
        )

    try:
        payload = _json.loads(out_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise RuntimeError(
            f"BGE worker {label} salio con rc=0 pero no entrego resultado;"
            f" stderr:\n{stderr_tail}"
        ) from exc
    if not payload.get("ok"):
        raise RuntimeError(
            f"BGE worker {label} fallo: {payload.get('error')!r};"
            f" traceback:\n{payload.get('traceback', '')[-1500:]}"
        )
    payload["elapsed_seconds"] = round(elapsed, 1)
    if progress is not None:
        progress.detail(f"{label} ok in {elapsed:.1f}s")
    return payload


def _run_release_build_process(
    dsn: str,
    *,
    rag_release_id: str,
) -> dict[str, object]:
    return _run_bge_worker(
        "build",
        [
            dsn,
            _EMBEDDING_PROFILE_ID,
            rag_release_id,
            str(_PROJECT_ROOT / "chunks"),
            str(_PROJECT_ROOT / "embeddings"),
        ],
        label="build",
    )


def _embed_questions_with_native_retry(
    dsn: str,
    *,
    progress: "_Progress",
) -> list[list[float]]:
    """Embebe las preguntas reintentando solo muerte nativa del hijo."""

    import json as _json

    cached_vectors = load_cached_query_embeddings(
        project_root=_PROJECT_ROOT,
        embedding_profile_id=_EMBEDDING_PROFILE_ID,
        questions=_QUESTIONS,
    )
    if cached_vectors is not None:
        progress.detail(
            f"reusing cached query embeddings for {len(_QUESTIONS)} questions"
        )
        return cached_vectors

    questions_path = _PROJECT_ROOT / ".worker_questions.json"
    questions_path.write_text(
        _json.dumps(list(_QUESTIONS), ensure_ascii=False), encoding="utf-8"
    )

    last_error: RuntimeError | None = None
    for attempt in range(1, _MAX_QUERY_PROCESS_ATTEMPTS + 1):
        try:
            payload = _run_bge_worker(
                "queries",
                [dsn, _EMBEDDING_PROFILE_ID, str(questions_path)],
                label=f"queries (intento {attempt}/{_MAX_QUERY_PROCESS_ATTEMPTS})",
                progress=progress,
            )
        except RuntimeError as exc:
            last_error = exc
            if attempt == _MAX_QUERY_PROCESS_ATTEMPTS:
                break
            continue

        vectors = payload["vectors"]
        dimension = int(payload["dimension"])
        assert len(vectors) == len(_QUESTIONS), (
            f"query embeddings={len(vectors)} preguntas={len(_QUESTIONS)}"
        )
        assert all(len(vector) == dimension for vector in vectors)
        save_cached_query_embeddings(
            project_root=_PROJECT_ROOT,
            embedding_profile_id=_EMBEDDING_PROFILE_ID,
            questions=_QUESTIONS,
            vectors=vectors,
        )
        return vectors

    raise RuntimeError(
        f"BGE queries subprocess fallo en todos los intentos"
        f" ({_MAX_QUERY_PROCESS_ATTEMPTS})"
    ) from last_error


def _run_bge_preflight(dsn: str, *, progress: _Progress) -> None:
    """Verifica que BGE soporta UN forward antes de gastar el build.

    Separa la senal: si el preflight muere nativamente, el problema es del
    runtime (Torch/OpenMP/venv/multiprocessing), no del pipeline ni del
    document embedding; si pasa, cualquier fallo posterior apunta al pipeline.
    """

    payload = _run_bge_worker(
        "preflight",
        [dsn, _EMBEDDING_PROFILE_ID],
        label="preflight",
        progress=progress,
    )
    dimension = int(payload["dimension"])


# ---------------------------------------------------------------------------
# Snapshot / release creation
# ---------------------------------------------------------------------------

class _Operator:
    def require_operator(self, *, actor_id: str) -> None:
        return None


def _create_fresh_snapshot_and_release(
    dsn: str,
    *,
    revisions: tuple[tuple[str, str], ...],
):
    from indexing.infrastructure.postgres.bundle_first import PsycopgTransactionManager
    from rag_platform.application.corpus_snapshot_service import (
        CreateCorpusSnapshotUseCase,
    )
    from rag_platform.application.platform_access import PlatformActor
    from rag_platform.application.release_service import (
        CreateRagReleaseDraftUseCase,
    )
    from rag_platform.domain.identity import IdentityKind, PlatformId
    from rag_platform.infrastructure.postgres.document_repositories import (
        PostgresCorpusSnapshotRepository,
        PostgresSourceDocumentRepository,
    )
    from rag_platform.infrastructure.postgres.project_repositories import (
        PostgresProjectRepository,
        PostgresRagVariantRepository,
        PostgresTargetBindingResolver,
    )
    from rag_platform.infrastructure.postgres.release_repositories import (
        PostgresRagReleaseRepository,
    )

    connection = _connect(dsn)
    connection.autocommit = False

    try:
        snapshot = CreateCorpusSnapshotUseCase(
            snapshots=PostgresCorpusSnapshotRepository(connection),
            documents=PostgresSourceDocumentRepository(connection),
            access_policy=_Operator(),
        ).execute(
            project_id=_PROJECT_SLUG,
            document_revision_ids=[
                revision_id
                for _relpath, revision_id in revisions
            ],
            actor=PlatformActor(actor_id=_ACTOR),
        )
        connection.commit()

        release = CreateRagReleaseDraftUseCase(
            variants=PostgresRagVariantRepository(connection),
            snapshots=PostgresCorpusSnapshotRepository(connection),
            bindings=PostgresTargetBindingResolver(connection),
            releases=PostgresRagReleaseRepository(connection),
            configuration_versions=PostgresProjectRepository(connection),
            release_id_factory=lambda: PlatformId(
                kind=IdentityKind.RAG_RELEASE,
                value="ragr_" + uuid.uuid4().hex[:16],
            ),
            access_policy=_Operator(),
            transactions=PsycopgTransactionManager(connection),
        ).execute(
            rag_variant_id=PlatformId(
                kind=IdentityKind.RAG_VARIANT,
                value=_VARIANT_ID,
            ),
            corpus_snapshot_id=snapshot.corpus_snapshot_id,
            target_binding_key=_BINDING_KEY,
            actor=PlatformActor(actor_id=_ACTOR),
        )
        connection.commit()

        return snapshot, release

    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def _build_fresh_release_with_native_retry(
    dsn: str,
    *,
    revisions: tuple[tuple[str, str], ...],
    progress: _Progress,
):
    """Create a fresh release for every native BGE build attempt.

    No partial release is resumed. A native child crash causes:
        partial derived state -> hard delete -> fresh snapshot -> fresh release
    """

    from concurrent.futures.process import BrokenProcessPool

    last_native_error: BrokenProcessPool | None = None

    for attempt in range(1, _MAX_BUILD_PROCESS_ATTEMPTS + 1):
        deleted = _clear_build_state(
            dsn,
            delete_snapshots_and_releases=True,
        )
        progress.detail(
            f"build attempt {attempt}: clean derived state "
            f"({_format_deleted_counts(deleted)})"
        )

        snapshot, release = _create_fresh_snapshot_and_release(
            dsn,
            revisions=revisions,
        )
        release_id = release.rag_release_id.value

        progress.detail(
            f"build attempt {attempt}: "
            f"snapshot={snapshot.corpus_snapshot_id.value} release={release_id}"
        )

        started = time.monotonic()

        try:
            report = _run_release_build_process(
                dsn,
                rag_release_id=release_id,
            )
        except BrokenProcessPool as exc:
            last_native_error = exc
            progress.detail(
                f"build BGE child died natively "
                f"({attempt}/{_MAX_BUILD_PROCESS_ATTEMPTS}); "
                "next attempt will start from a fresh release"
            )
            continue

        progress.detail(
            f"build succeeded attempt={attempt}/{_MAX_BUILD_PROCESS_ATTEMPTS} "
            f"in {time.monotonic() - started:.1f}s"
        )
        return snapshot, release, report, attempt

    raise RuntimeError(
        "BGE build subprocess murio nativamente en todos los intentos; "
        "no se intento resumir ninguna release parcial"
    ) from last_native_error


# ---------------------------------------------------------------------------
# Assertions / retrieval / report
# ---------------------------------------------------------------------------

def _release_integrity_facts(
    dsn: str,
    *,
    release_id: str,
    expected_revision_count: int,
) -> tuple[object, dict[str, object]]:
    from embedding.infrastructure.postgres.repositories import (
        PostgresEmbeddingProfileRepository,
    )

    connection = _connect(dsn)
    try:
        profile = PostgresEmbeddingProfileRepository(connection).get(
            _EMBEDDING_PROFILE_ID
        )

        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT count(*), "
                "       count(DISTINCT source_document_revision_id), "
                "       count(DISTINCT ordinal) "
                "FROM rag_release_memberships "
                "WHERE rag_release_id = %s",
                (release_id,),
            )
            row = cursor.fetchone()
            assert row is not None

            membership_total = int(row[0])
            membership_revisions = int(row[1])
            membership_ordinals = int(row[2])

            assert membership_total == expected_revision_count, (
                f"release memberships={membership_total}; "
                f"esperado={expected_revision_count}"
            )
            assert membership_revisions == expected_revision_count, (
                "la release tiene revisiones duplicadas o faltantes"
            )
            assert membership_ordinals == expected_revision_count, (
                "la release tiene ordinales duplicados o faltantes"
            )

            cursor.execute(
                f"SELECT COUNT(*) "
                f"FROM {_VECTOR_TABLE} AS v "
                f"WHERE v.project_id = %s "
                f"  AND EXISTS ("
                f"      SELECT 1 "
                f"      FROM rag_release_memberships AS m "
                f"      WHERE m.rag_release_id = %s "
                f"        AND m.project_id = v.project_id "
                f"        AND m.embedding_bundle_id = v.embedding_bundle_id"
                f"  )",
                (_PROJECT_ID, release_id),
            )
            total_vectors = int(cursor.fetchone()[0])
            assert total_vectors > 0, "la release no materializo vectores"

            cursor.execute(
                "SELECT count(DISTINCT chunk_bundle_id), "
                "       count(DISTINCT embedding_bundle_id), "
                "       count(DISTINCT materialization_id) "
                "FROM rag_release_memberships "
                "WHERE rag_release_id = %s",
                (release_id,),
            )
            bundle_row = cursor.fetchone()
            assert bundle_row is not None

            chunk_total = int(bundle_row[0])
            embedding_total = int(bundle_row[1])
            materializations = int(bundle_row[2])

            cursor.execute(
                "SELECT count(*) "
                "FROM indexing_nodes AS n "
                "WHERE n.project_id = %s "
                "  AND EXISTS ("
                "      SELECT 1 "
                "      FROM rag_release_memberships AS m "
                "      WHERE m.rag_release_id = %s "
                "        AND m.project_id = n.project_id "
                "        AND m.chunk_bundle_id = n.source_chunk_bundle_id"
                "  )",
                (_PROJECT_ID, release_id),
            )
            node_total = int(cursor.fetchone()[0])

            cursor.execute(
                "SELECT array_agg(DISTINCT rag_variant_id), "
                "       array_agg(DISTINCT rag_release_id) "
                "FROM embedding_runs "
                "WHERE project_id = %s AND rag_release_id = %s",
                (_PROJECT_ID, release_id),
            )
            run_variants, embedding_run_releases = cursor.fetchone()

            cursor.execute(
                "SELECT array_agg(DISTINCT rag_release_id) "
                "FROM indexing_runs "
                "WHERE project_id = %s AND rag_release_id = %s",
                (_PROJECT_ID, release_id),
            )
            (indexing_run_releases,) = cursor.fetchone()

            cursor.execute(
                "SELECT embedding_profile_id, semantic_recipe_fingerprint "
                "FROM rag_variants WHERE rag_variant_id = %s",
                (_VARIANT_ID,),
            )
            variant_row = cursor.fetchone()

        assert variant_row is not None, "rag variant no encontrada"
        variant_embedding_profile_id, variant_fingerprint = variant_row
        assert variant_embedding_profile_id == _EMBEDDING_PROFILE_ID

        run_releases = sorted(
            {
                value
                for value in [
                    *(embedding_run_releases or []),
                    *(indexing_run_releases or []),
                ]
                if value is not None
            }
        )
        assert run_releases == [release_id], (
            f"run release ids={run_releases}; esperado={[release_id]}"
        )

        facts = {
            "chunk_total": chunk_total,
            "embedding_total": embedding_total,
            "materializations": materializations,
            "node_total": node_total,
            "vector_total": total_vectors,
            "run_variants": [
                value
                for value in (run_variants or [])
                if value is not None
            ],
            "run_releases": run_releases,
            "variant_fingerprint": variant_fingerprint,
        }

        return profile, facts

    finally:
        connection.close()


def _retrieve_all_questions(
    dsn: str,
    *,
    release_id: str,
    query_vectors: list[list[float]],
    expected_hits: int,
    progress: _Progress,
) -> list[tuple[str, list[tuple]]]:
    connection = _connect(dsn)

    try:
        results: list[tuple[str, list[tuple]]] = []

        for index, question in enumerate(_QUESTIONS, start=1):
            progress.question(index, len(_QUESTIONS), question)
            started = time.monotonic()

            query_vector = query_vectors[index - 1]
            literal = (
                "["
                + ",".join(repr(float(component)) for component in query_vector)
                + "]"
            )

            with connection.cursor() as cursor:
                cursor.execute(
                    f"SELECT "
                    f"  v.node_id, "
                    f"  v.project_id, "
                    f"  n.source_relpath, "
                    f"  n.node_role, "
                    f"  COALESCE(n.section_title, p.section_title) AS section_title, "
                    f"  COALESCE(n.section_path, p.section_path) AS section_path, "
                    f"  left(n.text, 1200), "
                    f"  1 - (v.embedding <=> %s::vector) AS score "
                    f"FROM {_VECTOR_TABLE} AS v "
                    f"JOIN indexing_nodes AS n "
                    f"  ON n.project_id = v.project_id "
                    f" AND n.node_id = v.node_id "
                    f"LEFT JOIN indexing_nodes AS p "
                    f"  ON p.project_id = n.project_id "
                    f" AND p.node_id = n.parent_node_id "
                    f"WHERE v.project_id = %s "
                    f"  AND EXISTS ("
                    f"      SELECT 1 "
                    f"      FROM rag_release_memberships AS m "
                    f"      WHERE m.rag_release_id = %s "
                    f"        AND m.project_id = v.project_id "
                    f"        AND m.embedding_bundle_id = v.embedding_bundle_id"
                    f"  ) "
                    f"ORDER BY v.embedding <=> %s::vector "
                    f"LIMIT %s",
                    (
                        literal,
                        _PROJECT_ID,
                        release_id,
                        literal,
                        _TOP_K,
                    ),
                )
                hits = list(cursor.fetchall())

            assert len(hits) == expected_hits, (
                f"{question!r}: hits={len(hits)} esperado={expected_hits}"
            )
            assert all(row[1] == _PROJECT_ID for row in hits), (
                "retrieval devolvio vector de otro proyecto"
            )

            node_ids = [row[0] for row in hits]
            assert len(node_ids) == len(set(node_ids)), (
                "retrieval devolvio node_id duplicado"
            )

            seen_fingerprints: set[str] = set()
            deduped_hits: list[tuple] = []
            for row in hits:
                snippet_text = row[6] or ""
                normalized = " ".join(snippet_text.strip().lower().split())
                fp = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
                if fp not in seen_fingerprints:
                    seen_fingerprints.add(fp)
                    deduped_hits.append(row)
            hits = deduped_hits

            scores = [float(row[6]) for row in hits]
            assert scores == sorted(scores, reverse=True), (
                "retrieval no viene ordenado por similitud descendente"
            )

            progress.detail(
                f"q{index} done hits={len(hits)} "
                f"in {time.monotonic() - started:.2f}s"
            )
            results.append((question, hits))

        return results

    finally:
        connection.close()


def _write_retrieval_report(
    path: Path,
    *,
    results: list[tuple[str, list[tuple]]],
    facts: dict[str, object],
) -> None:
    lines = [
        "# Reporte end-to-end plataforma RAG (local, BGE-M3)",
        "",
        f"- Generado: {facts['generated_at']}",
        f"- Proyecto: `{facts['project_id']}`",
        f"- Variante: `{facts['variant_id']}`",
        f"- Release: `{facts['release_id']}`",
        f"- Build attempt: {facts['build_attempt']}",
        f"- Documentos: {facts['document_count']}",
        f"- Vectores release-scoped: {facts['vector_total']}",
        "",
        "## Pipeline",
        "",
        f"- chunk bundles: {facts['chunk_total']}",
        f"- embedding bundles: {facts['embedding_total']}",
        f"- indexing materializations: {facts['materializations']}",
        f"- indexing nodes: {facts['node_total']}",
        f"- embedding/indexing run release ids: `{facts['run_releases']}`",
        "",
        "## Embedding recipe",
        "",
        f"- provider: `{facts['embedding']['provider']}`",
        f"- model: `{facts['embedding']['model']}`",
        f"- dimension: {facts['embedding']['dimension']}",
        f"- metric: `{facts['embedding']['metric']}`",
        f"- normalization: `{facts['embedding']['normalization']}`",
        f"- profile: `{facts['embedding']['profile_id']}`",
        "",
        f"## Retrieval - {len(results)} preguntas, top_k={facts['top_k']}",
        "",
    ]

    for question, hits in results:
        lines.extend(
            [
                f"### {question}",
                "",
                "| # | score | documento | rol | seccion | seccion_ruta | chunk |",
                "|---|------:|-----------|-----|---------|--------------|-------|",
            ]
        )

        for rank, row in enumerate(hits, start=1):
            (
                _node_id,
                _project_id,
                source_relpath,
                role,
                section,
                section_path,
                snippet,
                score,
            ) = row

            safe_source = (source_relpath or "").replace("|", "\\|")
            safe_section = (section or "").replace("|", "\\|")
            safe_section_path = (section_path or "").replace("|", "\\|")
            safe_snippet = (
                (snippet or "")
                .replace("\n", " ")
                .replace("|", "\\|")[:1200]
            )

            lines.append(
                f"| {rank} | {float(score):.4f} | "
                f"{safe_source} | {role} | {safe_section} | {safe_section_path} | {safe_snippet} |"
            )

        lines.append("")

    lines.extend(["## Documentos incluidos", ""])
    for relpath in facts["documents"]:
        lines.append(f"- `{relpath}`")

    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


# ---------------------------------------------------------------------------
# The E2E
# ---------------------------------------------------------------------------

@pytest.mark.corpus
@pytest.mark.bge_runtime
@pytest.mark.postgres_live
def test_end_to_end_local_pipeline_and_retrieval(capsys, request) -> None:
    progress = _Progress(capsys, total_steps=10)

    progress.step("validating local corpus, DSN and seeded RAG variant")

    if not _RAW_ROOT.exists():
        pytest.skip(f"corpus ausente: {_RAW_ROOT}")

    raw_relpaths = _raw_relpaths()
    assert raw_relpaths, f"corpus raw vacio: {_RAW_ROOT}"

    dsn = _dsn()
    if not dsn:
        pytest.skip("sin DSN PostgreSQL")

    _assert_local_e2e_dsn(dsn)

    if not _variant_seeded(dsn):
        pytest.skip(
            "proyecto/variante no sembrados; "
            "corre scripts/rag_platform/seed_project.py"
        )

    _acquire_e2e_lock()

    def _cleanup_after_test() -> None:
        try:
            progress.step("hard deleting local E2E state")
            deleted = _hard_delete_e2e_project_state(
                dsn,
                raw_relpaths=raw_relpaths,
            )
            progress.detail(
                f"post-test cleanup: {_format_deleted_counts(deleted)}"
            )
        finally:
            _release_e2e_lock()

    request.addfinalizer(_cleanup_after_test)

    progress.step("hard deleting stale local E2E state")
    deleted = _hard_delete_e2e_project_state(
        dsn,
        raw_relpaths=raw_relpaths,
    )
    progress.detail(f"pre-test cleanup: {_format_deleted_counts(deleted)}")

    progress.step("running real raw ingestion and normalization")
    ingestion_cli = _load(
        "run_project_ingestion_e2e",
        "scripts/rag_platform/run_project_ingestion.py",
    )

    rc = ingestion_cli.main(
        [
            "--project-id",
            _PROJECT_ID,
            "--rag-variant-id",
            _VARIANT_ID,
            "--normalize",
            "--force",
        ]
    )
    assert rc == 0, "raw+normalize reporto fallos"
    capsys.readouterr()

    progress.step("verifying source revisions cover the entire raw corpus")
    revisions = _source_revisions_for_project(dsn)
    revision_relpaths = tuple(relpath for relpath, _ in revisions)

    assert revisions, "ingestion no registro source revisions"
    assert len(revisions) == len(raw_relpaths), (
        f"source revisions={len(revisions)} raw files={len(raw_relpaths)}"
    )
    assert len(revision_relpaths) == len(set(revision_relpaths)), (
        "hay source_relpath duplicados en source_document_revisions"
    )
    assert set(revision_relpaths) == set(raw_relpaths), (
        "source revisions no cubren exactamente el corpus raw; "
        f"faltan={sorted(set(raw_relpaths) - set(revision_relpaths))}, "
        f"sobran={sorted(set(revision_relpaths) - set(raw_relpaths))}"
    )

    progress.detail(
        f"raw_documents={len(raw_relpaths)} revisions={len(revisions)}"
    )

    progress.step("preflight: one minimal BGE forward in a clean subprocess")
    _run_bge_preflight(dsn, progress=progress)

    progress.step("building a fresh real RAG release")
    with _Heartbeat("release build"):
        snapshot, release, build_report, build_attempt = (
            _build_fresh_release_with_native_retry(
                dsn,
                revisions=revisions,
                progress=progress,
            )
        )

    release_id = release.rag_release_id.value

    assert str(build_report["rag_release_id"]) == release_id
    assert int(build_report["revisions_built"]) == len(revisions)
    assert (
        int(build_report["built_stages"])
        + int(build_report["reused_stages"])
        == len(revisions) * 4
    ), "cada revision debe resolver normalize/chunk/embed/index"

    progress.detail(
        f"release={release_id} "
        f"snapshot={snapshot.corpus_snapshot_id.value} "
        f"built={build_report['built_stages']} "
        f"reused={build_report['reused_stages']}"
    )

    progress.step("verifying release memberships and physical vectors")
    profile, persistence = _release_integrity_facts(
        dsn,
        release_id=release_id,
        expected_revision_count=len(revisions),
    )

    total_vectors = int(persistence["vector_total"])
    expected_hits = min(_TOP_K, total_vectors)

    progress.detail(
        f"memberships={len(revisions)} "
        f"vectors={total_vectors} "
        f"expected_hits_per_question={expected_hits}"
    )

    progress.step("embedding smoke queries with the release embedding profile")
    query_vectors = _embed_questions_with_native_retry(
        dsn,
        progress=progress,
    )

    assert len(query_vectors) == len(_QUESTIONS), (
        f"query embeddings={len(query_vectors)} questions={len(_QUESTIONS)}"
    )
    assert all(
        len(vector) == profile.dimension
        for vector in query_vectors
    ), (
        "dimension de query embedding no coincide con el embedding profile "
        f"{_EMBEDDING_PROFILE_ID} ({profile.dimension})"
    )

    progress.step("running release-scoped pgvector retrieval")
    results = _retrieve_all_questions(
        dsn,
        release_id=release_id,
        query_vectors=query_vectors,
        expected_hits=expected_hits,
        progress=progress,
    )

    progress.step("writing retrieval report for manual relevance inspection")

    facts = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "project_id": _PROJECT_ID,
        "variant_id": _VARIANT_ID,
        "release_id": release_id,
        "build_attempt": build_attempt,
        "documents": list(revision_relpaths),
        "document_count": len(revisions),
        "top_k": _TOP_K,
        **persistence,
        "embedding": {
            "provider": profile.provider,
            "model": profile.model,
            "dimension": profile.dimension,
            "metric": profile.distance_metric,
            "normalization": profile.normalization,
            "profile_id": _EMBEDDING_PROFILE_ID,
            "configuration_fingerprint": profile.expected_fingerprint().value,
        },
    }

    report_path = _REPO_ROOT / "e2e_retrieval_report.md"
    _write_retrieval_report(
        report_path,
        results=results,
        facts=facts,
    )

    progress.detail(f"report={report_path.name}")

