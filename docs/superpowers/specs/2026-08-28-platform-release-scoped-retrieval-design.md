# Platform Release-Scoped Retrieval Design

## Context

Today the `RAG / Releases` screen mixes two different concepts:

- Platform release lifecycle, which is organized around `project_id`, `rag_variant_id`, and `rag_release_id`
- Legacy retrieval diagnostics, which are organized around `retrieval_profile_id`

This makes the operator experience confusing in two ways:

1. The screen does not make it sufficiently clear which releases belong to which `rag variant`.
2. The Retrieval section does not let the operator test the exact RAG target they care about. It exposes legacy retrieval profiles instead of letting the operator choose a variant and one of its releases.

At the same time, production chatbot behavior must remain fail-closed and unchanged:

- The production chatbot API continues to require an explicit `rag_release_id`
- The production chatbot API continues to reject any release that is not `published`

The new Retrieval experience in Platform is therefore an **operator-only testing surface** over release-scoped evidence, not a change in production activation or chatbot serving semantics.

## Goals

- Replace the Retrieval panel inside `RAG Platform` with a release-scoped testing workflow.
- Let operators choose `rag variant` and `rag release` directly.
- Allow testing against `draft`, `validated`, and `published` releases inside Platform.
- Keep production chatbot dispatch restricted to `published` releases only.
- Make the release catalog clearly show which releases belong to which variant.
- Preserve fail-closed behavior when the chosen release has no resolvable retrieval lane or no evidence.

## Non-Goals

- Do not change the production chatbot API contract.
- Do not auto-activate legacy `retrieval_profiles` when building or publishing a release.
- Do not merge Platform release testing with the legacy Retrieval lane.
- Do not invent a global “active release” concept that the backend does not own.

## Options Considered

### Option 1: New Platform release-scoped retrieval endpoints

Expose Platform-specific retrieval test endpoints that accept `project_id`, `rag_variant_id`, and `rag_release_id`, and route them through the existing release-scoped retrieval backend.

Pros:

- Honest contract: the API matches what the operator is selecting
- Clear separation from legacy retrieval profiles
- Preserves fail-closed boundaries between operator testing and production chatbot dispatch

Cons:

- Adds new API surface

### Option 2: Extend legacy `/api/retrieval/*` to accept release identifiers

Pros:

- Reuses existing frontend panel structure

Cons:

- Mixes two incompatible mental models in one API
- Makes documentation and UI copy harder to keep precise
- Increases risk of hidden behavior drift between legacy and Platform

### Option 3: Translate release choice to a synthetic profile in the frontend

Pros:

- Smallest frontend-only surface change

Cons:

- Leaks backend internals into the frontend
- Still forces the UI to pretend the operator is choosing a profile, not a release
- Makes fail-closed reasoning weaker

### Decision

Choose **Option 1**.

## Backend Design

### New Platform retrieval test endpoints

Add Platform-scoped endpoints under `/api/platform/retrieval`:

- `GET /api/platform/retrieval/targets?project_id=...`
- `POST /api/platform/retrieval/validate`
- `POST /api/platform/retrieval/search`

#### `GET /targets`

Purpose:

- Return the set of retrieval test targets for the selected project.
- Organize data primarily by variant, with nested releases.

Response shape:

- `project_id`
- `variants[]`
  - `rag_variant_id`
  - `variant_state`
  - `releases[]`
    - `rag_release_id`
    - `release_number`
    - `release_state`
    - `corpus_snapshot_id`
    - `target_binding_key`
    - `release_manifest_hash`
    - `chatbot_production_eligible: boolean`
    - `operator_testable: boolean`

Rules:

- `chatbot_production_eligible = release_state == "published"`
- `operator_testable = release_state in {"draft", "validated", "published"}`
- `retired` and `failed` releases are visible for clarity but cannot be selected for operator testing

#### `POST /validate`

Request:

- `project_id`
- `rag_variant_id`
- `rag_release_id`

Behavior:

