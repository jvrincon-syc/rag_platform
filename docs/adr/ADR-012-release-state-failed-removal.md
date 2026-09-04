# ADR-012 — Remove ReleaseState.FAILED (failure lives on the build job)

- **Status**: Proposed (2026-09-04) — stub from `plans/2026-09-04-convergencia-mvp-limpieza.md`
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
