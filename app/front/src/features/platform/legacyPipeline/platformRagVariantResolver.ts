// Reconfirma la receta configurada en las pantallas Legacy (Operacion/Chunking/
// Embedding-Indexing) contra la matriz de variantes vigente y reusa o crea el
// `rag_variant_id` correspondiente. Fail-closed en cada paso: cero o varias
// coincidencias nombran los candidatos y nunca eligen arbitrariamente (nunca
// adivina por similitud de texto). El frontend jamas envia target fisico:
// `target_binding_key` es logico (Fase 7).
import type { LlamaControls } from "../../dashboard/dashboardTypes.js";
import {
  createVariant,
  getConfiguration,
  getVariantMatrix,
  listAllVariants,
  listChunkingProfiles,
  listProcessingProfiles,
} from "../platformApi.js";
import type {
  ChunkingProfileRead,
  ProcessingProfileRead,
  ProjectConfiguration,
  Variant,
  VariantMatrixCell,
} from "../platformTypes.js";
import { recordLastResolution, type PlatformPipelineRecipe } from "./platformRecipeDraft.js";

export type { PlatformPipelineRecipe } from "./platformRecipeDraft.js";

export type ResolvedPlatformRagVariant = {
  ragVariantId: string;
  cellId: string;
  targetBindingKey: string;
  created: boolean;
};

export type PlatformRagVariantResolverDeps = {
  getConfiguration: (projectId: string) => Promise<ProjectConfiguration>;
  listProcessingProfiles: (projectId: string) => Promise<ProcessingProfileRead[]>;
  listChunkingProfiles: (projectId: string) => Promise<ChunkingProfileRead[]>;
  getVariantMatrix: (projectId: string) => Promise<VariantMatrixCell[]>;
  listAllVariants: (projectId: string) => Promise<Variant[]>;
  createVariant: (projectId: string, body: { cell_id: string; variant_slug: string }) => Promise<Variant>;
};

const defaultPlatformApiDeps: PlatformRagVariantResolverDeps = {
  getConfiguration,
  listProcessingProfiles,
  listChunkingProfiles,
  getVariantMatrix,
  listAllVariants,
  createVariant,
};

type HttpErrorLike = { code?: string | null };

function resolveProcessingProfileId(
  llamaControls: LlamaControls | null,
  profiles: readonly ProcessingProfileRead[],
): string {
  if (!llamaControls) {
    throw new Error(
      "Configura el proveedor y la ruta en Operacion antes de continuar; no hay controles registrados para esta receta.",
    );
  }
  const candidates = profiles.filter((profile) => profile.provider === llamaControls.providerMode);
  if (candidates.length === 1) return candidates[0]!.processing_profile_id;
  if (candidates.length === 0) {
    throw new Error(
      `Ningun perfil de procesamiento del proyecto usa provider="${llamaControls.providerMode}". Configuralo en Operacion.`,
    );
  }
  const names = candidates.map((c) => `${c.processing_profile_id} (engine=${c.engine})`).join(", ");
  throw new Error(
    `Varios perfiles de procesamiento usan provider="${llamaControls.providerMode}": ${names}. Elige uno explicito en Operacion.`,
  );
}

function resolveChunkingProfileId(
  selected: string | null,
  profiles: readonly ChunkingProfileRead[],
): string {
  if (selected) return selected;
  if (profiles.length === 1) return profiles[0]!.chunking_profile_id;
  if (profiles.length === 0) {
    throw new Error("El proyecto no tiene perfiles de chunking configurados. Configura uno en la pantalla Chunking.");
  }
  throw new Error(
    `Hay ${profiles.length} perfiles de chunking disponibles; selecciona uno en la pantalla Chunking antes de continuar.`,
  );
}

function resolveEmbeddingProfileId(
  selected: string | null,
  configuration: ProjectConfiguration,
): string {
  if (selected) return selected;
  const enabled = configuration.embedding_profiles.filter((profile) => profile.enabled);
  if (enabled.length === 1) return enabled[0]!.embedding_profile_id;
  if (enabled.length === 0) {
    throw new Error(
      "El proyecto no tiene perfiles de embedding habilitados. Configura uno en Embedding/Indexing.",
    );
  }
  throw new Error(
    `Hay ${enabled.length} perfiles de embedding habilitados; selecciona uno en Embedding/Indexing antes de continuar.`,
  );
}

function resolveTargetBindingKey(
  embeddingProfileId: string,
  configuration: ProjectConfiguration,
): string {
  const matches = configuration.target_bindings.filter(
    (binding) => binding.embedding_profile_id === embeddingProfileId,
  );
  if (matches.length === 1) return matches[0]!.binding_key;
  if (matches.length === 0) {
    throw new Error(`No hay target binding configurado para el perfil de embedding ${embeddingProfileId}.`);
  }
  const keys = matches.map((binding) => binding.binding_key).join(", ");
  throw new Error(
    `Hay ${matches.length} target bindings para el perfil de embedding ${embeddingProfileId}: ${keys}. Configuracion ambigua, no se elige de forma arbitraria.`,
  );
}

