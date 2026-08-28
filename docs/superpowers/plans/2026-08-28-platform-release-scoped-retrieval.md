# Platform Release-Scoped Retrieval Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the legacy Retrieval panel inside RAG Platform with a release-scoped testing surface that lets operators choose a rag variant and one of its releases, while keeping production chatbot dispatch published-only.

**Architecture:** Add a Platform-specific retrieval testing surface under `/api/platform/retrieval` that reuses the existing release-scoped retrieval engine already introduced for chatbot dispatch. Keep release-state policy outside the shared retrieval adapter so Platform can test `draft`, `validated`, and `published` releases, while chatbot production remains `published`-only; then replace the frontend’s profile-based panel with a variant-first, release-scoped operator workflow that mirrors the grouped release map.

**Tech Stack:** FastAPI, Pydantic, Python pytest, React, TypeScript, Vitest, existing platform shared API client and CSS tokens.

**Spec:** `docs/superpowers/specs/2026-08-28-platform-release-scoped-retrieval-design.md`

## Global Constraints

- Replace the Retrieval panel inside `RAG Platform` with a release-scoped testing workflow.
- Let operators choose `rag variant` and `rag release` directly.
- Allow testing against `draft`, `validated`, and `published` releases inside Platform.
- Keep production chatbot dispatch restricted to `published` releases only.
- Make the release catalog clearly show which releases belong to which variant.
- Preserve fail-closed behavior when the chosen release has no resolvable retrieval lane or no evidence.
- Do not change the production chatbot API contract.
- Do not auto-activate legacy `retrieval_profiles` when building or publishing a release.
- Do not merge Platform release testing with the legacy Retrieval lane.
- Do not invent a global active release concept that the backend does not own.

---

### Task 1: Backend Platform Retrieval Surface

**Files:**
- Create: `app/back/src/rag_platform/application/release_scoped_retrieval_service.py`
- Modify: `app/back/src/rag_platform/application/services.py`
- Modify: `app/back/src/rag_platform/api/schemas.py`
- Modify: `app/back/src/rag_platform/api/router.py`
- Modify: `app/back/src/api/dependencies.py`
- Test: `app/back/tests/rag_platform/test_platform_api.py`
- Regression check: `app/back/tests/chatbot/test_chatbot_api.py`

**Interfaces:**
- Consumes: `ChatbotReleaseRetrievalPort.search(project_id, rag_variant_id, rag_release_id, question, top_k)` from `app/back/src/chatbot/application/ports.py`
- Consumes: `services.list_project_variants.execute(project_id, actor=actor)` and `services.list_project_releases.execute(project_id, actor=actor)` from `RagPlatformServices`
- Produces: `PlatformReleaseRetrievalService.list_targets(project_id: PlatformId, actor: PlatformActor) -> PlatformRetrievalTargetsView`
- Produces: `PlatformReleaseRetrievalService.validate(project_id: PlatformId, rag_variant_id: PlatformId, rag_release_id: PlatformId, actor: PlatformActor) -> PlatformReleaseRetrievalValidation`
- Produces: `PlatformReleaseRetrievalService.search(project_id: PlatformId, rag_variant_id: PlatformId, rag_release_id: PlatformId, query: str, top_k: int, actor: PlatformActor) -> PlatformReleaseRetrievalSearchResult`
- Produces: `GET /api/platform/retrieval/targets?project_id=...`
- Produces: `POST /api/platform/retrieval/validate`
- Produces: `POST /api/platform/retrieval/search`

- [ ] **Step 1: Write the failing backend tests**

```python
def test_platform_retrieval_targets_group_releases_by_variant(client: TestClient) -> None:
    project_id, variant_id, release_id = _seed_release(client, state="draft")
    response = client.get(f"/api/platform/retrieval/targets?project_id={project_id}")
    assert response.status_code == 200
    payload = response.json()
    assert payload["project_id"] == project_id
    assert payload["variants"][0]["rag_variant_id"] == variant_id
    assert payload["variants"][0]["releases"][0]["rag_release_id"] == release_id
    assert payload["variants"][0]["releases"][0]["operator_testable"] is True


def test_platform_retrieval_validate_accepts_validated_release(client: TestClient) -> None:
    project_id, variant_id, release_id = _seed_release(client, state="validated")
    response = client.post(
        "/api/platform/retrieval/validate",
        json={
            "project_id": project_id,
            "rag_variant_id": variant_id,
            "rag_release_id": release_id,
        },
    )
    assert response.status_code == 200
    assert response.json()["rag_release_id"] == release_id


def test_platform_retrieval_rejects_retired_release(client: TestClient) -> None:
    project_id, variant_id, release_id = _seed_release(client, state="retired")
    response = client.post(
        "/api/platform/retrieval/search",
        json={
            "project_id": project_id,
            "rag_variant_id": variant_id,
            "rag_release_id": release_id,
            "query": "politica",
            "top_k": 3,
        },
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "PLATFORM_RELEASE_NOT_OPERATOR_TESTABLE"
```

