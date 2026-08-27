# RAG Platform Legacy Pipeline Parity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

> **Execution protocol — overrides every `Run`/verification step below:** implementing agents NEVER execute test/build/verification commands (`pytest`, `vitest`, `tsc`, `node *.test.mjs`, `npm run test|build|api:*`, OpenAPI export scripts). Wherever a step says "Run", the agent instead: (1) writes the code and tests, (2) copies the command block verbatim into its report for the operator, (3) STOPS and WAITS until the operator pastes the output — only then proceeds or fixes. Read-only inspection (`rg`, `Select-String`, `git status`, `git diff`) is permitted. Agents never stage, commit, push, stash, or amend; version-control operations belong exclusively to the operator.

> **Mandatory pre-read before any implementation:** the implementing agent MUST read these files end-to-end before Task 1 and must explicitly say in its handoff that it read them. If any file cannot be opened, STOP and ask the operator; do not infer the missing context.
>
> - `docs/superpowers/plans/Plan_Ajustado_Plataforma_RAG_MultiProyecto(3).md` through Fase 7 at minimum.
> - `AGENTS.md` (requested as `agents.md`; root project rules).
> - `app/front/AGENTS_front.md` (requested as `agents_front.md`; frontend-specific rules).
> - `README_REGLAS.md`.
>
> After reading, the agent must restate the non-negotiable requirement in its own words: Platform pipeline tabs must mount the exact same Legacy pipeline views/modules, with Platform identity/data injected, never lookalike Platform replacements.

**Goal:** Turn RAG Platform into the operational multi-project shell for the real Legacy pipeline GUI: the operator selects a `project_id`, works with the same Legacy pipeline screens, and Platform injects the correct `project_id`, `rag_variant_id`, `corpus_snapshot_id`, and `rag_release_id` through typed adapters over `/api/platform/*`.

**Architecture:** `OperatorApp` keeps two sibling surfaces: `Legacy pipeline` remains the global, single-corpus lane, and `RAG Platform` becomes a project-scoped host for the exact same Legacy GUI modules. The shared Legacy GUI is extracted from `DashboardApp` behind a typed `DashboardPipelineDataSource`; Legacy keeps the existing `/api/*` datasource, while Platform provides a datasource over `platformApi` and `PlatformProjectContext`. This plan deliberately does not create a second visual implementation of the pipeline; it changes the data boundary, not the operator experience. No parallel backend pipeline is created; the only backend extension is the minimal review-decision contract in Task 3, because the current snapshot endpoint can approve inclusion but cannot persist a standalone reject decision without trying to put `blocked` inside a releaseable snapshot.

**Tech Stack:** React 18, TypeScript strict mode, Vite, Vitest/jsdom component tests, existing `platformApi`, FastAPI `/api/platform/*`, PostgreSQL migrations, pytest backend contract/regression tests.

**Spec:** `docs/superpowers/plans/Plan_Ajustado_Plataforma_RAG_MultiProyecto(3).md` through Fase 7, `docs/superpowers/plans/2026-08-21-platform-gui-rework-reuse-legacy.md`, and the operator correction in this session: Platform must show the same Legacy pipeline screens and JS modules, not different Platform replacements that only reuse visual style, labels, cards, or copy.

## Acceptance Definition: "Same Exact Legacy View" (Overrides Everything Below)

This clause wins over ANY other instruction in this plan. If a task, table row,
or code sample below can be read as permitting a lookalike screen, this clause
prevails and the task must be redone.

**The requirement, with no room for interpretation:** each Platform pipeline
view renders THE SAME exported React component tree that the global Legacy lane
renders today — the same files, the same modules, the same DOM — with only two
differences: the data source (`DashboardPipelineDataSource` over `/api/platform/*`)
and the scope (`project_id`, plus the `rag_variant_id` resolved from the
recipe configured across those same screens). One GUI implementation, two data
contexts.

```text
Platform "Operacion" tab          -> DashboardPipelineApp(view="operations")         <- same component as Legacy
Platform "Revision" tab           -> DashboardPipelineApp(view="review")             <- same DocumentWorkspaces review UI
Platform "Inventario" tab         -> DashboardPipelineApp(view="inventory")          <- same DocumentWorkspaces inventory UI
Platform "Chunking" tab           -> DashboardPipelineApp(view="chunking")           <- same ChunkingWorkspace
Platform "Embedding/Indexing" tab -> DashboardPipelineApp(view="embedding-indexing") <- same EmbeddingIndexingWorkspace
```

There is exactly ONE `DashboardPipelineApp`, ONE `DocumentWorkspaces.tsx`, ONE
`ChunkingWorkspace.tsx`, ONE `EmbeddingIndexingWorkspace.tsx` in the app. No
file under `features/platform/**` may render pipeline tables, cards,
inspectors, run controls, or stage panels of its own.

**Litmus test — apply to every file you touch:**

1. Name the file that renders what the operator sees on a Platform pipeline
   tab. If it is a platform-owned file drawing pipeline UI itself, STOP: that
   is a lookalike and violates this plan.
2. Mentally delete the Platform host (`PlatformLegacyPipelineWorkspace.tsx`):
   if your design needed to copy or port any Legacy component for Platform to
   work, the design is wrong — inject data, never duplicate UI.
3. Change a Legacy panel (add a column, fix a button). Platform must inherit
   the change automatically with zero parallel work. If Platform needs its own
   edit for the same improvement, you built two GUIs.
4. The ONLY new frontend files this plan allows are: datasource/adapters, pure
   mappers, the variant resolver + recipe draft, the thin Platform host, and
   their tests. Any other file rendering pipeline UI is outside the contract.

**Explicitly forbidden — this exact fault happened before:**

- New Platform screens reusing Legacy tokens, cards, buttons, chips, labels,
  or layout while reimplementing behavior ("we reused visual elements" is a
  FAILED acceptance, not partial credit).
- Relabeling Platform workspaces with Legacy names while mounting different
  modules.
- Informational/read-only summary panels standing in for operational Legacy
  screens.
- Porting Legacy panel logic into Platform-owned components or hooks "because
  it is cleaner".
- Any reachable route where a pipeline tab shows a Platform-built replacement
  (`DocumentIntakeWorkspace`, `CorpusSnapshotWorkspace` as "review",
  `ProjectInventoryWorkspace`, `PlatformReleaseBuildStageInfo`).

The ONLY permitted visual/behavioral differences under Platform scope are:
injected datasource results (including honest `N/D - no expuesto por
Platform` values), hiding the internal Legacy navigation when Platform owns
routing, the project scope subtitle, fail-closed notices for actions
Platform routes differently, AND controls whose contract Platform does not
have rendered disabled-with-reason instead of silently ignored. Verified
cases: the upload "Categoria" select (`POST /documents` accepts only
`file` + `source_relpath`), the OCR threshold input (no normalize contract),
and `Validar salida`/`Promover staging` (release-scoped actions owned by
`RAG / Releases`). The provider/route selects stay ENABLED: they feed the
recipe draft for variant resolution. A control that looks editable but does
nothing is a violation, same as a lookalike screen.

## Global Constraints

- Read "Acceptance Definition: Same Exact Legacy View" FIRST; it overrides every other instruction in this plan. Visual/style reuse without mounting the real Legacy modules is a failed implementation, not a partial one.
- The backend is treated as functional for release build; protect `npm run python -- -m pytest app/back/tests/rag_platform/test_end_to_end_release_build.py::test_release_build_persiste_rag_release_id -v`.
- RAG Platform is an operational multi-project platform for managing corpora, RAG variants, corpus snapshots, release builds, validation, publication, and version history. It is not a read-only viewer.
- A missing review-decision endpoint is a Platform contract gap, not a reason to hide `Aprobar`/`Rechazar` or call the review/inventory flow read-only.
- Do not rewrite or duplicate the pipeline business flow. Reuse the Legacy pipeline UI and panels by importing/extracting the actual existing JS/TSX modules.
- Reusing visual elements, design tokens, card styles, button styles, or table styles is not enough. The acceptance target is the same GUI behavior and component tree, scoped by Platform identity.
- Pipeline view labels and titles come from the existing Legacy dashboard contracts (`DASHBOARD_VIEWS` and `viewTitles`). Platform must not maintain a second copy with accented/unaccented labels, different titles, or read-only descriptions that can drift from the Legacy GUI.
- Platform must use existing project-scoped endpoints under `/api/platform/*`; do not call global Legacy endpoints for Platform data.
- Keep Legacy pipeline global and unchanged in behavior; it must not import Platform types.
- Platform may add only a thin datasource/adapter layer owned by `features/platform`.
- Platform identity is carried at adapter/use-case boundaries: `project_id` scopes documents and profiles, `rag_variant_id` scopes the intended RAG variant when needed, `corpus_snapshot_id` freezes a releaseable corpus, and `rag_release_id` belongs to release lifecycle/build/validate/publish/retire.
- `rag_variant_id` is constructed, not hand-picked: Platform resolves/creates it from the configurations the operator makes INSIDE the Legacy screens (provider/route in `Operacion`, chunking profile in `Chunking`, embedding profile in `Embedding/Indexing`) reconfirmed against the project variant-matrix. Normalize and release-draft flows receive only the resolved `rag_variant_id`; they never receive profile ids typed or stored outside the matrix.
- Not every pipeline screen has a `rag_release_id` yet. `Operacion`, `Revision`, `Inventario`, `Chunking`, and `Embedding/Indexing` operate on a selected project; the `rag_variant_id` they need is resolved at operation time from the recipe (see the resolution contract). `RAG / Releases` is where `corpus_snapshot_id` becomes a release draft and then a `rag_release_id`.
- The frontend never sends physical targets, table names, absolute paths, secrets, vectors, raw chunks, or `actor_id`.
- `project_id`, `rag_variant_id`, `corpus_snapshot_id`, `rag_release_id`, idempotency keys, status, and error envelopes remain visible where relevant.
- `needs_review` remains fail-closed and visible; never auto-approve, hide, or convert it into a fake success.
- Do not fabricate document metadata that Platform does not expose. Show `N/D` or an explicit "No expuesto por Platform" label inside the Legacy inspector fields.
- NO COMMIT / NO PUSH: agents never stage, commit, push, stash, or amend — not even "if everything is green". Work is handed over as working-tree state; version-control operations belong exclusively to the operator.
- NO TEST EXECUTION BY AGENTS: every command under a `Run`/verification step is executed ONLY by the operator. Each task closes by delivering the exact command list and STOPPING until the output comes back (see the Execution protocol at the top of this file).

---

## Product Context

The existing Legacy pipeline is already the operator's real workflow for one corpus:

```text
Operacion -> Revision -> Inventario -> Chunking -> Embedding/Indexing -> Retrieval/use
```

It has concrete behavior that operators recognize: status panels, upload/intake
controls, review actions, inventory inspectors, chunking run controls,
embedding/indexing activation flows, and retrieval readiness. Those screens are
not merely a visual theme. They encode the operational workflow and the mental
model the operator already uses to decide whether a corpus is ready.

RAG Platform is not supposed to replace that workflow with a second pipeline.
It is the control plane around the same pipeline when the organization has many
projects/corpora. Platform adds the identities and lifecycle controls that a
single global Legacy lane does not have:

```text
project_id          -> which corpus/project the operator is managing
rag_variant_id      -> which RAG configuration/variant is being prepared
corpus_snapshot_id  -> immutable set of approved revisions selected for a release
rag_release_id      -> built, validated, published, retired, or historical release
```

That means the Platform implementation must preserve the operator's existing
pipeline experience while changing where data comes from and which identifiers
travel with each operation. The correct move is:

```text
same Legacy GUI JS + Platform datasource + Platform identity context
```

The incorrect move is:

```text
new Platform screens + reused cards/tables/buttons + Legacy labels
```

The second version may look related, but it is a different product surface. It
forces the operator to relearn screens, loses behavior already present in
Legacy, and creates two places where pipeline logic can drift.

## What Went Wrong In Claude's Implementation

Claude appears to have interpreted "reuse the Legacy GUI" as "reuse Legacy-like
visual elements inside Platform." That led to a cosmetic reuse strategy:

- keep Platform-owned components;
- rename tabs to match Legacy concepts;
- reuse the same panel/card/table design language;
- replace missing operations with explanatory Platform-specific screens.

That is why Platform now has labels such as `Operacion`, `Revision`,
`Inventario`, `Chunking`, and `Embedding/Indexing`, but those labels do not open
the real Legacy modules. They open separate Platform modules with similar
language. The result is a semantic mismatch:

```text
The nav says:      "Legacy pipeline step"
The mounted code:  "new Platform replacement screen"
The user expected: "same Legacy JS, scoped by project_id"
```

The most visible example is `Revision`. In Legacy, `Revision` is where an
operator inspects document state and takes decisions such as `Aprobar` or
`Rechazar`. In Claude's Platform route, `Revision` was effectively redirected
to corpus snapshot management. Snapshot creation is a real Platform capability,
but it is not the same thing as the Legacy review screen. It belongs under
`RAG / Releases`, because snapshots are the bridge from reviewed corpus content
to a release draft.

The second example is `Chunking` and `Embedding/Indexing`. Instead of rendering
the Legacy run/activation/readiness screens with project-scoped data, Claude
mounted an informational release-build stage panel. That explains a lifecycle
concept, but it does not give the operator the same operational controls or the
same screen they asked for.

## Architectural Decision

The plan chooses datasource extraction rather than visual copying.

`DashboardApp` already owns the Legacy pipeline composition. The correct
refactor is to extract that composition into `DashboardPipelineApp` and make the
data boundary injectable:

```text
DashboardPipelineApp
  consumes DashboardPipelineDataSource
  renders the existing Legacy screens

Legacy pipeline route
  passes legacyDashboardDataSource
  uses existing global /api/* endpoints

RAG Platform route
  passes platformDashboardDataSource
  uses selected project_id and /api/platform/* endpoints
```

This creates one GUI implementation and two data contexts. Legacy stays global.
Platform becomes project-scoped. The shared GUI does not import Platform types,
because Platform-specific identifiers belong in the adapter layer, not in the
reusable pipeline components.

This is the lowest-risk architecture because it protects the screens operators
already use and keeps new Platform logic contained. If the team later improves
the Legacy review table, inventory inspector, chunking panel, or embedding
activation UI, Platform inherits that behavior automatically instead of needing
a second copy to be manually kept in sync.

## Identity And Lifecycle Rules

These rules prevent the implementation from mixing concerns:

- `project_id` is mandatory before Platform opens any pipeline screen. Without a
  selected project, the screen must ask the operator to select a project.
- `rag_variant_id` is derived from the effective pipeline recipe configured in
  the Legacy screens (see "RAG Variant Resolution Contract"); the persisted
  `selectedRagVariantId` preference is only a display cache of the last
  resolution, never the source of truth.
- `corpus_snapshot_id` is created only after document revisions have an
  inclusion decision that makes them eligible for release.
- `rag_release_id` starts after a release draft exists. It should not be forced
  into early pipeline steps that operate on project documents or snapshots.
- `actor_id` is server-side. The frontend may trigger an action, but it must not
  send an actor identifier.
- Physical targets, table names, vector index names, absolute paths, raw chunks,
  and secrets remain server-owned and hidden from the client.

The practical routing model is:

```text
Platform Projects       -> choose/configure project and variant
Operacion               -> Legacy operations GUI with project_id datasource
Revision                -> Legacy review GUI with project_id datasource
Inventario              -> Legacy inventory GUI with project_id datasource
Chunking                -> Legacy chunking GUI with project_id/variant datasource where supported
Embedding/Indexing      -> Legacy embedding/indexing GUI with project_id/variant datasource where supported
RAG / Releases          -> snapshots, release draft, build, validate, publish, retire, history
```

## RAG Variant Resolution Contract (Recipe Built By The Legacy Screens)

In Legacy the operator configures the pipeline piece by piece: provider and
route in `Operacion`, the chunking profile in `Chunking`, the embedding profile
in `Embedding/Indexing`. The Platform `rag_variant_id` must be the audit trail
of that exact configuration reconfirmed against the project variant-matrix. It
is never a loose selector, a free identifier, or a bare preference.

