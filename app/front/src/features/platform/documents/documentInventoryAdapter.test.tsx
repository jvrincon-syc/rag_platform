import { describe, expect, it } from "vitest";

import { toInventoryItem } from "./documentInventoryAdapter.js";
import type { ProjectDocumentRevision } from "../platformTypes.js";

function makeRevision(overrides: Partial<ProjectDocumentRevision> = {}): ProjectDocumentRevision {
  return {
    source_document_revision_id: "srev_1",
    logical_document_id: "ldoc_1",
    source_relpath: "manuales/seguridad/proc.pdf",
    file_size: 2048,
    raw_registered: true,
    normalized_registered: false,
    review_state: "pending",
    processing_status: "registered",
    uploaded_at: "2026-01-01T00:00:00Z",
    ...overrides,
  };
}

describe("documentInventoryAdapter", () => {
  it("mapea los campos que Platform sí expone", () => {
    const item = toInventoryItem(makeRevision());

    expect(item.id).toBe("srev_1");
    expect(item.displayName).toBe("manuales/seguridad/proc.pdf");
    expect(item.source).toBe("manuales/seguridad/proc.pdf");
    expect(item.size).toBe(2048);
    expect(item.createdAt).toBe("2026-01-01T00:00:00Z");
    expect(item.status).toEqual({ label: "registered", tone: "neutral" });
  });

  it("usa el logical_document_id como nombre cuando no hay source_relpath", () => {
    const item = toInventoryItem(makeRevision({ source_relpath: "" }));
    expect(item.displayName).toBe("ldoc_1");
  });

  it("asigna tonos visuales de revisión equivalentes a Legacy sin traducir el estado crudo", () => {
    expect(toInventoryItem(makeRevision({ review_state: "needs_review" })).reviewStatus).toEqual({
      label: "needs_review",
      tone: "warning",
    });
    expect(toInventoryItem(makeRevision({ review_state: "pending" })).reviewStatus).toEqual({
      label: "pending",
      tone: "warning",
    });
    expect(toInventoryItem(makeRevision({ review_state: "approved" })).reviewStatus).toEqual({
      label: "approved",
      tone: "success",
    });
    expect(toInventoryItem(makeRevision({ review_state: "processed" })).reviewStatus).toEqual({
      label: "processed",
      tone: "success",
    });
    expect(toInventoryItem(makeRevision({ review_state: "rejected" })).reviewStatus).toEqual({
      label: "rejected",
      tone: "danger",
    });
    expect(toInventoryItem(makeRevision({ review_state: "archived" })).reviewStatus).toEqual({
      label: "archived",
      tone: "neutral",
    });
  });

  it("deriva el estado de normalización desde los flags de registro", () => {
    expect(toInventoryItem(makeRevision({ normalized_registered: true })).normalizationStatus).toEqual({
      label: "Normalizado",
      tone: "success",
    });
    expect(
      toInventoryItem(makeRevision({ normalized_registered: false, raw_registered: true }))
        .normalizationStatus,
    ).toEqual({ label: "Pendiente", tone: "neutral" });
    expect(
      toInventoryItem(makeRevision({ normalized_registered: false, raw_registered: false }))
        .normalizationStatus,
    ).toEqual({ label: "Sin RAW", tone: "neutral" });
  });

  it("expone los IDs canónicos en metadata para el inspector", () => {
    const item = toInventoryItem(makeRevision());
    expect(item.metadata).toEqual([
      { label: "source_document_revision_id", value: "srev_1" },
      { label: "logical_document_id", value: "ldoc_1" },
    ]);
  });

  it("no inventa datos que Platform no tiene: quedan undefined", () => {
    const item = toInventoryItem(makeRevision());
    // Platform no conoce tipo, ingesta, OCR/confianza ni updatedAt.
    expect(item.documentType).toBeUndefined();
    expect(item.ingestionStatus).toBeUndefined();
    expect(item.confidence).toBeUndefined();
    expect(item.updatedAt).toBeUndefined();
  });
});