- [ ] **Step 2: Run the focused backend tests to verify they fail**

Run: `& 'C:/venvs/chatbot-sst/Scripts/python.exe' -m pytest app/back/tests/rag_platform/test_platform_api.py -q`

Expected: FAIL because `/api/platform/retrieval/*` routes and schemas do not exist yet.

- [ ] **Step 3: Write the minimal backend implementation**

```python
@dataclass(frozen=True)
class PlatformReleaseRetrievalService:
    releases: RagReleaseQueryPort
    variants: RagVariantQueryPort
    release_retrieval: ChatbotReleaseRetrievalPort

    def _assert_operator_testable(self, release: RagRelease) -> None:
        if release.state.value not in {"draft", "validated", "published"}:
            raise PlatformReleaseNotOperatorTestable(release.rag_release_id.value, release.state.value)

    def search(...):
        release = self._load_release(...)
        self._assert_operator_testable(release)
        return self.release_retrieval.search(
            project_id=release.project_id.value,
            rag_variant_id=release.rag_variant_id.value,
            rag_release_id=release.rag_release_id.value,
            question=query,
            top_k=top_k,
        )
```

```python
@router.get("/retrieval/targets", response_model=PlatformRetrievalTargetsSchema)
def list_platform_retrieval_targets(...):
    return targets_to_schema(
        services.platform_release_retrieval.list_targets(
            _parse_id(IdentityKind.PROJECT, project_id),
            actor=actor,
        )
    )


@router.post("/retrieval/search", response_model=PlatformRetrievalSearchResultSchema)
def platform_retrieval_search(payload: PlatformRetrievalSearchRequestSchema, ...):
    return platform_retrieval_search_to_schema(
        services.platform_release_retrieval.search(
            project_id=_parse_id(IdentityKind.PROJECT, payload.project_id),
            rag_variant_id=_parse_id(IdentityKind.RAG_VARIANT, payload.rag_variant_id),
            rag_release_id=_parse_id(IdentityKind.RAG_RELEASE, payload.rag_release_id),
            query=payload.query,
            top_k=payload.top_k,
            actor=actor,
        )
    )
```

- [ ] **Step 4: Run backend regression tests**

Run: `& 'C:/venvs/chatbot-sst/Scripts/python.exe' -m pytest app/back/tests/rag_platform/test_platform_api.py app/back/tests/chatbot/test_chatbot_api.py -q`

Expected: PASS, including the existing chatbot regression that still rejects non-`published` production releases.

- [ ] **Step 5: Commit or record the blocked Git state**

```bash
git add app/back/src/rag_platform/application/release_scoped_retrieval_service.py \
        app/back/src/rag_platform/application/services.py \
        app/back/src/rag_platform/api/schemas.py \
        app/back/src/rag_platform/api/router.py \
        app/back/src/api/dependencies.py \
        app/back/tests/rag_platform/test_platform_api.py \
        app/back/tests/chatbot/test_chatbot_api.py
git commit -m "feat: add platform release-scoped retrieval api"
```

If `git commit` is blocked by the pre-existing `.git/index.lock`, record the exact command failure in the task report and stop after keeping the tested file diffs intact.

### Task 2: Frontend Release-Scoped Retrieval Workspace

**Files:**
- Modify: `app/front/src/features/platform/platformApi.ts`
- Modify: `app/front/src/features/platform/platformTypes.ts`
- Modify: `app/front/src/features/platform/platformOpenApi.generated.ts`
- Create: `app/front/src/features/platform/releases/usePlatformReleaseRetrieval.ts`
- Create: `app/front/src/features/platform/releases/ReleaseScopedRetrievalPanel.tsx`
- Modify: `app/front/src/features/platform/releases/RagReleaseWorkspace.tsx`
- Modify: `app/front/src/features/platform/releases/ReleaseHistory.tsx`
- Modify: `app/front/src/styles/platform.css`
- Test: `app/front/src/features/platform/releases/RagReleaseWorkspace.test.tsx`
- Test: `app/front/src/features/platform/platformApi.test.mjs`

