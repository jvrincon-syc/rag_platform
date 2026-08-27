import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { RagReleaseWorkspace } from "./RagReleaseWorkspace.js";
import { PlatformProjectProvider } from "../PlatformProjectContext.js";
import { writePlatformPreferences } from "../platformPersistence.js";
import { DEFAULT_PLATFORM_PREFERENCES } from "../platformState.js";
import * as platformApi from "../platformApi.js";
import type {
  CorpusSnapshot,
  ProjectConfiguration,
  Release,
  ReleaseBuildAccepted,
  ReleaseBuildStatus,
  Variant,
} from "../platformTypes.js";

// Cliente HTTP mockeado en el límite de red: ningún test toca fetch. El build es
// asíncrono (ADR-010): `buildRelease` encola y `getReleaseBuildStatus` se pollea.
vi.mock("../platformApi.js", () => ({
  listAllReleases: vi.fn(),
  listAllVariants: vi.fn(),
  listAllCorpusSnapshots: vi.fn(),
  listAllDocuments: vi.fn(),
  createCorpusSnapshot: vi.fn(),
  getConfiguration: vi.fn(),
  getRelease: vi.fn(),
  createReleaseDraft: vi.fn(),
  buildRelease: vi.fn(),
  getReleaseBuildStatus: vi.fn(),
  validateRelease: vi.fn(),
  publishRelease: vi.fn(),
  retireRelease: vi.fn(),
}));

const api = vi.mocked(platformApi);

function makeVariant(overrides: Partial<Variant> = {}): Variant {
  return {
    rag_variant_id: "var_1",
    project_id: "proj_alpha",
    chunking_profile_id: "chunk_1",
    processing_profile_id: "proc_1",
    embedding_profile_id: "emb_1",
    semantic_recipe_fingerprint: "fp_1",
    state: "buildable",
    created_at: "2026-01-01T00:00:00Z",
    ...overrides,
  };
}

function makeSnapshot(overrides: Partial<CorpusSnapshot> = {}): CorpusSnapshot {
  return {
    corpus_snapshot_id: "corpus_1",
    project_id: "proj_alpha",
    manifest_hash: "sha256:abcd",
    document_count: 3,
    documents: [],
    created_at: "2026-01-01T00:00:00Z",
    ...overrides,
  };
}

function makeConfiguration(overrides: Partial<ProjectConfiguration> = {}): ProjectConfiguration {
  return {
    corpus_organization_policy: "source-folders-v1",
    created_at: "2026-01-01T00:00:00Z",
    document_types: [],
    embedding_profiles: [],
    target_bindings: [{ binding_key: "primary", embedding_profile_id: "emb_1" }],
    version: 1,
    ...overrides,
  };
}

function makeRelease(overrides: Partial<Release> = {}): Release {
  return {
    rag_release_id: "rel_1",
    project_id: "proj_alpha",
    rag_variant_id: "var_1",
    corpus_snapshot_id: "corpus_1",
    target_binding_key: "primary",
    configuration_version: 1,
    release_number: 1,
    state: "draft",
    release_manifest_hash: null,
    validated_at: null,
    reason: null,
    created_at: "2026-01-02T00:00:00Z",
    created_by: "op",
    ...overrides,
  };
}

function makeAccepted(overrides: Partial<ReleaseBuildAccepted> = {}): ReleaseBuildAccepted {
  return {
    build_job_id: "bjob_1",
    rag_release_id: "rel_1",
    state: "queued",
    ...overrides,
  };
}

function makeBuildStatus(overrides: Partial<ReleaseBuildStatus> = {}): ReleaseBuildStatus {
  return {
    build_job_id: "bjob_1",
    rag_release_id: "rel_1",
    state: "succeeded",
    revisions_built: 3,
    reused_stages: 1,
    built_stages: 2,
    error_code: null,
    error_message: null,
    ...overrides,
  };
}

// Los clientes `listAll*` devuelven el listado completo (array plano), no una página.
function selectInStorage(projectId: string, releaseId?: string): void {
  writePlatformPreferences({
    ...DEFAULT_PLATFORM_PREFERENCES,
    selectedProjectId: projectId,
    selectedRagReleaseId: releaseId ?? null,
  });
}

