import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { EmbeddingBundleInspector } from "./EmbeddingBundleInspector.js";
import type { EmbeddingBundleSummary } from "../embeddingTypes.js";

function bundle(overrides: Partial<EmbeddingBundleSummary> = {}): EmbeddingBundleSummary {
  return {
    embeddingBundleId: "bundle-1",
    sourceChunkBundleId: "chunk-bundle-1",
    embeddingProfileId: "local-bge-m3-v1",
    provider: "local",
    model: "bge-m3",
    modelRevision: "v1",
    dimension: 1024,
    normalization: "l2",
    distanceMetric: "cosine",
    configurationFingerprint: null,
    corpusVersion: "corpus-1",
    bundleSchemaVersion: "1.0",
    sourceContentFingerprint: null,
    vectorDtype: "float32",
    vectorShape: "1024",
    vectorCount: 10,
    checksums: {},
    status: "sealed",
    validationStatus: "passed",
    readinessStatus: "ready",
    sealedAt: "2026-01-01T00:00:00Z",
    links: { self: "", chunks: "", validation: "", indexingReadiness: "" },
    ...overrides,
  };
}

function renderPanel(props: Partial<Parameters<typeof EmbeddingBundleInspector>[0]> = {}) {
  render(
    <EmbeddingBundleInspector
      bundle={bundle()}
      loading={false}
      error={null}
      chunksPage={null}
      chunksLoading={false}
      validation={null}
      readiness={null}
      {...props}
    />,
  );
}

describe("EmbeddingBundleInspector", () => {
  it("shows a danger alert when validation failed to load, instead of silently omitting the section", () => {
    renderPanel({ validationError: "No se pudo cargar la validacion." });

    expect(screen.getByRole("alert").textContent).toContain("No se pudo cargar la validacion.");
  });

  it("shows a danger alert when readiness failed to load, instead of silently omitting the section", () => {
    renderPanel({ readinessError: "No se pudo cargar el readiness." });

    expect(screen.getByRole("alert").textContent).toContain("No se pudo cargar el readiness.");
  });

  it("omits validation/readiness sections when data is simply not loaded yet (no error)", () => {
    renderPanel();

    expect(screen.queryByRole("alert")).toBeNull();
    expect(screen.queryByText(/Indexing readiness/)).toBeNull();
  });

  it("renders the real validation checks when data is present", () => {
    renderPanel({
      validation: {
        embeddingBundleId: "bundle-1",
        status: "passed",
        validatorVersion: "v1",
        checks: [{ name: "dimension_match", passed: true, detail: "" }],
      },
    });

    expect(screen.getByText("dimension_match")).toBeTruthy();
    expect(screen.queryByRole("alert")).toBeNull();
  });
});