**Interfaces:**
- Consumes: `listPlatformRetrievalTargets(projectId: string) -> Promise<PlatformRetrievalTargets>`
- Consumes: `validatePlatformReleaseRetrieval(body: PlatformReleaseRetrievalValidateRequest) -> Promise<PlatformReleaseRetrievalValidation>`
- Consumes: `searchPlatformReleaseRetrieval(body: PlatformReleaseRetrievalSearchRequest) -> Promise<PlatformReleaseRetrievalSearchResult>`
- Consumes: `selectedReleaseId`, `selectRelease`, and release catalog data from `useRagReleaseWorkspace`
- Produces: `usePlatformReleaseRetrieval(args) -> { targets, selectedVariantId, selectedReleaseId, validationResult, searchResult, ... }`
- Produces: a replacement for the legacy retrieval profile-based panel inside `RagReleaseWorkspace`

- [ ] **Step 1: Write the failing frontend tests**

```tsx
it("permite elegir variant y release testable para retrieval desde Platform", async () => {
  renderRagReleaseWorkspace();
  expect(await screen.findByRole("heading", { name: /Retrieval por release/i })).toBeTruthy();
  expect(screen.getByText(/Prueba interna \+ chatbot producción/i)).toBeTruthy();
});

it("limpia resultados viejos cuando cambia la variant seleccionada", async () => {
  renderRagReleaseWorkspace();
  await user.click(await screen.findByRole("button", { name: /Buscar evidencia/i }));
  await user.selectOptions(screen.getByLabelText(/RAG variant/i), "var_beta");
  expect(screen.queryByText(/Top K/)).toBeTruthy();
  expect(screen.queryByText(/doc-1/)).toBeNull();
});

it("deshabilita releases retired y failed en retrieval de Platform", async () => {
  renderRagReleaseWorkspace();
  expect(await screen.findByText(/visible pero no testeable/i)).toBeTruthy();
});
```

- [ ] **Step 2: Run the focused frontend tests to verify they fail**

Run: `node node_modules/vitest/vitest.mjs run src/features/platform/releases/RagReleaseWorkspace.test.tsx`

Expected: FAIL because the workspace still renders the legacy retrieval profile panel.

- [ ] **Step 3: Write the minimal frontend implementation**

```ts
export function listPlatformRetrievalTargets(projectId: string) {
  return getJson<PlatformRetrievalTargets>(
    `${BASE}/retrieval/targets${buildQuery({ project_id: projectId })}`,
  );
}

export function validatePlatformReleaseRetrieval(body: PlatformReleaseRetrievalValidateRequest) {
  return postJson<PlatformReleaseRetrievalValidation>(`${BASE}/retrieval/validate`, body);
}
```

```tsx
<section className="panel" aria-label="Retrieval por release">
  <div className="panel-heading">
    <div>
      <h2>Retrieval por release</h2>
      <span>Prueba operativa sobre la release seleccionada, separada del chatbot published-only.</span>
    </div>
  </div>
  <ReleaseScopedRetrievalPanel
    projectId={workspace.projectId}
    releases={data.releases}
    variants={data.variants}
    selectedRelease={workspace.selectedRelease}
  />
</section>
```

- [ ] **Step 4: Run frontend regression checks**

Run: `node node_modules/vitest/vitest.mjs run src/features/platform/releases/RagReleaseWorkspace.test.tsx`

Run: `node node_modules/vitest/vitest.mjs run src/features/platform/platformApi.test.mjs`

Run: `node node_modules/typescript/bin/tsc -p tsconfig.test.json --noEmit`

Run: `node scripts/build.mjs`

Expected: PASS, with the workspace now clearly grouped by variant and the new retrieval panel targeting release-scoped Platform endpoints.

- [ ] **Step 5: Commit or record the blocked Git state**

```bash
git add app/front/src/features/platform/platformApi.ts \
        app/front/src/features/platform/platformTypes.ts \
        app/front/src/features/platform/platformOpenApi.generated.ts \
        app/front/src/features/platform/releases/usePlatformReleaseRetrieval.ts \
        app/front/src/features/platform/releases/ReleaseScopedRetrievalPanel.tsx \
        app/front/src/features/platform/releases/RagReleaseWorkspace.tsx \
        app/front/src/features/platform/releases/ReleaseHistory.tsx \
        app/front/src/styles/platform.css \
        app/front/src/features/platform/releases/RagReleaseWorkspace.test.tsx \
        app/front/src/features/platform/platformApi.test.mjs
git commit -m "feat: add platform release-scoped retrieval workspace"
```

If `git commit` is blocked by the pre-existing `.git/index.lock`, record the exact command failure in the task report and stop after keeping the tested file diffs intact.
