// Registro por proyecto de lo que el operador configuro DENTRO de las
// pantallas Legacy (Operacion/Chunking/Embedding-Indexing), para que el
// resolutor de variante lo reconfirme contra la matriz. Modulo puro (sin
// React/contexto): solo ids y metadata de proveedor, nunca targets fisicos.
// El leg de Operacion guarda `LlamaControls` crudo (provider metadata) porque
// su mapeo a `processing_profile_id` requiere red y lo hace el resolutor,
// fresco, en cada resolucion (nunca se cachea un id resuelto aqui).
import type { LlamaControls } from "../../dashboard/dashboardTypes.js";

export type PlatformPipelineRecipe = {
  llamaControls: LlamaControls | null;
  chunkingProfileId: string | null;
  embeddingProfileId: string | null;
};

export type PlatformRecipeResolution = {
  ragVariantId: string;
  cellId: string;
  targetBindingKey: string;
  created: boolean;
  resolvedAt: string;
};

function emptyRecipe(): PlatformPipelineRecipe {
  return { llamaControls: null, chunkingProfileId: null, embeddingProfileId: null };
}

const recipes = new Map<string, PlatformPipelineRecipe>();
const resolutions = new Map<string, PlatformRecipeResolution>();

export function readRecipeDraft(projectId: string): PlatformPipelineRecipe {
  return { ...(recipes.get(projectId) ?? emptyRecipe()) };
}

export function recordProcessingControls(projectId: string, controls: LlamaControls): void {
  recipes.set(projectId, { ...(recipes.get(projectId) ?? emptyRecipe()), llamaControls: controls });
}

export function recordChunkingProfile(projectId: string, chunkingProfileId: string): void {
  recipes.set(projectId, { ...(recipes.get(projectId) ?? emptyRecipe()), chunkingProfileId });
}

export function recordEmbeddingProfile(projectId: string, embeddingProfileId: string): void {
  recipes.set(projectId, { ...(recipes.get(projectId) ?? emptyRecipe()), embeddingProfileId });
}

// Cache de SOLO DISPLAY: cada operacion vuelve a resolver contra la matriz
// vigente; esto nunca sustituye la resolucion real ni se lee de vuelta hacia
// `resolveOrCreatePlatformRagVariant`.
export function recordLastResolution(projectId: string, resolution: PlatformRecipeResolution): void {
  resolutions.set(projectId, resolution);
}

export function lastResolution(projectId: string): PlatformRecipeResolution | null {
  return resolutions.get(projectId) ?? null;
}

export function __resetForTests(): void {
  recipes.clear();
  resolutions.clear();
}
