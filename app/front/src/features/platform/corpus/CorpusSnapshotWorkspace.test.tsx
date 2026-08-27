import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { CorpusSnapshotWorkspace } from "./CorpusSnapshotWorkspace.js";
import { PlatformProjectProvider } from "../PlatformProjectContext.js";
import { readPlatformPreferences, writePlatformPreferences } from "../platformPersistence.js";
import { DEFAULT_PLATFORM_PREFERENCES } from "../platformState.js";
import * as platformApi from "../platformApi.js";
import type { CorpusSnapshot, ProjectDocumentRevision } from "../platformTypes.js";

// Cliente HTTP mockeado en el límite de red: ningún test toca fetch.
vi.mock("../platformApi.js", () => ({
  listAllDocuments: vi.fn(),
  listAllCorpusSnapshots: vi.fn(),
  createCorpusSnapshot: vi.fn(),
}));

const api = vi.mocked(platformApi);

function makeRevision(overrides: Partial<ProjectDocumentRevision> = {}): ProjectDocumentRevision {
  return {
    source_document_revision_id: "srev_1",
    logical_document_id: "ldoc_1",
    source_relpath: "manuales/proc.pdf",
    file_size: 1024,
    raw_registered: true,
    normalized_registered: true,
    review_state: "processed",
    processing_status: "normalized",
    uploaded_at: "2026-01-01T00:00:00Z",
    ...overrides,
  };
}

function makeSnapshot(overrides: Partial<CorpusSnapshot> = {}): CorpusSnapshot {
  return {
    corpus_snapshot_id: "corpus_new",
    project_id: "proj_alpha",
    manifest_hash: "sha256:abcd",
    document_count: 1,
    documents: [],
    created_at: "2026-01-01T00:00:00Z",
    ...overrides,
  };
}

function selectProjectInStorage(projectId: string): void {
  writePlatformPreferences({ ...DEFAULT_PLATFORM_PREFERENCES, selectedProjectId: projectId });
}

function renderCorpusSnapshotWorkspace() {
  return render(
    <PlatformProjectProvider>
      <CorpusSnapshotWorkspace />
    </PlatformProjectProvider>,
  );
}

beforeEach(() => {
  window.localStorage.clear();
  api.listAllDocuments.mockResolvedValue([]);
  api.listAllCorpusSnapshots.mockResolvedValue([]);
  api.createCorpusSnapshot.mockResolvedValue(makeSnapshot());
});