```ts
// app/front/src/features/platform/legacyPipeline/platformRagVariantResolver.ts
export type PlatformPipelineRecipe = {
  processingProfileId: string | null; // from Operacion providerMode/route
  chunkingProfileId: string | null;   // from Chunking screen selection/catalog
  embeddingProfileId: string | null;  // from Embedding/Indexing selection/catalog
};

export type ResolvedPlatformRagVariant = {
  ragVariantId: string;
  cellId: string;
  targetBindingKey: string;
  created: boolean;
};

export function resolveOrCreatePlatformRagVariant(input: {
  projectId: string;
  recipe: PlatformPipelineRecipe;
}): Promise<ResolvedPlatformRagVariant>;
```

Resolution rules (fail-closed, verified against the real backend contracts):

1. Fresh reads every resolution: `getConfiguration(projectId)` +
   `listProcessingProfiles(projectId)` + `listChunkingProfiles(projectId)` +
   `getVariantMatrix(projectId)`. Never reuse a matrix fetched for a previous
   operation.
2. Processing leg: map the Legacy `LlamaControls` (`providerMode`/`route`) to a
   `ProcessingProfileRead` by unique metadata match on `provider` (+`engine`;
   the schema exposes both). Zero or multiple matches fail closed naming the
   candidates. Never guess by string similarity.
3. Chunking/embedding legs: the operator's selection inside the Legacy screen
   wins (captured by the Platform-injected clients from Task 6 — no UI
   changes). With no explicit selection yet, auto-resolve ONLY when the project
   catalog has exactly one chunking profile / exactly one enabled embedding
   profile (`EmbeddingProfileSchema.enabled`). Otherwise fail closed telling
   the operator which screen to configure.
4. Binding leg: `configuration.target_bindings` must resolve to exactly one
   logical `binding_key`. Several bindings fail closed listing the options;
   never choose arbitrarily.
5. Matrix match: find the `VariantMatrixCell` whose
   `(processing_profile_id, chunking_profile_id, embedding_profile_id)` equals
   the recipe. If `buildable === false`, fail closed showing `blocked_reason`.
   If no cell matches after one refresh, fail closed (configuration drift).
6. Reuse-or-create: look among `listAllVariants(projectId)` for a variant with
   the same profile-id triple (`VariantSchema` exposes the three ids but NOT
   `target_binding_key`/`configuration_version`, so matching is by triple). If
   none, `createVariant({cell_id, variant_slug})` with a deterministic slug
   derived from the cell. On `409 DUPLICATE_VARIANT_RECIPE` re-list and reuse;
   on `409 STALE_VARIANT_MATRIX_CELL` restart from rule 1.
7. Display cache without breaking purity: the resolver is a plain module with
   NO React/context imports, so it cannot write `preferences`. It records the
   outcome in `platformRecipeDraft.lastResolution(projectId)` for display;
   every operation re-resolves regardless of any cache. Consumers —
   `normalizeDocuments` and `createReleaseDraft`
   (`CreateReleaseDraftRequestSchema` requires `rag_variant_id` +
   `corpus_snapshot_id` + `target_binding_key`) — accept only resolver output
   or a variant listed from `/variants`; a hand-typed or preference-only id is
   a contract violation.

Implementation hygiene (modularity/auditability):

- `resolveOrCreatePlatformRagVariant(input, deps = defaultPlatformApiDeps)`:
  API calls go through an injected deps object defaulting to `platformApi`, so
  unit tests stub behavior without network or module mocks.
- `platformRecipeDraft` exposes `__resetForTests()`; module state is keyed by
  `project_id` and stores only ids/metadata — never physical targets.
- Every fail-closed path returns/throws ONE actionable message naming the
  screen and the offending options (candidates list, `blocked_reason`,
  `binding_key`s), so the Legacy notice area shows an auditable reason.

## Why A Narrow Backend Addition Is Still In Scope

Fase 7 already implemented the release-oriented Platform backend. The cited
release-build E2E test is green and must be protected. The frontend should not
invent a different backend just to make the GUI work.

However, real Legacy `Revision` parity requires a standalone decision action.
The current corpus snapshot endpoint accepts inclusion decisions for revisions
that are going into a snapshot, but a rejected revision should not be inserted
into a releaseable snapshot just so the UI can remember it was rejected. That is
why this plan adds one narrow endpoint:

```text
POST /api/platform/projects/{project_id}/document-revisions/{source_document_revision_id}/review-decision
```

This endpoint stores the operator decision independently from release snapshot
creation. It preserves the product rule that Platform is operational while also
preserving the release rule that blocked revisions are not part of a releaseable
snapshot.

## Non-Goals

- Do not redesign the Legacy pipeline UI.
- Do not create a new Platform pipeline with Legacy-looking components.
- Do not call global Legacy endpoints from Platform and pretend the data is
  project-scoped.
- Do not expose server-owned physical targets or internal storage/index names to
  make a frontend screen easier to populate.
- Do not move release lifecycle into `Revision`. Snapshot creation and releases
  belong in `RAG / Releases`.
- Do not broaden backend scope beyond the review-decision gap needed for
  `Aprobar`/`Rechazar` parity.

## Current Fault To Correct

Claude changed Platform navigation labels to `Operacion`, `Revision`, `Inventario`, `Chunking`, and `Embedding/Indexing`, but mounted Platform-specific screens:

- `operations` renders `DocumentIntakeWorkspace`.
- `review` renders `CorpusSnapshotWorkspace`.
- `inventory` renders `ProjectInventoryWorkspace`.
- `chunking` renders `PlatformReleaseBuildStageInfo`.
- `embedding-indexing` renders `PlatformReleaseBuildStageInfo`.

That is not the requested result. The requested result is:

```text
RAG Platform
  Projects / project selection
  Operacion              -> same Legacy operations screen, project-scoped
  Revision               -> same Legacy review screen, project-scoped
  Inventario             -> same Legacy inventory screen, project-scoped
  Chunking               -> same Legacy chunking screen, project-scoped
  Embedding/Indexing     -> same Legacy embedding/indexing screen, project-scoped
  RAG / Releases         -> snapshot creation plus release/version management over /api/platform/*
```

The second fault is semantic: the older plan and several Platform components
describe the Platform inspector/inventory as `read-only` because a standalone
decision endpoint was missing. That conclusion is wrong for the product. The
correct rule is:

```text
RAG Platform is operational.
Only server-owned physical target bindings and immutable release artifacts are read-only.
Review, inventory, intake, snapshot, release, validation, publish, and retire flows are operational surfaces.
```

If `Rechazar` cannot be persisted with the current Fase 7 endpoints, the answer
is Task 3's narrow backend contract, not a passive UI.

## Endpoint Contract From Fase 7 And Current Router

Fase 7 completed the admin Platform API with these protected contracts:

```text
GET    /api/platform/projects
POST   /api/platform/projects
GET    /api/platform/projects/{project_id}
PATCH  /api/platform/projects/{project_id}
GET    /api/platform/projects/{project_id}/configuration
PATCH  /api/platform/projects/{project_id}/configuration
GET    /api/platform/projects/{project_id}/variant-matrix
GET    /api/platform/projects/{project_id}/variants
POST   /api/platform/projects/{project_id}/variants
POST   /api/platform/corpus-snapshots
POST   /api/platform/releases
GET    /api/platform/releases/{rag_release_id}
POST   /api/platform/releases/{rag_release_id}/build
POST   /api/platform/releases/{rag_release_id}/validate
POST   /api/platform/releases/{rag_release_id}/publish
POST   /api/platform/releases/{rag_release_id}/retire
```

The current router also exposes project document and profile endpoints already consumed by the frontend:

```text
GET    /api/platform/projects/{project_id}/documents
POST   /api/platform/projects/{project_id}/documents
POST   /api/platform/projects/{project_id}/normalize
GET    /api/platform/projects/{project_id}/processing-profiles
GET    /api/platform/projects/{project_id}/chunking-profiles
GET    /api/platform/projects/{project_id}/corpus-snapshots
GET    /api/platform/projects/{project_id}/releases
GET    /api/platform/releases/{rag_release_id}/build-status
```

The plan below uses those endpoints. It also acknowledges a proven gap: `POST
/api/platform/corpus-snapshots` accepts `eligibility_decisions` for inclusion
decisions, but `CreateCorpusSnapshotUseCase` rejects `EligibilityDecision.BLOCKED`
so a rejected revision cannot be stored as part of a snapshot. Task 3 adds the
missing operational review-decision endpoint required for full `Rechazar` parity.

## Behavior Contract By Platform View

