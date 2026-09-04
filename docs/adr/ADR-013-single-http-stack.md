# ADR-013 — Single HTTP stack (retire the GUI ThreadingHTTPServer)

- **Status**: Proposed (2026-09-04) — stub from `plans/2026-09-04-convergencia-mvp-limpieza.md`
- **Related**: ADR-010 (async durable build — documents the shared-connection/bridge pain)

## Context

Two HTTP stacks run today:
- `ingestion.gui.server` — a `ThreadingHTTPServer` that serves manual routes (`/api/auth`, `/api/upload`, `/api/review`, `/api/pipeline/run`, `/api/settings`, `/api/validate`, `/api/promote`, `/api/chunking`) and bridges the rest to FastAPI via `AsgiBridge`, translating cookie→bearer and serializing everything through a global `_PIPELINE_BRIDGE_LOCK`.
- `api.app` (FastAPI) — the modern stack, also mounted by `chatbot_runtime` in Docker.

The bridge **omits FastAPI lifespan/warmup**, so behavior differs by entrypoint (systematic drift). The manual business routes are reached only through the now-dead legacy front surface; only `/api/auth/*` is still used by the SPA (`operatorAuthApi.ts`).

## Decision

**Collapse to one FastAPI stack.** Migrate `/api/auth/*` to a FastAPI router; delete the manual business routes with the legacy front (PR-5); then remove `ThreadingHTTPServer`, `AsgiBridge`, `_PIPELINE_BRIDGE_LOCK`, manual JSON/multipart/CORS/auth injection, and `_safe_rollback`. Use a connection-per-request/pool instead of the shared global psycopg2 connection. Gated by `SST_FEATURE_UNIFIED_HTTP` until cutover.

## Consequences

- `+` One lifecycle (lifespan + warmup + reconcilers) on every request path; no drift.
- `+` No global serialization lock; real concurrency via a pool.
- `+` Self-registration hole closed (empty scope ≠ global operator).
- `−` Auth session must be re-implemented on FastAPI (cookie same-origin retained).
- Requires PR-8 (after PR-4, PR-6).
