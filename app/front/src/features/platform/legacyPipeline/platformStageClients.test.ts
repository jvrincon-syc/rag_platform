import { beforeEach, describe, expect, it, vi } from "vitest";
import * as platformApi from "../platformApi.js";
import {
  createPlatformChunkingApiClient,
  createPlatformEmbeddingIndexingApiClient,
} from "./platformStageClients.js";
import { __resetForTests, readRecipeDraft } from "./platformRecipeDraft.js";

vi.mock("../platformApi.js", () => ({
  listChunkingProfiles: vi.fn(),
}));

const api = vi.mocked(platformApi);

beforeEach(() => {
  __resetForTests();
});

describe("createPlatformChunkingApiClient", () => {
  it("mapea los perfiles de chunking del proyecto con token params en null (N/D, sin inventar)", async () => {
    api.listChunkingProfiles.mockResolvedValue([
      { chunking_profile_id: "cp_a", strategy: "structural-v1", fingerprint: "f".repeat(64), status: "verified" },
    ]);
    const client = createPlatformChunkingApiClient("proj_demo");

    const profiles = await client.loadProfiles();

    expect(api.listChunkingProfiles).toHaveBeenCalledWith("proj_demo");
    expect(profiles).toEqual([
      {
        profileId: "cp_a",
        childMinTokens: null,
        childTargetTokens: null,
        childMaxTokens: null,
        overlapRatio: null,
        overlapMinTokens: null,
        overlapMaxTokens: null,
      },
    ]);
  });

  it("al lanzar una corrida registra el perfil en la receta y falla cerrado (sin endpoint por proyecto)", async () => {
    const client = createPlatformChunkingApiClient("proj_demo");

    await expect(
      client.createRun({
        idempotencyKey: "k",
        request: { scope: "corpus", documentIds: [], profileId: "cp_a", force: false },
      }),
    ).rejects.toThrow(/No disponible en Platform/);

    // El perfil quedo registrado para el resolver de variante (RAG / Releases).
    expect(readRecipeDraft("proj_demo").chunkingProfileId).toBe("cp_a");
  });

  it("no hay documentos ya chunkeados por proyecto: pagina vacia explicita (nunca global)", async () => {
    const client = createPlatformChunkingApiClient("proj_demo");
    const page = await client.loadStoredDocuments();
    expect(page.items).toEqual([]);
    expect(page.totalItems).toBe(0);
  });

  it("validacion opcional devuelve null (honesto: sin reporte por proyecto)", async () => {
    const client = createPlatformChunkingApiClient("proj_demo");
    expect(await client.loadValidationOptional("run_x")).toBeNull();
  });
});

describe("createPlatformEmbeddingIndexingApiClient", () => {
  it("embedding: catalogo de perfiles vacio (Platform no expone read-model rico)", async () => {
    const client = createPlatformEmbeddingIndexingApiClient("proj_demo");
    const page = await client.embedding.loadProfiles();
    expect(page.items).toEqual([]);
  });

  it("indexing.loadOverview falla cerrado como no disponible (nunca pega al global)", async () => {
    const client = createPlatformEmbeddingIndexingApiClient("proj_demo");
    await expect(client.indexing.loadOverview()).rejects.toThrow(/No disponible en Platform/);
  });

  it("retrieval: catalogo de perfiles vacio y buscar evidencia no disponible", async () => {
    const client = createPlatformEmbeddingIndexingApiClient("proj_demo");
    expect((await client.retrieval.loadProfiles()).items).toEqual([]);
    await expect(
      client.retrieval.search({ retrievalProfileId: "r", query: "q", topK: 5 }),
    ).rejects.toThrow(/No disponible en Platform/);
  });

  it("embedding.createRun registra el perfil en la receta y falla cerrado", async () => {
    const client = createPlatformEmbeddingIndexingApiClient("proj_demo");
    await expect(
      client.embedding.createRun({ chunkBundleId: "cb", profileId: "eprof_a" }, {}),
    ).rejects.toThrow(/No disponible en Platform/);
    expect(readRecipeDraft("proj_demo").embeddingProfileId).toBe("eprof_a");
  });
});