| Platform view | Must render | Primary identity | Platform datasource responsibility | Must not render |
| --- | --- | --- | --- | --- |
| `Projects` | Existing Platform project management/configuration UI | none until selected | list, create, select, configure projects and variants | Legacy global pipeline |
| `Operacion` | Existing Legacy operation/intake GUI from `DashboardApp` | `project_id` | load project document status, upload/register documents, normalize selected project revisions through `resolveOrCreatePlatformRagVariant` (this screen's provider/route controls feed the recipe) | `DocumentIntakeWorkspace` as a separate replacement |
| `Revision` | Existing Legacy review GUI from `DocumentWorkspaces` | `project_id` | map Platform document revisions into Legacy review rows and persist `Aprobar`/`Rechazar` through Platform review decisions | `CorpusSnapshotWorkspace` |
| `Inventario` | Existing Legacy inventory GUI from `DocumentWorkspaces` | `project_id` | map Platform project document read-models into Legacy inventory rows without inventing unavailable metadata | `ProjectInventoryWorkspace` |
| `Chunking` | Existing Legacy chunking GUI from `ChunkingWorkspace` | `project_id`; the profile selected in this screen feeds the variant resolver | use project-scoped profile/stage contracts where exposed; otherwise render the Legacy screen with an explicit unavailable contract state | `PlatformReleaseBuildStageInfo` |
| `Embedding/Indexing` | Existing Legacy embedding/indexing GUI from `EmbeddingIndexingWorkspace` | `project_id`; the embedding profile selected here feeds the variant resolver | use project-scoped embedding/indexing contracts where exposed; otherwise render the Legacy screen with an explicit unavailable contract state | `PlatformReleaseBuildStageInfo` |
| `RAG / Releases` | Platform release workspace plus snapshot builder | `project_id`, `corpus_snapshot_id`, `rag_release_id` | create snapshots, create release drafts, build, validate, publish, retire, show release history | Legacy review/inventory screens |

This table is an acceptance contract, not just documentation. Tests in Task 1
and Task 5 must fail if a Platform tab is wired to a replacement screen instead
of the existing Legacy GUI module.

## Implementation Strategy And Why The Order Matters

The plan starts by writing tests against the requested product contract before
touching components. This matters because the current implementation already
has UI that looks plausible; without boundary tests, another agent can keep the
wrong screens and merely polish them.

Then it extracts `DashboardPipelineApp` from `DashboardApp`. This is the key
technical move: it makes Legacy GUI reuse possible without making Legacy depend
on Platform. The extraction must preserve the global Legacy route first, because
breaking the working single-corpus lane would make the Platform refactor unsafe.

After that, the plan fills the only known backend gap for true review parity:
the standalone Platform review-decision endpoint. This keeps `Revision`
operational and prevents the UI from becoming read-only just because one action
was missing from the API surface.

Only then does Platform mount the shared Legacy GUI. At that point the Platform
host can pass a real project-scoped datasource instead of importing replacement
screens. Snapshot creation is moved into `RAG / Releases` during this step
because snapshots are part of release/version lifecycle, not the Legacy review
screen.

The final tasks clean up Claude's unreachable replacement screens and run the
operator's backend release-build regression plus frontend test/build checks. The
cleanup is deliberately last so the implementation has a rollback path while the
new shared GUI route is being proven.

---

## Code Audit Corrections Added 2026-08-25

This section resolves mismatches found while contrasting the plan with the
current codebase:

- `PlatformWorkspace.test.tsx` currently protects the wrong behavior: it asserts
  `Intake documental`, `Snapshots de corpus`, `Inventario del proyecto`, and the
  release-build info text. Task 1 must replace those assertions after selecting
  a project, because the shared Platform context requires a selected project
  before pipeline screens can load.
- `DashboardApp` currently defaults to `review`, not `operations`. Extraction
  tests must click or force `operations` before asserting the operation heading.
- `platformNavigation.ts` must derive the five pipeline entries from
  `DASHBOARD_VIEWS`; do not hand-maintain a Platform copy of `Operacion`,
  `Revision`, `Inventario`, `Chunking`, or `Embedding/Indexing`.
- `DashboardPipelineApp` needs both `forcedActiveView` and
  `hideInternalNavigation`. When Platform controls the active view from its own
  sidebar, the inner Legacy sidebar and topbar switcher must be hidden to avoid
  two competing navigation systems.
- `source_document_revisions` has a simple primary key and does not yet expose a
  `(project_id, source_document_revision_id)` uniqueness target. The review
  decision migration must add that unique index before adding a composite FK, so
  the database rejects cross-project decisions even if an application bug slips
  through.
- RAG Platform domain errors are centralized in
  `app/back/src/rag_platform/domain/errors.py` and mapped by `app/back/src/api/app.py`.
  The review-decision use case should raise a domain error such as
  `InvalidReviewDecision`; the router should not translate raw `ValueError`
  branches into ad hoc HTTP errors.
- OpenAPI generation is two-step in this repo: first export
  `docs/api/pipeline-openapi.json`, then regenerate
  `platformOpenApi.generated.ts`. `api:check` is a final drift guard, not a
  green expectation while generated files have expected uncommitted diffs.
- `useEmbeddingIndexingPipeline.ts` delegates polling to
  `useEmbeddingRunPolling` and `useIndexingRunPolling`, and those hooks import
  global API functions directly. Task 6 must inject the run loaders into polling
  too; otherwise Platform would still call global stage endpoints while appearing
  project-scoped.
- `runPipeline` in the Platform datasource must choose revision IDs from the raw
  Platform document read-model, not from the already-mapped Legacy
  `StatusPayload`, so blocked/needs-review decisions cannot be normalized by a
  display-state mapping accident.
- Verified backend facts that constrain the design (2026-08-25 audit):
  `ProcessingProfileReadSchema` exposes `provider`/`engine`/`fingerprint`/
  `status` (enables resolution rule 2); `ChunkingProfileReadSchema` exposes ONLY
  `strategy`/`fingerprint`/`status` — no token parameters (see Task 6 honesty
  rules); `CreateReleaseDraftRequestSchema` requires `rag_variant_id`,
  `corpus_snapshot_id`, and `target_binding_key`; `VariantSchema` exposes the
  three profile ids but NOT `target_binding_key`/`configuration_version`, so
  variant reuse matching is done by the profile-id triple; duplicates raise
  `DuplicateVariantRecipe` (409), stale cells raise `StaleVariantMatrixCell`
  (409), and `createVariant` accepts only `{cell_id, variant_slug}`.
- `EmbeddingIndexingWorkspace` receives `activeStage`/state/callback props owned
  by `DashboardApp` component state. The Task 2 extraction keeps that state
  inside `DashboardPipelineApp`, so Platform mounts the shell without ever
  touching those props; Task 6 only adds optional datasource inputs behind
  legacy defaults.
- `PlatformWorkspace.tsx` switch currently mounts `DocumentIntakeWorkspace`,
  `CorpusSnapshotWorkspace`, `ProjectInventoryWorkspace`, and twice
  `PlatformReleaseBuildStageInfo`; `platformNavigation.ts` hardcodes accented
  labels (`Operación`, `Revisión`, `Inventario`) plus an inventory title with
  `(solo lectura)`. Deriving entries from `DASHBOARD_VIEWS` removes both drifts
  at once and is what makes the Task 1 boundary test pass.
- `RagPlatformServices` is a frozen dataclass built by
  `_build_rag_platform_services` and constructed directly by several tests;
  adding the required `submit_revision_review_decision` field requires updating
  EVERY construction site before pytest can run.
- Second-pass verified UI facts (2026-08-25): the Legacy upload panel renders a
  `Categoria` select (`DashboardChrome.tsx`) that Platform's
  `POST /documents` contract cannot carry — disabled-with-reason under
  Platform; `StatusPayload.settings` is a REQUIRED object
  (`ocrReviewThreshold`, `ocrReviewThresholdPercent`, `llamaControls?`) so the
  mapper must fill it with neutral values while the OCR input stays
  disabled-with-reason; the inventory header is literally `Ruta del documento`
  and `PlatformWorkspace` exposes `aria-label="Proyecto activo"` (Task 1
  assertions are grounded); `useCorpusSnapshotWorkspace` takes `projectId`
  from `PlatformProjectContext`; the domain→schema mapper for document rows is
  `document_row_to_schema`.
- Third-pass verified facts (2026-08-25): the four root `.test.mjs` suites
  (`documentReview`, `ocrSettings`, `pipelineRequest`, `llamaRoutes`) import
  ONLY pure helpers from `.tmp-tests` — extraction cannot break them; the
  existing `dashboardLegacyBoundary.test.mjs` asserts `DASHBOARD_VIEWS`
  order/titles from compiled output — also extraction-safe and it validates
  this plan's single-source navigation rule; the deleted
  `features/platform/variants/` directory has ZERO remaining importers (grep
  verified) — the deletion is clean and the resolver revives its API surface,
  not its UI; `ProjectInventoryWorkspace`/`PlatformReleaseBuildStageInfo` are
  referenced only by `PlatformWorkspace.tsx` plus themselves (safe Task 7
  deletions); backend revert of the aborted review agent left ZERO leftovers
  (`InvalidReviewDecision`/`revision_review` grep = empty); `OperatorApp`
  defaults to surface `"platform"` and mounts `<DashboardApp/>` vs
  `<PlatformWorkspace/>` as siblings — exactly the architecture this plan
  assumes.

---

## Coordination With docs/revision Plans 01–05 And The Audit Backlog

An independent audit (`docs/revision/2026-08-25_auditoria-app-hallazgos.md`)
produced five pending correction plans plus a backlog. Several touch the SAME
files as this plan. Rules to avoid silent overwrites ("vibecoding" damage):

1. One plan at a time, delivered as an ISOLATED working-tree change-set that
   the operator applies/commits separately (AGENTS §10 isolation — the commit
   itself is the operator's action, never the agent's); never widen one plan's
   scope into another's. This plan must NOT fix the defects owned by plans
   01–05 — the shared Platform GUI renders whatever the global Legacy lane
   renders, including its known bugs, until their own plans close them.

Shared-file matrix (verified):

| File | Revision plan | This plan | Rule |
| --- | --- | --- | --- |
| `features/embeddingIndexing/useEmbeddingIndexingPipeline.ts` | Plan 02 (adds error states/catches at :252,:471,:472,:730,:731) | Task 6 (thread injectable clients) | Execute Plan 02 FIRST, then rebase Task 6 on top; Task 6 preserves every error state Plan 02 added — injection changes WHO loads data, never HOW failures are surfaced |
| `api/dependencies.py`, `in_memory/repositories.py`, `postgres/release_repositories.py` | Plan 04 (reconcile + TTL) | Task 3 (review-decision repo wiring) | Additive edits in different regions, delivered as separate operator-applied change-sets; either order works, and the operator re-runs `pytest app/back/tests/rag_platform -q` between them (agents deliver the command, never run it) |
| `chunking/application/run_service.py` validation JSON | Plan 01 (honest failed-status reports) | Task 5/6 render Legacy Chunking screen | No code contact: Platform shows the SAME fabricated-validation behavior as global Legacy until Plan 01 closes; do not patch it here |
| `ingestion/gui/server.py`, `ingestion/pipeline.py` | Plans 05/03 | none | No overlap |

Backlog amendments caused by THIS plan (record so nobody executes stale orders):

- Backlog 🗑️.7 ("delete orphaned `getVariantMatrix` + `VariantMatrixCell`") is
  SUPERSEDED: the variant resolver makes them live core contracts again.
  Cancelled while this plan stands; re-evaluate only after parity ships.
- Backlog 🗑️.10 (`setSelectedRagVariant` dead writer): still true today, but
  the setter stays reserved as the display-cache mirror of
  `lastResolution`; do not delete while the resolver exists.
- Backlog 🗑️.11 (`NormalizationPanel` copy pointing at the deleted matrix):
  resolved differently by this plan — `DocumentIntakeWorkspace` becomes
  unreachable rollback code and draft-time resolution replaces manual variant
  creation UX (Task 5 Step 5 updates the surviving `ReleaseDraftForm` copy).
- Backlog 🗑️.9 (`tsconfig.test.json:49` referencing deleted
  `useVariantMatrixWorkspace.ts`): harmless dead glob today, cleaned in Task 7.
- Protected uncommitted work (never revert/piso): runner internal_error_id
  tests, `artifact_store.py` (+37), `project_repositories.py` (+34),
  `release_repositories.py` (+5), `in_memory/repositories.py` (±2), and the
  whole Phases 0–4 front working tree.

## File Structure

Create:

- `app/front/src/features/dashboard/DashboardPipelineApp.tsx` - extracted Legacy pipeline shell and view composition, parameterized by datasource and scope label.
- `app/front/src/features/dashboard/dashboardDataSource.ts` - typed datasource interface consumed by `DashboardPipelineApp`.
- `app/front/src/features/dashboard/legacyDashboardDataSource.ts` - adapter from existing `dashboardApi.ts` functions to `DashboardPipelineDataSource`.
- `app/front/src/features/platform/legacyPipeline/PlatformLegacyPipelineWorkspace.tsx` - Platform host that reads `PlatformProjectContext` and mounts `DashboardPipelineApp`.
- `app/front/src/features/platform/legacyPipeline/platformDashboardDataSource.ts` - datasource over `platformApi` for project-scoped Legacy pipeline UI.
- `app/front/src/features/platform/legacyPipeline/platformDashboardMappers.ts` - pure mappers from Platform read-models to Legacy `StatusPayload` and `DocumentRecord`.
- `app/front/src/features/platform/legacyPipeline/platformDashboardMappers.test.ts` - mapper regression tests; no JSX is needed.
- `app/front/src/features/platform/legacyPipeline/platformRagVariantResolver.ts` - implements `resolveOrCreatePlatformRagVariant`: recipe from the Legacy screens reconfirmed against variant-matrix, reuse-or-create with fail-closed errors.
- `app/front/src/features/platform/legacyPipeline/platformRagVariantResolver.test.ts` - resolver contract tests: unique metadata match, reuse, create, duplicate-reuse, blocked/stale/ambiguous fail-closed.
- `app/front/src/features/platform/legacyPipeline/platformRecipeDraft.ts` - records the operator's chunking/embedding selections made inside the Legacy screens (via the Task 6 injected clients), keyed by project; no UI changes.
- `app/front/src/features/platform/platformLegacyPipelineBoundary.test.mjs` - static boundary test proving Platform no longer mounts the wrong workspaces for pipeline views.
- `app/front/src/features/platform/corpus/CorpusSnapshotBuilderPanel.tsx` - reusable snapshot builder panel hosted by `RAG / Releases`, not by Platform `Revision`.
- `app/back/src/rag_platform/application/revision_review_service.py` - narrow use case for project-scoped operator review decisions over existing `EligibilityDecision`.
- `app/back/tests/rag_platform/test_revision_review_decisions.py` - backend contract tests for approve/reject decisions without release leakage.
- `migrations/20260825_01_create_source_revision_review_decisions.sql` - durable audit table for latest review decisions by revision.

Modify:

- `app/front/src/features/dashboard/DashboardApp.tsx` - become a thin wrapper around `DashboardPipelineApp` using `legacyDashboardDataSource`.
- `app/front/src/features/dashboard/DashboardApp.test.tsx` - keep Legacy behavior green after extraction.
- `app/front/src/features/dashboard/components/DashboardChrome.tsx` - only if a control needs a disabled reason or label prop to keep the same screen honest under Platform.
- `app/front/src/features/dashboard/components/DocumentWorkspaces.tsx` - only if review actions need a typed capability flag; preserve default Legacy behavior.
- `app/front/src/features/chunking/ChunkingWorkspace.tsx` - accept optional project scope and datasource inputs while defaulting to existing Legacy behavior.
- `app/front/src/features/chunking/useChunkingWorkspace.ts` - accept optional datasource; default to existing `chunkingApi`.
- `app/front/src/features/embeddingIndexing/EmbeddingIndexingWorkspace.tsx` - accept optional datasource/context inputs while defaulting to existing Legacy behavior.
- `app/front/src/features/embeddingIndexing/useEmbeddingIndexingPipeline.ts` - accept optional datasource group; default to existing embedding/indexing/retrieval APIs.
- `app/front/src/features/embedding/hooks/useEmbeddingRunPolling.ts` - accept an injected run loader so Platform polling does not call global endpoints.
- `app/front/src/features/indexing/hooks/useIndexingRunPolling.ts` - accept an injected run loader so Platform polling does not call global endpoints.
- `app/front/src/features/platform/PlatformWorkspace.tsx` - remove re-labeled Platform workspaces and mount `PlatformLegacyPipelineWorkspace`.
- `app/front/src/features/platform/platformNavigation.ts` - derive pipeline entries from `DASHBOARD_VIEWS`/`viewTitles`; only Platform-specific entries such as `Projects` and `RAG / Releases` stay local.
- `app/front/src/features/platform/PlatformWorkspace.test.tsx` - replace tests that protect the wrong behavior.
- `app/front/src/features/platform/corpus/CorpusSnapshotWorkspace.tsx` - become a wrapper around `CorpusSnapshotBuilderPanel` or stay as rollback-only code after the panel extraction.
- `app/front/src/features/platform/releases/RagReleaseWorkspace.tsx` - host `CorpusSnapshotBuilderPanel` before release draft/history/lifecycle.
- `app/front/src/features/platform/releases/useRagReleaseWorkspace.ts` - draft creation obtains `rag_variant_id` only from `resolveOrCreatePlatformRagVariant` or from the project's listed variants; any free-text/manual variant input is removed.
- `app/front/src/features/platform/releases/RagReleaseWorkspace.test.tsx` - prove a project can create/select a snapshot from `RAG / Releases`.
- `app/back/src/rag_platform/domain/errors.py` - add `InvalidReviewDecision` as a stable domain error.
- `app/back/src/rag_platform/application/context.py` - add the review decision repository protocol/record if keeping application ports centralized there.
- `app/back/src/rag_platform/application/document_query_service.py` - include the latest operational eligibility decision in the project document read-model.
- `app/back/src/rag_platform/application/services.py` - add the review-decision use case to `RagPlatformServices`.
- `app/back/src/rag_platform/api/schemas.py` - add request/response schemas and expose latest eligibility decision in document rows.
- `app/back/src/rag_platform/api/router.py` - add the project-scoped review decision endpoint.
- `app/back/src/api/dependencies.py` - wire the in-memory/Postgres review decision repositories into the existing platform service container.
- `app/back/src/rag_platform/infrastructure/in_memory/repositories.py` - add an in-memory review decision repository for unit/API tests.
- `app/back/src/rag_platform/infrastructure/postgres/document_repositories.py` - add the Postgres review decision repository.
- `docs/api/pipeline-openapi.json` - regenerated OpenAPI after adding backend schemas/routes.
- `app/front/src/features/platform/platformOpenApi.generated.ts` - regenerated TypeScript types from OpenAPI.
- `app/front/src/features/platform/platformApi.ts` - add the generated wrapper for the review decision endpoint.
- `app/front/src/features/platform/platformTypes.ts` - export generated review decision request/response types.

Remove after replacement:

- `app/front/src/features/platform/PlatformReleaseBuildStageInfo.tsx`
- `app/front/src/features/platform/documents/ProjectInventoryWorkspace.tsx`

Keep available for rollback until the new tests pass:

- `app/front/src/features/platform/documents/DocumentIntakeWorkspace.tsx`
- `app/front/src/features/platform/corpus/CorpusSnapshotWorkspace.tsx`
- `app/front/src/features/platform/releases/RagReleaseWorkspace.tsx`

The final Platform nav must not route `operations`, `review`, `inventory`, `chunking`, or `embedding-indexing` to `DocumentIntakeWorkspace`, `CorpusSnapshotWorkspace`, `ProjectInventoryWorkspace`, or `PlatformReleaseBuildStageInfo`.

---

### Task 1: Lock The Requested UI Contract Before Editing

**Files:**
- Modify: `app/front/src/features/platform/PlatformWorkspace.test.tsx`
- Create: `app/front/src/features/platform/platformLegacyPipelineBoundary.test.mjs`

**Interfaces:**
- Consumes: existing `PlatformWorkspace`.
- Produces: failing tests that describe the desired Platform behavior.

- [ ] **Step 1: Replace the current component assertions**

In `PlatformWorkspace.test.tsx`, keep the existing `makeProject`,
`paginateProjects`, and API mock style. Add sentinels for the heavy Legacy stage
components so this remains a routing/parity test, matching the pattern already
used in `DashboardApp.test.tsx`:

```tsx
vi.mock("../chunking/ChunkingWorkspace.js", () => ({
  ChunkingWorkspace: () => <h2>Chunking sentinel</h2>,
}));

vi.mock("../embeddingIndexing/EmbeddingIndexingWorkspace.js", () => ({
  EmbeddingIndexingWorkspace: () => <h2>Embedding Indexing sentinel</h2>,
}));
```

Then change the first test so it selects a project and expects Legacy screen
content under Platform:

```tsx
it("renderiza las pantallas reales del pipeline legacy dentro de Platform", async () => {
  const user = userEvent.setup();
  const alpha = makeProject();
  api.listProjects.mockResolvedValue(paginateProjects([alpha]));
  api.listAllDocuments.mockResolvedValue([
    {
      file_size: 2048,
      logical_document_id: "sdoc_manual",
      normalized_registered: false,
      processing_status: "needs_review",
      raw_registered: true,
      review_state: "needs_review",
      source_document_revision_id: "srev_needs_review",
      source_relpath: "manuales/manual.pdf",
      uploaded_at: "2026-08-25T12:00:00Z",
    },
  ]);

  render(<PlatformWorkspace />);

  expect(await screen.findByRole("heading", { name: "RAG Platform" })).toBeTruthy();
  await user.click(await screen.findByText("Proyecto Alpha"));
  expect(screen.getByLabelText("Proyecto activo").textContent).toContain("Proyecto Alpha");

  await user.click(screen.getByRole("button", { name: "Operacion" }));
  expect(await screen.findByRole("heading", { name: "Legacy pipeline - Operacion de ingesta" })).toBeTruthy();
  expect(screen.getByRole("button", { name: /Ejecutar ingesta local/i })).toBeTruthy();
  expect(screen.queryByRole("heading", { name: "Intake documental" })).toBeNull();

  await user.click(screen.getByRole("button", { name: "Revision" }));
  expect(await screen.findByRole("heading", { name: "Legacy pipeline - Revision documental" })).toBeTruthy();
  expect(screen.getAllByRole("button", { name: "Aprobar" }).length).toBeGreaterThan(0);
  expect(screen.getAllByRole("button", { name: "Rechazar" }).length).toBeGreaterThan(0);
  expect(screen.queryByRole("heading", { name: "Snapshots de corpus" })).toBeNull();

  await user.click(screen.getByRole("button", { name: "Inventario" }));
  expect(await screen.findByRole("heading", { name: "Legacy pipeline - Inventario documental" })).toBeTruthy();
  expect(screen.getByRole("columnheader", { name: "Ruta del documento" })).toBeTruthy();
  expect(screen.queryByRole("heading", { name: "Inventario del proyecto" })).toBeNull();
  expect(screen.queryByText(/solo lectura|read-only/i)).toBeNull();

  await user.click(screen.getByRole("button", { name: "Chunking" }));
  expect(await screen.findByRole("heading", { name: "Chunking sentinel" })).toBeTruthy();
  expect(screen.queryByText(/dentro del build de una release/i)).toBeNull();

  await user.click(screen.getByRole("button", { name: "Embedding/Indexing" }));
  expect(await screen.findByRole("heading", { name: "Embedding Indexing sentinel" })).toBeTruthy();
  expect(screen.queryByRole("heading", { name: "Embedding / Indexing" })).toBeNull();
});
```

- [ ] **Step 2: Add a static boundary test**

Create `platformLegacyPipelineBoundary.test.mjs`:

```js
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const source = readFileSync(
  "src/features/platform/PlatformWorkspace.tsx",
  "utf8",
);
const navigation = readFileSync(
  "src/features/platform/platformNavigation.ts",
  "utf8",
);

test("Platform pipeline views mount the project-scoped legacy pipeline host", () => {
  assert.match(source, /PlatformLegacyPipelineWorkspace/);
  assert.doesNotMatch(source, /DocumentIntakeWorkspace/);
  assert.doesNotMatch(source, /CorpusSnapshotWorkspace/);
  assert.doesNotMatch(source, /ProjectInventoryWorkspace/);
  assert.doesNotMatch(source, /PlatformReleaseBuildStageInfo/);
  assert.doesNotMatch(navigation, /read-only|solo lectura/i);
});

test("Pipeline nav entries derive from the Legacy dashboard contracts, not hand copies", () => {
  assert.match(
    navigation,
    /dashboardNavigation/,
    "platformNavigation.ts must import DASHBOARD_VIEWS instead of duplicating labels",
  );
  assert.doesNotMatch(
    navigation,
    /Operación|Revisión/,
    "pipeline labels must come verbatim from DASHBOARD_VIEWS sidebarLabels",
  );
});
```

- [ ] **Step 3: Register the static boundary test**

Modify `app/front/package.json` test script by adding:

```text
node src/features/platform/platformLegacyPipelineBoundary.test.mjs
```

Place it near the existing platform `.test.mjs` entries.

- [ ] **Step 4: Deliver the red-test commands to the operator (do NOT run them)**

Hand these over verbatim, then STOP and WAIT for the pasted output:

```bash
npm --prefix app/front exec vitest run src/features/platform/PlatformWorkspace.test.tsx
npm --prefix app/front run test
```

Expected result before implementation: the component test fails because Platform renders `Intake documental`, `Snapshots de corpus`, and info panels instead of Legacy screens. The static boundary test fails because `PlatformWorkspace.tsx` imports the wrong workspaces.

---

### Task 2: Extract DashboardApp Without Changing Legacy Behavior

**Files:**
- Create: `app/front/src/features/dashboard/dashboardDataSource.ts`
- Create: `app/front/src/features/dashboard/legacyDashboardDataSource.ts`
- Create: `app/front/src/features/dashboard/DashboardPipelineApp.tsx`
- Modify: `app/front/src/features/dashboard/DashboardApp.tsx`
- Test: `app/front/src/features/dashboard/DashboardApp.test.tsx`

**Interfaces:**
- Consumes: existing `dashboardApi.ts`, `dashboardTypes.ts`, `DashboardChrome.tsx`, `DocumentWorkspaces.tsx`, `ChunkingWorkspace`, `EmbeddingIndexingWorkspace`.
- Produces:

```ts
export type DashboardPipelineDataSource = {
  loadStatus: () => Promise<StatusPayload>;
  uploadDocument: (form: DashboardUploadForm) => Promise<ActionResult>;
  submitReview: (options: {
    documentId: string;
    decision: DecisionKind;
    reason: string;
  }) => Promise<ActionResult>;
  runPipeline: (options: {
    controls: LlamaControls;
    ocrReviewThresholdPercent: number;
  }) => Promise<ActionResult>;
  saveSettings: (options: {
    ocrReviewThresholdPercent: number;
    llamaControls: LlamaControls;
  }) => Promise<{
    ok?: boolean;
    settings?: StatusPayload["settings"];
    status?: StatusPayload;
  }>;
  validateBundle: (options: { stagingRoot?: string | null }) => Promise<ActionResult>;
  promoteStaging: (options: { stagingRoot: string }) => Promise<ActionResult>;
};
```

- [ ] **Step 1: Write the extraction regression**

In `DashboardApp.test.tsx`, assert that Legacy still renders the same operation/review/inventory/chunking/embedding screens and still calls the global Legacy endpoints through mocked `dashboardApi.ts`.

Use this assertion shape:

```tsx
expect(await screen.findByRole("heading", { name: "Legacy pipeline - Revision documental" })).toBeTruthy();
await user.click(screen.getByTitle("Legacy pipeline - Operacion de ingesta"));
expect(await screen.findByRole("heading", { name: "Legacy pipeline - Operacion de ingesta" })).toBeTruthy();
expect(screen.getByRole("button", { name: /Actualizar/i })).toBeTruthy();
expect(screen.getByText(/Operaciones SST/i)).toBeTruthy();
```

- [ ] **Step 2: Create the datasource interface**

Create `dashboardDataSource.ts` with the exact `DashboardPipelineDataSource` type from this task.

- [ ] **Step 3: Create the Legacy datasource**

Create `legacyDashboardDataSource.ts`:

```ts
import {
  loadDashboardStatus,
  promoteDashboardStaging,
  runDashboardPipeline,
  saveDashboardSettings,
  submitDashboardReview,
  uploadDashboardDocument,
  validateDashboardBundle,
} from "./dashboardApi.js";
import type { DashboardPipelineDataSource } from "./dashboardDataSource.js";

export const legacyDashboardDataSource: DashboardPipelineDataSource = {
  loadStatus: loadDashboardStatus,
  uploadDocument: uploadDashboardDocument,
  submitReview: submitDashboardReview,
  runPipeline: runDashboardPipeline,
  saveSettings: saveDashboardSettings,
  validateBundle: validateDashboardBundle,
  promoteStaging: promoteDashboardStaging,
};
```

- [ ] **Step 4: Move the current DashboardApp body**

Move the current `DashboardApp` implementation into `DashboardPipelineApp.tsx`
VERBATIM — cut/paste the JSX structure, class names, hooks, and handlers. This
is a relocation, not a rewrite or cleanup; the only permitted edits are listed
below and the datasource call swaps. Change only these inputs:

```ts
export function DashboardPipelineApp({
  dataSource,
  scopeSubtitle,
  forcedActiveView,
  hideInternalNavigation = false,
  userChipLabel = "Operaciones SST",
}: {
  dataSource: DashboardPipelineDataSource;
  scopeSubtitle?: string;
  forcedActiveView?: AppView;
  hideInternalNavigation?: boolean;
  userChipLabel?: string;
}) {
  // Existing DashboardApp state and render stay here.
}
```

Inside the extracted body, introduce one local source of truth for the visible
view:

```ts
const activeView = forcedActiveView ?? preferences.activeView;
```

Use `activeView` for `viewTitles`, `isChunkingView`, `isStandaloneWorkspaceView`,
and every render branch. `preferences.activeView` remains the persisted Legacy
preference only when `forcedActiveView` is absent.

Replace calls:

```ts
loadDashboardStatus()        -> dataSource.loadStatus()
uploadDashboardDocument(...) -> dataSource.uploadDocument(...)
submitDashboardReview(...)   -> dataSource.submitReview(...)
runDashboardPipeline(...)    -> dataSource.runPipeline(...)
saveDashboardSettings(...)   -> dataSource.saveSettings(...)
validateDashboardBundle(...) -> dataSource.validateBundle(...)
promoteDashboardStaging(...) -> dataSource.promoteStaging(...)
```

For the subtitle, keep the existing Legacy string and append the optional project scope:

```ts
const activeViewSubtitle = scopeSubtitle
  ? `${baseSubtitle} - ${scopeSubtitle}`
  : baseSubtitle;
```

Hide both Legacy navigation surfaces when Platform owns the active view:

```tsx
{hideInternalNavigation || forcedActiveView ? null : (
  <DashboardSidebar ... />
)}

{hideInternalNavigation || forcedActiveView ? null : (
  <div className="view-switcher" aria-label="Cambiar vista">
    ...
  </div>
)}
```

This keeps the exact Legacy GUI modules while avoiding duplicate nav inside the
Platform shell.

- [ ] **Step 5: Make DashboardApp a wrapper**

Replace `DashboardApp.tsx` with:

```tsx
import { DashboardPipelineApp } from "./DashboardPipelineApp.js";
import { legacyDashboardDataSource } from "./legacyDashboardDataSource.js";

export function DashboardApp() {
  return <DashboardPipelineApp dataSource={legacyDashboardDataSource} />;
}
```

- [ ] **Step 6: Deliver the extraction-test commands to the operator (do NOT run them)**

Hand these over verbatim, then STOP and WAIT for the pasted output:

```bash
npm --prefix app/front exec vitest run src/features/dashboard/DashboardApp.test.tsx
npm --prefix app/front run test
```

Expected result after this task: Legacy behavior stays green and `DashboardApp` is now reusable without Platform importing Legacy globals directly.

---

### Task 3: Add Operational Platform Review Decisions

**Files:**
- Create: `app/back/src/rag_platform/application/revision_review_service.py`
- Create: `app/back/tests/rag_platform/test_revision_review_decisions.py`
- Create: `migrations/20260825_01_create_source_revision_review_decisions.sql`
- Modify: `app/back/tests/rag_platform/test_platform_document_api.py`
- Modify: `app/back/src/rag_platform/domain/errors.py`
- Modify: `app/back/src/rag_platform/application/context.py`
- Modify: `app/back/src/rag_platform/application/document_query_service.py`
- Modify: `app/back/src/rag_platform/application/services.py`
- Modify: `app/back/src/rag_platform/api/schemas.py`
- Modify: `app/back/src/rag_platform/api/router.py`
- Modify: `app/back/src/api/dependencies.py`
- Modify: `app/back/src/rag_platform/infrastructure/in_memory/repositories.py`
- Modify: `app/back/src/rag_platform/infrastructure/postgres/document_repositories.py`
- Modify: `docs/api/pipeline-openapi.json`
- Modify: `app/front/src/features/platform/platformOpenApi.generated.ts`
- Modify: `app/front/src/features/platform/platformApi.ts`
- Modify: `app/front/src/features/platform/platformTypes.ts`

**Interfaces:**
- Consumes: existing `EligibilityDecision`, `SourceDocumentRepository`, `PlatformActor`, `RagPlatformServices`, and project access policy.
- Produces:

```py
@dataclass(frozen=True)
class RevisionReviewDecisionRecord:
    decision_id: str
    project_id: str
    source_document_revision_id: str
    eligibility_decision: EligibilityDecision
    reason: str
    decided_by: str
    decided_at: datetime

class RevisionReviewDecisionRepository(Protocol):
    def add(self, record: RevisionReviewDecisionRecord) -> RevisionReviewDecisionRecord: ...
    def latest_for_project(self, project_id: PlatformId) -> dict[str, RevisionReviewDecisionRecord]: ...

class SubmitRevisionReviewDecisionUseCase:
    def execute(
        self,
        *,
        project_id: PlatformId,
        source_document_revision_id: PlatformId,
        decision: EligibilityDecision,
        reason: str,
        actor: PlatformActor,
    ) -> RevisionReviewDecisionRecord: ...
```

```http
POST /api/platform/projects/{project_id}/document-revisions/{source_document_revision_id}/review-decision
Content-Type: application/json

{
  "decision": "approved_after_review" | "operator_waiver" | "blocked",
  "reason": "texto obligatorio"
}
```

`actor_id` is resolved server-side from `get_actor`; the client never sends it.

- [ ] **Step 1: Write backend unit tests for approve/reject**

Create `test_revision_review_decisions.py`:

```py
from datetime import datetime, timezone

import pytest

from rag_platform.application.platform_access import PlatformActor
from rag_platform.application.revision_review_service import (
    SubmitRevisionReviewDecisionUseCase,
)
from rag_platform.domain.errors import InvalidReviewDecision, RevisionProjectMismatch
from rag_platform.domain.identity import IdentityKind, PlatformId
from rag_platform.domain.models import (
    EligibilityDecision,
    RevisionReviewState,
    SourceDocument,
    SourceDocumentRevision,
)
from rag_platform.infrastructure.in_memory.repositories import (
    AllowAllAccessPolicy,
    InMemoryRevisionReviewDecisionRepository,
    InMemorySourceDocumentRepository,
)


def _pid(kind: IdentityKind, value: str) -> PlatformId:
    return PlatformId(kind=kind, value=value)


def _seed_revision(
    documents: InMemorySourceDocumentRepository,
    *,
    project_id: str = "proj_sst-general",
    revision_id: str = "srev_manual",
    review_state: RevisionReviewState = RevisionReviewState.NEEDS_REVIEW,
) -> None:
    logical_id = _pid(IdentityKind.SOURCE_DOCUMENT, "sdoc_manual")
    project_pid = _pid(IdentityKind.PROJECT, project_id)
    documents.upsert_document(
        SourceDocument(
            logical_document_id=logical_id,
            project_id=project_pid,
            source_relpath="manuales/manual.pdf",
            created_at=datetime(2026, 8, 25, tzinfo=timezone.utc),
        )
    )
    documents.add_revision(
        SourceDocumentRevision(
            source_document_revision_id=_pid(
                IdentityKind.SOURCE_DOCUMENT_REVISION,
                revision_id,
            ),
            logical_document_id=logical_id,
            project_id=project_pid,
            source_relpath="manuales/manual.pdf",
            raw_content_hash="a" * 64,
            file_size=42,
            uploaded_by="operator-1",
            uploaded_at=datetime(2026, 8, 25, tzinfo=timezone.utc),
            review_state=review_state,
        )
    )


def _use_case():
    documents = InMemorySourceDocumentRepository()
    decisions = InMemoryRevisionReviewDecisionRepository()
    use_case = SubmitRevisionReviewDecisionUseCase(
        documents=documents,
        decisions=decisions,
        access_policy=AllowAllAccessPolicy(),
        decision_id_factory=lambda: "rrd_001",
        clock=lambda: datetime(2026, 8, 25, 12, 0, tzinfo=timezone.utc),
    )
    return use_case, documents, decisions


def test_submit_reject_persists_blocked_without_snapshot_membership() -> None:
    use_case, documents, decisions = _use_case()
    _seed_revision(documents)

    record = use_case.execute(
        project_id=_pid(IdentityKind.PROJECT, "proj_sst-general"),
        source_document_revision_id=_pid(
            IdentityKind.SOURCE_DOCUMENT_REVISION,
            "srev_manual",
        ),
        decision=EligibilityDecision.BLOCKED,
        reason="OCR incompleto; no apto para publicar.",
        actor=PlatformActor(actor_id="operator-1"),
    )

    assert record.project_id == "proj_sst-general"
    assert record.source_document_revision_id == "srev_manual"
    assert record.eligibility_decision is EligibilityDecision.BLOCKED
    latest = decisions.latest_for_project(_pid(IdentityKind.PROJECT, "proj_sst-general"))
    assert latest["srev_manual"].eligibility_decision is EligibilityDecision.BLOCKED


def test_submit_approve_persists_approved_after_review() -> None:
    use_case, documents, decisions = _use_case()
    _seed_revision(documents)

    record = use_case.execute(
        project_id=_pid(IdentityKind.PROJECT, "proj_sst-general"),
        source_document_revision_id=_pid(
            IdentityKind.SOURCE_DOCUMENT_REVISION,
            "srev_manual",
        ),
        decision=EligibilityDecision.APPROVED_AFTER_REVIEW,
        reason="Revision humana completada.",
        actor=PlatformActor(actor_id="operator-1"),
    )

    assert record.eligibility_decision is EligibilityDecision.APPROVED_AFTER_REVIEW
    latest = decisions.latest_for_project(_pid(IdentityKind.PROJECT, "proj_sst-general"))
    assert latest["srev_manual"].reason == "Revision humana completada."


def test_submit_review_decision_rejects_cross_project_revision() -> None:
    use_case, documents, _ = _use_case()
    _seed_revision(documents, project_id="proj_otro")

    with pytest.raises(RevisionProjectMismatch):
        use_case.execute(
            project_id=_pid(IdentityKind.PROJECT, "proj_sst-general"),
            source_document_revision_id=_pid(
                IdentityKind.SOURCE_DOCUMENT_REVISION,
                "srev_manual",
            ),
            decision=EligibilityDecision.BLOCKED,
            reason="No pertenece al proyecto.",
            actor=PlatformActor(actor_id="operator-1"),
        )


def test_submit_review_decision_requires_reason() -> None:
    use_case, documents, _ = _use_case()
    _seed_revision(documents)

    with pytest.raises(InvalidReviewDecision, match="reason is required"):
        use_case.execute(
            project_id=_pid(IdentityKind.PROJECT, "proj_sst-general"),
            source_document_revision_id=_pid(
                IdentityKind.SOURCE_DOCUMENT_REVISION,
                "srev_manual",
            ),
            decision=EligibilityDecision.BLOCKED,
            reason=" ",
            actor=PlatformActor(actor_id="operator-1"),
        )
```

- [ ] **Step 2: Add the HTTP/read-model regression**

In `test_platform_document_api.py`, add:

```py
def test_review_decision_endpoint_persists_and_read_model_exposes(
    env: tuple[TestClient, Path],
) -> None:
    client, _ = env
    _create_project(client, "demo")
    srev = _upload(
        client,
        "demo",
        source_relpath="manuals/guia.md",
        content=b"hola",
    ).json()["source_document_revision_id"]

    response = client.post(
        f"/api/platform/projects/proj_demo/document-revisions/{srev}/review-decision",
        json={
            "decision": "blocked",
            "reason": "OCR incompleto; no apto para publicar.",
        },
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["project_id"] == "proj_demo"
    assert body["source_document_revision_id"] == srev
    assert body["eligibility_decision"] == "blocked"
    assert "decided_by" not in body

    listed = client.get("/api/platform/projects/proj_demo/documents").json()["items"]
    assert listed[0]["eligibility_decision"] == "blocked"
    assert listed[0]["eligibility_reason"] == "OCR incompleto; no apto para publicar."
    assert listed[0]["eligibility_decided_at"] is not None


def test_review_decision_endpoint_rejects_actor_id_in_body(
    env: tuple[TestClient, Path],
) -> None:
    client, _ = env
    _create_project(client, "demo")
    srev = _upload(
        client,
        "demo",
        source_relpath="manuals/guia.md",
        content=b"hola",
    ).json()["source_document_revision_id"]

    response = client.post(
        f"/api/platform/projects/proj_demo/document-revisions/{srev}/review-decision",
        json={
            "decision": "blocked",
            "reason": "No apto.",
            "actor_id": "body-attacker",
        },
    )

    assert response.status_code == 422
```

- [ ] **Step 3: Deliver the red backend commands to the operator (do NOT run them)**

Hand these over verbatim, then STOP and WAIT for the pasted output:

```bash
npm run python -- -m pytest app/back/tests/rag_platform/test_revision_review_decisions.py -q
npm run python -- -m pytest app/back/tests/rag_platform/test_platform_document_api.py::test_review_decision_endpoint_persists_and_read_model_exposes app/back/tests/rag_platform/test_platform_document_api.py::test_review_decision_endpoint_rejects_actor_id_in_body -q
```

Expected before implementation: import failure for `revision_review_service` and `InMemoryRevisionReviewDecisionRepository`.

- [ ] **Step 4: Add the application port and use case**

In `domain/errors.py`, add a stable domain error:

```py
class InvalidReviewDecision(RagPlatformError):
    """La decision operacional de revision no cumple el contrato de Platform."""

    code = "INVALID_REVIEW_DECISION"
    http_status = 422
```

In `application/context.py`, keep the review decision port beside the existing
application repository protocols. Add imports for `dataclass`, `datetime`, and
`EligibilityDecision` if they are not already present:

```py
@dataclass(frozen=True)
class RevisionReviewDecisionRecord:
    decision_id: str
    project_id: str
    source_document_revision_id: str
    eligibility_decision: EligibilityDecision
    reason: str
    decided_by: str
    decided_at: datetime


@runtime_checkable
class RevisionReviewDecisionRepository(Protocol):
    def add(self, record: RevisionReviewDecisionRecord) -> RevisionReviewDecisionRecord:
        """Persist one operator decision."""

    def latest_for_project(
        self, project_id: PlatformId
    ) -> dict[str, RevisionReviewDecisionRecord]:
        """Return the latest decision per source revision for a project."""
```

Create `revision_review_service.py`:

```py
from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone

from rag_platform.application.context import (
    PlatformAccessPolicy,
    RevisionReviewDecisionRecord,
    RevisionReviewDecisionRepository,
    SourceDocumentRepository,
)
from rag_platform.application.platform_access import (
    PlatformActor,
    require_project_operator,
)
from rag_platform.domain.errors import InvalidReviewDecision, RevisionProjectMismatch
from rag_platform.domain.identity import PlatformId
from rag_platform.domain.models import EligibilityDecision


class SubmitRevisionReviewDecisionUseCase:
    def __init__(
        self,
        *,
        documents: SourceDocumentRepository,
        decisions: RevisionReviewDecisionRepository,
        access_policy: PlatformAccessPolicy,
        decision_id_factory: Callable[[], str],
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._documents = documents
        self._decisions = decisions
        self._access_policy = access_policy
        self._decision_id_factory = decision_id_factory
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def execute(
        self,
        *,
        project_id: PlatformId,
        source_document_revision_id: PlatformId,
        decision: EligibilityDecision,
        reason: str,
        actor: PlatformActor,
    ) -> RevisionReviewDecisionRecord:
        require_project_operator(self._access_policy, actor=actor, project_id=project_id)
        cleaned_reason = reason.strip()
        if not cleaned_reason:
            raise InvalidReviewDecision("reason is required")

        revision = self._documents.get_revision(source_document_revision_id)
        if revision.project_id != project_id:
            raise RevisionProjectMismatch(source_document_revision_id.value)

        if decision is EligibilityDecision.NOT_REQUIRED:
            raise InvalidReviewDecision(
                "not_required is derived server-side and cannot be submitted"
            )

        return self._decisions.add(
            RevisionReviewDecisionRecord(
                decision_id=self._decision_id_factory(),
                project_id=project_id.value,
                source_document_revision_id=source_document_revision_id.value,
                eligibility_decision=decision,
                reason=cleaned_reason,
                decided_by=actor.actor_id,
                decided_at=self._clock(),
            )
        )
```

- [ ] **Step 5: Add in-memory and Postgres repositories**

In `in_memory/repositories.py` add:

```py
class InMemoryRevisionReviewDecisionRepository:
    def __init__(self) -> None:
        self._records: dict[str, RevisionReviewDecisionRecord] = {}
        self._lock = threading.Lock()

    def add(self, record: RevisionReviewDecisionRecord) -> RevisionReviewDecisionRecord:
        with self._lock:
            self._records[record.decision_id] = record
        return record

    def latest_for_project(
        self, project_id: PlatformId
    ) -> dict[str, RevisionReviewDecisionRecord]:
        with self._lock:
            records = [
                record for record in self._records.values()
                if record.project_id == project_id.value
            ]
        latest: dict[str, RevisionReviewDecisionRecord] = {}
        for record in sorted(records, key=lambda item: (item.decided_at, item.decision_id)):
            latest[record.source_document_revision_id] = record
        return latest
```

Add imports:

```py
from rag_platform.application.context import RevisionReviewDecisionRecord
```

In `document_repositories.py` add:

```py
from rag_platform.application.context import RevisionReviewDecisionRecord


class PostgresRevisionReviewDecisionRepository:
    def __init__(self, connection: object) -> None:
        self._connection = connection

    def add(self, record: RevisionReviewDecisionRecord) -> RevisionReviewDecisionRecord:
        with self._connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO source_document_revision_review_decisions"
                " (decision_id, project_id, source_document_revision_id,"
                " eligibility_decision, reason, decided_by, decided_at)"
                " VALUES (%s, %s, %s, %s, %s, %s, %s)"
                " ON CONFLICT (decision_id) DO NOTHING",
                (
                    record.decision_id,
                    record.project_id,
                    record.source_document_revision_id,
                    record.eligibility_decision.value,
                    record.reason,
                    record.decided_by,
                    record.decided_at,
                ),
            )
        return record

    def latest_for_project(
        self, project_id: PlatformId
    ) -> dict[str, RevisionReviewDecisionRecord]:
        with self._connection.cursor() as cursor:
            cursor.execute(
                "SELECT DISTINCT ON (source_document_revision_id)"
                " decision_id, project_id, source_document_revision_id,"
                " eligibility_decision, reason, decided_by, decided_at"
                " FROM source_document_revision_review_decisions"
                " WHERE project_id = %s"
                " ORDER BY source_document_revision_id, decided_at DESC, decision_id DESC",
                (project_id.value,),
            )
            rows = cursor.fetchall()
        return {
            str(row[2]): RevisionReviewDecisionRecord(
                decision_id=str(row[0]),
                project_id=str(row[1]),
                source_document_revision_id=str(row[2]),
                eligibility_decision=EligibilityDecision(str(row[3])),
                reason=str(row[4]),
                decided_by=str(row[5]),
                decided_at=row[6],
            )
            for row in rows
        }
```

- [ ] **Step 6: Add the migration**

Create `migrations/20260825_01_create_source_revision_review_decisions.sql`:

```sql
-- Operational review decisions for RAG Platform document revisions.
-- This table is append-only by decision_id. It does not mutate immutable source
-- revisions and it does not put blocked revisions inside corpus snapshots.

CREATE TABLE IF NOT EXISTS source_document_revision_review_decisions (
    decision_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES rag_projects(project_id),
    source_document_revision_id TEXT NOT NULL,
    eligibility_decision TEXT NOT NULL
        CHECK (eligibility_decision IN (
            'approved_after_review',
            'operator_waiver',
            'blocked'
        )),
    reason TEXT NOT NULL CHECK (length(btrim(reason)) > 0),
    decided_by TEXT NOT NULL,
    decided_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Existing source_document_revisions has a simple PK. This composite uniqueness
-- target lets the review-decision table enforce project ownership in the DB.
CREATE UNIQUE INDEX IF NOT EXISTS uq_source_document_revisions_project_revision
    ON source_document_revisions (project_id, source_document_revision_id);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'source_revision_review_decisions_project_revision_fk'
    ) THEN
        ALTER TABLE source_document_revision_review_decisions
            ADD CONSTRAINT source_revision_review_decisions_project_revision_fk
            FOREIGN KEY (project_id, source_document_revision_id)
            REFERENCES source_document_revisions (
                project_id,
                source_document_revision_id
            );
    END IF;
END
$$;

CREATE INDEX IF NOT EXISTS idx_revision_review_decisions_latest
    ON source_document_revision_review_decisions (
        project_id,
        source_document_revision_id,
        decided_at DESC,
        decision_id DESC
    );
```

- [ ] **Step 7: Extend the project document read-model**

In `document_query_service.py`, add optional `review_decisions` injection and row fields:

```py
eligibility_decision: str | None = None
eligibility_reason: str | None = None
eligibility_decided_at: datetime | None = None
```

Inside `ListProjectDocumentsUseCase.execute`, after `revisions = ...`:

```py
latest_decisions = (
    {}
    if self._review_decisions is None
    else self._review_decisions.latest_for_project(project_id)
)
```

When creating `ProjectDocumentRevisionRow`:

```py
decision = latest_decisions.get(revision_id)
...
eligibility_decision=(
    None if decision is None else decision.eligibility_decision.value
),
eligibility_reason=None if decision is None else decision.reason,
eligibility_decided_at=None if decision is None else decision.decided_at,
```

- [ ] **Step 8: Add schemas and router endpoint**

In `schemas.py` add:

```py
class SubmitRevisionReviewDecisionRequestSchema(StrictModel):
    decision: EligibilityDecision
    reason: str = Field(min_length=1, max_length=2000)


class RevisionReviewDecisionSchema(StrictModel):
    decision_id: str
    project_id: str
    source_document_revision_id: str
    eligibility_decision: str
    reason: str
    decided_at: datetime
```

Also import `EligibilityDecision` from `rag_platform.domain.models` in
`schemas.py` so OpenAPI exposes the allowed values instead of an untyped string.

In `ProjectDocumentRevisionSchema` add nullable fields:

```py
eligibility_decision: str | None = None
eligibility_reason: str | None = None
eligibility_decided_at: datetime | None = None
```

Update the existing domain→schema mapper `document_row_to_schema` (in
`schemas.py`) to map the three new nullable fields from
`ProjectDocumentRevisionRow`, and extend the unit test that covers that
mapper — adding a schema field without updating its mapper silently drops the
value from every API response.

In `router.py` add:

```py
@router.post(
    "/projects/{project_id}/document-revisions/{source_document_revision_id}/review-decision",
    response_model=RevisionReviewDecisionSchema,
)
def submit_revision_review_decision(
    project_id: str,
    source_document_revision_id: str,
    payload: SubmitRevisionReviewDecisionRequestSchema,
    services: RagPlatformServices = Depends(get_platform_services),
    actor: PlatformActor = Depends(get_actor),
) -> RevisionReviewDecisionSchema:
    record = services.submit_revision_review_decision.execute(
        project_id=_parse_id(IdentityKind.PROJECT, project_id),
        source_document_revision_id=_parse_id(
            IdentityKind.SOURCE_DOCUMENT_REVISION,
            source_document_revision_id,
        ),
        decision=payload.decision,
        reason=payload.reason,
        actor=actor,
    )
    return RevisionReviewDecisionSchema(
        decision_id=record.decision_id,
        project_id=record.project_id,
        source_document_revision_id=record.source_document_revision_id,
        eligibility_decision=record.eligibility_decision.value,
        reason=record.reason,
        decided_at=record.decided_at,
    )
```

- [ ] **Step 9: Wire the service container**

In `services.py`, add:

```py
submit_revision_review_decision: SubmitRevisionReviewDecisionUseCase
```

In `app/back/src/api/dependencies.py`, construct `review_decisions` beside
`documents` in both the in-memory and PostgreSQL branches of
`_build_rag_platform_services`:

```py
if connection is None:
    review_decisions = InMemoryRevisionReviewDecisionRepository()
else:
    review_decisions = PostgresRevisionReviewDecisionRepository(connection)
```

Pass it to:

```py
list_documents = ListProjectDocumentsUseCase(
    documents=documents,
    normalized=normalized,
    access_policy=access_policy,
    review_decisions=review_decisions,
)
```

and to `RagPlatformServices`:

```py
submit_revision_review_decision=SubmitRevisionReviewDecisionUseCase(
    documents=documents,
    decisions=review_decisions,
    access_policy=access_policy,
    decision_id_factory=lambda: f"rrd_{uuid.uuid4().hex}",
),
```

`RagPlatformServices` is a frozen dataclass and is also constructed directly by
backend tests; a new required field breaks every site that does not pass it.
Find and update them all before running pytest:

```bash
rg -n "RagPlatformServices\(" app/back
```

- [ ] **Step 10: Add frontend wrapper**

In `platformTypes.ts` export:

```ts
export type SubmitRevisionReviewDecisionRequest =
  Schemas["SubmitRevisionReviewDecisionRequestSchema"];
export type RevisionReviewDecision = Schemas["RevisionReviewDecisionSchema"];
```

In `platformApi.ts` add:

```ts
export function submitRevisionReviewDecision(
  projectId: string,
  sourceDocumentRevisionId: string,
  body: SubmitRevisionReviewDecisionRequest,
  options?: PipelinePostOptions,
): Promise<RevisionReviewDecision> {
  return postJson<RevisionReviewDecision>(
    `${BASE}/projects/${projectId}/document-revisions/${sourceDocumentRevisionId}/review-decision`,
    body,
    options,
  );
}
```

- [ ] **Step 11: Deliver the OpenAPI/test commands to the operator (do NOT run them)**

Hand these over verbatim, then STOP and WAIT for the pasted output:

```bash
npm run python -- -m pytest app/back/tests/rag_platform/test_revision_review_decisions.py -q
npm run python -- -m pytest app/back/tests/rag_platform/test_platform_document_api.py::test_review_decision_endpoint_persists_and_read_model_exposes app/back/tests/rag_platform/test_platform_document_api.py::test_review_decision_endpoint_rejects_actor_id_in_body -q
npm run python -- -m pytest app/back/tests/rag_platform/test_corpus_snapshots.py app/back/tests/rag_platform/test_release_lifecycle.py -q
npm run python -- scripts/api/export_pipeline_openapi.py
npm --prefix app/front run api:generate
npm --prefix app/front run api:check
```

Expected result: review decisions are persisted outside snapshots, `blocked`
still fails closed for snapshot/release membership, and frontend generated types
include the new request/response schemas. If `api:check` fails only because the
expected generated OpenAPI/TypeScript files are modified but not yet staged,
inspect the diff and rerun it as a final drift guard after the generated files
are part of the intended change.

---

### Task 4: Build The Platform Datasource Over Existing Project Endpoints

**Files:**
- Create: `app/front/src/features/platform/legacyPipeline/platformDashboardMappers.ts`
- Create: `app/front/src/features/platform/legacyPipeline/platformDashboardMappers.test.ts`
- Create: `app/front/src/features/platform/legacyPipeline/platformDashboardDataSource.ts`
- Modify: `app/front/src/features/platform/platformApi.ts` only if an existing endpoint wrapper is missing from `platformApi.ts`

**Interfaces:**
- Consumes: `Project`, `ProjectConfiguration`, `ProjectDocumentRevision`, `ProjectNormalizeReport`, `Variant`, `CorpusSnapshot`, `Release`, and functions from `platformApi.ts`.
- Produces:

```ts
export function toPlatformDashboardStatus(input: {
  projectId: string;
  projectName: string;
  configuration: ProjectConfiguration;
  documents: readonly ProjectDocumentRevision[];
}): StatusPayload;

export function createPlatformDashboardDataSource(input: {
  projectId: string;
  projectName: string;
}): DashboardPipelineDataSource;
```

The datasource never takes `selectedRagVariantId` as input. Variant identity is
produced at operation time by `resolveOrCreatePlatformRagVariant` from the
recipe captured across the Legacy screens: `runPipeline`/`saveSettings` record
the Operacion leg (`recordProcessingControls`), and the chunking/embedding legs
are recorded by the Task 6 injected clients into `platformRecipeDraft`.

- [ ] **Step 1: Write mapper tests**

Create tests that lock the fail-closed mapping:

```ts
import { describe, expect, it } from "vitest";
import { toPlatformDashboardStatus } from "./platformDashboardMappers.js";
import type { ProjectConfiguration, ProjectDocumentRevision } from "../platformTypes.js";

const config: ProjectConfiguration = {
  corpus_organization_policy: "source-folders-v1",
  created_at: "2026-08-25T00:00:00Z",
  document_types: [],
  embedding_profiles: [],
  target_bindings: [],
  version: 3,
};

function revision(overrides: Partial<ProjectDocumentRevision> = {}): ProjectDocumentRevision {
  return {
    file_size: 2048,
    logical_document_id: "doc_manual",
    normalized_registered: true,
    processing_status: "processed",
    raw_registered: true,
    review_state: "processed",
    source_document_revision_id: "srev_1",
    source_relpath: "manuales/manual.pdf",
    uploaded_at: "2026-08-25T12:00:00Z",
    ...overrides,
  };
}

describe("platform dashboard mappers", () => {
  it("maps project document revisions to the legacy StatusPayload without physical fields", () => {
    const payload = toPlatformDashboardStatus({
      projectId: "proj_sst-general",
      projectName: "SST General",
      configuration: config,
      documents: [revision()],
    });

    expect(payload.summary.total).toBe(1);
    expect(payload.summary.processed).toBe(1);
    expect(payload.summary.needsReview).toBe(0);
    expect(payload.summary.schemaVersion).toBe("platform-config-v3");
    expect(payload.documents[0]).toMatchObject({
      documentId: "srev_1",
      sourceRelpath: "manuales/manual.pdf",
      documentName: "manual.pdf",
      category: null,
      ocrConfidenceLabel: "N/D",
      processingStatus: "processed",
      displayStatus: "processed",
      reviewStatus: "not_required",
    });
  });

  it("keeps needs_review visible and pending in the legacy review screen", () => {
    const payload = toPlatformDashboardStatus({
      projectId: "proj_sst-general",
      projectName: "SST General",
      configuration: config,
      documents: [
        revision({
          source_document_revision_id: "srev_needs_review",
          normalized_registered: false,
          processing_status: "needs_review",
          review_state: "needs_review",
        }),
      ],
    });

    expect(payload.summary.needsReview).toBe(1);
    expect(payload.needsReview).toHaveLength(1);
    expect(payload.needsReview[0].reviewStatus).toBe("pending");
    expect(payload.needsReview[0].reviewReasons).toEqual(["needs_review"]);
  });

  it("maps operational blocked decisions to the legacy rejected state", () => {
    const payload = toPlatformDashboardStatus({
      projectId: "proj_sst-general",
      projectName: "SST General",
      configuration: config,
      documents: [
        revision({
          eligibility_decision: "blocked",
          eligibility_reason: "OCR incompleto; no apto para publicar.",
          eligibility_decided_at: "2026-08-25T12:00:00Z",
          review_state: "needs_review",
        }),
      ],
    });

    expect(payload.summary.rejected).toBe(1);
    expect(payload.documents[0].reviewStatus).toBe("rejected");
    expect(payload.documents[0].displayStatus).toBe("rejected");
    expect(payload.documents[0].decision).toMatchObject({
      decision: "rejected",
      reason: "OCR incompleto; no apto para publicar.",
    });
  });
});
```

- [ ] **Step 2: Implement the pure mapper**

Implement `toPlatformDashboardStatus` with these rules:

```ts
const knownProcessingStatuses = new Set(["pending", "processed", "failed", "needs_review"]);

function toProcessingStatus(value: string): ProcessingStatus {
  if (value === "registered") return "pending";
  if (value === "normalized") return "processed";
  return knownProcessingStatuses.has(value) ? (value as ProcessingStatus) : "needs_review";
}

function toReviewStatus(revision: ProjectDocumentRevision): ReviewStatus {
  if (
    revision.eligibility_decision === "approved_after_review" ||
    revision.eligibility_decision === "operator_waiver"
  ) {
    return "approved";
  }
  if (revision.eligibility_decision === "blocked") return "rejected";
  if (revision.review_state === "needs_review") return "pending";
  return "not_required";
}

function toDisplayStatus(revision: ProjectDocumentRevision): DisplayStatus {
  const reviewStatus = toReviewStatus(revision);
  if (reviewStatus === "approved" || reviewStatus === "rejected") return reviewStatus;
  if (revision.review_state === "needs_review") return "needs_review";
  return toProcessingStatus(revision.processing_status);
}

function toReviewDecision(revision: ProjectDocumentRevision): ReviewDecision | null {
  const reviewStatus = toReviewStatus(revision);
  if (reviewStatus !== "approved" && reviewStatus !== "rejected") return null;
  return {
    document_id: revision.source_document_revision_id,
    source_relpath: revision.source_relpath,
    decision: reviewStatus,
    reason: revision.eligibility_reason ?? "Decision operacional Platform",
    decided_at: revision.eligibility_decided_at ?? revision.uploaded_at,
  };
}
```

For fields Platform does not expose:

```ts
category: null,
mimeType: null,
ingestionProvider: "unregistered",
ingestionProviderLabel: "No expuesto por Platform",
ingestionMethod: "platform",
ingestionMethodLabel: "No expuesto por Platform",
ocrConfidenceKind: "no_expuesto",
ocrConfidenceValue: null,
ocrConfidencePercent: null,
ocrConfidenceLabel: "N/D",
decision: toReviewDecision(revision),
```

This is not data invention because the labels say the contract does not expose the value.

Completeness rules (TS is strict; every required field must be filled
honestly — verified against `dashboardTypes.ts`):

- `DocumentRecord`: `documentName` derives from `source_relpath` basename;
  `detectedExtension` from its extension or `"bin"`; `fileSize` = Platform
  `file_size`; `ingestionDate` = `uploaded_at`; `mimeType: null`;
  `reviewReasons: ["needs_review"]` ONLY when review is pending, otherwise
  `[]`; `reviewDetails: []`.
- `summary`: fill ALL counters (`total`, `processed`, `needsReview`,
  `normalizedNeedsReview`, `failed`, `approved`, `rejected`, plus `runId:
  null`, `generatedAt: new Date().toISOString()`, and
  `schemaVersion: \`platform-config-v${configuration.version}\``).
- `settings` is REQUIRED (`{ocrReviewThreshold, ocrReviewThresholdPercent,
  llamaControls?}`): fill neutral values (thresholds `0`) plus the last
  provider controls recorded in the recipe draft; the Operacion OCR input is
  disabled-with-reason under Platform so these neutral numbers are never
  mistaken for live configuration.
- `llamaFirst`: neutral false-shaped object per its type; `errors: []`;
  `validation: null`; `manifests: {}`. Platform surfaces validation through
  `RAG / Releases`, never through this payload.

- [ ] **Step 3: Implement the Platform datasource**

Create `platformDashboardDataSource.ts`:

```ts
import type { DashboardPipelineDataSource } from "../../dashboard/dashboardDataSource.js";
import type { LlamaControls } from "../../dashboard/dashboardTypes.js";
import {
  getConfiguration,
  listAllDocuments,
  normalizeDocuments,
  submitRevisionReviewDecision,
  uploadDocument,
} from "../platformApi.js";
import { toPlatformDashboardStatus } from "./platformDashboardMappers.js";
import {
  readRecipeDraft,
  recordProcessingControls,
  resolveOrCreatePlatformRagVariant,
} from "./platformRagVariantResolver.js";

export function createPlatformDashboardDataSource(input: {
  projectId: string;
  projectName: string;
}): DashboardPipelineDataSource {
  async function loadStatus() {
    const [configuration, documents] = await Promise.all([
      getConfiguration(input.projectId),
      listAllDocuments(input.projectId),
    ]);
    return toPlatformDashboardStatus({
      projectId: input.projectId,
      projectName: input.projectName,
      configuration,
      documents,
    });
  }

  return {
    loadStatus,
    async uploadDocument(form) {
      if (!form.file) throw new Error("Selecciona un archivo .pdf o .md.");
      // Honestidad: POST /documents solo acepta file + source_relpath. La
      // categoria del panel Legacy NO tiene contrato Platform: su select se
      // renderiza deshabilitado-con-motivo y nunca se envia ni se simula.
      const folder = form.folder.trim().replace(/^\/+|\/+$/g, "");
      const sourceRelpath = folder ? `${folder}/${form.file.name}` : form.file.name;
      const revision = await uploadDocument(input.projectId, form.file, sourceRelpath);
      return {
        ok: true,
        status: revision.processing_status,
        sourceRelpath: revision.source_relpath,
        summary: { uploaded: 1 },
        statusPayload: await loadStatus(),
      };
    },
    async runPipeline({ controls }) {
      // The variant is BUILT from the screens' configuration (recipe first).
      recordProcessingControls(input.projectId, controls);
      const resolved = await resolveOrCreatePlatformRagVariant({
        projectId: input.projectId,
        recipe: readRecipeDraft(input.projectId),
      });

      // Audit correction enforced: choose revision IDs from the RAW Platform
      // read-model (listAllDocuments), never from the mapped Legacy
      // StatusPayload display states.
      const revisions = await listAllDocuments(input.projectId);
      const revisionIds = revisions
        .filter((revision) => revision.eligibility_decision !== "blocked")
        .filter(
          (revision) =>
            revision.review_state === "processed" ||
            revision.eligibility_decision === "approved_after_review" ||
            revision.eligibility_decision === "operator_waiver",
        )
        .map((revision) => revision.source_document_revision_id);

      const report = await normalizeDocuments(input.projectId, {
        rag_variant_id: resolved.ragVariantId,
        document_revision_ids: revisionIds,
        force: false,
      });
      return {
        ok: report.failed === 0,
        status: report.failed === 0 ? "processed" : "failed",
        runId: report.rag_variant_id,
        summary: {
          processed: report.processed,
          needs_review: report.needs_review,
          failed: report.failed,
          skipped: report.skipped,
        },
        statusPayload: await loadStatus(),
      };
    },
    async saveSettings({ llamaControls }) {
      // Honesto: lo UNICO que se persiste es el leg de Operacion de la receta
      // (por proyecto, alcance de sesion) para el resolutor. El umbral OCR no
      // tiene contrato Platform: su input va deshabilitado-con-motivo y nunca
      // se simula su guardado.
      recordProcessingControls(input.projectId, llamaControls);
      return {
        ok: true,
        status: await loadStatus(),
      };
    },
    // Botones deshabilitados-con-motivo bajo Platform (capacidad declarada via
    // el prop opcional de DashboardChrome); estos throws son el fail-closed de
    // respaldo por si algo los invoca igualmente.
    async validateBundle() {
      throw new Error("En Platform la validacion se ejecuta desde RAG / Releases sobre un rag_release_id.");
    },
    async promoteStaging() {
      throw new Error("Platform no promueve staging global; crea snapshot y release por proyecto.");
    },
    async submitReview({ documentId, decision, reason }) {
      const eligibilityDecision =
        decision === "approved" ? "approved_after_review" : "blocked";
      const record = await submitRevisionReviewDecision(input.projectId, documentId, {
        decision: eligibilityDecision,
        reason,
      });
      return {
        ok: true,
        status: decision,
        runId: record.decision_id,
        summary: { [decision]: 1 },
        statusPayload: await loadStatus(),
      };
    },
  };
}
```

The generated `NormalizeProjectDocumentsRequest` currently uses `document_revision_ids`; keep that exact field name. `resolveOrCreatePlatformRagVariant` throws the fail-closed messages from the resolution contract; `runPipeline` must surface them verbatim in the Legacy notice area — never fall back to a preference-stored variant.

- [ ] **Step 4: Deliver the mapper/resolver commands to the operator (do NOT run them)**

Hand these over verbatim, then STOP and WAIT for the pasted output:

```bash
npm --prefix app/front exec vitest run src/features/platform/legacyPipeline/platformDashboardMappers.test.ts
npm --prefix app/front run test
```

Expected result: mapper tests pass, and any TypeScript mismatch points to the exact generated Platform request field.

- [ ] **Step 5: Implement the variant resolver (recipe → `rag_variant_id`) red-first**

Create `platformRecipeDraft.ts` — a per-project record of what the operator
configured inside the Legacy screens. The Operacion leg is written by
`recordProcessingControls(projectId, controls)` from the datasource; the
chunking/embedding legs are written by the Task 6 injected clients when the
operator selects/launches in those screens. It stores only ids and provider
metadata, never physical targets.

Create `platformRagVariantResolver.ts` implementing every rule of the
"RAG Variant Resolution Contract" section over `getConfiguration`,
`listProcessingProfiles`, `listChunkingProfiles`, `getVariantMatrix`,
`listAllVariants`, and `createVariant`.

Write `platformRagVariantResolver.test.ts` locking at least these cases:

```ts
describe("resolveOrCreatePlatformRagVariant", () => {
  it("reusa la variante existente cuando la tripleta de perfiles ya tiene variante");
  it("crea la variante cuando la celda es construible y no existe variante");
  it("ante 409 DUPLICATE_VARIANT_RECIPE re-lista las variantes y reusa la existente");
  it("fallo cerrado mostrando blocked_reason cuando la celda no es construible");
  it("fallo cerrado cuando providerMode no mapea a un unico processing profile (lista candidatos)");
  it("fallo cerrado pidiendo la pantalla Chunking cuando hay varios perfiles y sin seleccion del operador");
  it("auto-resuelve el leg unico cuando el catalogo tiene exactamente un perfil de chunking / un embedding habilitado");
  it("fallo cerrado listando binding_key cuando hay varios target bindings");
  it("nunca llama a normalize ni crea variantes fuera de la matriz");
});
```

Hand these to the operator verbatim (do NOT run them); STOP and WAIT for output:

```bash
npm --prefix app/front exec vitest run src/features/platform/legacyPipeline/platformRagVariantResolver.test.ts src/features/platform/legacyPipeline/platformDashboardMappers.test.ts
npm --prefix app/front run test
```

Expected result: the resolver contract is green and both consumers
(`runPipeline` here, release drafting in Task 5) compile against resolver
output instead of the bare `selectedRagVariantId` preference.

---

### Task 5: Mount The Legacy Pipeline UI Inside Platform

**Files:**
- Create: `app/front/src/features/platform/legacyPipeline/PlatformLegacyPipelineWorkspace.tsx`
- Modify: `app/front/src/features/platform/PlatformWorkspace.tsx`
- Modify: `app/front/src/features/platform/platformNavigation.ts`
- Modify: `app/front/src/features/platform/PlatformWorkspace.test.tsx`
- Remove after green tests: `app/front/src/features/platform/PlatformReleaseBuildStageInfo.tsx`
- Remove after green tests: `app/front/src/features/platform/documents/ProjectInventoryWorkspace.tsx`

**Interfaces:**
- Consumes: `DashboardPipelineApp`, `createPlatformDashboardDataSource`, `PlatformProjectContext`, `PlatformView`.
- Produces: Platform pipeline views that render the real Legacy UI.

- [ ] **Step 1: Create the Platform host**

Create `PlatformLegacyPipelineWorkspace.tsx`:

```tsx
import { useMemo } from "react";
import { StatePanel } from "../../../components/ui/StatePanel.js";
import { DashboardPipelineApp } from "../../dashboard/DashboardPipelineApp.js";
import type { AppView } from "../../dashboard/dashboardTypes.js";
import { usePlatformProjectContext } from "../PlatformProjectContext.js";
import { createPlatformDashboardDataSource } from "./platformDashboardDataSource.js";

export function PlatformLegacyPipelineWorkspace({ activeView }: { activeView: AppView }) {
  const { projectId, selectedProject } = usePlatformProjectContext();

  // The datasource resolves rag_variant_id at operation time via
  // resolveOrCreatePlatformRagVariant; preferences.selectedRagVariantId is only
  // a display cache and is never passed down as an input.
  const dataSource = useMemo(() => {
    if (!projectId) return null;
    return createPlatformDashboardDataSource({
      projectId,
      projectName: selectedProject?.display_name ?? projectId,
    });
  }, [projectId, selectedProject?.display_name]);

  if (!projectId || !dataSource) {
    return (
      <section className="panel">
        <StatePanel kind="info" message="Selecciona un proyecto para abrir el pipeline Legacy con scope Platform." />
      </section>
    );
  }

  return (
    <DashboardPipelineApp
      dataSource={dataSource}
      forcedActiveView={activeView}
      scopeSubtitle={`Proyecto ${selectedProject?.display_name ?? projectId}`}
      userChipLabel={selectedProject?.display_name ?? projectId}
    />
  );
}
```

Add `forcedActiveView` to `DashboardPipelineApp` in Task 2 so Platform controls which Legacy view is visible from Platform nav while Legacy global keeps its own sidebar/preferences.

- [ ] **Step 2: Change Platform routing**

In `PlatformWorkspace.tsx`, remove these imports:

```ts
import { DocumentIntakeWorkspace } from "./documents/DocumentIntakeWorkspace.js";
import { ProjectInventoryWorkspace } from "./documents/ProjectInventoryWorkspace.js";
import { CorpusSnapshotWorkspace } from "./corpus/CorpusSnapshotWorkspace.js";
import { PlatformReleaseBuildStageInfo } from "./PlatformReleaseBuildStageInfo.js";
```

Add:

```ts
import { PlatformLegacyPipelineWorkspace } from "./legacyPipeline/PlatformLegacyPipelineWorkspace.js";
```

Change the switch:

```tsx
case "operations":
  return <PlatformLegacyPipelineWorkspace activeView="operations" />;
case "review":
  return <PlatformLegacyPipelineWorkspace activeView="review" />;
case "inventory":
  return <PlatformLegacyPipelineWorkspace activeView="inventory" />;
case "chunking":
  return <PlatformLegacyPipelineWorkspace activeView="chunking" />;
case "embedding-indexing":
  return <PlatformLegacyPipelineWorkspace activeView="embedding-indexing" />;
case "releases":
  return <RagReleaseWorkspace />;
```

- [ ] **Step 3: Consume the props already added in Task 2 (nothing new here)**

`DashboardPipelineApp` ALREADY exposes `forcedActiveView` and
`hideInternalNavigation` with the `activeView = forcedActiveView ??
preferences.activeView` derivation from Task 2 Step 4. Do NOT add them again.
This step only verifies, by reading the extracted file, that:

```ts
const activeView = forcedActiveView ?? preferences.activeView;
```

exists once, that every render branch reads `activeView`, and that both inner
navigation surfaces stay hidden when either flag is set:

```tsx
{hideInternalNavigation || forcedActiveView ? null : (
  <div className="view-switcher" aria-label="Cambiar vista">
    ...
  </div>
)}
```

Platform passes `forcedActiveView={activeView}` per Step 1; Legacy global
passes neither and keeps its own navigation and persisted preference.

- [ ] **Step 4: Move snapshot creation into RAG / Releases**

Extract the body of `CorpusSnapshotWorkspace` into `CorpusSnapshotBuilderPanel.tsx`:

```tsx
export function CorpusSnapshotBuilderPanel({ compact = false }: { compact?: boolean }) {
  const workspace = useCorpusSnapshotWorkspace();
  // Keep the existing selection, eligibility decision, fail-closed message,
  // history, and Crear snapshot button. Do not render a top-level workspace nav.
}
```

Architecture note: `useCorpusSnapshotWorkspace` reads `projectId` from
`PlatformProjectContext`, so the extracted panel works unchanged inside
`RagReleaseWorkspace` as long as it stays under the same provider. Do NOT
thread `project_id` through props or duplicate the hook for that.

Keep `CorpusSnapshotWorkspace.tsx` as a wrapper during migration:

```tsx
import { CorpusSnapshotBuilderPanel } from "./CorpusSnapshotBuilderPanel.js";

export function CorpusSnapshotWorkspace() {
  return (
    <main className="workspace operator-workspace platform-workspace">
      <CorpusSnapshotBuilderPanel />
    </main>
  );
}
```

Mount the panel inside `RagReleaseWorkspace` before the draft form:

```tsx
<section className="panel" aria-label="Snapshot de corpus">
  <div className="panel-heading">
    <div>
      <h2>Snapshot de corpus</h2>
      <span>Congela revisiones aprobadas antes de crear una release.</span>
    </div>
  </div>
  <div className="ui-panel-body">
    <CorpusSnapshotBuilderPanel compact />
  </div>
</section>
```

Update `RagReleaseWorkspace.test.tsx` with:

```tsx
expect(await screen.findByRole("button", { name: /Crear snapshot/i })).toBeTruthy();
expect(screen.getByRole("button", { name: /Crear draft/i })).toBeTruthy();
```

This keeps snapshot creation operational without using `Revision` as a mislabeled corpus screen.

- [ ] **Step 5: Keep RAG / Releases as the one Platform-specific route**

Leave `RagReleaseWorkspace` mounted only for `releases`. It now owns snapshot creation, release draft creation, build, validation, publication, retirement, and release history over `/api/platform/*`.

Release draft creation must obtain `rag_variant_id` through
`resolveOrCreatePlatformRagVariant` (recipe built from the Legacy screens) or
from the project's listed variants, per the resolution contract. The
`target_binding_key` comes from the same resolution; `corpus_snapshot_id` comes
from `CorpusSnapshotBuilderPanel`. A hand-typed variant id is forbidden.

`ReleaseDraftForm` already selects among LISTED variants (an allowed source);
keep that select. But its empty-state helper copy says "créala en la matriz"
— a dead-end pointing at the deleted matrix screen. Rewrite it to describe
the real flow: the variant is resolved automatically from the recipe
configured in Operacion/Chunking/Embedding-Indexing, and appears listed after
the first operation resolves or creates it.

- [ ] **Step 6: Deliver the parity commands to the operator (do NOT run them)**

Hand these over verbatim, then STOP and WAIT for the pasted output:

```bash
npm --prefix app/front exec vitest run src/features/platform/PlatformWorkspace.test.tsx
npm --prefix app/front run test
```

Expected result: Platform no longer renders `Intake documental`, `Snapshots de corpus`, `Inventario del proyecto`, or the release-build info panels for pipeline views.

---

### Task 6: Project-Scope Chunking And Embedding/Indexing Without Losing Legacy UI

**Files:**
- Modify: `app/front/src/features/chunking/ChunkingWorkspace.tsx`
- Modify: `app/front/src/features/chunking/useChunkingWorkspace.ts`
- Modify: `app/front/src/features/chunking/chunkingApi.ts`
- Modify: `app/front/src/features/embeddingIndexing/EmbeddingIndexingWorkspace.tsx`
- Modify: `app/front/src/features/embeddingIndexing/useEmbeddingIndexingPipeline.ts`
- Modify: `app/front/src/features/embedding/embeddingApi.ts`
- Modify: `app/front/src/features/indexing/indexingApi.ts`
- Modify: `app/front/src/features/retrieval/retrievalApi.ts`
- Test: existing feature API tests plus `PlatformWorkspace.test.tsx`

**Interfaces:**
- Consumes: existing Legacy stage panels.
- Produces optional datasource injection for stage hooks.

These edits are INJECTION-ONLY: default parameters must keep Legacy behavior
identical (same renders, same calls, same tests). Do not restyle, restructure
JSX, split components, or "improve" the Legacy stage screens while threading
the clients. When Platform runs these screens, the injected clients also feed
`platformRecipeDraft` (chunking/embedding selections) per the resolution
contract.

```ts
export type ChunkingApiClient = {
  loadProfiles: typeof loadChunkingProfiles;
  createRun: typeof createChunkingRun;
  loadRun: typeof loadChunkingRun;
  loadRunDocuments: typeof loadChunkingRunDocuments;
  loadStoredDocuments: typeof loadChunkingStoredDocuments;
  loadValidationOptional: typeof loadChunkingValidationOptional;
  loadParents: typeof loadChunkingParents;
  loadChildren: typeof loadChunkingChildren;
};
```

- [x] **Step 1: Add hook injection with legacy defaults**

Change:

```ts
export function useChunkingWorkspace()
```

to:

```ts
export function useChunkingWorkspace(api: ChunkingApiClient = legacyChunkingApiClient)
```

Replace direct calls such as `loadChunkingProfiles()` with `api.loadProfiles()`.

- [x] **Step 2: Pass the optional client from the component**

Change:

```ts
export function ChunkingWorkspace()
```

to:

```ts
export function ChunkingWorkspace({ api }: { api?: ChunkingApiClient }) {
  const workspace = useChunkingWorkspace(api);
  ...
}
```

Legacy callers pass nothing and keep the same behavior.

- [x] **Step 3: Repeat the datasource pattern for embedding/indexing/retrieval**

Create small client types near `useEmbeddingIndexingPipeline.ts`:

```ts
export type EmbeddingIndexingApiClient = {
  embedding: {
    loadProfiles: typeof loadEmbeddingProfiles;
    loadChunkBundles: typeof loadChunkBundles;
    loadChunkBundleSummary: typeof loadChunkBundleSummary;
    createRun: typeof createEmbeddingRun;
    loadRun: typeof loadEmbeddingRun;
    loadBundle: typeof loadEmbeddingBundle;
    loadBundleChunks: typeof loadEmbeddingBundleChunks;
    loadBundleValidation: typeof loadEmbeddingBundleValidation;
    loadIndexingReadiness: typeof loadEmbeddingIndexingReadiness;
  };
  indexing: {
    loadOverview: typeof loadIndexingOverview;
    createRun: typeof createIndexingRun;
    loadRun: typeof loadIndexingRun;
    loadRunDocuments: typeof loadIndexingRunDocuments;
    loadRunErrors: typeof loadIndexingRunErrors;
    loadRetrievalReadiness: typeof loadIndexingRetrievalReadiness;
    activateRun: typeof activateIndexingRun;
  };
  retrieval: {
    loadProfiles: typeof loadRetrievalProfiles;
    loadStatus: typeof loadRetrievalProfileStatus;
    validate: typeof validateRetrievalProfile;
    search: typeof searchRetrieval;
  };
};
```

Default it to the current global APIs. Platform can then inject a project-aware client as endpoints become available without replacing the UI.

- [x] **Step 4: For Platform, never call global stage APIs as project data**

If a project-scoped endpoint exists in `platformApi`, the Platform client must call it. If an equivalent endpoint does not exist, the Platform datasource must return an explicit empty/error state that says the contract is unavailable for that project; it must still render the Legacy screen and controls, not a different Platform info panel.

Honesty rules for Platform stage data (schemas verified 2026-08-25):

- `ChunkingProfileReadSchema` exposes ONLY `chunking_profile_id`, `strategy`,
  `fingerprint`, and `status`. It has NO token/overlap parameters. Mapping them
  to `0` or any number would fabricate configuration on screen — FORBIDDEN.
  The Platform client returns those numeric fields as `null` plus an explicit
  unavailable marker, and the Legacy panel renders them as
  `N/D - no expuesto por Platform` through the smallest possible optional prop
  change. Never invent thresholds.
- `ProcessingProfileReadSchema` exposes `provider`, `engine`, `fingerprint`,
  `status`: show them verbatim; they are also the metadata used by resolution
  rule 2 of the variant resolver.
- Any stage action without a project-scoped endpoint keeps rendering the Legacy
  control (disabled-with-reason) or returns an explicit unavailable result; the
  screen itself stays identical.

Example shape:

```ts
loadProfiles: async () =>
  (await listChunkingProfiles(projectId)).map((profile) => ({
    profileId: profile.chunking_profile_id,
    strategyLabel: profile.strategy,
    fingerprint: profile.fingerprint,
    status: profile.status,
    childMinTokens: null, // Platform no expone parametros de tokens
    childTargetTokens: null,
    childMaxTokens: null,
    overlapRatio: null,
    overlapMinTokens: null,
    overlapMaxTokens: null,
  })),
```

plus the minimal optional prop that renders numeric cells as `N/D` when the
value is `null`. When the operator launches a chunking run from this screen,
the injected client records the selected profile id into
`platformRecipeDraft` for the variant resolver.

- [x] **Step 5: Deliver the stage-regression commands to the operator (do NOT run them)**

Hand these over verbatim, then STOP and WAIT for the pasted output:

```bash
npm --prefix app/front run test
npm --prefix app/front run build
```

Expected result: Legacy stage tests remain green, and Platform still renders the real stage screens.

> **Task 6 CERRADA (2026-08-26).** Verde del operador: `npm --prefix app/front run
> test` (115/115, 22 files) + `run build` OK.
>
> **Qué se hizo (parity plan Task 6 completo, incluye Plan 02 como prerequisito
> de `useEmbeddingIndexingPipeline.ts`):**
> - **Plan 02 (silent failures):** los 5 `.catch(() => null)` del hook ahora
>   escriben estados de error dedicados (`overviewError`, `bundleValidationError`,
>   `bundleReadinessError`, `indexingErrorsError`, `indexingReadinessError`) con
>   reset al inicio de cada efecto y en las ramas NOT_FOUND. `EmbeddingBundleInspector`
>   / `ActivationPanel` reciben props opcionales `validationError`/`readinessError`
>   y pintan `notice-danger` en vez de omitir la sección; `EmbeddingIndexingWorkspace`
>   cablea las props + banner de `overviewError`. Tests nuevos:
>   `EmbeddingBundleInspector.test.tsx`, `IndexingErrorsPanel.test.tsx`, caso de
>   readiness-error en `ActivationPanel.test.tsx`.
> - **Injection seam (Legacy idéntico por default):** `ChunkingApiClient` +
>   `legacyChunkingApiClient` en `chunkingApi.ts`; `useChunkingWorkspace(api=…)` +
>   `ChunkingWorkspace({api?})`. `EmbeddingIndexingApiClient` (grupos embedding/
>   indexing/retrieval) + default global en `useEmbeddingIndexingPipeline.ts`; las
>   24 llamadas ruteadas por el cliente; deps de `useCallback`/efectos actualizadas.
>   `useEmbeddingRunPolling`/`useIndexingRunPolling` aceptan un `loadRun` inyectado,
>   threaded desde el cliente (audit: si no, el polling pegaría al global).
> - **Step 4 (clientes Platform project-aware, sin fallback global):**
>   `platformStageClients.ts` con `createPlatformChunkingApiClient` (perfiles reales
>   vía `listChunkingProfiles`, token params `null`→`N/D`; `createRun` registra el
>   perfil en `platformRecipeDraft` y falla cerrado; stored/parents/children vacío
>   explícito; validation `null`) y `createPlatformEmbeddingIndexingApiClient`
>   (catálogos vacíos + acciones "No disponible en Platform… corre dentro del build
>   de una release"; `embedding.createRun` registra el perfil). Cableados en
>   `PlatformLegacyPipelineWorkspace` (memoizados por `projectId`) y forwarded por
>   `DashboardPipelineApp` (props opcionales `chunkingApi`/`embeddingIndexingApi`;
>   Legacy pasa `undefined` → default global, comportamiento intacto). Test nuevo
>   `platformStageClients.test.ts` (8 casos).
> - **Cambio de tipo autorizado por el plan:** `ChunkingProfile` token params
>   `number | null`; `chunkingProfileSummary` y `ChunkingProfilePanel` pintan
>   `N/D - no expuesto por Platform`. Legacy siempre trae números → sin cambio.
>
> **Desviación honesta:** el catálogo de perfiles de embedding bajo Platform es
> vacío (la config solo expone `embedding_profile_id`+`enabled`, insuficiente para
> el `EmbeddingProfile` rico Legacy sin inventar ~15 campos). El leg de embedding de
> la receta lo resuelve el variant resolver desde la configuración (Task 4), no la
> pantalla. Regla "nunca inventar" respetada.

---

### Task 7: Remove Claude's Wrong Replacement Screens And Read-Only Copy

**Files:**
- Delete: `app/front/src/features/platform/PlatformReleaseBuildStageInfo.tsx`
- Delete: `app/front/src/features/platform/documents/ProjectInventoryWorkspace.tsx`
- Modify: `app/front/src/features/platform/platformNavigation.ts`
- Modify: `app/front/src/features/platform/documents/DocumentIntakeWorkspace.tsx`
- Modify: `app/front/src/features/platform/documents/documentInventoryConfig.tsx`
- Modify: `app/front/src/features/platform/documents/documentInventoryAdapter.ts`
- Modify: `app/front/src/features/platform/corpus/corpusInventoryConfig.tsx`
- Modify or delete tests that only protect those replacements:
  - `app/front/src/features/platform/documents/documentInventoryAdapter.test.tsx`
  - `app/front/src/features/platform/documents/DocumentIntakeWorkspace.test.tsx`
  - `app/front/src/features/platform/corpus/CorpusSnapshotWorkspace.test.tsx`

**Interfaces:**
- Consumes: passing Task 5/6 tests.
- Produces: no reachable Platform route uses the wrong screens, and no Platform workflow is described as read-only.

- [x] **Step 1: Confirm no imports remain**

Read-only inspection — the agent MAY run this directly (no tests involved):

```bash
rg -n "PlatformReleaseBuildStageInfo|ProjectInventoryWorkspace|DocumentIntakeWorkspace|CorpusSnapshotWorkspace|platform/variants" app/front/src app/front/tsconfig.test.json
```

Expected before deletion: only files scheduled for deletion or kept rollback files mention them, plus the dead tsconfig entry.

- [x] **Step 2: Delete only unreachable replacements**

Use `apply_patch` deletions for:

```text
app/front/src/features/platform/PlatformReleaseBuildStageInfo.tsx
app/front/src/features/platform/documents/ProjectInventoryWorkspace.tsx
```

Also remove the stale `tsconfig.test.json` include entry pointing at the
deleted `src/features/platform/variants/useVariantMatrixWorkspace.ts`
(leftover of the variants refactor; harmless dead glob today, misleading
tomorrow).

Do not delete `DocumentIntakeWorkspace.tsx` or `CorpusSnapshotWorkspace.tsx` in this task unless `rg` proves no test or release flow references them. They can stay as dead-end rollback code until the operator approves cleanup.

- [x] **Step 3: Update tests that asserted the wrong behavior**

Remove assertions such as:

```tsx
expect(screen.getByText(/dentro del build de una release/i)).toBeTruthy();
expect(await screen.findByRole("heading", { name: "Snapshots de corpus" })).toBeTruthy();
expect(await screen.findByRole("heading", { name: "Intake documental" })).toBeTruthy();
```

Replace them with the parity assertions from Task 1.

- [x] **Step 4: Remove stale read-only language**

Read-only inspection — the agent MAY run this directly (no tests involved):

```bash
rg -n "read-only|solo lectura|Solo lectura" app/front/src/features/platform docs/superpowers/plans/2026-08-21-platform-gui-rework-reuse-legacy.md
```

Allowed matches after cleanup:

```text
app/front/src/features/platform/projects/ProjectConfigurationForm.tsx
app/front/src/features/platform/projects/ProjectWorkspace.test.tsx
app/front/src/features/platform/releases/ReleaseDraftForm.tsx
app/front/src/features/platform/releases/useRagReleaseWorkspace.ts
```

Those matches are about server-owned physical target bindings. Remove or rewrite matches that describe `operations`, `review`, `inventory`, `documents`, `corpus`, or the inspector as read-only.

- [x] **Step 5: Deliver the frontend regression commands to the operator (do NOT run them)**

Hand these over verbatim, then STOP and WAIT for the pasted output:

```bash
npm --prefix app/front run test
npm --prefix app/front run build
```

Expected result: the old replacement screens are unreachable, and the build has no unresolved imports.

> **Task 7 CERRADA (2026-08-26).** Verde del operador: `npm --prefix app/front run
> test` + `run build`.
> - Borrados `PlatformReleaseBuildStageInfo.tsx` y `documents/ProjectInventoryWorkspace.tsx`
>   (solo se auto-referenciaban; el boundary test asegura su ausencia en `PlatformWorkspace.tsx`).
> - `tsconfig.test.json`: retirado el glob muerto `variants/useVariantMatrixWorkspace.ts`.
> - Copy read-only: reescritos los comentarios del inspector de documentos/corpus a
>   "inspector de DETALLE — las decisiones operativas viven en la pantalla de Revisión
>   Legacy / la columna de elegibilidad del snapshot builder"; `DocumentIntakeWorkspace`
>   marcado como rollback dead-end. Los matches `read-only`/`solo lectura` restantes son
>   exactamente los permitidos por el plan (target bindings server-owned:
>   `ProjectConfigurationForm`, `ProjectWorkspace.test`, `ReleaseDraftForm`,
>   `useRagReleaseWorkspace`) + las 2 aserciones NEGATIVAS de los tests de frontera.
> - Aserciones de comportamiento incorrecto: ya reemplazadas en Task 5
>   (`PlatformWorkspace.test.tsx` afirma las pantallas Legacy + negativos de las
>   borradas). El heading "Intake documental" del test de `DocumentIntakeWorkspace`
>   prueba el componente rollback aislado (permitido; se conserva como código de reversión).

---

### Task 8: Protect Backend Green Path And Runtime Parity

**Files:**
- Modify: `docs/superpowers/plans/2026-08-21-platform-gui-rework-reuse-legacy.md`
- No release-build backend changes expected beyond Task 3's narrow review-decision contract.

**Interfaces:**
- Consumes: final frontend implementation.
- Produces: documented closure and verification commands.

- [x] **Step 1: Hand the backend green-path command to the operator (do NOT run it)**

Deliver verbatim, then STOP and WAIT for the pasted output:

```bash
npm run python -- -m pytest app/back/tests/rag_platform/test_end_to_end_release_build.py::test_release_build_persiste_rag_release_id -v
```

Expected result: success. If this fails, stop frontend closure and report the backend regression with the exact failing assertion.

- [x] **Step 2: Hand the frontend verification commands to the operator (do NOT run them)**

Deliver verbatim, then STOP and WAIT for the pasted output:

```bash
npm --prefix app/front run test
npm --prefix app/front run build
```

Expected result: success.

- [x] **Step 3: Runtime smoke with project selection (OPERATOR executes; agent only documents results)**

The operator starts the app with the existing project command:

```bash
npm run gui:dev
```

Manual smoke:

```text
1. Login with the operator test account.
2. Open RAG Platform.
3. Select project SST General.
4. Click Operacion. Confirm the Legacy operation screen appears and the project chip says SST General.
5. Click Revision. Confirm the Legacy review table/inspector appears, not Snapshots de corpus.
6. Click Inventario. Confirm the Legacy inventory table/inspector appears, not Inventario del proyecto.
7. Click Chunking. Confirm the Legacy chunking launch/run/parents/children layout appears, not an info panel.
8. Click Embedding/Indexing. Confirm the Legacy embedding/indexing/activation/retrieval layout appears.
9. Click RAG / Releases. Confirm release lifecycle still works with rag_release_id.
```

- [x] **Step 4: Update the older plan with the correction**

Append a dated note to `2026-08-21-platform-gui-rework-reuse-legacy.md`:

```markdown
> **Correction 2026-08-25:** The previous Phase 8 direction reused neutral Platform replacements and relabeled them as Legacy views. It also treated missing review-decision wiring as a reason to make Platform inspectors read-only. The corrected implementation mounts the actual Legacy pipeline UI through `DashboardPipelineApp` and a project-scoped Platform datasource. Platform is operational: `Aprobar`/`Rechazar` persist through the Platform review-decision contract, snapshot creation moves to `RAG / Releases`, and read-only language applies only to server-owned physical target bindings or immutable release artifacts.
```

- [x] **Step 5: Final self-review**

Check:

```bash
rg -n "DocumentIntakeWorkspace|CorpusSnapshotWorkspace|ProjectInventoryWorkspace|PlatformReleaseBuildStageInfo" app/front/src/features/platform/PlatformWorkspace.tsx app/front/src/features/platform
rg -n "indexing_target_id|actor_id|idx_vec_|target_bindings" app/front/src/features/platform app/front/src/features/dashboard
git diff --check
git status --short
```

Expected result: `PlatformWorkspace.tsx` does not import replacement pipeline screens; frontend does not expose physical targets or actor fields; whitespace check is clean; git status shows only expected files.

> **Task 8 CERRADA (2026-08-27) — PLAN COMPLETO.** Verde del operador:
> - Backend green-path gate: `test_end_to_end_release_build.py::test_release_build_persiste_rag_release_id` **PASSED** (180s).
> - Frontend: `npm --prefix app/front run test` **verde** (tras endurecer 2 tests
>   flaky de `OperatorApp.test.tsx` — carrera de timing bajo carga: esperaban el
>   heading, presente también en el estado "Comprobando sesión…", y leían el label
>   sync; ahora esperan el campo/botón del formulario con `findBy*`. No se tocó
>   código de operador ni de seguridad). `npm --prefix app/front run build` **OK**.
> - Self-review (Step 5): `PlatformWorkspace.tsx` no importa pantallas de reemplazo;
>   sin fuga de target físico/actor en runtime (solo `binding_key` lógico + catálogo
>   OpenAPI generado inerte). Único hit de `git diff --check`: trailing space en
>   `in_memory/repositories.py:518`, trabajo paralelo PROTEGIDO del operador (no de
>   este plan) — no tocado.
> - **Fix de layout runtime (2026-08-27):** las 6 vistas se veían amontonadas porque
>   `DashboardPipelineApp` monta el MISMO shell Legacy (`.app-shell`, grid de 2
>   columnas sidebar+workspace) y Platform oculta el sidebar → el workspace caía en
>   la columna de 224px. Fix: `app-shell--no-sidebar` (1 columna) cuando el sidebar
>   está oculto, sin dejar de ser el mismo front. Legacy con sidebar queda idéntico.
> - **Nota de seguridad (fuera de scope, docs/revision):** `secrets.env` está
>   gitignored y NO trackeado → sin fuga en git. C1/C2 (rotar credenciales + sintaxis
>   `:47`) y Plan 04/06/07 siguen pendientes en su propio backlog.
>
> **Definition of Done cumplida:** Platform monta el pipeline Legacy real por
> `project_id`, `Aprobar`/`Rechazar` persisten (`approved_after_review`/`blocked`),
> variante desde `resolveOrCreatePlatformRagVariant`, snapshots+releases en
> `RAG / Releases`, lane Legacy intacta, backend E2E verde, sin fuga de targets/actor,
> metadata ausente = no-disponible (nunca inventada), read-only solo para bindings
> server-owned. Sin commit/push (política).

---

## Definition Of Done

- RAG Platform shows project management first.
- After selecting a project, Platform `Operacion`, `Revision`, `Inventario`, `Chunking`, and `Embedding/Indexing` render the actual Legacy pipeline UI, not re-labeled Platform screens.
- Platform pipeline data comes from `/api/platform/*` using the selected `project_id`.
- Legacy global pipeline remains available and behaviorally unchanged.
- Platform `Revision` exposes real Legacy `Aprobar`/`Rechazar`; approved maps to `approved_after_review` and rejected maps to `blocked` in the Platform review-decision contract.
- Every `rag_variant_id` used by normalize or release drafting originates from `resolveOrCreatePlatformRagVariant` (variant-matrix reconfirmation) or from variants listed for the project; the persisted `selectedRagVariantId` preference is display cache only.
- The recipe legs come from the operator's real configuration inside the Legacy screens (provider/route in Operacion, chunking profile in Chunking, embedding profile in Embedding/Indexing); an incomplete or ambiguous recipe fails closed naming the screen and options — never guesses.
- `RAG / Releases` owns corpus snapshot creation plus release management and keeps `corpus_snapshot_id` and `rag_release_id` visible.
- The backend E2E release build test named by the operator stays green.
- `npm --prefix app/front run test` and `npm --prefix app/front run build` pass.
- No physical target, table name, secret, vector, raw chunk, or `actor_id` is exposed in frontend code or persisted preferences.
- Missing Platform metadata appears as unavailable, not invented.
- Read-only language is allowed only for server-controlled fields such as physical target bindings. It must never describe the Platform workflow, review flow, inventory flow, or release management surface.
- The older plan is updated with a correction note explaining Claude's wrong direction, the anti-read-only correction, and the replacement strategy.

## Self-Review

- Context coverage: the plan now explains the product intent, why Platform is an operational multi-project control plane, and why the accepted solution is the same Legacy GUI JS plus Platform datasource/identity context instead of cosmetic visual reuse.
- Spec coverage: the plan uses the Fase 7 `/api/platform/*` contracts, preserves Fase 7 security invariants, keeps Legacy compatible, and implements the operator request for the same Legacy screens under Platform.
- Fault coverage: the plan explicitly documents Claude's wrong interpretation: reusing visual elements and labels while mounting different Platform screens. Task 1 changes the tests that protected that behavior; Task 3 fixes the operational review-decision gap; Task 5 replaces routing; Task 7 removes the wrong info/replacement screens and read-only copy from Platform routing.
- Identity coverage: `project_id`, `rag_variant_id`, `corpus_snapshot_id`, and `rag_release_id` each have a defined lifecycle boundary so implementers do not force release identifiers into early project pipeline screens or hide release lifecycle inside `Revision`.
- Type consistency: `DashboardPipelineDataSource`, `DashboardPipelineApp`, `SubmitRevisionReviewDecisionUseCase`, `createPlatformDashboardDataSource`, and `PlatformLegacyPipelineWorkspace` signatures are defined before use.
- Test coverage: each behavior-changing task has a focused red/green check plus the affected frontend/backend regression; final closure includes the backend E2E named by the operator.
