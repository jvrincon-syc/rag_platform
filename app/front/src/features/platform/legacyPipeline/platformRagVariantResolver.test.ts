import { beforeEach, describe, expect, it, vi } from "vitest";
import {
  resolveOrCreatePlatformRagVariant,
  type PlatformRagVariantResolverDeps,
} from "./platformRagVariantResolver.js";
import { __resetForTests, lastResolution } from "./platformRecipeDraft.js";
import type {
  ChunkingProfileRead,
  ProcessingProfileRead,
  ProjectConfiguration,
  Variant,
  VariantMatrixCell,
} from "../platformTypes.js";

function config(overrides: Partial<ProjectConfiguration> = {}): ProjectConfiguration {
  return {
    corpus_organization_policy: "source-folders-v1",
    created_at: "2026-08-25T00:00:00Z",
    document_types: [],
    embedding_profiles: [{ embedding_profile_id: "eprof_a", enabled: true }],
    target_bindings: [{ binding_key: "bnd_a", embedding_profile_id: "eprof_a" }],
    version: 1,
    ...overrides,
  };
}

function processingProfile(overrides: Partial<ProcessingProfileRead> = {}): ProcessingProfileRead {
  return {
    engine: "pdfium-tesseract",
    fingerprint: "f".repeat(64),
    processing_profile_id: "pp_local",
    provider: "local",
    status: "verified",
    ...overrides,
  };
}

function chunkingProfile(overrides: Partial<ChunkingProfileRead> = {}): ChunkingProfileRead {
  return {
    chunking_profile_id: "cp_default",
    fingerprint: "a".repeat(64),
    status: "verified",
    strategy: "structural-v1",
    ...overrides,
  };
}

function matrixCell(overrides: Partial<VariantMatrixCell> = {}): VariantMatrixCell {
  return {
    buildable: true,
    cell_id: "pp_local|cp_default|eprof_a|bnd_a|1",
    chunking_profile_id: "cp_default",
    configuration_version: 1,
    embedding_profile_id: "eprof_a",
    processing_profile_id: "pp_local",
    target_binding_key: "bnd_a",
    ...overrides,
  };
}

function variant(overrides: Partial<Variant> = {}): Variant {
  return {
    chunking_profile_id: "cp_default",
    created_at: "2026-08-25T00:00:00Z",
    embedding_profile_id: "eprof_a",
    processing_profile_id: "pp_local",
    project_id: "proj_demo",
    rag_variant_id: "ragv_existing",
    semantic_recipe_fingerprint: "fingerprint",
    state: "active",
    ...overrides,
  };
}

function httpError(code: string): Error & { code: string } {
  return Object.assign(new Error(`http error ${code}`), { code });
}

function makeDeps(
  overrides: Partial<PlatformRagVariantResolverDeps> = {},
): PlatformRagVariantResolverDeps {
  return {
    getConfiguration: vi.fn().mockResolvedValue(config()),
    listProcessingProfiles: vi.fn().mockResolvedValue([processingProfile()]),
    listChunkingProfiles: vi.fn().mockResolvedValue([chunkingProfile()]),
    getVariantMatrix: vi.fn().mockResolvedValue([matrixCell()]),
    listAllVariants: vi.fn().mockResolvedValue([]),
    createVariant: vi.fn().mockResolvedValue(variant({ rag_variant_id: "ragv_created" })),
    ...overrides,
  };
}

const RECIPE = {
  llamaControls: { providerMode: "local" as const, route: "classify,parse,extract" as const },
  chunkingProfileId: "cp_default",
  embeddingProfileId: "eprof_a",
};

