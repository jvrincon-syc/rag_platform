import { FileText } from "lucide-react";

import { InventoryChip } from "../../../components/ui/inventory/DocumentInventory.js";
import type {
  DocumentInventoryItem,
  InventoryColumn,
  InventoryFilter,
  InventoryInspectorSection,
} from "../../../components/ui/inventory/inventoryTypes.js";

// Configuración de presentación Platform para el inventario neutral. Platform
// declara SOLO las columnas que su contrato puede llenar: `[document,
// normalization, review, date]`. El tipo de documento, la ingesta, el OCR y la
// confianza no existen en Platform, así que esas columnas no se declaran (no se
// pintan vacías). El inspector es un panel de DETALLE (no un formulario de
// decisión): `decisionActions` se pasa `undefined` porque en Platform las
// decisiones operativas viven en su superficie propia (la columna de
// elegibilidad del snapshot builder y la pantalla Legacy de Revisión con
// Aprobar/Rechazar), no en este sidecar de inventario.

export const platformDocumentColumns: InventoryColumn[] = [
  {
    key: "document",
    header: "Documento",
    render: (item, ctx) => (
      <div className="doc-cell">
        <FileText size={15} aria-hidden="true" />
        <span>{item.displayName}</span>
        {/* Línea secundaria = ID de revisión (patrón legacy ruta+id). En Platform
            displayName ya es la ruta, así que repetir `source` duplicaría el texto. */}
        <small>{item.id}</small>
        <button
          className="row-detail-button"
          type="button"
          aria-label={`Ver detalle de ${item.displayName}`}
          onClick={ctx.onInspect}
        >
          Ver detalle
        </button>
      </div>
    ),
  },
  {
    key: "normalization",
    header: "Normalización",
    render: (item) =>
      item.normalizationStatus ? <InventoryChip chip={item.normalizationStatus} /> : null,
  },
  {
    key: "review",
    header: "Revisión",
    render: (item) => (item.reviewStatus ? <InventoryChip chip={item.reviewStatus} /> : null),
  },
  {
    key: "date",
    header: "Registrado",
    render: (item) => (item.createdAt ? formatDateTime(item.createdAt) : "-"),
  },
];

// Un único filtro por estado. Fail-closed: "Requieren revisión" aísla las
// revisiones needs_review sin ocultarlas.
export const platformDocumentFilters: InventoryFilter[] = [
  {
    id: "estado",
    label: "Filtrar por estado",
    options: [
      { value: "", label: "Todos los estados" },
      { value: "needs_review", label: "Requieren revisión" },
      { value: "normalized", label: "Normalizados" },
      { value: "not_normalized", label: "Sin normalizar" },
    ],
    matches: (item, value) => {
      if (value === "needs_review") {
        return item.reviewStatus?.label === "needs_review";
      }
      const normalized = item.normalizationStatus?.label === "Normalizado";
      if (value === "normalized") {
        return normalized;
      }
      if (value === "not_normalized") {
        return !normalized;
      }
      return true;
    },
  },
];

// Inspector de detalle: rejilla con los IDs canónicos (del adapter) más los
// estados auditables que Platform sí tiene. processing_status se muestra aquí
// aunque no sea columna, para no ocultarlo. No decide (approve/reject vive en la
// pantalla de Revisión operativa), solo muestra procedencia.
export const platformInspectorSections: InventoryInspectorSection[] = [
  {
    kind: "metadata",
    fields: (item) => [
      ...(item.metadata ?? []),
      ...(item.normalizationStatus
        ? [{ label: "Normalización", value: item.normalizationStatus.label }]
        : []),
      ...(item.reviewStatus ? [{ label: "review_state", value: item.reviewStatus.label }] : []),
      ...(item.status ? [{ label: "processing_status", value: item.status.label }] : []),
      ...(item.size != null ? [{ label: "Tamaño", value: formatBytes(item.size) }] : []),
      ...(item.createdAt ? [{ label: "uploaded_at", value: formatDateTime(item.createdAt) }] : []),
    ],
  },
];

export function platformSelectionSummary(selectedCount: number, total: number): string {
  return `${selectedCount} de ${total} seleccionadas`;
}

export function platformCheckboxLabel(item: DocumentInventoryItem): string {
  return `Seleccionar revisión ${item.id} para normalizar`;
}

function formatBytes(value: number): string {
  if (!Number.isFinite(value)) return "0 B";
  if (value < 1024) return `${value} B`;
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(0)} KB`;
  return `${(value / 1024 / 1024).toFixed(2)} MB`;
}

function formatDateTime(value: string): string {
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }
  return new Intl.DateTimeFormat("es-CO", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(parsed);
}
