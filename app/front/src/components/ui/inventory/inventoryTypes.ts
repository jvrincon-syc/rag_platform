import type { ReactNode } from "react";
import type { StatusTone } from "../StatusBadge.js";

// Modelo de vista NEUTRAL para inventarios de documentos. Es un SUPERSET de
// capacidades de presentación: los campos ricos son opcionales para que cada
// superficie (Platform hoy, Legacy al migrar) llene solo lo que su contrato
// expone, sin inventar datos ausentes. No acopla a ningún schema concreto.
export type InventoryTone = StatusTone;

// Chip de estado tonificado (texto + tono, nunca solo color; a11y §8).
export type InventoryStatusChip = { label: string; tone: InventoryTone };

export type InventoryMetadataField = { label: string; value: string };

export type DocumentInventoryItem = {
  id: string;
  displayName: string;
  documentType?: string;
  status?: InventoryStatusChip;
  normalizationStatus?: InventoryStatusChip;
  reviewStatus?: InventoryStatusChip;
  ingestionStatus?: InventoryStatusChip;
  confidence?: string;
  size?: number;
  source?: string;
  createdAt?: string;
  updatedAt?: string;
  metadata?: InventoryMetadataField[];
};

// Contexto por fila que la tabla ofrece a los renderers de columna: permite que
// una columna dispare el inspector sin que la superficie conozca su estado.
export type InventoryRowContext = {
  onInspect: () => void;
  isInspected: boolean;
};

// Columna declarada por la superficie. Una columna sin dato NO se declara: se
// omite por config en vez de pintar celdas vacías.
export type InventoryColumn = {
  key: string;
  header: string;
  render: (item: DocumentInventoryItem, ctx: InventoryRowContext) => ReactNode;
};

export type InventoryFilterOption = { value: string; label: string };

// Filtro de tipo select. `value === ""` significa "todos" y no filtra. La lógica
// de coincidencia la aporta la superficie (`matches`); el componente solo aplica.
export type InventoryFilter = {
  id: string;
  label: string;
  options: InventoryFilterOption[];
  matches: (item: DocumentInventoryItem, value: string) => boolean;
};

// Selección para acciones en bloque (p. ej. normalizar). El fail-closed
// (excluir needs_review de "seleccionar todos") lo decide la superficie: aquí
// solo se pinta el checkbox y se refleja el estado provisto.
export type InventorySelection = {
  selectedIds: ReadonlySet<string>;
  onToggle: (id: string) => void;
  checkboxLabel: (item: DocumentInventoryItem) => string;
  columnHeader: string;
  summary: (selectedCount: number, total: number) => string;
};

// Acción de barra (search/bulk). El estado deshabilitado lo calcula la
// superficie desde su hook; el componente solo lo renderiza.
export type InventoryAction = {
  key: string;
  label: string;
  onSelect: () => void;
  disabled?: boolean;
};

// Secciones del inspector lateral. `metadata` es la rejilla principal; `list`
// cubre motivos/detalles auditables para la migración futura de Legacy.
export type InventoryInspectorSection =
  | {
      kind: "metadata";
      title?: string;
      fields: (item: DocumentInventoryItem) => InventoryMetadataField[];
    }
  | {
      kind: "list";
      title: string;
      items: (item: DocumentInventoryItem) => string[];
      emptyLabel: string;
    };

// Acciones de decisión del inspector (approve/reject en Legacy). Capability-
// driven: Platform lo pasa `undefined` y el inspector queda read-only. Nunca se
// renderiza una acción no soportada.
export type InventoryDecisionAction = {
  key: string;
  label: string;
  tone: "primary" | "danger";
  icon?: ReactNode;
  onSelect: (item: DocumentInventoryItem) => void;
  disabled?: (item: DocumentInventoryItem) => boolean;
};
