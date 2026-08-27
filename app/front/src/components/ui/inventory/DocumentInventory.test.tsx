import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { DocumentInventory } from "./DocumentInventory.js";
import type {
  DocumentInventoryItem,
  InventoryColumn,
  InventoryInspectorSection,
} from "./inventoryTypes.js";

const items: DocumentInventoryItem[] = [
  { id: "a", displayName: "alpha.pdf", source: "alpha.pdf" },
  { id: "b", displayName: "beta.md", source: "beta.md" },
];

const columns: InventoryColumn[] = [
  {
    key: "document",
    header: "Documento",
    render: (item, ctx) => (
      <button type="button" aria-label={`Ver detalle de ${item.displayName}`} onClick={ctx.onInspect}>
        {item.displayName}
      </button>
    ),
  },
];

const sections: InventoryInspectorSection[] = [
  { kind: "metadata", fields: (item) => [{ label: "id", value: item.id }] },
];

function renderInventory(overrides: Partial<Parameters<typeof DocumentInventory>[0]> = {}) {
  return render(
    <DocumentInventory
      items={items}
      columns={columns}
      inspectorSections={sections}
      inspectorTitle="Detalle"
      tableLabel="Inventario de prueba"
      emptyLabel="Sin documentos"
      {...overrides}
    />,
  );
}

describe("DocumentInventory (neutral)", () => {
  it("renderiza acciones de decisión solo cuando la superficie las declara", async () => {
    const onSelect = vi.fn();
    const user = userEvent.setup();
    renderInventory({
      decisionActions: [
        { key: "approve", label: "Aprobar", tone: "primary", onSelect },
      ],
    });

    await user.click(screen.getByRole("button", { name: "Ver detalle de alpha.pdf" }));
    await user.click(screen.getByRole("button", { name: "Aprobar" }));
    expect(onSelect).toHaveBeenCalledWith(items[0]);
  });

  it("sin decisionActions el inspector queda read-only", async () => {
    const user = userEvent.setup();
    renderInventory();

    await user.click(screen.getByRole("button", { name: "Ver detalle de alpha.pdf" }));
    // El inspector abrió (el nombre aparece en fila + inspector: varios nodos).
    expect(screen.getAllByText("alpha.pdf").length).toBeGreaterThan(0);
    // Read-only: sin acciones de decisión declaradas, no se renderiza ninguna.
    expect(screen.queryByRole("button", { name: "Aprobar" })).toBeNull();
  });

  it("el buscador filtra las filas visibles", async () => {
    const user = userEvent.setup();
    renderInventory({ searchPlaceholder: "Buscar" });

    await user.type(screen.getByRole("searchbox", { name: "Buscar" }), "beta");
    expect(screen.getByRole("button", { name: "Ver detalle de beta.md" })).toBeTruthy();
    expect(screen.queryByRole("button", { name: "Ver detalle de alpha.pdf" })).toBeNull();
  });

  it("muestra el mensaje de sin resultados cuando el filtro vacía la tabla", async () => {
    const user = userEvent.setup();
    renderInventory({ searchPlaceholder: "Buscar" });

    await user.type(screen.getByRole("searchbox", { name: "Buscar" }), "zzz");
    expect(screen.getByText("No hay documentos con los filtros actuales.")).toBeTruthy();
  });
});