function findMatrixCell(
  matrix: readonly VariantMatrixCell[],
  processingProfileId: string,
  chunkingProfileId: string,
  embeddingProfileId: string,
): VariantMatrixCell {
  const cell = matrix.find(
    (candidate) =>
      candidate.processing_profile_id === processingProfileId &&
      candidate.chunking_profile_id === chunkingProfileId &&
      candidate.embedding_profile_id === embeddingProfileId,
  );
  if (!cell) {
    throw new Error(
      "Ninguna celda de la matriz vigente coincide con esta combinacion de perfiles (deriva de configuracion). Vuelve a configurar Chunking/Embedding-Indexing.",
    );
  }
  if (!cell.buildable) {
    throw new Error(
      `La combinacion seleccionada no es construible: ${cell.blocked_reason ?? "motivo no informado por el backend"}.`,
    );
  }
  return cell;
}

function findMatchingVariant(
  variants: readonly Variant[],
  processingProfileId: string,
  chunkingProfileId: string,
  embeddingProfileId: string,
): Variant | null {
  return (
    variants.find(
      (variant) =>
        variant.processing_profile_id === processingProfileId &&
        variant.chunking_profile_id === chunkingProfileId &&
        variant.embedding_profile_id === embeddingProfileId,
    ) ?? null
  );
}

// Slug determinista y corto (<=128 chars exigidos por el backend) derivado del
// `cell_id` (que ya codifica los 4 ids + version); no es criptografico, solo
// necesita ser estable para el mismo cell_id.
function deterministicVariantSlug(cellId: string): string {
  let hash = 0;
  for (let index = 0; index < cellId.length; index += 1) {
    hash = (Math.imul(hash, 31) + cellId.charCodeAt(index)) >>> 0;
  }
  return `platform-${hash.toString(16)}`;
}

function finalizeResolution(
  projectId: string,
  resolved: ResolvedPlatformRagVariant,
): ResolvedPlatformRagVariant {
  recordLastResolution(projectId, { ...resolved, resolvedAt: new Date().toISOString() });
  return resolved;
}

async function resolveOnce(
  input: { projectId: string; recipe: PlatformPipelineRecipe },
  deps: PlatformRagVariantResolverDeps,
  attempt: number,
): Promise<ResolvedPlatformRagVariant> {
  // Rule 1: lecturas frescas en cada resolucion; nunca se reusa una matriz de
  // una operacion previa.
  const [configuration, processingProfiles, chunkingProfiles, matrix] = await Promise.all([
    deps.getConfiguration(input.projectId),
    deps.listProcessingProfiles(input.projectId),
    deps.listChunkingProfiles(input.projectId),
    deps.getVariantMatrix(input.projectId),
  ]);

  const processingProfileId = resolveProcessingProfileId(input.recipe.llamaControls, processingProfiles);
  const chunkingProfileId = resolveChunkingProfileId(input.recipe.chunkingProfileId, chunkingProfiles);
  const embeddingProfileId = resolveEmbeddingProfileId(input.recipe.embeddingProfileId, configuration);
  const targetBindingKey = resolveTargetBindingKey(embeddingProfileId, configuration);
  const cell = findMatrixCell(matrix, processingProfileId, chunkingProfileId, embeddingProfileId);

  const variants = await deps.listAllVariants(input.projectId);
  const existing = findMatchingVariant(variants, processingProfileId, chunkingProfileId, embeddingProfileId);
  if (existing) {
    return finalizeResolution(input.projectId, {
      ragVariantId: existing.rag_variant_id,
      cellId: cell.cell_id,
      targetBindingKey,
      created: false,
    });
  }

  try {
    const created = await deps.createVariant(input.projectId, {
      cell_id: cell.cell_id,
      variant_slug: deterministicVariantSlug(cell.cell_id),
    });
    return finalizeResolution(input.projectId, {
      ragVariantId: created.rag_variant_id,
      cellId: cell.cell_id,
      targetBindingKey,
      created: true,
    });
  } catch (error) {
    const code = (error as HttpErrorLike | null)?.code ?? null;
    if (code === "DUPLICATE_VARIANT_RECIPE") {
      const refreshed = await deps.listAllVariants(input.projectId);
      const reused = findMatchingVariant(refreshed, processingProfileId, chunkingProfileId, embeddingProfileId);
      if (reused) {
        return finalizeResolution(input.projectId, {
          ragVariantId: reused.rag_variant_id,
          cellId: cell.cell_id,
          targetBindingKey,
          created: false,
        });
      }
      throw new Error(
        "El backend reporto una variante duplicada pero no se encontro al re-listar. Vuelve a intentarlo.",
      );
    }
    if (code === "STALE_VARIANT_MATRIX_CELL" && attempt < 1) {
      return resolveOnce(input, deps, attempt + 1);
    }
    throw error;
  }
}

export function resolveOrCreatePlatformRagVariant(
  input: { projectId: string; recipe: PlatformPipelineRecipe },
  deps: PlatformRagVariantResolverDeps = defaultPlatformApiDeps,
): Promise<ResolvedPlatformRagVariant> {
  return resolveOnce(input, deps, 0);
}