- Resolve the release fail-closed
- Verify that the release belongs to the given project and variant
- Verify that the release is operator-testable
- Run release-scoped validation using the existing release retrieval lane
- Return validation results tied to the selected release

#### `POST /search`

Request:

- `project_id`
- `rag_variant_id`
- `rag_release_id`
- `query`
- `top_k`

Behavior:

- Resolve the selected release fail-closed
- Verify membership and operator scope
- Search evidence against that release’s scoped artifacts
- Return provenance-rich evidence including `rag_release_id`

### Reuse existing release-scoped retrieval implementation

Do not build a second retrieval engine.

Reuse the logic already introduced in:

- `chatbot.infrastructure.release_scoped_retrieval`

Refactor it behind a shared application port that both of these use cases can call:

- chatbot production dispatch
- Platform operator retrieval testing

The policy difference is only release-state eligibility:

- chatbot production: `published` only
- Platform retrieval testing: `draft`, `validated`, `published`

This state-policy check should live outside the low-level search adapters, so the retrieval engine stays state-agnostic.

### Error handling

Add explicit fail-closed error cases for operator testing:

- release does not belong to project
- release does not belong to variant
- release state not testable
- no release-scoped retrieval lane available
- no evidence found

These should remain distinct from chatbot production errors so logs and UI copy remain precise.

## Frontend Design

### Replace the legacy Retrieval panel in Platform

Inside `RAG / Releases`, replace the current profile-based Retrieval panel with a Platform retrieval test panel that works like this:

1. Choose `rag variant`
2. Choose `release`
3. See release status and eligibility badges
4. Run validation
5. Run evidence search

This panel no longer loads `retrieval_profiles` for Platform testing.

### Release map clarity

The left-side release catalog remains grouped by variant and becomes the primary navigation model:

- each `rag variant` gets its own visual group
- each group lists its releases in descending release order
- each release shows status badges
- `published` releases show `Usable por API chatbot`
- selected release shows `En gestión`

The Retrieval test panel mirrors this same hierarchy so the operator never has to mentally translate between “variant/release” and “profile”.

### Retrieval test panel copy

The panel should say clearly:

- this is a Platform retrieval test
- it runs against the selected release
- production chatbot remains `published`-only

Badges:

- `draft` → `Prueba interna`
- `validated` → `Prueba interna`
- `published` → `Prueba interna + chatbot producción`
- `retired` / `failed` → visible but non-testable

### State flow

Frontend state should be driven by:

- selected project
- selected variant
- selected release
- retrieval test status
- retrieval test validation result
- retrieval test search result

When the selected variant changes:

- clear selected release if it no longer belongs to that variant
- clear stale validation and search results

When the selected release changes:

- clear stale validation and search results
- refresh the release-scoped test status if available

## Testing Strategy

### Backend

Add tests for:

- listing grouped retrieval targets by variant and release
- validating a `draft` release in Platform
- validating a `validated` release in Platform
- validating a `published` release in Platform
- rejecting `retired` and `failed` releases for Platform retrieval testing
- preserving chatbot production rejection for non-`published` releases
- searching evidence against release-scoped artifacts with correct provenance

### Frontend

Add or update component tests for:

- grouped variant → release selection
- disabled selection for non-testable releases
- status badges per release state
- copy that distinguishes operator testing from production chatbot behavior
- clearing stale search/validation results when variant or release changes
- preserving the clearer release grouping by variant in the main catalog

## Risks

- If shared release-scoped retrieval logic is not extracted cleanly, chatbot and Platform could drift.
- If Platform retrieval test endpoints accidentally reuse chatbot production state checks, operators will lose the ability to test `draft` and `validated` releases.
- If UI copy is vague, the old confusion will persist even after the contract is fixed.

## Rollout

1. Extract shared release-scoped retrieval use cases/policy boundaries in backend.
2. Add Platform retrieval test endpoints.
3. Replace the Platform retrieval panel frontend.
4. Update tests.
5. Verify that chatbot production behavior still rejects non-`published` releases.