describe("CorpusSnapshotWorkspace", () => {
  it("renderiza las revisiones normalizadas candidatas reutilizando el inventario neutral", async () => {
    selectProjectInStorage("proj_alpha");
    api.listAllDocuments.mockResolvedValue([makeRevision()]);

    renderCorpusSnapshotWorkspace();

    // displayName = source_relpath; segunda línea = source_document_revision_id.
    expect(await screen.findByText("manuales/proc.pdf")).toBeTruthy();
    expect(screen.getByText("srev_1")).toBeTruthy();
    // La caja de búsqueda y el filtro por estado vienen del inventario reutilizado.
    expect(screen.getByRole("searchbox", { name: /Buscar por ruta o ID/ })).toBeTruthy();
    expect(screen.getByRole("combobox", { name: /Filtrar por estado/ })).toBeTruthy();
  });

  it("sin proyecto muestra estado vacío direccional y no llama a la API", async () => {
    renderCorpusSnapshotWorkspace();

    expect(
      await screen.findByText(/Selecciona un proyecto para construir un snapshot/),
    ).toBeTruthy();
    expect(api.listAllDocuments).not.toHaveBeenCalled();
    expect(api.listAllCorpusSnapshots).not.toHaveBeenCalled();
  });

  it("muestra el estado de carga mientras resuelven las revisiones", async () => {
    selectProjectInStorage("proj_alpha");
    // Promesa colgada: candidates permanece en loading.
    api.listAllDocuments.mockReturnValue(new Promise<ProjectDocumentRevision[]>(() => {}));

    renderCorpusSnapshotWorkspace();

    expect(await screen.findByText(/Cargando revisiones elegibles/)).toBeTruthy();
  });

  it("con proyecto sin revisiones normalizadas muestra estado vacío direccional", async () => {
    selectProjectInStorage("proj_alpha");
    // Sin RAW normalizado: el hook filtra y candidates queda empty.
    api.listAllDocuments.mockResolvedValue([]);

    renderCorpusSnapshotWorkspace();

    expect(await screen.findByText(/No hay revisiones normalizadas/)).toBeTruthy();
  });

  it("ante un error de carga surfacea el mensaje fail-closed con opción de reintentar", async () => {
    selectProjectInStorage("proj_alpha");
    api.listAllDocuments.mockRejectedValue({ status: 403, code: "FORBIDDEN" });

    renderCorpusSnapshotWorkspace();

    expect((await screen.findAllByText(/No autorizado para esta operación/)).length).toBeGreaterThan(0);
    expect(screen.getByRole("button", { name: /Reintentar/ })).toBeTruthy();
  });

  it("la búsqueda filtra las revisiones por ruta o ID", async () => {
    selectProjectInStorage("proj_alpha");
    api.listAllDocuments.mockResolvedValue([
      makeRevision({ source_document_revision_id: "srev_1", source_relpath: "manuales/proc.pdf" }),
      makeRevision({
        source_document_revision_id: "srev_2",
        logical_document_id: "ldoc_2",
        source_relpath: "anexos/plan.pdf",
      }),
    ]);

    const user = userEvent.setup();
    renderCorpusSnapshotWorkspace();

    await screen.findByText("manuales/proc.pdf");
    await user.type(screen.getByRole("searchbox", { name: /Buscar por ruta o ID/ }), "anexos");

    expect(screen.getByText("anexos/plan.pdf")).toBeTruthy();
    expect(screen.queryByText("manuales/proc.pdf")).toBeNull();
  });

  it("el filtro por estado aísla las revisiones needs_review sin ocultarlas del corpus", async () => {
    selectProjectInStorage("proj_alpha");
    api.listAllDocuments.mockResolvedValue([
      makeRevision({ source_document_revision_id: "srev_1", review_state: "processed" }),
      makeRevision({
        source_document_revision_id: "srev_2",
        logical_document_id: "ldoc_2",
        source_relpath: "anexos/plan.pdf",
        review_state: "needs_review",
      }),
    ]);

    const user = userEvent.setup();
    renderCorpusSnapshotWorkspace();

    await screen.findByText("manuales/proc.pdf");
    await user.selectOptions(
      screen.getByRole("combobox", { name: /Filtrar por estado/ }),
      "needs_review",
    );

    expect(screen.getByText("anexos/plan.pdf")).toBeTruthy();
    expect(screen.queryByText("manuales/proc.pdf")).toBeNull();
  });

  it("selecciona en bloque solo las revisiones elegibles sin auto-incluir needs_review", async () => {
    selectProjectInStorage("proj_alpha");
    api.listAllDocuments.mockResolvedValue([
      makeRevision({ source_document_revision_id: "srev_1", review_state: "processed" }),
      makeRevision({
        source_document_revision_id: "srev_2",
        logical_document_id: "ldoc_2",
        source_relpath: "anexos/plan.pdf",
        review_state: "needs_review",
      }),
    ]);

    const user = userEvent.setup();
    renderCorpusSnapshotWorkspace();

    await user.click(
      await screen.findByRole("button", { name: "Seleccionar todas las elegibles" }),
    );

    expect(screen.getByText("1 de 2 seleccionadas")).toBeTruthy();
    const checkboxes = screen.getAllByRole("checkbox", { name: /Incluir revisión/ });
    expect((checkboxes[0] as HTMLInputElement).checked).toBe(true);
    expect((checkboxes[1] as HTMLInputElement).checked).toBe(false);
  });

  it("crea un snapshot de revisiones processed sin eligibility_decisions", async () => {
    selectProjectInStorage("proj_alpha");
    api.listAllDocuments.mockResolvedValue([makeRevision()]);

    const user = userEvent.setup();
    renderCorpusSnapshotWorkspace();

    await user.click(
      await screen.findByRole("checkbox", { name: /Incluir revisión srev_1/ }),
    );
    await user.click(screen.getByRole("button", { name: /Crear snapshot/ }));

    await waitFor(() => expect(api.createCorpusSnapshot).toHaveBeenCalledTimes(1));
    const body = api.createCorpusSnapshot.mock.calls[0][0];
    expect(body.project_id).toBe("proj_alpha");
    expect(body.document_revision_ids).toEqual(["srev_1"]);
    // Una revisión processed no manda decisión: `not_required` es implícito server-side.
    expect("eligibility_decisions" in body).toBe(false);
  });

  it("exige decisión explícita para una revisión needs_review antes de crear", async () => {
    selectProjectInStorage("proj_alpha");
    api.listAllDocuments.mockResolvedValue([makeRevision({ review_state: "needs_review" })]);

    const user = userEvent.setup();
    renderCorpusSnapshotWorkspace();

    // Antes de seleccionar, la fila needs_review pide decisión al incluir (no select).
    expect(await screen.findByText(/Requiere decisión al incluir/)).toBeTruthy();

    await user.click(
      await screen.findByRole("checkbox", { name: /Incluir revisión srev_1/ }),
    );
    // Seleccionada sin decisión: Crear está bloqueado con motivo visible.
    expect(screen.getByRole("button", { name: /Crear snapshot/ })).toHaveProperty(
      "disabled",
      true,
    );
    expect(screen.getByText(/Faltan decisiones de elegibilidad/)).toBeTruthy();

    // Al aparecer el select y elegir una decisión, el gate se libera.
    await user.selectOptions(
      screen.getByRole("combobox", { name: /Decisión de elegibilidad para srev_1/ }),
      "approved_after_review",
    );
    const createButton = screen.getByRole("button", { name: /Crear snapshot/ });
    expect(createButton).toHaveProperty("disabled", false);

    await user.click(createButton);
    await waitFor(() => expect(api.createCorpusSnapshot).toHaveBeenCalledTimes(1));
    const body = api.createCorpusSnapshot.mock.calls[0][0];
    expect(body.eligibility_decisions).toEqual({ srev_1: "approved_after_review" });
  });

  it("tras crear, persiste solo el corpus_snapshot_id y refresca el historial", async () => {
    selectProjectInStorage("proj_alpha");
    api.listAllDocuments.mockResolvedValue([makeRevision()]);

    const user = userEvent.setup();
    renderCorpusSnapshotWorkspace();

    await user.click(
      await screen.findByRole("checkbox", { name: /Incluir revisión srev_1/ }),
    );
    await user.click(screen.getByRole("button", { name: /Crear snapshot/ }));

    await waitFor(() =>
      expect(readPlatformPreferences().selectedCorpusSnapshotId).toBe("corpus_new"),
    );
    // El historial se recarga tras crear (segunda llamada al helper plano).
    await waitFor(() => expect(api.listAllCorpusSnapshots.mock.calls.length).toBeGreaterThan(1));
    // No se filtró nada sensible: solo el ID de navegación.
    const stored = readPlatformPreferences();
    expect(Object.keys(stored)).not.toContain("manifest_hash");
  });

  it("ante 409 cross-project surfacea un mensaje fail-closed", async () => {
    selectProjectInStorage("proj_alpha");
    api.listAllDocuments.mockResolvedValue([makeRevision()]);
    api.createCorpusSnapshot.mockRejectedValue({
      status: 409,
      code: "REVISION_PROJECT_MISMATCH",
    });

    const user = userEvent.setup();
    renderCorpusSnapshotWorkspace();

    await user.click(
      await screen.findByRole("checkbox", { name: /Incluir revisión srev_1/ }),
    );
    await user.click(screen.getByRole("button", { name: /Crear snapshot/ }));

    expect(await screen.findByText(/inválida o pertenece a otro proyecto/)).toBeTruthy();
  });
});
