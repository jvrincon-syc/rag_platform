// Datasource Platform para el shell de pipeline Legacy compartido
// (`DashboardPipelineApp`): mismo arbol de componentes que Legacy, alimentado
// por `/api/platform/*` y con identidad de proyecto inyectada. La variante RAG
// (PR-4 4.1) es la ya persistida en DB y seleccionada por el operador
// (`ragVariantId`, resuelta por `PlatformLegacyPipelineWorkspace` contra el
// catalogo real de variantes) -- nunca una receta reconstruida desde un Map
// efimero alimentado por controles de UI que se resetean en cada refresh.
import type { DashboardPipelineDataSource } from "../../dashboard/dashboardDataSource.js";
import {
  getConfiguration,
  listAllDocuments,
  normalizeDocuments,
  submitRevisionReviewDecision,
  uploadDocument,
} from "../platformApi.js";
import { toPlatformDashboardStatus } from "./platformDashboardMappers.js";

export function createPlatformDashboardDataSource(input: {
  projectId: string;
  projectName: string;
  ragVariantId: string | null;
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
    async runPipeline() {
      // Fail-closed: sin una variante RAG elegida (ver el selector en
      // Operacion) nunca se adivina ni se crea una implicitamente.
      if (!input.ragVariantId) {
        throw new Error(
          "Selecciona una variante RAG del proyecto (arriba, en Operacion) antes de ejecutar la normalizacion.",
        );
      }

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
        rag_variant_id: input.ragVariantId,
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
    async saveSettings() {
      // Proveedor/OCR no tienen contrato de persistencia en Platform (la
      // receta real es la variante RAG seleccionada arriba, nunca este panel):
      // solo refresca el estado, nunca fabrica un "guardado" que no ocurrio.
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
