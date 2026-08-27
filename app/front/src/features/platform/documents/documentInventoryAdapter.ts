import type { StatusTone } from "../../../components/ui/StatusBadge.js";
import type { DocumentInventoryItem } from "../../../components/ui/inventory/inventoryTypes.js";
import type { ProjectDocumentRevision } from "../platformTypes.js";

const REVIEW_STATE_TONES: Record<string, StatusTone> = {
  approved: "success",
  needs_review: "warning",
  pending: "warning",
  processed: "success",
  rejected: "danger",
};

// Adapter Platform: ProjectDocumentRevision -> DocumentInventoryItem. Solo mapea
// lo que el contrato Platform expone. Los campos ricos que Platform NO tiene
// (documentType, ingestionStatus, confidence) quedan `undefined`: nunca se
// inventan ni se rellenan con "unknown" como dato semántico (fail-closed).
export function toInventoryItem(revision: ProjectDocumentRevision): DocumentInventoryItem {
  return {
    id: revision.source_document_revision_id,
    displayName: revision.source_relpath || revision.logical_document_id,
    source: revision.source_relpath,
    // review_state se muestra crudo (auditable), con el mismo tono semantico de Legacy.
    reviewStatus: { label: revision.review_state, tone: REVIEW_STATE_TONES[revision.review_state] ?? "neutral" },
    normalizationStatus: revision.normalized_registered
      ? { label: "Normalizado", tone: "success" }
      : { label: revision.raw_registered ? "Pendiente" : "Sin RAW", tone: "neutral" },
    // processing_status crudo: es el estado técnico auditable, no se traduce.
    status: { label: revision.processing_status, tone: "neutral" },
    size: revision.file_size,
    createdAt: revision.uploaded_at,
    // IDs canónicos para el inspector de detalle. El target físico y el actor
    // nunca cruzan la UI (invariantes Fase 7): solo IDs lógicos/de revisión.
    metadata: [
      { label: "source_document_revision_id", value: revision.source_document_revision_id },
      { label: "logical_document_id", value: revision.logical_document_id },
    ],
  };
}

export function toInventoryItems(
  revisions: readonly ProjectDocumentRevision[],
): DocumentInventoryItem[] {
  return revisions.map(toInventoryItem);
}
