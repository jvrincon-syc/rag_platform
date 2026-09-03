import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { DashboardApp } from "./DashboardApp.js";
import * as dashboardApi from "./dashboardApi.js";
import type { StatusPayload } from "./dashboardTypes.js";

vi.mock("../chunking/ChunkingWorkspace.js", () => ({
  ChunkingWorkspace: () => <h2>Chunking sentinel</h2>,
}));

vi.mock("../embeddingIndexing/EmbeddingIndexingWorkspace.js", () => ({
  EmbeddingIndexingWorkspace: () => <h2>Embedding Indexing sentinel</h2>,
}));

vi.mock("./dashboardApi.js", () => ({
  loadDashboardStatus: vi.fn(),
  promoteDashboardStaging: vi.fn(),
  runDashboardPipeline: vi.fn(),
  saveDashboardSettings: vi.fn(),
  submitDashboardReview: vi.fn(),
  uploadDashboardDocument: vi.fn(),
  validateDashboardBundle: vi.fn(),
}));

const api = vi.mocked(dashboardApi);

function makeDocument(overrides: Partial<StatusPayload["documents"][number]> = {}) {
  return {
    documentId: "doc_1",
    sourceRelpath: "manuales/uno.pdf",
    documentName: "Manual uno",
    detectedExtension: ".pdf",
    mimeType: "application/pdf",
    category: "general_sst",
    fileSize: 1024,
    ingestionProvider: "local" as const,
    ingestionProviderLabel: "Local",
    ingestionMethod: "pdfplumber",
    ingestionMethodLabel: "pdfplumber",
    ocrConfidenceKind: "digital",
    ocrConfidenceValue: null,
    ocrConfidencePercent: null,
    ocrConfidenceLabel: "N/D",
    processingStatus: "processed" as const,
    displayStatus: "processed" as const,
    reviewStatus: "not_required" as const,
    ingestionDate: "2026-01-01T00:00:00Z",
    reviewReasons: [],
    reviewDetails: [],
    decision: null,
    ...overrides,
  };
}

function makeStatus(): StatusPayload {
  const inventory = makeDocument();
  const review = makeDocument({
    documentId: "doc_review",
    documentName: "Manual por revisar",
    sourceRelpath: "manuales/revision.pdf",
    processingStatus: "needs_review",
    displayStatus: "needs_review",
    reviewStatus: "pending",
    reviewReasons: ["ocr_low_confidence"],
  });
  return {
    summary: {
      total: 2,
      processed: 1,
      needsReview: 1,
      normalizedNeedsReview: 0,
      failed: 0,
      approved: 0,
      rejected: 0,
      runId: "run_1",
      generatedAt: "2026-01-01T00:00:00Z",
      schemaVersion: "2.0",
    },
    llamaFirst: {
      provider: "local",
      configurationStatus: "configured",
      cloudEnabled: false,
      localFallbackEnabled: true,
    },
    settings: {
      ocrReviewThreshold: 0.8,
      ocrReviewThresholdPercent: 80,
    },
    documents: [inventory, review],
    needsReview: [review],
    errors: [],
    validation: { status: "passed", errors: 0, path: "data/docs_normalized/_manifests" },
    manifests: {},
  };
}

beforeEach(() => {
  window.localStorage.clear();
  api.loadDashboardStatus.mockResolvedValue(makeStatus());
});

describe("DashboardApp legacy regression", () => {
  it("mantiene navegables review, inventario, chunking y embedding/indexing", async () => {
    const user = userEvent.setup();
    render(<DashboardApp />);

    expect(await screen.findByRole("heading", { name: "RAG Platform - Revision documental" })).toBeTruthy();
    expect(screen.getAllByText("Manual por revisar").length).toBeGreaterThan(0);

    await user.click(screen.getByTitle("RAG Platform - Operacion de ingesta"));
    expect(await screen.findByRole("heading", { name: "RAG Platform - Operacion de ingesta" })).toBeTruthy();
    expect(screen.getByRole("button", { name: /Actualizar/i })).toBeTruthy();
    expect(screen.getByText(/Operaciones SST/i)).toBeTruthy();

    await user.click(screen.getByTitle("RAG Platform - Inventario documental"));
    expect(await screen.findByRole("heading", { name: "RAG Platform - Inventario documental" })).toBeTruthy();
    expect(screen.getByRole("table")).toBeTruthy();

    await user.click(screen.getByTitle("RAG Platform - Chunking local"));
    expect(await screen.findByRole("heading", { name: "Chunking sentinel" })).toBeTruthy();

    await user.click(screen.getByTitle("RAG Platform - Embedding e Indexing"));
    expect(await screen.findByRole("heading", { name: "Embedding Indexing sentinel" })).toBeTruthy();
  });
});
