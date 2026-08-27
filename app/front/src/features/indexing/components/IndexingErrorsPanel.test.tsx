import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { IndexingErrorsPanel } from "./IndexingErrorsPanel.js";

describe("IndexingErrorsPanel", () => {
  it("shows the failure alert and never the green 'sin errores' note when the load failed", () => {
    render(<IndexingErrorsPanel errorsPage={null} loading={false} error="No se pudo cargar." />);

    expect(screen.getByRole("alert").textContent).toContain("No se pudo cargar.");
    expect(screen.queryByText("Sin errores registrados para este run.")).toBeNull();
  });

  it("shows the green 'sin errores' note only on a real success with zero errors", () => {
    render(
      <IndexingErrorsPanel
        errorsPage={{ items: [], page: 1, pageSize: 25, totalItems: 0, totalPages: 1 }}
        loading={false}
        error={null}
      />,
    );

    expect(screen.getByText("Sin errores registrados para este run.")).toBeTruthy();
    expect(screen.queryByRole("alert")).toBeNull();
  });
});
