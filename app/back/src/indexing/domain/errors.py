"""Domain errors for bundle-first indexing, each carrying its public code."""

from __future__ import annotations


class IndexingDomainError(Exception):
    """Base class for indexing domain errors with a stable public code."""

    code = "INDEXING_DOMAIN_ERROR"
    http_status = 400


class IndexingRunNotFound(IndexingDomainError):
    """The indexing run does not exist."""

    code = "INDEXING_RUN_NOT_FOUND"
    http_status = 404


class IndexingTargetIncompatible(IndexingDomainError):
    """The resolved target cannot store this bundle's vectors."""

    code = "INDEXING_TARGET_INCOMPATIBLE"
    http_status = 409


class IndexingExecutorBusy(IndexingDomainError):
    """The bounded indexing queue is saturated."""

    code = "INDEXING_EXECUTOR_BUSY"
    http_status = 429


class IndexingIdempotencyConflict(IndexingDomainError):
    """One idempotency key was reused for a different request fingerprint."""

    code = "IDEMPOTENCY_CONFLICT"
    http_status = 409


class IndexingActivationBlocked(IndexingDomainError):
    """Activation was refused because a readiness precondition failed."""

    code = "INDEXING_ACTIVATION_BLOCKED"
    http_status = 409


class PostgresUnavailable(IndexingDomainError):
    """PostgreSQL is not configured or not reachable."""

    code = "POSTGRES_UNAVAILABLE"
    http_status = 503


class PgvectorUnavailable(IndexingDomainError):
    """The pgvector extension or a target table is not usable."""

    code = "PGVECTOR_UNAVAILABLE"
    http_status = 503


class VectorStoreWriteError(RuntimeError):
    """Vector store write failed and should trigger rollback.

    PR-7 7.1: moved from ``infrastructure/llama_index/pgvector_store.py`` (the
    legacy write lane being retired) since productive bundle-first modules
    (postgres vector repository, profile registry, in-memory bundle_first)
    import it too — it never belonged to the legacy package, it just lived
    there historically. Kept as a plain ``RuntimeError`` (not an
    ``IndexingDomainError``): no caller translates it to an HTTP code, it
    signals a write failure that must trigger a rollback in the caller's own
    transaction scope.
    """
