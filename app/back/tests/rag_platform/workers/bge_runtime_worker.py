"""Entrypoint de procesos REALES para los workloads BGE del E2E live.

En esta maquina, el primer forward de Torch/BGE-M3 muere con access violation
(0xC0000005) dentro de CUALQUIER hijo creado por ``multiprocessing`` (pool o
Process, spawn), de forma deterministica; el mismo codigo ejecutado como
script plano pasa consistente. Por eso el E2E lanza este modulo como proceso
real (``subprocess``) en lugar de usar multiprocessing. Beneficios adicionales:
exitcode nativo real, stderr completo (faulthandler) y timeout con kill del SO.

Contrato:
    python bge_runtime_worker.py <mode> <out_json_path> [args...]

    preflight <dsn> <profile_id>
    build     <dsn> <profile_id> <rag_release_id> <chunks_root> <embeddings_root>
    queries   <dsn> <profile_id> <questions_json_path>

Escribe ``{"ok": true, ...}`` en ``out_json_path`` y termina con exitcode 0;
ante error Python escribe ``{"ok": false, "error": ...}`` y sale con 3. Una
muerte nativa la detecta el padre por exitcode != 0 (codigo del SO).
"""

import json
import logging
import os
import sys
import time
import traceback
from pathlib import Path

_WORKER_FILE = Path(__file__).resolve()
_REPO_ROOT = _WORKER_FILE.parents[5]

_MODES = ("preflight", "build", "queries")


def _configure_runtime() -> None:
    """Entorno nativo del hijo antes de Torch/FlagEmbedding."""

    os.environ["OMP_NUM_THREADS"] = "1"
    os.environ["MKL_NUM_THREADS"] = "1"
    os.environ["OPENBLAS_NUM_THREADS"] = "1"
    os.environ["NUMEXPR_NUM_THREADS"] = "1"
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    os.environ["EMBEDDING_BATCH_SIZE"] = "1"
    os.environ.setdefault("HF_HUB_CACHE", ".cache/huggingface")

    import faulthandler

    faulthandler.enable(all_threads=True)

    import torch

    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)


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


def _attach_build_logging():
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


def _detach_build_logging(state) -> None:
    handler, previous_root_level, previous_levels = state
    root = logging.getLogger()
    root.removeHandler(handler)
    root.setLevel(previous_root_level)
    for namespace, level in previous_levels.items():
        logging.getLogger(namespace).setLevel(level)


def _load_profile(dsn: str, profile_id: str):
    import psycopg2

    from embedding.infrastructure.postgres.repositories import (
        PostgresEmbeddingProfileRepository,
    )

    connection = psycopg2.connect(**_parse_dsn(dsn))
    try:
        return PostgresEmbeddingProfileRepository(connection).get(profile_id)
    finally:
        connection.close()


def _parse_dsn(dsn: str):
    from psycopg2.extensions import parse_dsn

    return parse_dsn(dsn)


def _run_preflight(argv: list[str]) -> dict:
    dsn, profile_id = argv[0], argv[1]
    profile = _load_profile(dsn, profile_id)

    from embedding.application.engine_registry import DefaultEmbeddingEngineRegistry

    engine = DefaultEmbeddingEngineRegistry().resolve_query_engine(profile)
    vectors = engine.embed_queries(["prueba de funcionamiento bge"])
    assert vectors, "preflight sin vectores"
    dimension = len(vectors[0])
    assert dimension == int(profile.dimension), (
        f"dimension {dimension} != perfil {profile.dimension}"
    )
    return {"dimension": dimension}


def _query_section_coverage(dsn: str) -> dict:
    import psycopg2

    connection = psycopg2.connect(**_parse_dsn(dsn))
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT "
                "  COUNT(*) AS total_nodes, "
                "  COUNT(section_title) AS nodes_with_section, "
                "  COUNT(DISTINCT section_title) AS distinct_sections "
                "FROM indexing_nodes"
            )
            total, with_section, distinct = cursor.fetchone()
        return {
            "total_nodes": int(total),
            "nodes_with_section": int(with_section),
            "distinct_sections": int(distinct),
            "section_coverage_pct": round(
                100.0 * int(with_section) / int(total), 1
            ) if int(total) > 0 else 0.0,
        }
    finally:
        connection.close()


def _run_build(argv: list[str]) -> dict:
    dsn, _profile_id, rag_release_id_value = argv[0], argv[1], argv[2]
    chunks_root, embeddings_root = Path(argv[3]), Path(argv[4])

    os.environ["SST_POSTGRES_DSN"] = dsn
    os.environ["SST_PERSISTENCE_MODE"] = "postgres"
    os.environ["SST_FEATURE_RAG_PLATFORM_V1"] = "true"

    from api.dependencies import build_pipeline_services_from_env
    from rag_platform.application.platform_access import PlatformActor
    from rag_platform.domain.identity import IdentityKind, PlatformId

    log_state = _attach_build_logging()
    try:
        services = build_pipeline_services_from_env(
            chunks_root=chunks_root,
            embeddings_root=embeddings_root,
        )
        try:
            report = services.rag_platform_build.execute(
                rag_release_id=PlatformId(
                    kind=IdentityKind.RAG_RELEASE, value=rag_release_id_value
                ),
                actor=PlatformActor(actor_id="operator-retrieval-e2e"),
            )
        finally:
            services.close()
    finally:
        _detach_build_logging(log_state)

    return {
        "rag_release_id": str(report.rag_release_id),
        "revisions_built": int(report.revisions_built),
        "reused_stages": int(report.reused_stages),
        "built_stages": int(report.built_stages),
        **_query_section_coverage(dsn),
    }


def _run_queries(argv: list[str]) -> dict:
    dsn, profile_id = argv[0], argv[1]
    questions = json.loads(Path(argv[2]).read_text(encoding="utf-8"))
    profile = _load_profile(dsn, profile_id)

    from embedding.application.engine_registry import DefaultEmbeddingEngineRegistry

    engine = DefaultEmbeddingEngineRegistry().resolve_query_engine(profile)
    vectors = engine.embed_queries(list(questions))
    return {
        "dimension": int(profile.dimension),
        "vectors": [[float(c) for c in vector] for vector in vectors],
    }


def main() -> int:
    if len(sys.argv) < 3:
        print("usage: bge_runtime_worker.py <mode> <out_json> [...]", file=sys.stderr)
        return 2
    mode, out_json_path = sys.argv[1], Path(sys.argv[2])
    argv = sys.argv[3:]
    if mode not in _MODES:
        print(f"modo desconocido: {mode}", file=sys.stderr)
        return 2

    _configure_runtime()
    try:
        runner = {
            "preflight": _run_preflight,
            "build": _run_build,
            "queries": _run_queries,
        }[mode]
        started_at = time.monotonic()
        payload = runner(argv)
        payload["elapsed_seconds"] = round(time.monotonic() - started_at, 1)
        out_json_path.write_text(
            json.dumps({"ok": True, **payload}), encoding="utf-8"
        )
        return 0
    except BaseException as exc:  # noqa: BLE001 - se reporta por el archivo
        out_json_path.write_text(
            json.dumps(
                {"ok": False, "error": repr(exc), "traceback": traceback.format_exc()}
            ),
            encoding="utf-8",
        )
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
