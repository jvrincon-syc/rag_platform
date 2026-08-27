import { useMemo, useState } from "react";
import { FileText, ListFilter, Search } from "lucide-react";

import { StatusBadge } from "../StatusBadge.js";
import type {
  DocumentInventoryItem,
  InventoryAction,
  InventoryColumn,
  InventoryDecisionAction,
  InventoryFilter,
  InventoryInspectorSection,
  InventorySelection,
  InventoryStatusChip,
} from "./inventoryTypes.js";

// Inventario documental NEUTRAL y config-driven: toolbar (search + filtros +
// acciones en bloque), tabla por columnas declaradas e inspector lateral
// read-only por defecto. No importa tipos de ninguna superficie; recibe items ya
// resueltos y configuración explícita. La superficie (Platform/Legacy) decide
// columnas, filtros, secciones del inspector y si hay acciones de decisión.
export function DocumentInventory({
  items,
  columns,
  filters = [],
  searchPlaceholder = "Buscar documento",
  getSearchText,
  selection,
  bulkActions = [],
  inspectorSections,
  inspectorTitle,
  decisionActions,
  tableLabel,
  emptyLabel,
  noMatchesLabel = "No hay documentos con los filtros actuales.",
}: {
  items: DocumentInventoryItem[];
  columns: InventoryColumn[];
  filters?: InventoryFilter[];
  searchPlaceholder?: string;
  getSearchText?: (item: DocumentInventoryItem) => string;
  selection?: InventorySelection;
  bulkActions?: InventoryAction[];
  inspectorSections: InventoryInspectorSection[];
  inspectorTitle: string;
  decisionActions?: InventoryDecisionAction[];
  tableLabel: string;
  emptyLabel: string;
  noMatchesLabel?: string;
}) {
  const [query, setQuery] = useState("");
  const [filterValues, setFilterValues] = useState<Record<string, string>>({});
  const [inspectedId, setInspectedId] = useState<string | null>(null);

  const searchText = getSearchText ?? defaultSearchText;

  const visibleItems = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();
    return items.filter((item) => {
      if (normalizedQuery && !searchText(item).toLowerCase().includes(normalizedQuery)) {
        return false;
      }
      return filters.every((filter) => {
        const value = filterValues[filter.id] ?? "";
        return value === "" || filter.matches(item, value);
      });
    });
  }, [items, query, filters, filterValues, searchText]);

  // El inspector persiste sobre el corpus completo aunque el filtro oculte la fila.
  const inspectedItem = inspectedId
    ? (items.find((item) => item.id === inspectedId) ?? null)
    : null;

  const selectedCount = selection
    ? items.filter((item) => selection.selectedIds.has(item.id)).length
    : 0;

  return (
    <div className="inventory-layout">
      <div className="inventory-main">
        <InventoryToolbar
          query={query}
          onQueryChange={setQuery}
          searchPlaceholder={searchPlaceholder}
          filters={filters}
          filterValues={filterValues}
          onFilterChange={(id, value) =>
            setFilterValues((current) => ({ ...current, [id]: value }))
          }
          selectionSummary={selection ? selection.summary(selectedCount, items.length) : null}
          hasSelection={selectedCount > 0}
          bulkActions={bulkActions}
        />
        <InventoryTable
          items={visibleItems}
          columns={columns}
          selection={selection}
          inspectedId={inspectedId}
          onInspect={setInspectedId}
          tableLabel={tableLabel}
          emptyLabel={items.length === 0 ? emptyLabel : noMatchesLabel}
        />
      </div>
      <DocumentInspector
        item={inspectedItem}
        title={inspectorTitle}
        sections={inspectorSections}
        decisionActions={decisionActions}
      />
    </div>
  );
}

function defaultSearchText(item: DocumentInventoryItem): string {
  return [item.displayName, item.source ?? "", item.id].join(" ");
}

