// Datasource Platform para el shell de pipeline Legacy compartido
// (`DashboardPipelineApp`): mismo arbol de componentes que Legacy, alimentado
// por `/api/platform/*` y con identidad de proyecto inyectada. La variante
// RAG nunca se toma de una preferencia guardada: se resuelve/crea aqui a
// partir de la receta configurada en las pantallas Legacy (ver
// `platformRagVariantResolver`).
import type { DashboardPipelineDataSource } from "../../dashboard/dashboardDataSource.js";
import {
  getConfiguration,
  listAllDocuments,
  normalizeDocuments,
  submitRevisionReviewDecision,
  uploadDocument,
} from "../platformApi.js";
import { toPlatformDashboardStatus } from "./platformDashboardMappers.js";
import { readRecipeDraft, recordProcessingControls } from "./platformRecipeDraft.js";
import { resolveOrCreatePlatformRagVariant } from "./platformRagVariantResolver.js";

export function createPlatformDashboardDataSource(input: {
  projectId: string;
  projectName: string;
}): DashboardPipelineDataSource {
  async function loadStatus() {
    const [configuration, documents] = await Promise.all([
      getConfiguration(input.projectId),
      listAllDocuments(input.projectId),
    ]);
    return toPlatformDashboardStatus({
      projectId: input.projectId,
      projectName: input.projectName,
      configuration,
      documents,
    });
  }

  return {
    loadStatus,
    async uploadDocument(form) {
      if (!form.file) throw new Error("Selecciona un archivo .pdf o .md.");
      // POST /documents solo acepta file + source_relpath. El nombre del
      // documento se deriva del documentName del formulario.
      const name = form.documentName.trim() || form.file.name;
      const folder = form.folder.trim().replace(/^\/+|\/+$/g, "");
      const baseName = name.includes(".") ? name : `${name}${form.file.name.match(/\.[^.]+$/)?.[0] ?? ".md"}`;
      const sourceRelpath = folder ? `${folder}/${baseName}` : baseName;
      const revision = await uploadDocument(input.projectId, form.file, sourceRelpath);
      return {
        ok: true,
        status: revision.processing_status,
        sourceRelpath: revision.source_relpath,
        summary: { uploaded: 1 },
        statusPayload: await loadStatus(),
      };
    },
    async runPipeline({ controls }) {
      // La variante se CONSTRUYE a partir de la configuracion de las pantallas
      // (receta primero), nunca de una preferencia guardada.
      recordProcessingControls(input.projectId, controls);
      const resolved = await resolveOrCreatePlatformRagVariant({
        projectId: input.projectId,
        recipe: readRecipeDraft(input.projectId),
      });

      // Los ids de revision salen del read-model CRUDO de Platform
      // (listAllDocuments), nunca del StatusPayload ya mapeado a display Legacy.
      const revisions = await listAllDocuments(input.projectId);
      const revisionIds = revisions
        .filter((revision) => revision.eligibility_decision !== "blocked")
        .filter(
          (revision) =>
            revision.review_state === "processed" ||
            revision.eligibility_decision === "approved_after_review" ||
            revision.eligibility_decision === "operator_waiver",
        )
        .map((revision) => revision.source_document_revision_id);

      const report = await normalizeDocuments(input.projectId, {
        rag_variant_id: resolved.ragVariantId,
        document_revision_ids: revisionIds,
        force: false,
      });
      return {
        ok: report.failed === 0,
        status: report.failed === 0 ? "processed" : "failed",
        runId: report.rag_variant_id,
        summary: {
          processed: report.processed,
          needs_review: report.needs_review,
          failed: report.failed,
          skipped: report.skipped,
        },
        statusPayload: await loadStatus(),
      };
    },
    async saveSettings({ llamaControls }) {
      // Lo UNICO que persiste es el leg de Operacion de la receta (por
      // proyecto, alcance de sesion) para el resolutor. El umbral OCR no tiene
      // contrato Platform: su input va deshabilitado-con-motivo y nunca se
      // simula su guardado.
      recordProcessingControls(input.projectId, llamaControls);
      return {
        ok: true,
        status: await loadStatus(),
      };
    },
    // Botones deshabilitados-con-motivo bajo Platform (capacidad declarada via
    // el prop opcional de DashboardChrome); estos throws son el fail-closed de
    // respaldo por si algo los invoca igualmente.
    async validateBundle() {
      throw new Error(
        "En Platform la validacion se ejecuta desde RAG / Releases sobre un rag_release_id.",
      );
    },
    async promoteStaging() {
      throw new Error("Platform no promueve staging global; crea snapshot y release por proyecto.");
    },
    async submitReview({ documentId, decision, reason }) {
      const eligibilityDecision = decision === "approved" ? "approved_after_review" : "blocked";
      const record = await submitRevisionReviewDecision(input.projectId, documentId, {
        decision: eligibilityDecision,
        reason,
      });
      return {
        ok: true,
        status: decision,
        runId: record.decision_id,
        summary: { [decision]: 1 },
        statusPayload: await loadStatus(),
      };
    },
  };
}
