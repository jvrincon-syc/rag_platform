import { Cpu, Layers, Loader2, PackagePlus, Scissors } from "lucide-react";
import type { CorpusSnapshot, Variant } from "../platformTypes.js";
import { describeVariant } from "./variantRecipe.js";

// Formulario del draft: en vez de exponer el `rag_variant_id` críptico, deja ELEGIR
// la receta en términos humanos — Embedding (BGE / Voyage) y Chunking (preset) — y
// resuelve la variante concreta que ya existe con esa combinación. El body final es
// EXACTO: {corpus_snapshot_id, rag_variant_id, target_binding_key} (claves lógicas,
// nunca targets físicos). No inventa combinaciones: solo ofrece las que hay variante.
export function ReleaseDraftForm({
  variants,
  snapshots,
  bindingKeys,
  variantId,
  snapshotId,
  bindingKey,
  creating,
  canCreate,
  onVariantChange,
  onSnapshotChange,
  onBindingKeyChange,
  onCreate,
}: {
  variants: Variant[];
  snapshots: CorpusSnapshot[];
  bindingKeys: string[];
  variantId: string | null;
  snapshotId: string | null;
  bindingKey: string | null;
  creating: boolean;
  canCreate: boolean;
  onVariantChange: (value: string) => void;
  onSnapshotChange: (value: string) => void;
  onBindingKeyChange: (value: string) => void;
  onCreate: () => void;
}) {
  const missing: string[] = [];
  if (variants.length === 0) {
    missing.push("una variante RAG (provisiona un backend de embedding en el proyecto)");
  }
  if (snapshots.length === 0) missing.push("un snapshot de corpus");
  if (bindingKeys.length === 0) missing.push("un target binding en la configuración");

  const disabledReason = creating
    ? "Creando draft..."
    : missing.length > 0
      ? `Falta ${missing.join(", ")}.`
      : !variantId
        ? "Elige embedding y chunking."
        : !snapshotId
          ? "Selecciona un snapshot."
          : !bindingKey
            ? "Selecciona un target binding key."
            : null;

  // Recetas legibles de cada variante disponible. La variante activa fija qué
  // embedding/chunking aparecen seleccionados en los dos selectores.
  const recipes = variants.map((variant) => ({ variant, recipe: describeVariant(variant) }));
  const current = recipes.find((entry) => entry.variant.rag_variant_id === variantId) ?? null;

  const embeddingLabels = distinct(recipes.map((entry) => entry.recipe.embeddingLabel));
  const currentEmbedding = current?.recipe.embeddingLabel ?? embeddingLabels[0] ?? "";
  const chunkingLabels = distinct(
    recipes
      .filter((entry) => entry.recipe.embeddingLabel === currentEmbedding)
      .map((entry) => entry.recipe.chunkingLabel),
  );
  const currentChunking = current?.recipe.chunkingLabel ?? chunkingLabels[0] ?? "";

  // Resuelve la variante existente para una combinación (embedding, chunking).
  // Al cambiar de embedding intenta conservar el chunking; si esa pareja no existe,
  // cae al primer chunking disponible de ese embedding.
  function resolveVariant(embeddingLabel: string, chunkingLabel: string): void {
    const exact = recipes.find(
      (entry) =>
        entry.recipe.embeddingLabel === embeddingLabel &&
        entry.recipe.chunkingLabel === chunkingLabel,
    );
    const fallback = recipes.find((entry) => entry.recipe.embeddingLabel === embeddingLabel);
    const resolved = exact ?? fallback;
    if (resolved) {
      onVariantChange(resolved.variant.rag_variant_id);
    }
  }

  return (
    <form
      className="release-draft-form"
      onSubmit={(event) => {
        event.preventDefault();
        onCreate();
      }}
    >
      <div className="release-recipe-fields">
        <div className="ui-field">
          <label htmlFor="release-embedding">
            <Cpu size={13} aria-hidden="true" /> Embedding
          </label>
          <select
            id="release-embedding"
            value={currentEmbedding}
            disabled={variants.length === 0}
            onChange={(event) => resolveVariant(event.target.value, currentChunking)}
          >
            {variants.length === 0 ? <option value="">Sin variantes</option> : null}
            {embeddingLabels.map((label) => (
              <option key={label} value={label}>
                {label}
              </option>
            ))}
          </select>
          <span className="ui-field-note">
            Espacio vectorial de la variante. Local vs Lightning se elige por build (abajo).
            {embeddingLabels.includes("Voyage")
              ? null
              : " ¿Falta Voyage? Provisiónala en Projects → Backend de embedding."}
          </span>
        </div>

        <div className="ui-field">
          <label htmlFor="release-chunking">
            <Scissors size={13} aria-hidden="true" /> Chunking
          </label>
          <select
            id="release-chunking"
            value={currentChunking}
            disabled={variants.length === 0 || chunkingLabels.length === 0}
            onChange={(event) => resolveVariant(currentEmbedding, event.target.value)}
          >
            {chunkingLabels.length === 0 ? <option value="">Sin presets</option> : null}
            {chunkingLabels.map((label) => (
              <option key={label} value={label}>
                {label}
              </option>
            ))}
          </select>
          <span className="ui-field-note">Preset de segmentación del corpus.</span>
        </div>
      </div>

      {current ? (
        <p className="release-resolved-variant" role="note">
          <Layers size={13} aria-hidden="true" />
          Variante resuelta: <code>{current.variant.rag_variant_id}</code>{" "}
          <span className={`ui-status-chip ${current.variant.state === "blocked" ? "warning" : "success"}`}>
            {current.variant.state}
          </span>
        </p>
      ) : null}

      <div className="ui-field">
        <label htmlFor="release-snapshot">Snapshot de corpus</label>
        <select
          id="release-snapshot"
          value={snapshotId ?? ""}
          disabled={snapshots.length === 0}
          onChange={(event) => onSnapshotChange(event.target.value)}
        >
          {snapshots.length === 0 ? <option value="">Sin snapshots disponibles</option> : null}
          {snapshots.map((snapshot) => (
            <option key={snapshot.corpus_snapshot_id} value={snapshot.corpus_snapshot_id}>
              {snapshot.corpus_snapshot_id} · {snapshot.document_count} doc(s)
            </option>
          ))}
        </select>
      </div>

      <div className="ui-field">
        <label htmlFor="release-binding">Target binding key (lógico)</label>
        <select
          id="release-binding"
          value={bindingKey ?? ""}
          disabled={bindingKeys.length === 0}
          onChange={(event) => onBindingKeyChange(event.target.value)}
        >
          {bindingKeys.length === 0 ? <option value="">Sin bindings configurados</option> : null}
          {bindingKeys.map((key) => (
            <option key={key} value={key}>
              {key}
            </option>
          ))}
        </select>
      </div>

      <div className="platform-actions">
        <button
          className="primary-button"
          type="submit"
          disabled={!canCreate}
          title={disabledReason ?? undefined}
        >
          {creating ? <Loader2 className="spin" size={16} /> : <PackagePlus size={16} />}
          Crear draft
        </button>
        {disabledReason ? (
          <span className="ui-hint" role="note">
            {disabledReason}
          </span>
        ) : null}
      </div>
    </form>
  );
}

function distinct(values: string[]): string[] {
  return [...new Set(values)];
}
