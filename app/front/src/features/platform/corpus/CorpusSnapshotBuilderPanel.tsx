import { FileText, Loader2, RefreshCw } from "lucide-react";
import { DashboardNotice } from "../../dashboard/components/DashboardChrome.js";
import { StatePanel } from "../../../components/ui/StatePanel.js";
import { DocumentInventory } from "../../../components/ui/inventory/DocumentInventory.js";
import type { InventoryAction } from "../../../components/ui/inventory/inventoryTypes.js";
import { toInventoryItems } from "../documents/documentInventoryAdapter.js";
import { platformInspectorSections } from "../documents/documentInventoryConfig.js";
import { SnapshotHistory } from "./SnapshotHistory.js";
import {
  buildCorpusInventoryColumns,
  corpusCheckboxLabel,
  corpusSelectionSummary,
  corpusSnapshotFilters,
} from "./corpusInventoryConfig.js";
import { useCorpusSnapshotWorkspace } from "./useCorpusSnapshotWorkspace.js";

// Panel reusable del constructor de snapshot de corpus: estado en el hook
// (lee `project_id` de `PlatformProjectContext`, no de props), presentación en
// el inventario neutral + historial. Hospedado por `RAG / Releases`
// (snapshot -> draft) y, durante la migración, por `CorpusSnapshotWorkspace`
// para no perder cobertura de tests mientras se recompone la ruta.
export function CorpusSnapshotBuilderPanel({ compact = false }: { compact?: boolean } = {}) {
  const workspace = useCorpusSnapshotWorkspace();
  const loading = workspace.candidates.status === "loading";

  return (
    <div className={compact ? "corpus-grid corpus-grid-compact" : "corpus-grid"}>
      {workspace.notice ? (
        <DashboardNotice tone={workspace.notice.tone} message={workspace.notice.message} />
      ) : null}

      <section className="panel corpus-builder" aria-label="Constructor de snapshot">
        <div className="panel-heading">
          <div>
            <h2>Constructor</h2>
            <span>
              Elige revisiones normalizadas; una `needs_review` exige una decisión de
              elegibilidad explícita antes de entrar.
            </span>
          </div>
          <div className="topbar-actions">
            <button
              className="ghost-button"
              type="button"
              onClick={workspace.refresh}
              disabled={!workspace.projectId || loading}
            >
              {loading ? <Loader2 className="spin" size={16} /> : <RefreshCw size={16} />}
              Actualizar
            </button>
          </div>
        </div>
        <div className="ui-panel-body">
          <SnapshotBuilderBody workspace={workspace} />
        </div>
      </section>

      <section className="panel corpus-history" aria-label="Historial de snapshots">
        <div className="panel-heading">
          <div>
            <h2>Historial</h2>
            <span>Snapshots inmutables; el seleccionado se rehidrata tras un refresh.</span>
          </div>
        </div>
        <div className="ui-panel-body">
          <SnapshotHistory
            state={workspace.history}
            selectedSnapshotId={workspace.selectedSnapshotId}
          />
        </div>
      </section>
    </div>
  );
}

// Cuerpo del constructor: los estados no-felices pasan por StatePanel (consistente
// con Intake); el estado `ready` reutiliza el inventario neutral + la acción de
// crear. El gate fail-closed (needs_review sin decisión) se refleja como motivo
// VISIBLE del bloqueo, nunca como un botón fantasma.
function SnapshotBuilderBody({
  workspace,
}: {
  workspace: ReturnType<typeof useCorpusSnapshotWorkspace>;
}) {
  const { candidates } = workspace;

  if (candidates.status === "no-project") {
    return (
      <StatePanel
        kind="info"
        icon={<FileText size={24} />}
        message="Selecciona un proyecto para construir un snapshot de corpus."
      />
    );
  }
  if (candidates.status === "loading") {
    return <StatePanel kind="loading" message="Cargando revisiones elegibles..." />;
  }
  if (candidates.status === "error") {
    return (
      <StatePanel kind="error" message={candidates.message} onRetry={workspace.refresh} />
    );
  }
  if (candidates.status === "empty") {
    return (
      <StatePanel
        kind="info"
        icon={<FileText size={24} />}
        message="No hay revisiones normalizadas. Normaliza documentos antes de crear un snapshot."
      />
    );
  }

  // Acciones en bloque sobre la selección del hook. El estado deshabilitado lo
  // calcula el hook (fail-closed: "todas las elegibles" nunca incluye needs_review);
  // el inventario neutral solo lo pinta.
  const bulkActions: InventoryAction[] = [
    {
      key: "select-all",
      label: "Seleccionar todas las elegibles",
      onSelect: workspace.selectAllEligibleRevisions,
      disabled:
        workspace.bulkSelectableRevisionCount === 0 || workspace.allBulkSelectableSelected,
    },
    {
      key: "clear",
      label: "Limpiar",
      onSelect: workspace.clearRevisionSelection,
      disabled: workspace.selectedRevisionIds.size === 0,
    },
  ];

  const columns = buildCorpusInventoryColumns({
    decisions: workspace.decisions,
    selectedIds: workspace.selectedRevisionIds,
    onSetDecision: workspace.setDecision,
  });

  // Motivo visible del bloqueo: nunca se deshabilita "Crear" sin explicar por qué.
  const disabledReason = workspace.creating
    ? "Creando snapshot..."
    : workspace.selectedRevisionIds.size === 0
      ? "Selecciona al menos una revisión."
      : workspace.pendingReviewIds.length > 0
        ? `Faltan decisiones de elegibilidad para ${workspace.pendingReviewIds.length} revisión(es) needs_review.`
        : null;

  return (
    <>
      <DocumentInventory
        items={toInventoryItems(candidates.revisions)}
        columns={columns}
        filters={corpusSnapshotFilters}
        searchPlaceholder="Buscar por ruta o ID"
        selection={{
          selectedIds: workspace.selectedRevisionIds,
          onToggle: workspace.toggleRevision,
          checkboxLabel: corpusCheckboxLabel,
          columnHeader: "Incluir",
          summary: corpusSelectionSummary,
        }}
        bulkActions={bulkActions}
        inspectorSections={platformInspectorSections}
        inspectorTitle="Detalle de revisión"
        decisionActions={undefined}
        tableLabel="Revisiones elegibles para el snapshot"
        emptyLabel="No hay revisiones normalizadas. Normaliza documentos antes de crear un snapshot."
      />

      <div className="platform-actions">
        <button
          className="primary-button"
          type="button"
          onClick={workspace.createSnapshot}
          disabled={!workspace.canCreate}
          title={disabledReason ?? undefined}
        >
          {workspace.creating ? <Loader2 className="spin" size={16} /> : null}
          Crear snapshot
        </button>
        {disabledReason ? (
          <span className="ui-hint" role="note">
            {disabledReason}
          </span>
        ) : null}
      </div>
    </>
  );
}
