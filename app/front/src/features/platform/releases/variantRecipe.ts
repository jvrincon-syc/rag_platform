import type { Variant } from "../platformTypes.js";

// Lectura HUMANA de la receta de una variante a partir de sus profile IDs. La
// variante es la que fija de verdad el embedding y el chunking (el runtime
// local/remoto de BGE se elige aparte, por build). Aquí solo se traduce, nunca se
// inventa: un profile desconocido se muestra crudo para no mentir sobre la receta.

export type EmbeddingKind = "bge" | "voyage" | "other";

export type VariantRecipe = {
  embeddingKind: EmbeddingKind;
  embeddingLabel: string;
  chunkingLabel: string;
};

// BGE-M3 (local-bge-*) y Voyage (local-voyage-*) son los dos espacios vectoriales
// reales del sistema; distinta familia = distinta variante (no intercambiables).
export function describeVariant(variant: Variant): VariantRecipe {
  const emb = variant.embedding_profile_id.toLowerCase();
  const embeddingKind: EmbeddingKind = emb.includes("voyage")
    ? "voyage"
    : emb.includes("bge")
      ? "bge"
      : "other";
  const embeddingLabel =
    embeddingKind === "voyage"
      ? "Voyage"
      : embeddingKind === "bge"
        ? "BGE-M3"
        : variant.embedding_profile_id;
  return {
    embeddingKind,
    embeddingLabel,
    chunkingLabel: friendlyChunking(variant.chunking_profile_id),
  };
}

// Presets de chunking conocidos → nombre corto; el resto se muestra tal cual.
function friendlyChunking(chunkingProfileId: string): string {
  const known: Record<string, string> = {
    "cp_structural-syc": "Structural",
    "structural-v1": "Structural v1",
    "structural-v2": "Structural v2",
  };
  return known[chunkingProfileId] ?? chunkingProfileId;
}
