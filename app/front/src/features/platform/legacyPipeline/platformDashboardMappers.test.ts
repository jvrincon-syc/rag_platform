import { describe, expect, it } from "vitest";
import { toPlatformDashboardStatus } from "./platformDashboardMappers.js";
import type { ProjectConfiguration, ProjectDocumentRevision } from "../platformTypes.js";

const config: ProjectConfiguration = {
  corpus_organization_policy: "source-folders-v1",
  created_at: "2026-08-25T00:00:00Z",
  document_types: [],
  embedding_profiles: [],
  target_bindings: [],
  version: 3,
};

function revision(overrides: Partial<ProjectDocumentRevision> = {}): ProjectDocumentRevision {
  return {
    file_size: 2048,
    logical_document_id: "doc_manual",
    normalized_registered: true,
    processing_status: "processed",
    raw_registered: true,
    review_state: "processed",
    source_document_revision_id: "srev_1",
    source_relpath: "manuales/manual.pdf",
    uploaded_at: "2026-08-25T12:00:00Z",
    ...overrides,
  };
}

describe("platform dashboard mappers", () => {
  it("maps project document revisions to the legacy StatusPayload without physical fields", () => {
    const payload = toPlatformDashboardStatus({
      projectId: "proj_sst-general",
      projectName: "SST General",
      configuration: config,
      documents: [revision()],
    });

    expect(payload.summary.total).toBe(1);
    expect(payload.summary.processed).toBe(1);
    expect(payload.summary.needsReview).toBe(0);
    expect(payload.summary.schemaVersion).toBe("platform-config-v3");
    expect(payload.documents[0]).toMatchObject({
      documentId: "srev_1",
      sourceRelpath: "manuales/manual.pdf",
      documentName: "manual.pdf",
      category: null,
      ocrConfidenceLabel: "N/D",
      processingStatus: "processed",
      displayStatus: "processed",
      reviewStatus: "not_required",
    });
  });

  it("keeps needs_review visible and pending in the legacy review screen", () => {
    const payload = toPlatformDashboardStatus({
      projectId: "proj_sst-general",
      projectName: "SST General",
      configuration: config,
      documents: [
        revision({
          source_document_revision_id: "srev_needs_review",
          normalized_registered: false,
          processing_status: "needs_review",
          review_state: "needs_review",
        }),
      ],
    });

    expect(payload.summary.needsReview).toBe(1);
    expect(payload.needsReview).toHaveLength(1);
    expect(payload.needsReview[0].reviewStatus).toBe("pending");
    expect(payload.needsReview[0].reviewReasons).toEqual(["needs_review"]);
  });

  it("maps operational blocked decisions to the legacy rejected state", () => {
    const payload = toPlatformDashboardStatus({
      projectId: "proj_sst-general",
      projectName: "SST General",
      configuration: config,
      documents: [
        revision({
          eligibility_decision: "blocked",
          eligibility_reason: "OCR incompleto; no apto para publicar.",
          eligibility_decided_at: "2026-08-25T12:00:00Z",
          review_state: "needs_review",
        }),
      ],
    });

    expect(payload.summary.rejected).toBe(1);
    expect(payload.documents[0].reviewStatus).toBe("rejected");
    expect(payload.documents[0].displayStatus).toBe("rejected");
    expect(payload.documents[0].decision).toMatchObject({
      decision: "rejected",
      reason: "OCR incompleto; no apto para publicar.",
    });
  });
});
