import type {
  DocumentInventoryItem,
  InventoryColumn,
} from "../../../components/ui/inventory/inventoryTypes.js";
import {
  platformDocumentColumns,
  platformDocumentFilters,
} from "../documents/documentInventoryConfig.js";
import type { EligibilityDecision } from "./useCorpusSnapshotWorkspace.js";

// Configuración Platform del inventario neutral para el CONSTRUCTOR de snapshots.
// Reutiliza tal cual las columnas y el filtro por estado de Intake documental
// (`[document, normalization, review, date]`) y AÑADE una columna propia de corpus:
// la decisión de elegibilidad, que solo el constructor necesita. El resto del
// inventario (search, inspector de detalle, selección) es idéntico a Documents;
// la decisión operativa vive en la columna de elegibilidad, no en el inspector.

export const corpusSnapshotFilters = platformDocumentFilters;

export function corpusCheckboxLabel(item: DocumentInventoryItem): string {
  return `Incluir revisión ${item.id} en el snapshot`;
}

export function corpusSelectionSummary(selectedCount: number, total: number): string {
  return `${selectedCount} de ${total} seleccionadas`;
}

// La columna de elegibilidad es una FACTORÍA porque su render depende del estado
// vivo del hook (selección + decisiones). Se construye donde ese estado está en
// alcance (el workspace) y captura `{decisions, selectedIds, onSetDecision}`.
// Regla de dominio (fail-closed): una revisión `needs_review` SELECCIONADA exige
// una decisión de inclusión explícita; deseleccionarla la excluye (no se manda
// `blocked`). Una revisión no `needs_review` no requiere decisión.
export function buildCorpusInventoryColumns({
  decisions,
  selectedIds,
  onSetDecision,
}: {
  decisions: Readonly<Record<string, EligibilityDecision>>;
  selectedIds: ReadonlySet<string>;
  onSetDecision: (revisionId: string, decision: EligibilityDecision) => void;
}): InventoryColumn[] {
  return [
    ...platformDocumentColumns,
    {
      key: "eligibility",
      header: "Decisión de elegibilidad",
      render: (item) => {
        const selected = selectedIds.has(item.id);
        // `needs_review` es la autoridad de elegibilidad (review_state crudo del
        // adapter). El chip ya lo muestra en la columna Revisión; aquí se decide.
        const needsReview = item.reviewStatus?.label === "needs_review";
        if (selected && needsReview) {
          return (
            <select
              aria-label={`Decisión de elegibilidad para ${item.id}`}
              value={decisions[item.id] ?? ""}
              onChange={(event) =>
                onSetDecision(item.id, event.target.value as EligibilityDecision)
              }
            >
              <option value="" disabled>
                Elegir decisión…
              </option>
              <option value="approved_after_review">Aprobar tras revisión</option>
              <option value="operator_waiver">Waiver de operador</option>
            </select>
          );
        }
        if (needsReview) {
          return <span className="ui-hint">Requiere decisión al incluir</span>;
        }
        return <span className="ui-hint">No requerida</span>;
      },
    },
  ];
}