function InventoryToolbar({
  query,
  onQueryChange,
  searchPlaceholder,
  filters,
  filterValues,
  onFilterChange,
  selectionSummary,
  hasSelection,
  bulkActions,
}: {
  query: string;
  onQueryChange: (value: string) => void;
  searchPlaceholder: string;
  filters: InventoryFilter[];
  filterValues: Record<string, string>;
  onFilterChange: (id: string, value: string) => void;
  selectionSummary: string | null;
  hasSelection: boolean;
  bulkActions: InventoryAction[];
}) {
  // Énfasis contextual: con selección activa la barra se realza (solo CSS, sin
  // ocultar ni retirar controles — el conteo sigue presente para a11y y tests).
  return (
    <div
      className={hasSelection ? "inventory-tools has-selection" : "inventory-tools"}
      role="search"
    >
      <label className="search-field">
        <Search size={16} aria-hidden="true" />
        <input
          type="search"
          value={query}
          placeholder={searchPlaceholder}
          aria-label={searchPlaceholder}
          onChange={(event) => onQueryChange(event.target.value)}
        />
      </label>
      {filters.map((filter) => (
        <label className="filter-field" key={filter.id}>
          <ListFilter size={16} aria-hidden="true" />
          <select
            value={filterValues[filter.id] ?? ""}
            aria-label={filter.label}
            onChange={(event) => onFilterChange(filter.id, event.target.value)}
          >
            {filter.options.map((option) => (
              <option value={option.value} key={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>
      ))}
      {selectionSummary ? (
        <span
          className={
            hasSelection
              ? "inventory-selection-summary active"
              : "inventory-selection-summary"
          }
          aria-live="polite"
        >
          {selectionSummary}
        </span>
      ) : null}
      {bulkActions.map((action) => (
        <button
          className="ghost-button"
          type="button"
          key={action.key}
          onClick={action.onSelect}
          disabled={action.disabled}
        >
          {action.label}
        </button>
      ))}
    </div>
  );
}

function InventoryTable({
  items,
  columns,
  selection,
  inspectedId,
  onInspect,
  tableLabel,
  emptyLabel,
}: {
  items: DocumentInventoryItem[];
  columns: InventoryColumn[];
  selection?: InventorySelection;
  inspectedId: string | null;
  onInspect: (id: string) => void;
  tableLabel: string;
  emptyLabel: string;
}) {
  const columnCount = columns.length + (selection ? 1 : 0);
  return (
    <div className="table-wrap">
      <table aria-label={tableLabel}>
        <thead>
          <tr>
            {selection ? <th scope="col">{selection.columnHeader}</th> : null}
            {columns.map((column) => (
              <th scope="col" key={column.key}>
                {column.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {items.map((item) => {
            const isInspected = item.id === inspectedId;
            return (
              <tr key={item.id} className={isInspected ? "selected-row" : ""}>
                {selection ? (
                  <td>
                    <input
                      type="checkbox"
                      checked={selection.selectedIds.has(item.id)}
                      onChange={() => selection.onToggle(item.id)}
                      aria-label={selection.checkboxLabel(item)}
                    />
                  </td>
                ) : null}
                {columns.map((column) => (
                  <td key={column.key}>
                    {column.render(item, {
                      onInspect: () => onInspect(item.id),
                      isInspected,
                    })}
                  </td>
                ))}
              </tr>
            );
          })}
          {items.length === 0 ? (
            <tr>
              <td className="empty-cell" colSpan={columnCount}>
                {emptyLabel}
              </td>
            </tr>
          ) : null}
        </tbody>
      </table>
    </div>
  );
}

function DocumentInspector({
  item,
  title,
  sections,
  decisionActions,
}: {
  item: DocumentInventoryItem | null;
  title: string;
  sections: InventoryInspectorSection[];
  decisionActions?: InventoryDecisionAction[];
}) {
  if (!item) {
    return (
      <aside className="panel document-inspector" aria-label={title}>
        <div className="panel-heading inspector-heading">
          <div>
            <h3>{title}</h3>
          </div>
        </div>
        <div className="inspector-empty">
          <FileText size={28} aria-hidden="true" />
          <span>Selecciona un documento para ver sus datos auditables.</span>
        </div>
      </aside>
    );
  }

  return (
    <aside className="panel document-inspector" aria-label={title}>
      <div className="panel-heading inspector-heading">
        <div>
          <h3>{title}</h3>
        </div>
        {item.reviewStatus ? <InventoryChip chip={item.reviewStatus} /> : null}
      </div>
      <div className="inspector-body">
        <div className="inspector-title">
          <FileText size={18} aria-hidden="true" />
          <div>
            <strong>{item.displayName}</strong>
            {item.source ? <span>{item.source}</span> : null}
          </div>
        </div>

        {sections.map((section, index) => (
          <InspectorSection key={section.kind + index} section={section} item={item} />
        ))}

        {decisionActions && decisionActions.length > 0 ? (
          <section className="inspector-section">
            <h3>Decisión</h3>
            <div className="inspector-actions">
              {decisionActions.map((action) => (
                <button
                  key={action.key}
                  type="button"
                  className={action.tone === "danger" ? "reject-button" : "approve-button"}
                  disabled={action.disabled ? action.disabled(item) : false}
                  onClick={() => action.onSelect(item)}
                >
                  {action.icon}
                  {action.label}
                </button>
              ))}
            </div>
          </section>
        ) : null}
      </div>
    </aside>
  );
}

function InspectorSection({
  section,
  item,
}: {
  section: InventoryInspectorSection;
  item: DocumentInventoryItem;
}) {
  if (section.kind === "metadata") {
    const fields = section.fields(item);
    if (fields.length === 0) {
      return null;
    }
    return (
      <dl className="metadata-grid">
        {fields.map((field) => (
          <div key={field.label}>
            <dt>{field.label}</dt>
            <dd>{field.value}</dd>
          </div>
        ))}
      </dl>
    );
  }

  const listItems = section.items(item);
  return (
    <section className="inspector-section">
      <h3>{section.title}</h3>
      {listItems.length > 0 ? (
        <ul className="detail-list">
          {listItems.map((entry) => (
            <li key={entry}>{entry}</li>
          ))}
        </ul>
      ) : (
        <span className="muted">{section.emptyLabel}</span>
      )}
    </section>
  );
}

export function InventoryChip({ chip }: { chip: InventoryStatusChip }) {
  return <StatusBadge label={chip.label} tone={chip.tone} />;
}
