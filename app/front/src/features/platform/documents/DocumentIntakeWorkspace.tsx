import {
  AlertTriangle,
  CheckCircle2,
  FileCheck2,
  FileStack,
  FileText,
  Loader2,
  RefreshCw,
} from "lucide-react";
import { DashboardNotice } from "../../dashboard/components/DashboardChrome.js";
import { MetricCard } from "../../../components/ui/MetricCard.js";
import { StatePanel } from "../../../components/ui/StatePanel.js";
import { DocumentInventory } from "../../../components/ui/inventory/DocumentInventory.js";
import type { InventoryAction } from "../../../components/ui/inventory/inventoryTypes.js";
import { RawUploadPanel } from "./RawUploadPanel.js";
import { NormalizationPanel } from "./NormalizationPanel.js";
import { toInventoryItems } from "./documentInventoryAdapter.js";
import {
  platformCheckboxLabel,
  platformDocumentColumns,
  platformDocumentFilters,
  platformInspectorSections,
  platformSelectionSummary,
} from "./documentInventoryConfig.js";
import { useDocumentIntakeWorkspace } from "./useDocumentIntakeWorkspace.js";

// Rollback / dead-end (parity plan 2026-08-25, Task 5-7): Platform ya NO monta
// esta pantalla — la ruta `operations` renderiza el pipeline Legacy real. Se
// conserva como código de reversión hasta que el operador apruebe su limpieza.
// Composición del workspace de intake documental: estado en el hook,
// presentación en los paneles (subir RAW, normalizar) y en el inventario neutral
// (search + filtro + tabla + inspector de detalle). Aquí solo layout, topbar,
// resumen, notice y el cableado del inventario contra las acciones del hook.
export function DocumentIntakeWorkspace() {
  const workspace = useDocumentIntakeWorkspace();
  const loading = workspace.documents.status === "loading";
  // Resumen de procedencia derivado del read-model ya cargado (sin fetch extra).
  const revisions =
    workspace.documents.status === "ready" ? workspace.documents.revisions : [];
  const normalizedCount = revisions.filter((r) => r.normalized_registered).length;
  const needsReviewCount = revisions.filter((r) => r.review_state === "needs_review").length;

  // Acciones en bloque sobre la selección del hook. El estado deshabilitado se
  // calcula aquí (regla de negocio del hook); el inventario neutral solo pinta.
  const bulkActions: InventoryAction[] = [
    {
      key: "select-all",
      label: "Seleccionar todos",
      onSelect: workspace.selectAllRevisions,
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

  return (
    <main className="workspace operator-workspace platform-workspace">
      <header className="topbar">
        <div>
          <h1>Intake documental</h1>
          <p>Lleva documentos desde RAW hasta normalizados dentro del proyecto.</p>
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
      </header>

      {workspace.notice ? (
        <DashboardNotice tone={workspace.notice.tone} message={workspace.notice.message} />
      ) : null}

      {revisions.length > 0 ? (
        <section className="document-summary" aria-label="Resumen de intake">
          <MetricCard
            label="Documentos"
            value={revisions.length}
            icon={<FileStack size={18} />}
            tone="neutral"
          />
          <MetricCard
            label="RAW registrados"
            value={revisions.filter((r) => r.raw_registered).length}
            icon={<FileCheck2 size={18} />}
            tone="neutral"
          />
          <MetricCard
            label="Normalizados"
            value={normalizedCount}
            icon={<CheckCircle2 size={18} />}
            tone={normalizedCount > 0 ? "success" : "neutral"}
          />
          <MetricCard
            label="Requieren revisión"
            value={needsReviewCount}
            icon={<AlertTriangle size={18} />}
            tone={needsReviewCount > 0 ? "warning" : "neutral"}
          />
        </section>
      ) : null}

      <section className="document-grid">
        <div className="document-aside">
          <RawUploadPanel
            disabled={!workspace.projectId}
            uploading={workspace.uploading}
            lastUploadedRevisionId={workspace.lastUploadedRevisionId}
            onUpload={workspace.upload}
          />
          <NormalizationPanel
            variants={workspace.variants}
            selectedVariantId={workspace.selectedVariantId}
            selectedCount={workspace.selectedRevisionIds.size}
            force={workspace.force}
            normalizing={workspace.normalizing}
            canNormalize={workspace.canNormalize}
            report={workspace.report}
            onSelectVariant={workspace.selectVariant}
            onToggleForce={workspace.toggleForce}
            onNormalize={workspace.normalize}
          />
        </div>

        <section className="panel document-main" aria-label="Revisiones registradas">
          <div className="panel-heading">
            <div>
              <h2>Revisiones registradas</h2>
              <span>Marca las revisiones a normalizar; los estados usan texto además de color.</span>
            </div>
          </div>
          <div className="ui-panel-body">
            {workspace.documents.status === "ready" ? (
              <DocumentInventory
                items={toInventoryItems(workspace.documents.revisions)}
                columns={platformDocumentColumns}
                filters={platformDocumentFilters}
                searchPlaceholder="Buscar por ruta o ID"
                selection={{
                  selectedIds: workspace.selectedRevisionIds,
                  onToggle: workspace.toggleRevision,
                  checkboxLabel: platformCheckboxLabel,
                  columnHeader: "Seleccionar",
                  summary: platformSelectionSummary,
                }}
                bulkActions={bulkActions}
                inspectorSections={platformInspectorSections}
                inspectorTitle="Detalle de revisión"
                // Inspector de detalle sin acciones de decisión: en Platform el
                // approve/reject operativo vive en la pantalla Legacy de Revisión
                // (montada por la ruta `review`), no en este inventario.
                decisionActions={undefined}
                tableLabel="Revisiones de documentos del proyecto"
                emptyLabel="Aún no hay documentos en este proyecto. Sube un RAW para empezar."
              />
            ) : workspace.documents.status === "loading" ? (
              <StatePanel kind="loading" message="Cargando revisiones..." />
            ) : workspace.documents.status === "error" ? (
              <StatePanel
                kind="error"
                message={workspace.documents.message}
                onRetry={workspace.refresh}
              />
            ) : workspace.documents.status === "empty" ? (
              <StatePanel
                kind="info"
                icon={<FileText size={24} />}
                message="Aún no hay documentos en este proyecto. Sube un RAW para empezar."
              />
            ) : (
              <StatePanel
                kind="info"
                icon={<FileText size={24} />}
                message="Selecciona un proyecto para ver sus documentos registrados."
              />
            )}
          </div>
        </section>
      </section>
    </main>
  );
}
