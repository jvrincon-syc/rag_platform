// Adaptador puro Platform -> contrato Legacy (`StatusPayload`/`DocumentRecord`).
// Nunca inventa metadata que Platform no expone: los campos ausentes quedan
// `null`/"No expuesto por Platform" en vez de simular un valor real (AGENTS §9).
import type {
  DecisionKind,
  DisplayStatus,
  DocumentRecord,
  ProcessingStatus,
  ReviewDecision,
  ReviewStatus,
  StatusPayload,
} from "../../dashboard/dashboardTypes.js";
import type { ProjectConfiguration, ProjectDocumentRevision } from "../platformTypes.js";

const KNOWN_PROCESSING_STATUSES = new Set<ProcessingStatus>([
  "pending",
  "processed",
  "failed",
  "needs_review",
]);

function toProcessingStatus(value: string): ProcessingStatus {
  if (value === "registered") return "pending";
  if (value === "normalized") return "processed";
  return KNOWN_PROCESSING_STATUSES.has(value as ProcessingStatus)
    ? (value as ProcessingStatus)
    : "needs_review";
}

function toReviewStatus(revision: ProjectDocumentRevision): ReviewStatus {
  if (
    revision.eligibility_decision === "approved_after_review" ||
    revision.eligibility_decision === "operator_waiver"
  ) {
    return "approved";
  }
  if (revision.eligibility_decision === "blocked") return "rejected";
  if (revision.review_state === "needs_review") return "pending";
  return "not_required";
}

function toDisplayStatus(revision: ProjectDocumentRevision): DisplayStatus {
  const reviewStatus = toReviewStatus(revision);
  if (reviewStatus === "approved" || reviewStatus === "rejected") return reviewStatus;
  if (revision.review_state === "needs_review") return "needs_review";
  return toProcessingStatus(revision.processing_status);
}

function toReviewDecision(revision: ProjectDocumentRevision): ReviewDecision | null {
  const reviewStatus = toReviewStatus(revision);
  if (reviewStatus !== "approved" && reviewStatus !== "rejected") return null;
  return {
    document_id: revision.source_document_revision_id,
    source_relpath: revision.source_relpath,
    decision: reviewStatus as DecisionKind,
    reason: revision.eligibility_reason ?? "Decision operacional Platform",
    decided_at: revision.eligibility_decided_at ?? revision.uploaded_at,
  };
}

function basename(sourceRelpath: string): string {
  const parts = sourceRelpath.split("/");
  return parts[parts.length - 1] ?? sourceRelpath;
}

function detectExtension(sourceRelpath: string): string {
  const name = basename(sourceRelpath);
  const dotIndex = name.lastIndexOf(".");
  return dotIndex > 0 ? name.slice(dotIndex) : "bin";
}

function toDocumentRecord(revision: ProjectDocumentRevision): DocumentRecord {
  const reviewStatus = toReviewStatus(revision);
  const displayStatus = toDisplayStatus(revision);
  return {
    documentId: revision.source_document_revision_id,
    sourceRelpath: revision.source_relpath,
    documentName: basename(revision.source_relpath),
    detectedExtension: detectExtension(revision.source_relpath),
    mimeType: null,
    category: null,
    fileSize: revision.file_size,
    ingestionProvider: "unregistered",
    ingestionProviderLabel: "No expuesto por Platform",
    ingestionMethod: "platform",
    ingestionMethodLabel: "No expuesto por Platform",
    ocrConfidenceKind: "no_expuesto",
    ocrConfidenceValue: null,
    ocrConfidencePercent: null,
    ocrConfidenceLabel: "N/D",
    processingStatus: toProcessingStatus(revision.processing_status),
    displayStatus,
    reviewStatus,
    ingestionDate: revision.uploaded_at,
    reviewReasons: reviewStatus === "pending" ? ["needs_review"] : [],
    reviewDetails: [],
    decision: toReviewDecision(revision),
  };
}

export function toPlatformDashboardStatus(input: {
  projectId: string;
  projectName: string;
  configuration: ProjectConfiguration;
  documents: readonly ProjectDocumentRevision[];
}): StatusPayload {
  const documents = input.documents.map(toDocumentRecord);

  let processed = 0;
  let needsReview = 0;
  let normalizedNeedsReview = 0;
  let failed = 0;
  let approved = 0;
  let rejected = 0;
  input.documents.forEach((revision, index) => {
    const record = documents[index]!;
    switch (record.displayStatus) {
      case "processed":
        processed += 1;
        break;
      case "needs_review":
        needsReview += 1;
        if (revision.normalized_registered) normalizedNeedsReview += 1;
        break;
      case "failed":
        failed += 1;
        break;
      case "approved":
        approved += 1;
        break;
      case "rejected":
        rejected += 1;
        break;
      default:
        break;
    }
  });

  return {
    summary: {
      total: documents.length,
      processed,
      needsReview,
      normalizedNeedsReview,
      failed,
      approved,
      rejected,
      runId: null,
      generatedAt: new Date().toISOString(),
      schemaVersion: `platform-config-v${input.configuration.version}`,
    },
    llamaFirst: {
      provider: "unregistered",
      configurationStatus: "not_configured",
      cloudEnabled: false,
      localFallbackEnabled: false,
    },
    settings: {
      ocrReviewThreshold: 0,
      ocrReviewThresholdPercent: 0,
    },
    documents,
    needsReview: documents.filter((record) => record.reviewStatus === "pending"),
    errors: [],
    validation: null,
    manifests: {},
  };
}