describe("resolveOrCreatePlatformRagVariant", () => {
  beforeEach(() => {
    __resetForTests();
  });

  it("reusa la variante existente cuando la tripleta de perfiles ya tiene variante", async () => {
    const deps = makeDeps({ listAllVariants: vi.fn().mockResolvedValue([variant()]) });

    const resolved = await resolveOrCreatePlatformRagVariant({ projectId: "proj_demo", recipe: RECIPE }, deps);

    expect(resolved).toEqual({
      ragVariantId: "ragv_existing",
      cellId: matrixCell().cell_id,
      targetBindingKey: "bnd_a",
      created: false,
    });
    expect(deps.createVariant).not.toHaveBeenCalled();
    expect(lastResolution("proj_demo")?.ragVariantId).toBe("ragv_existing");
  });

  it("crea la variante cuando la celda es construible y no existe variante", async () => {
    const deps = makeDeps();

    const resolved = await resolveOrCreatePlatformRagVariant({ projectId: "proj_demo", recipe: RECIPE }, deps);

    expect(resolved.created).toBe(true);
    expect(resolved.ragVariantId).toBe("ragv_created");
    expect(deps.createVariant).toHaveBeenCalledWith("proj_demo", {
      cell_id: matrixCell().cell_id,
      variant_slug: expect.any(String),
    });
  });

  it("ante 409 DUPLICATE_VARIANT_RECIPE re-lista las variantes y reusa la existente", async () => {
    const listAllVariants = vi.fn()
      .mockResolvedValueOnce([])
      .mockResolvedValueOnce([variant({ rag_variant_id: "ragv_reused" })]);
    const deps = makeDeps({
      listAllVariants,
      createVariant: vi.fn().mockRejectedValue(httpError("DUPLICATE_VARIANT_RECIPE")),
    });

    const resolved = await resolveOrCreatePlatformRagVariant({ projectId: "proj_demo", recipe: RECIPE }, deps);

    expect(resolved).toEqual({
      ragVariantId: "ragv_reused",
      cellId: matrixCell().cell_id,
      targetBindingKey: "bnd_a",
      created: false,
    });
    expect(listAllVariants).toHaveBeenCalledTimes(2);
  });

  it("fallo cerrado mostrando blocked_reason cuando la celda no es construible", async () => {
    const deps = makeDeps({
      getVariantMatrix: vi
        .fn()
        .mockResolvedValue([matrixCell({ buildable: false, blocked_reason: "embedding profile deshabilitado" })]),
    });

    await expect(
      resolveOrCreatePlatformRagVariant({ projectId: "proj_demo", recipe: RECIPE }, deps),
    ).rejects.toThrow("embedding profile deshabilitado");
    expect(deps.createVariant).not.toHaveBeenCalled();
  });

  it("fallo cerrado cuando providerMode no mapea a un unico processing profile (lista candidatos)", async () => {
    const deps = makeDeps({
      listProcessingProfiles: vi
        .fn()
        .mockResolvedValue([
          processingProfile({ processing_profile_id: "pp_one", engine: "engine-a" }),
          processingProfile({ processing_profile_id: "pp_two", engine: "engine-b" }),
        ]),
    });

    await expect(
      resolveOrCreatePlatformRagVariant({ projectId: "proj_demo", recipe: RECIPE }, deps),
    ).rejects.toThrow(/pp_one.*pp_two|pp_two.*pp_one/);
    expect(deps.createVariant).not.toHaveBeenCalled();
  });

  it("fallo cerrado pidiendo la pantalla Chunking cuando hay varios perfiles y sin seleccion del operador", async () => {
    const deps = makeDeps({
      listChunkingProfiles: vi
        .fn()
        .mockResolvedValue([
          chunkingProfile({ chunking_profile_id: "cp_one" }),
          chunkingProfile({ chunking_profile_id: "cp_two" }),
        ]),
    });
    const recipe = { ...RECIPE, chunkingProfileId: null };

    await expect(
      resolveOrCreatePlatformRagVariant({ projectId: "proj_demo", recipe }, deps),
    ).rejects.toThrow(/Chunking/);
    expect(deps.createVariant).not.toHaveBeenCalled();
  });

  it("auto-resuelve el leg unico cuando el catalogo tiene exactamente un perfil de chunking / un embedding habilitado", async () => {
    const deps = makeDeps();
    const recipe = { llamaControls: RECIPE.llamaControls, chunkingProfileId: null, embeddingProfileId: null };

    const resolved = await resolveOrCreatePlatformRagVariant({ projectId: "proj_demo", recipe }, deps);

    expect(resolved.created).toBe(true);
    expect(deps.createVariant).toHaveBeenCalledWith("proj_demo", {
      cell_id: matrixCell().cell_id,
      variant_slug: expect.any(String),
    });
  });

  it("fallo cerrado listando binding_key cuando hay varios target bindings", async () => {
    const deps = makeDeps({
      getConfiguration: vi.fn().mockResolvedValue(
        config({
          target_bindings: [
            { binding_key: "bnd_a", embedding_profile_id: "eprof_a" },
            { binding_key: "bnd_b", embedding_profile_id: "eprof_a" },
          ],
        }),
      ),
    });

    await expect(
      resolveOrCreatePlatformRagVariant({ projectId: "proj_demo", recipe: RECIPE }, deps),
    ).rejects.toThrow(/bnd_a.*bnd_b|bnd_b.*bnd_a/);
    expect(deps.createVariant).not.toHaveBeenCalled();
  });

  it("nunca llama a normalize ni crea variantes fuera de la matriz", async () => {
    const deps = makeDeps({ getVariantMatrix: vi.fn().mockResolvedValue([]) });

    await expect(
      resolveOrCreatePlatformRagVariant({ projectId: "proj_demo", recipe: RECIPE }, deps),
    ).rejects.toThrow();
    expect(deps.createVariant).not.toHaveBeenCalled();
  });
});
