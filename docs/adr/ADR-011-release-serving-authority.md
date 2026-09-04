# ADR-011 — Release serving authority: PUBLISHED + memberships

- **Status**: Proposed (2026-09-04) — stub from `plans/2026-09-04-convergencia-mvp-limpieza.md`
- **Related**: ADR-006 (project/variant/release), ADR-009 (per-project isolation), ADR-010 (async durable build)

## Context

Two incompatible serving models coexist:
- **Low-level**: a lane is servable when `retrieval_profile.active = true` **and** vectors `is_active = true`. Exposed via `/api/platform/releases/{id}/activate` and the UI ("Activar en vivo: sin esto el chatbot recupera 0 resultados").
- **Release-scoped**: a lane is servable when the release is `PUBLISHED` and rows are in `rag_release_memberships`.

The chatbot's `PostgresReleaseScopedRetrievalPort.search()` already filters by `project_id + embedding_profile_id + indexing_target_id + corpus_version + rag_release_memberships + processing_status + review_status` and does **not** require `is_active`. So `/activate` is not a real prerequisite — the two models disagree about what "live" means.

## Decision

**`PUBLISHED` release + exact `rag_release_memberships` is the single serving authority.** The release-scoped retrieval path ignores `is_active` and the "active retrieval profile" concept. `/activate` is removed from the public release lifecycle; if retained, it is an internal admin operation (ADR-014) that does not gate the chatbot. Gated by `SST_FEATURE_RELEASE_SERVING_ONLY` during rollout.

## Consequences

- `+` One coherent definition of "servable"; no UI claim that contradicts the code.
- `+` `publish` must be fail-closed on a built lane (a published release always answers).
- `−` The "Activar en vivo" UX is removed/rewired; operators no longer toggle serving per vector.
- Requires PR-2. Supersedes the serving implications of ADR-010's activation notes.
