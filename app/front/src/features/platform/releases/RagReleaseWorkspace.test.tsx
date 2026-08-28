import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { RagReleaseWorkspace } from "./RagReleaseWorkspace.js";
import { PlatformProjectProvider } from "../PlatformProjectContext.js";
import { writePlatformPreferences } from "../platformPersistence.js";
import { DEFAULT_PLATFORM_PREFERENCES } from "../platformState.js";
import * as platformApi from "../platformApi.js";
import * as retrievalApi from "../../retrieval/retrievalApi.js";
import type { RetrievalValidationResult } from "../../retrieval/retrievalTypes.js";
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

// Panel de retrieval (global, ADR-006): endpoints legacy `/api/retrieval/*`
// mockeados aparte de `platformApi`, nunca ligados a una release.
vi.mock("../../retrieval/retrievalApi.js", () => ({
  loadRetrievalProfiles: vi.fn(),
  loadRetrievalProfileStatus: vi.fn(),
  validateRetrievalProfile: vi.fn(),
  searchRetrieval: vi.fn(),
}));

const api = vi.mocked(platformApi);
const retrieval = vi.mocked(retrievalApi);

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
  retrieval.loadRetrievalProfiles.mockResolvedValue({
    items: [],
    page: 1,
    pageSize: 25,
    totalItems: 0,
    totalPages: 0,
  });
  retrieval.loadRetrievalProfileStatus.mockResolvedValue({
    profile: {
      retrievalProfileId: "retrieval-profile-abc",
      consumerScopeType: "tenant",
      consumerScopeId: "sst",
      corpusVersion: "corpus-1",
      embeddingProfileId: "local-bge-m3-v1",
      indexingTargetId: "target-local",
      lexicalFallbackPolicy: "allowed_when_vector_unavailable",
      active: true,
      validationStatus: "passed",
      validatedAt: "2026-01-01T00:00:00Z",
      lastRuntimeStatus: "healthy",
      createdAt: "2026-01-01T00:00:00Z",
      deprecatedAt: null,
    },
    runtime: {
      retrievalProfileId: "retrieval-profile-abc",
      embeddingProfileId: "local-bge-m3-v1",
      indexingTargetId: "target-local",
      queryEngineAvailable: true,
      engineRevisionObserved: "5617a9f",
      vectorRetrievalEnabled: true,
      lexicalFallbackAllowed: false,
      blockedReason: null,
    },
    readiness: {
      retrievalProfileId: "retrieval-profile-abc",
      ready: true,
      activeVectorRows: 42,
      activeDocumentCount: 7,
      embeddingBundleId: "bundle-1",
      blockingReasons: [],
    },
  });
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

  it("(b4) seleccionar una release ya construida muestra su informe sin pedir un build nuevo", async () => {
    // Bug reportado: el informe quedaba en "idle" para cualquier release que no
    // se hubiera construido en la sesión actual del navegador, aunque el server
    // ya tuviera un build succeeded real -- la release parecía no seleccionable.
    selectInStorage("proj_alpha", "rel_1");
    api.listAllReleases.mockResolvedValue([makeRelease()]);
    // getReleaseBuildStatus ya resuelve "succeeded" por el beforeEach (histórico).
    renderRagReleaseWorkspace();

    expect(await screen.findByText("Revisiones construidas")).toBeTruthy();
    expect(screen.getByText("Etapas construidas")).toBeTruthy();
    // Ver el histórico no es "acabar de construir": no debe encolar ni disparar
    // el aviso de éxito de una acción que el usuario nunca pidió.
    expect(api.buildRelease).not.toHaveBeenCalled();
    expect(screen.queryByText(/Build completado/)).toBeNull();
  });

  it("(c) ofrece solo las acciones válidas por estado", async () => {
    // draft → Build + Validate; no Publicar/Retirar.
    selectInStorage("proj_alpha", "rel_1");
    api.listAllReleases.mockResolvedValue([makeRelease({ state: "draft" })]);
    const draft = renderRagReleaseWorkspace();
    expect(await screen.findByRole("button", { name: /Construir \(build\)/ })).toBeTruthy();
    expect(screen.getByRole("button", { name: /^Validar$/ })).toBeTruthy();
    expect(screen.queryByRole("button", { name: /Publicar/ })).toBeNull();
    expect(screen.queryByRole("button", { name: /Retirar/ })).toBeNull();
    draft.unmount();

    // validated → Publicar + Retirar; no Build/Validate.
    api.listAllReleases.mockResolvedValue([makeRelease({ state: "validated" })]);
    const validated = renderRagReleaseWorkspace();
    expect(await screen.findByRole("button", { name: /Publicar/ })).toBeTruthy();
    expect(screen.getByRole("button", { name: /Retirar/ })).toBeTruthy();
    expect(screen.queryByRole("button", { name: /Construir \(build\)/ })).toBeNull();
    expect(screen.queryByRole("button", { name: /^Validar$/ })).toBeNull();
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
    // Al seleccionar la release se siembra su build-status una vez (para mostrar
    // el informe si ya tenía un build previo); el encolado fallido no debe sumar
    // otra consulta encima de esa siembra inicial (fail-closed, sin éxito aparente).
    expect(api.getReleaseBuildStatus).toHaveBeenCalledTimes(1);
  });

  it("(e) 409 INVALID_RELEASE_TRANSITION: refetch de la release", async () => {
    selectInStorage("proj_alpha", "rel_1");
    api.listAllReleases.mockResolvedValue([makeRelease()]);
    api.validateRelease.mockRejectedValue({ status: 409, code: "INVALID_RELEASE_TRANSITION" });
    api.getRelease.mockResolvedValue(makeRelease({ state: "validated" }));
    const user = userEvent.setup();
    renderRagReleaseWorkspace();

    await user.click(await screen.findByRole("button", { name: /^Validar$/ }));

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

  it("(h) retrieval se muestra como diagnostico global, no ligado a la release", async () => {
    selectInStorage("proj_alpha", "rel_1");
    api.listAllReleases.mockResolvedValue([makeRelease()]);
    retrieval.loadRetrievalProfiles.mockResolvedValue({
      items: [
        {
          retrievalProfileId: "retrieval-profile-abc",
          consumerScopeType: "tenant",
          consumerScopeId: "sst",
          corpusVersion: "corpus-1",
          embeddingProfileId: "local-bge-m3-v1",
          indexingTargetId: "target-local",
          lexicalFallbackPolicy: "allowed_when_vector_unavailable",
          active: true,
          validationStatus: "passed",
          validatedAt: "2026-01-01T00:00:00Z",
          lastRuntimeStatus: "healthy",
          createdAt: "2026-01-01T00:00:00Z",
          deprecatedAt: null,
        },
      ],
      page: 1,
      pageSize: 25,
      totalItems: 1,
      totalPages: 1,
    });
    const user = userEvent.setup();
    renderRagReleaseWorkspace();

    expect(
      await screen.findByText(/nunca lo activa ni lo cambia/),
    ).toBeTruthy();
    await user.click(await screen.findByRole("button", { name: /retrieval-profile-abc/ }));
    await waitFor(() =>
      expect(retrieval.loadRetrievalProfileStatus).toHaveBeenCalledWith("retrieval-profile-abc"),
    );
  });

  it("agrupa las releases por variante y marca cuales ya son usables por la API chatbot", async () => {
    selectInStorage("proj_alpha", "rel_2");
    api.listAllVariants.mockResolvedValue([
      makeVariant({ rag_variant_id: "var_alpha", state: "buildable" }),
      makeVariant({ rag_variant_id: "var_beta", state: "buildable" }),
    ]);
    api.listAllReleases.mockResolvedValue([
      makeRelease({
        rag_release_id: "rel_1",
        rag_variant_id: "var_alpha",
        state: "draft",
        release_number: 1,
      }),
      makeRelease({
        rag_release_id: "rel_2",
        rag_variant_id: "var_alpha",
        state: "published",
        release_number: 2,
        release_manifest_hash: "sha256:rel-2",
      }),
      makeRelease({
        rag_release_id: "rel_3",
        rag_variant_id: "var_beta",
        state: "published",
        release_number: 1,
        release_manifest_hash: "sha256:rel-3",
      }),
    ]);

    renderRagReleaseWorkspace();

    expect(await screen.findByText("Mapa RAG del proyecto")).toBeTruthy();
    expect(screen.getAllByText("var_alpha").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("var_beta").length).toBeGreaterThanOrEqual(1);
    expect(
      screen.getByText(/La API chatbot no elige una release activa global/i),
    ).toBeTruthy();
    expect(screen.getAllByText(/Usable por API chatbot/i).length).toBeGreaterThanOrEqual(2);
    expect(
      screen.getByText(/La API chatbot puede responder con esta release/i),
    ).toBeTruthy();
  });

  it("(i) retrieval no aplica una validacion tardia al perfil equivocado tras cambiar de seleccion", async () => {
    selectInStorage("proj_alpha", "rel_1");
    api.listAllReleases.mockResolvedValue([makeRelease()]);
    const profileA = {
      retrievalProfileId: "retrieval-profile-a",
      consumerScopeType: "tenant",
      consumerScopeId: "sst",
      corpusVersion: "corpus-1",
      embeddingProfileId: "local-bge-m3-v1",
      indexingTargetId: "target-local",
      lexicalFallbackPolicy: "allowed_when_vector_unavailable",
      active: true,
      validationStatus: "passed",
      validatedAt: "2026-01-01T00:00:00Z",
      lastRuntimeStatus: "healthy",
      createdAt: "2026-01-01T00:00:00Z",
      deprecatedAt: null,
    };
    const profileB = { ...profileA, retrievalProfileId: "retrieval-profile-b", active: false };
    retrieval.loadRetrievalProfiles.mockResolvedValue({
      items: [profileA, profileB],
      page: 1,
      pageSize: 25,
      totalItems: 2,
      totalPages: 1,
    });
    // La validacion de A queda pendiente hasta que el test la resuelva a mano,
    // simulando que sigue en vuelo cuando el operador ya cambio de perfil.
    let resolveValidateA: (value: RetrievalValidationResult) => void = () => {};
    retrieval.validateRetrievalProfile.mockImplementation((profileId: string) => {
      if (profileId === "retrieval-profile-a") {
        return new Promise<RetrievalValidationResult>((resolve) => {
          resolveValidateA = resolve;
        });
      }
      return Promise.resolve({
        retrievalProfileId: profileId,
        status: "passed",
        validatorVersion: "retrieval-validator-v1",
        queryDimension: 1024,
        candidatesFound: 3,
        blockingReasons: [],
      });
    });

    const user = userEvent.setup();
    renderRagReleaseWorkspace();

    await user.click(await screen.findByRole("button", { name: /retrieval-profile-a/ }));
    await user.click(await screen.findByRole("button", { name: /^Validar perfil$/ }));
    expect(retrieval.validateRetrievalProfile).toHaveBeenCalledWith("retrieval-profile-a");

    // Cambia de perfil ANTES de que la validacion de A resuelva.
    await user.click(await screen.findByRole("button", { name: /retrieval-profile-b/ }));

    // La validacion tardia de A resuelve ahora, con B ya seleccionado.
    resolveValidateA({
      retrievalProfileId: "retrieval-profile-a",
      status: "failed",
      validatorVersion: "retrieval-validator-v1",
      queryDimension: null,
      candidatesFound: 0,
      blockingReasons: ["NO_ACTIVE_VECTOR_ROWS"],
    });

    // El resultado de A nunca debe pintarse como si fuera de B.
    await waitFor(() => expect(retrieval.loadRetrievalProfileStatus).toHaveBeenCalledWith("retrieval-profile-b"));
    expect(screen.queryByText("NO_ACTIVE_VECTOR_ROWS")).toBeNull();
  });

  it("(j) un fallo al cargar releases no oculta el diagnostico de retrieval (independiente)", async () => {
    selectInStorage("proj_alpha");
    api.listAllReleases.mockRejectedValue({ status: 500, code: "INTERNAL" });

    renderRagReleaseWorkspace();

    expect(await screen.findByText(/HTTP 500|Reintentar/)).toBeTruthy();
    expect(
      await screen.findByText(/nunca lo activa ni lo cambia/),
    ).toBeTruthy();
    expect(retrieval.loadRetrievalProfiles).toHaveBeenCalled();
  });

  it("(k) reintentar tras un fallo retira el aviso HTTP 500 al cargar bien", async () => {
    selectInStorage("proj_alpha");
    api.listAllReleases.mockRejectedValueOnce({ status: 500, code: "INTERNAL" });
    api.listAllReleases.mockResolvedValueOnce([]);
    const user = userEvent.setup();
    renderRagReleaseWorkspace();

    const errorText = /Ocurrio un error inesperado en el pipeline/;
    expect((await screen.findAllByText(errorText)).length).toBeGreaterThan(0);
    await user.click(await screen.findByRole("button", { name: /Reintentar/ }));

    await waitFor(() => expect(screen.queryAllByText(errorText).length).toBe(0));
    expect(await screen.findByRole("button", { name: /Crear draft/i })).toBeTruthy();
  });
});
