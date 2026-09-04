# ADR-012 — Remove ReleaseState.FAILED (failure lives on the build job)

- **Status**: Accepted / implemented (backend, 2026-09-04) — stub from `plans/2026-09-04-convergencia-mvp-limpieza.md`, implemented in PR-2 2.4
- **Related**: ADR-010 (async durable build), ADR-011 (serving authority)

## Context

`rag_platform/domain/lifecycle.py:45-67` defines `ReleaseState.FAILED` as terminal with transitions `DRAFT→FAILED` and `VALIDATED→FAILED`, and the front has a `failed` screen. But **no productive code transitions a release into `FAILED`**: when a build fails, `run_one_build` marks `ReleaseBuildJob.state = failed` (ADR-010), not the release. The state is a zombie: modeled and rendered, never reached.

## Decision

**Remove `ReleaseState.FAILED`.** A failed build leaves the release in `DRAFT`; the failure is observable on the `ReleaseBuildJob` (`error_code`/`error_message`). The operator fixes the cause and re-builds the same DRAFT release.

Transitions become:
```
DRAFT → VALIDATED → PUBLISHED → RETIRED
```

## Consequences

- `+` No unreachable state; domain matches behavior.
- `+` Retry is natural (re-build the DRAFT), no need to create a new release on failure.
- `−` Deletes the front `failed` screen and the FAILED transitions/tests.
- **Alternative (rejected)**: implement a real transition into `FAILED` and force a new release to retry — more state, worse retry UX for an internal MVP.
- Requires PR-2.

## Implementation note (2026-09-04)

Backend implemented in PR-2 task 2.4: `rag_platform/domain/lifecycle.py` (`ReleaseState.FAILED` and its transitions removed), `test_release_lifecycle.py`, and a new regression `test_build_fallido_deja_release_en_draft` in `test_release_incremental_build.py`. The front `failed` screen (this ADR's stated consequence) is **not** removed — out of scope for the backend-only session that implemented this; tracked as a follow-up.
