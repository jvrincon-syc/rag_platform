import { useEffect, useMemo, useState } from "react";
import { Cpu, Loader2, Scissors } from "lucide-react";
import { StatePanel } from "../../../components/ui/StatePanel.js";
import { DashboardPipelineApp } from "../../dashboard/DashboardPipelineApp.js";
import type { AppView } from "../../dashboard/dashboardTypes.js";
import { usePlatformProjectContext } from "../PlatformProjectContext.js";
import { listAllVariants } from "../platformApi.js";
import type { Variant } from "../platformTypes.js";
import { describeVariant } from "../releases/variantRecipe.js";
import { createPlatformDashboardDataSource } from "./platformDashboardDataSource.js";

// Host Platform del pipeline Legacy compartido: monta el MISMO
// `DashboardPipelineApp` que la lane Legacy, con datasource/scope propios de
// proyecto. No dibuja tablas/paneles/inspectores de pipeline por su cuenta.
export function PlatformLegacyPipelineWorkspace({ activeView }: { activeView: AppView }) {
  const { projectId, selectedProject, preferences, setSelectedRagVariant } =
    usePlatformProjectContext();

  // Solo Operacion necesita una variante RAG resuelta: es la que usa la
  // normalizacion nativa (PR-4 4.1). Revision/Inventario no la requieren, asi
  // que el fetch se evita fuera de Operacion.
  const needsVariant = activeView === "operations";
  const [variants, setVariants] = useState<Variant[]>([]);
  const [variantsLoading, setVariantsLoading] = useState(false);
  const [variantsError, setVariantsError] = useState<string | null>(null);

  useEffect(() => {
    if (!needsVariant || !projectId) {
      return;
    }
    const controller = new AbortController();
    setVariantsLoading(true);
    setVariantsError(null);
    void (async () => {
      try {
        const all = await listAllVariants(projectId, { signal: controller.signal });
        if (controller.signal.aborted) return;
        setVariants(all);
      } catch (error) {
        if (controller.signal.aborted) return;
        setVariantsError(
          error instanceof Error ? error.message : "No se pudo cargar el catalogo de variantes.",
        );
      } finally {
        if (!controller.signal.aborted) setVariantsLoading(false);
      }
    })();
    return () => controller.abort();
  }, [needsVariant, projectId]);

  // Fail-closed: auto-selecciona SOLO cuando hay exactamente una variante y
  // ninguna seleccion valida todavia; nunca adivina entre varias (mismo
  // criterio que el resto del resolutor de receta). Si la seleccion guardada
  // deja de existir en el catalogo vivo, se limpia en vez de arrastrar un id
  // muerto.
  useEffect(() => {
    if (!needsVariant) return;
    const current = preferences.selectedRagVariantId;
    const stillValid = current !== null && variants.some((v) => v.rag_variant_id === current);
    if (stillValid) return;
    if (current !== null && !stillValid) {
      setSelectedRagVariant(null);
      return;
    }
    if (variants.length === 1) {
      setSelectedRagVariant(variants[0]!.rag_variant_id);
    }
  }, [needsVariant, variants, preferences.selectedRagVariantId, setSelectedRagVariant]);

  const ragVariantId = needsVariant ? preferences.selectedRagVariantId : null;

  const dataSource = useMemo(() => {
    if (!projectId) return null;
    return createPlatformDashboardDataSource({
      projectId,
      projectName: selectedProject?.display_name ?? projectId,
      ragVariantId,
    });
  }, [projectId, selectedProject?.display_name, ragVariantId]);

  if (!projectId || !dataSource) {
    return (
      <section className="panel">
        <StatePanel
          kind="info"
          message="Selecciona un proyecto para abrir el pipeline Legacy con scope Platform."
        />
      </section>
    );
  }

  return (
    <>
      {needsVariant ? (
        <OperationsVariantBar
          variants={variants}
          loading={variantsLoading}
          error={variantsError}
          selectedId={ragVariantId}
          onSelect={setSelectedRagVariant}
        />
      ) : null}
      <DashboardPipelineApp
        dataSource={dataSource}
        forcedActiveView={activeView}
        scopeSubtitle={`Proyecto ${selectedProject?.display_name ?? projectId}`}
        userChipLabel={selectedProject?.display_name ?? projectId}
      />
    </>
  );
}

// Barra de contexto de la variante RAG que usara la normalizacion nativa
// (Operacion). Nunca crea una variante: elegir/crear vive en Projects/RAG
// Releases (DB); esto solo selecciona entre las ya existentes del proyecto.
function OperationsVariantBar({
  variants,
  loading,
  error,
  selectedId,
  onSelect,
}: {
  variants: Variant[];
  loading: boolean;
  error: string | null;
  selectedId: string | null;
  onSelect: (variantId: string | null) => void;
}) {
  const selected = variants.find((v) => v.rag_variant_id === selectedId) ?? null;
  const recipe = selected ? describeVariant(selected) : null;

  return (
    <section className="panel operations-variant-bar" aria-label="Variante RAG para esta operacion">
      <div className="ui-field">
        <label htmlFor="operations-variant-select">Variante RAG</label>
        {loading ? (
          <span className="ui-hint">
            <Loader2 className="spin" size={14} aria-hidden="true" /> Cargando variantes...
          </span>
        ) : error ? (
          <span role="alert" className="ui-field-note">
            {error}
          </span>
        ) : variants.length === 0 ? (
          <span role="alert" className="ui-field-note">
            Este proyecto no tiene variantes RAG. Crea o provisiona una en Projects antes de
            normalizar.
          </span>
        ) : (
          <>
            <select
              id="operations-variant-select"
              value={selectedId ?? ""}
              onChange={(event) => onSelect(event.target.value || null)}
            >
              <option value="" disabled>
                {variants.length > 1 ? "Selecciona una variante..." : "Sin seleccion"}
              </option>
              {variants.map((variant) => (
                <option key={variant.rag_variant_id} value={variant.rag_variant_id}>
                  {variant.rag_variant_id}
                </option>
              ))}
            </select>
            {recipe ? (
              <span className="ui-hint">
                <Cpu size={12} aria-hidden="true" /> {recipe.embeddingLabel} ·{" "}
                <Scissors size={12} aria-hidden="true" /> {recipe.chunkingLabel}
              </span>
            ) : (
              <span className="ui-hint">Elige la variante que fija la receta de esta normalizacion.</span>
            )}
          </>
        )}
      </div>
    </section>
  );
}
