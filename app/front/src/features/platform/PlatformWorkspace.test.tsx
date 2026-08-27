import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { PlatformWorkspace } from "./PlatformWorkspace.js";
import * as platformApi from "./platformApi.js";
import type {
  PaginatedProjects,
  Project,
  ProjectConfiguration,
} from "./platformTypes.js";

// La sub-nav compone workspaces hermanos, todos por proyecto seleccionado. Se
// mockea el cliente HTTP para verificar el switch de vistas sin tocar la red.
// Reorganización 2026-08: la nav espeja el pipeline legacy (Operación/Revisión/
// Inventario/Chunking/Embedding-Indexing) + Projects + RAG/Releases; se retiraron
// las vistas custom documents/variants/corpus.
vi.mock("./platformApi.js", () => ({
  listProjects: vi.fn(),
  getProject: vi.fn(),
  getConfiguration: vi.fn(),
  createProject: vi.fn(),
  updateProject: vi.fn(),
  updateConfiguration: vi.fn(),
  listAllVariants: vi.fn(),
  listProcessingProfiles: vi.fn(),
  listChunkingProfiles: vi.fn(),
  getVariantMatrix: vi.fn(),
  createVariant: vi.fn(),
  listAllDocuments: vi.fn(),
  uploadDocument: vi.fn(),
  normalizeDocuments: vi.fn(),
  submitRevisionReviewDecision: vi.fn(),
  listAllCorpusSnapshots: vi.fn(),
  createCorpusSnapshot: vi.fn(),
  listAllReleases: vi.fn(),
  getRelease: vi.fn(),
  createReleaseDraft: vi.fn(),
  buildRelease: vi.fn(),
  getReleaseBuildStatus: vi.fn(),
  validateRelease: vi.fn(),
  publishRelease: vi.fn(),
  retireRelease: vi.fn(),
}));

vi.mock("../chunking/ChunkingWorkspace.js", () => ({
  ChunkingWorkspace: () => <h2>Chunking sentinel</h2>,
}));

vi.mock("../embeddingIndexing/EmbeddingIndexingWorkspace.js", () => ({
  EmbeddingIndexingWorkspace: () => <h2>Embedding Indexing sentinel</h2>,
}));

const api = vi.mocked(platformApi);

const emptyProjects: PaginatedProjects = {
  items: [],
  page: 1,
  page_size: 25,
  total_items: 0,
  total_pages: 1,
};
const emptyConfiguration: ProjectConfiguration = {
  corpus_organization_policy: "source-folders-v1",
  created_at: "2026-01-01T00:00:00Z",
  document_types: [],
  embedding_profiles: [],
  target_bindings: [],
  version: 1,
};

function makeProject(overrides: Partial<Project> = {}): Project {
  return {
    project_id: "proj_alpha",
    display_name: "Proyecto Alpha",
    state: "active",
    configuration: emptyConfiguration,
    created_at: "2026-01-01T00:00:00Z",
    ...overrides,
  };
}

function paginateProjects(items: Project[]): PaginatedProjects {
  return {
    items,
    page: 1,
    page_size: 25,
    total_items: items.length,
    total_pages: 1,
  };
}

beforeEach(() => {
  window.localStorage.clear();
  api.listProjects.mockResolvedValue(emptyProjects);
  api.listAllVariants.mockResolvedValue([]);
  api.listAllDocuments.mockResolvedValue([]);
  api.listAllCorpusSnapshots.mockResolvedValue([]);
  api.listAllReleases.mockResolvedValue([]);
  api.getReleaseBuildStatus.mockResolvedValue(null);
  api.getConfiguration.mockResolvedValue(emptyConfiguration);
});

describe("PlatformWorkspace", () => {
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
    expect(
      await screen.findByRole("heading", { name: "Legacy pipeline - Operacion de ingesta" }),
    ).toBeTruthy();
    expect(screen.getByRole("button", { name: /Ejecutar ingesta local/i })).toBeTruthy();
    expect(screen.queryByRole("heading", { name: "Intake documental" })).toBeNull();

    await user.click(screen.getByRole("button", { name: "Revision" }));
    expect(
      await screen.findByRole("heading", { name: "Legacy pipeline - Revision documental" }),
    ).toBeTruthy();
    expect(screen.getAllByRole("button", { name: "Aprobar" }).length).toBeGreaterThan(0);
    expect(screen.getAllByRole("button", { name: "Rechazar" }).length).toBeGreaterThan(0);
    expect(screen.queryByRole("heading", { name: "Snapshots de corpus" })).toBeNull();

    await user.click(screen.getByRole("button", { name: "Inventario" }));
    expect(
      await screen.findByRole("heading", { name: "Legacy pipeline - Inventario documental" }),
    ).toBeTruthy();
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

  it("comparte el proyecto seleccionado entre vistas de Platform", async () => {
    const user = userEvent.setup();
    const alpha = makeProject();
    const beta = makeProject({ project_id: "proj_beta", display_name: "Proyecto Beta" });
    api.listProjects.mockResolvedValue(paginateProjects([alpha, beta]));

    render(<PlatformWorkspace />);

    await screen.findByRole("heading", { name: "RAG Platform" });
    await user.click(screen.getByText("Proyecto Beta"));

    expect(screen.getByLabelText("Proyecto activo").textContent).toContain("Proyecto Beta");

    await user.click(screen.getByRole("button", { name: "Inventario" }));

    expect(
      await screen.findByRole("heading", { name: "Legacy pipeline - Inventario documental" }),
    ).toBeTruthy();
    expect(screen.getByLabelText("Proyecto activo").textContent).toContain("Proyecto Beta");
    expect(api.listAllDocuments).toHaveBeenCalledWith("proj_beta");
  });
});
