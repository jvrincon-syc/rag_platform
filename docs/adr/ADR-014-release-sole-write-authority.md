# ADR-014 — RAG Release is the sole public write authority

- **Status**: Proposed (2026-09-04) — stub from `plans/2026-09-04-convergencia-mvp-limpieza.md`
- **Related**: ADR-006 (project/variant/release), ADR-011 (serving authority)

## Context

The FastAPI still exposes low-level write endpoints that mutate the same layers the Release lifecycle orchestrates:
- `POST /api/embedding/runs`
- `POST /api/indexing/runs`, `/activations`, `/rollbacks`
- `POST /api/retrieval/profiles`, `/profiles/{id}/activate`

These are current bundle-first implementations (not dead code), but they form a second write plane that can create indexing runs, activate bundles, and roll back outside a Release. The front's operational flow (Config → Release Build) already covers chunk/embed/index in one DB-persisted job; the standalone stage screens run nothing (`platformStageClients.ts` throws).

## Decision

**Only the RAG Release lifecycle is a public write authority.** The low-level write endpoints become internal/admin (or are removed once no consumer remains); the bundle-first use cases stay importable for Release + tests. Read/status/search/validate stay public as diagnostics. Rollback becomes a Release operation.

## Consequences

- `+` One place to reason about writes and provenance; no out-of-band mutation.
- `+` The front converges on Config + Release Build; recipe persisted via Variant/Config (DB), not the in-memory Map.
- `−` Any external caller of the low-level write endpoints must move to the Release flow or an admin path.
- Requires PR-6; enables PR-7 (retire the legacy document write lane).