function renderRagReleaseWorkspace() {
  return render(
    <PlatformProjectProvider>
      <RagReleaseWorkspace />
    </PlatformProjectProvider>,
  );
}

beforeEach(() => {
  window.localStorage.clear();
  api.listAllReleases.mockResolvedValue([]);
  api.listAllVariants.mockResolvedValue([makeVariant()]);
  api.listAllCorpusSnapshots.mockResolvedValue([makeSnapshot()]);
  api.listAllDocuments.mockResolvedValue([]);
  api.createCorpusSnapshot.mockResolvedValue(makeSnapshot());
  api.getConfiguration.mockResolvedValue(makeConfiguration());
  api.getRelease.mockResolvedValue(makeRelease());
  api.createReleaseDraft.mockResolvedValue(makeRelease());
  api.buildRelease.mockResolvedValue(makeAccepted());
  api.getReleaseBuildStatus.mockResolvedValue(makeBuildStatus());
  api.validateRelease.mockResolvedValue(makeRelease({ state: "validated" }));
  api.publishRelease.mockResolvedValue(makeRelease({ state: "published" }));
  api.retireRelease.mockResolvedValue(makeRelease({ state: "retired", reason: "obsoleta" }));
});

describe("RagReleaseWorkspace", () => {
  it("monta el constructor de snapshot de corpus antes del draft (Task 5)", async () => {
    selectInStorage("proj_alpha");
    api.listAllDocuments.mockResolvedValue([
      {
        source_document_revision_id: "srev_1",
        logical_document_id: "ldoc_1",
        source_relpath: "manuales/proc.pdf",
        file_size: 1024,
        raw_registered: true,
        normalized_registered: true,
        review_state: "processed",
        processing_status: "normalized",
        uploaded_at: "2026-01-01T00:00:00Z",
      },
    ]);
    renderRagReleaseWorkspace();

    expect(await screen.findByRole("button", { name: /Crear snapshot/i })).toBeTruthy();
    expect(screen.getByRole("button", { name: /Crear draft/i })).toBeTruthy();
  });

  it("(a) crea un draft con el body lógico exacto", async () => {
    selectInStorage("proj_alpha");
    const user = userEvent.setup();
    renderRagReleaseWorkspace();

    const createButton = await screen.findByRole("button", { name: /Crear draft/ });
    // Los selectores se siembran tras la carga; espera a que el botón se habilite.
    await waitFor(() => expect(createButton).toHaveProperty("disabled", false));
    await user.click(createButton);

    await waitFor(() => expect(api.createReleaseDraft).toHaveBeenCalledTimes(1));
    const body = api.createReleaseDraft.mock.calls[0][0];
    expect(body).toEqual({
      corpus_snapshot_id: "corpus_1",
      rag_variant_id: "var_1",
      target_binding_key: "primary",
    });
    // Nunca IDs físicos ni target_bindings mutados.
    expect("indexing_target_id" in body).toBe(false);
  });

  it("(b) build encola y, al pollear succeeded, muestra el informe", async () => {
    selectInStorage("proj_alpha", "rel_1");
    api.listAllReleases.mockResolvedValue([makeRelease()]);
    const user = userEvent.setup();
    renderRagReleaseWorkspace();

    await user.click(await screen.findByRole("button", { name: /Construir \(build\)/ }));

    // El build NO bloquea: se encola y el estado se observa por polling.
    await waitFor(() => expect(api.getReleaseBuildStatus).toHaveBeenCalledWith("rel_1", expect.anything()));
    // Al alcanzar `succeeded`, el informe se renderiza con las tres métricas.
    expect(await screen.findByText("Revisiones construidas")).toBeTruthy();
    expect(screen.getByText("Etapas construidas")).toBeTruthy();
    expect(screen.getByText("Etapas reutilizadas")).toBeTruthy();
    // El resumen accesible incluye los valores construido/reutilizado.
    expect(
      await screen.findByText(
        /Build completado: 3 revisión\(es\), 2 etapa\(s\) construida\(s\), 1 reutilizada/,
      ),
    ).toBeTruthy();
    // Encolado una sola vez (no se re-encola por render ni por cada poll).
    expect(api.buildRelease).toHaveBeenCalledTimes(1);
  });

  it("(b2) build → poll failed muestra el error del proveedor sin ocultarlo", async () => {
    selectInStorage("proj_alpha", "rel_1");
    api.listAllReleases.mockResolvedValue([makeRelease()]);
    api.getReleaseBuildStatus.mockResolvedValue(
      makeBuildStatus({
        state: "failed",
        revisions_built: null,
        reused_stages: null,
        built_stages: null,
        error_code: "RELEASE_BUILD_TOO_LARGE",
        error_message: "El snapshot excede el límite.",
      }),
    );
    const user = userEvent.setup();
    renderRagReleaseWorkspace();

    await user.click(await screen.findByRole("button", { name: /Construir \(build\)/ }));

    // El fallo se surface fail-closed en DOS sitios (notice de acción + panel del
    // informe de build); ambos son visibles a propósito, por eso getAllByText.
    const failures = await screen.findAllByText(/Build fallido \(RELEASE_BUILD_TOO_LARGE\)/);
    expect(failures.length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText(/El snapshot excede el límite/).length).toBeGreaterThanOrEqual(1);
  });

  it("(b3) getReleaseBuildStatus null (sin build) no finge éxito", async () => {
    selectInStorage("proj_alpha", "rel_1");
    api.listAllReleases.mockResolvedValue([makeRelease()]);
    // El backend devuelve null hasta que aparece el job; el loop sigue en curso.
    api.getReleaseBuildStatus.mockResolvedValue(null);
    const user = userEvent.setup();
    renderRagReleaseWorkspace();

    await user.click(await screen.findByRole("button", { name: /Construir \(build\)/ }));

    // En curso (encolado), nunca "Revisiones construidas" ni un éxito aparente.
    expect(await screen.findByText(/Build encolado \(job bjob_1\)/)).toBeTruthy();
    expect(screen.queryByText("Revisiones construidas")).toBeNull();
  });

  it("(c) ofrece solo las acciones válidas por estado", async () => {
    // draft → Build + Validate; no Publicar/Retirar.
    selectInStorage("proj_alpha", "rel_1");
    api.listAllReleases.mockResolvedValue([makeRelease({ state: "draft" })]);
    const draft = renderRagReleaseWorkspace();
    expect(await screen.findByRole("button", { name: /Construir \(build\)/ })).toBeTruthy();
    expect(screen.getByRole("button", { name: /Validar/ })).toBeTruthy();
    expect(screen.queryByRole("button", { name: /Publicar/ })).toBeNull();
    expect(screen.queryByRole("button", { name: /Retirar/ })).toBeNull();
    draft.unmount();

    // validated → Publicar + Retirar; no Build/Validate.
    api.listAllReleases.mockResolvedValue([makeRelease({ state: "validated" })]);
    const validated = renderRagReleaseWorkspace();
    expect(await screen.findByRole("button", { name: /Publicar/ })).toBeTruthy();
    expect(screen.getByRole("button", { name: /Retirar/ })).toBeTruthy();
    expect(screen.queryByRole("button", { name: /Construir \(build\)/ })).toBeNull();
    expect(screen.queryByRole("button", { name: /Validar/ })).toBeNull();
    validated.unmount();

    // published → solo Retirar.
    api.listAllReleases.mockResolvedValue([makeRelease({ state: "published" })]);
    renderRagReleaseWorkspace();
    expect(await screen.findByRole("button", { name: /Retirar/ })).toBeTruthy();
    expect(screen.queryByRole("button", { name: /Publicar/ })).toBeNull();
  });

  it("(d) 409 IDEMPOTENCY_KEY_CONFLICT: muestra conflicto y no reintenta solo", async () => {
    selectInStorage("proj_alpha", "rel_1");
    api.listAllReleases.mockResolvedValue([makeRelease()]);
    api.buildRelease.mockRejectedValue({ status: 409, code: "IDEMPOTENCY_KEY_CONFLICT" });
    const user = userEvent.setup();
    renderRagReleaseWorkspace();

    await user.click(await screen.findByRole("button", { name: /Construir \(build\)/ }));

    expect(await screen.findByText(/Conflicto de clave de idempotencia/)).toBeTruthy();
    // No hay reintento automático: la acción se llamó exactamente una vez.
    expect(api.buildRelease).toHaveBeenCalledTimes(1);
    // El encolado falló: no se arranca el polling (fail-closed, sin éxito aparente).
    expect(api.getReleaseBuildStatus).not.toHaveBeenCalled();
  });

  it("(e) 409 INVALID_RELEASE_TRANSITION: refetch de la release", async () => {
    selectInStorage("proj_alpha", "rel_1");
    api.listAllReleases.mockResolvedValue([makeRelease()]);
    api.validateRelease.mockRejectedValue({ status: 409, code: "INVALID_RELEASE_TRANSITION" });
    api.getRelease.mockResolvedValue(makeRelease({ state: "validated" }));
    const user = userEvent.setup();
    renderRagReleaseWorkspace();

    await user.click(await screen.findByRole("button", { name: /Validar/ }));

    await waitFor(() => expect(api.getRelease).toHaveBeenCalledWith("rel_1"));
  });

  it("(f) retirar exige un motivo explícito", async () => {
    selectInStorage("proj_alpha", "rel_1");
    api.listAllReleases.mockResolvedValue([makeRelease({ state: "published" })]);
    const user = userEvent.setup();
    renderRagReleaseWorkspace();

    await user.click(await screen.findByRole("button", { name: /Retirar/ }));
    // El botón de confirmación está deshabilitado sin motivo.
    const confirm = screen.getByRole("button", { name: /Confirmar retiro/ });
    expect(confirm).toHaveProperty("disabled", true);

    await user.type(screen.getByLabelText(/Motivo del retiro/), "obsoleta");
    expect(screen.getByRole("button", { name: /Confirmar retiro/ })).toHaveProperty(
      "disabled",
      false,
    );
    await user.click(screen.getByRole("button", { name: /Confirmar retiro/ }));

    await waitFor(() => expect(api.retireRelease).toHaveBeenCalledTimes(1));
    expect(api.retireRelease.mock.calls[0][1]).toEqual({ reason: "obsoleta" });
  });

  it("(g) D7: el reintento de la misma intención reusa la clave; una nueva intención acuña otra", async () => {
    selectInStorage("proj_alpha", "rel_1");
    api.listAllReleases.mockResolvedValue([makeRelease()]);
    // 1er intento: fallo recuperable al ENCOLAR (no rota clave); 2º y 3º: encolan.
    api.buildRelease
      .mockRejectedValueOnce({ status: 503, code: "POSTGRES_UNAVAILABLE" })
      .mockResolvedValueOnce(makeAccepted())
      .mockResolvedValueOnce(makeAccepted());
    const user = userEvent.setup();
    renderRagReleaseWorkspace();

    const buildButton = await screen.findByRole("button", { name: /Construir \(build\)/ });

    // Intento 1 (falla) → intento 2 (reintento de la MISMA intención, éxito).
    await user.click(buildButton);
    await screen.findByText(/error|falló|Ocurrio/i);
    await user.click(buildButton);
    await screen.findByText("Revisiones construidas");

    await waitFor(() => expect(api.buildRelease).toHaveBeenCalledTimes(2));
    const key1 = api.buildRelease.mock.calls[0][1]?.idempotencyKey;
    const key2 = api.buildRelease.mock.calls[1][1]?.idempotencyKey;
    expect(key1).toBeTruthy();
    expect(key2).toBe(key1); // reintento reusa la clave

    // Nueva intención tras respuesta terminal (éxito) → clave distinta.
    await user.click(buildButton);
    await waitFor(() => expect(api.buildRelease).toHaveBeenCalledTimes(3));
    const key3 = api.buildRelease.mock.calls[2][1]?.idempotencyKey;
    expect(key3).toBeTruthy();
    expect(key3).not.toBe(key2);
  });

  it("sin proyecto no llama a la API y muestra estado direccional", async () => {
    renderRagReleaseWorkspace();
    expect(
      await screen.findByText(/Selecciona un proyecto para gestionar sus releases/),
    ).toBeTruthy();
    expect(api.listAllReleases).not.toHaveBeenCalled();
    expect(api.getConfiguration).not.toHaveBeenCalled();
  });
});
