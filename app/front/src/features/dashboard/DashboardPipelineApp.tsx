import { FormEvent, useEffect, useMemo, useState } from "react";
import { RefreshCw } from "lucide-react";
import { validateOcrThresholdPercent } from "../../ocrSettings.js";
import { matchesDocumentReviewQuery } from "../../documentReview.js";
import { ChunkingWorkspace } from "../chunking/ChunkingWorkspace.js";
import type { ChunkingApiClient } from "../chunking/chunkingApi.js";
import { EmbeddingIndexingWorkspace } from "../embeddingIndexing/EmbeddingIndexingWorkspace.js";
import type { EmbeddingIndexingApiClient } from "../embeddingIndexing/useEmbeddingIndexingPipeline.js";
import {
  DashboardNotice,
  DashboardSummary,
  LlamaStatusPanel,
  PipelinePanel,
  UploadPanel,
} from "./components/DashboardChrome.js";
import { DashboardSidebar } from "./components/DashboardSidebar.js";
import { InventoryWorkspace, ReviewWorkspace } from "./components/DocumentWorkspaces.js";
import type { DashboardPipelineDataSource } from "./dashboardDataSource.js";
import { DASHBOARD_VIEWS } from "./dashboardNavigation.js";
import { useDashboardPreferences } from "./hooks/useDashboardPreferences.js";
import {
  DEFAULT_APPROVE_REASON,
  DEFAULT_REJECT_REASON,
  type ActionResult,
  type AppView,
  type DashboardUploadForm,
  type DocumentRecord,
  type StatusPayload,
  viewTitles,
} from "./dashboardTypes.js";
import type { NoticeTone } from "./typesInternal.js";

type DashboardNoticeState = {
  tone: NoticeTone;
  message: string;
} | null;

const STATUS_REFRESH_ERROR = "No se pudo cargar el estado.";

export function DashboardPipelineApp({
  dataSource,
  scopeSubtitle,
  forcedActiveView,
  hideInternalNavigation = false,
  userChipLabel = "Operaciones SST",
  chunkingApi,
  embeddingIndexingApi,
}: {
  dataSource: DashboardPipelineDataSource;
  scopeSubtitle?: string;
  forcedActiveView?: AppView;
  hideInternalNavigation?: boolean;
  userChipLabel?: string;
  // Clientes de etapa inyectables (default = undefined -> Legacy global). Platform
  // pasa clientes project-aware para que Chunking/Embedding-Indexing no peguen a
  // endpoints globales (plan 2026-08-25, Task 6 Step 4). Legacy no pasa nada.
  chunkingApi?: ChunkingApiClient;
  embeddingIndexingApi?: EmbeddingIndexingApiClient;
}) {
  const [status, setStatus] = useState<StatusPayload | null>(null);
  const [loading, setLoading] = useState(true);
  const [busyAction, setBusyAction] = useState<string | null>(null);
  const [notice, setNotice] = useState<DashboardNoticeState>(null);
  const [query, setQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [ingestionFilter, setIngestionFilter] = useState("all");
  const [reviewNotes, setReviewNotes] = useState<Record<string, string>>({});
  const [lastResult, setLastResult] = useState<ActionResult | null>(null);
  const [uploadForm, setUploadForm] = useState<DashboardUploadForm>({
    category: "general_sst",
    folder: "manuales",
    file: null,
  });

  const {
    preferences,
    setActiveView,
    setEmbeddingIndexingState,
    setEmbeddingIndexingActiveStage,
    setLlamaControls,
    setOcrThresholdInput,
    setSelectedDocumentId,
  } = useDashboardPreferences(status);

  const activeView = forcedActiveView ?? preferences.activeView;
  const isChunkingView = activeView === "chunking";
  const isStandaloneWorkspaceView =
    activeView === "chunking" || activeView === "embedding-indexing";
  const baseSubtitle = isChunkingView
    ? "Pipeline de ingesta actual - Inspeccion de corridas parent-child y evidencia de chunks"
    : `Pipeline de ingesta actual - Schema ${status?.summary.schemaVersion ?? "2.0"} - ${
        status?.summary.runId ?? "sin run"
      }`;
  const activeViewSubtitle = scopeSubtitle ? `${baseSubtitle} - ${scopeSubtitle}` : baseSubtitle;

  const loadStatus = async () => {
    setLoading(true);
    try {
      const payload = await dataSource.loadStatus();
      setStatus(payload);
    } catch (error) {
      setNotice({
        tone: "danger",
        message: error instanceof Error ? error.message : STATUS_REFRESH_ERROR,
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadStatus();
    // `dataSource` is a stable singleton for Legacy (never re-runs there); for
    // Platform it changes identity per selected project, so switching projects
    // while a pipeline view is already mounted reloads status for the new scope.
  }, [dataSource]);

  const ocrThresholdValidation = useMemo(
    () => validateOcrThresholdPercent(preferences.ocrThresholdInput),
    [preferences.ocrThresholdInput],
  );

  const documents = status?.documents ?? [];
  const pendingReview = status?.needsReview ?? [];

  const categories = useMemo(() => {
    return Array.from(
      new Set(documents.map((document) => document.category).filter(Boolean)),
    ).sort() as string[];
  }, [documents]);

  const ingestionMethodOptions = useMemo(() => {
    return Array.from(
      new Map(
        documents
          .filter((document) => document.ingestionProvider !== "unregistered")
          .map((document) => [
            document.ingestionMethod,
            {
              value: `method:${document.ingestionMethod}`,
              label: document.ingestionMethodLabel,
            },
          ]),
      ).values(),
    ).sort((left, right) => left.label.localeCompare(right.label));
  }, [documents]);

  const filteredDocuments = useMemo(() => {
    return documents.filter((document) => {
      const matchesQuery = matchesDocumentReviewQuery(document, query);
      const matchesStatus =
        statusFilter === "all" ||
        document.displayStatus === statusFilter ||
        document.processingStatus === statusFilter ||
        document.reviewStatus === statusFilter;
      const matchesIngestion =
        ingestionFilter === "all" ||
        ingestionFilter === `provider:${document.ingestionProvider}` ||
        ingestionFilter === `method:${document.ingestionMethod}`;
      return matchesQuery && matchesStatus && matchesIngestion;
    });
  }, [documents, ingestionFilter, query, statusFilter]);

  const selectedReviewDocument = resolveSelectedDocument(
    preferences.selectedDocumentIds.review,
    pendingReview,
  );
  const selectedInventoryDocument = resolveSelectedDocument(
    preferences.selectedDocumentIds.inventory,
    filteredDocuments,
  );

  const handleUpload = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!uploadForm.file) {
      setNotice({ tone: "warning", message: "Selecciona un archivo .pdf o .md." });
      return;
    }

    setBusyAction("upload");
    try {
      const payload = await dataSource.uploadDocument(uploadForm);
      setLastResult(payload);
      setUploadForm((current) => ({ ...current, file: null }));
      setNotice({
        tone: "success",
        message: `Documento cargado: ${payload.sourceRelpath ?? "sin ruta"}`,
      });
      await loadStatus();
    } catch (error) {
      setNotice({
        tone: "danger",
        message: error instanceof Error ? error.message : "No se pudo cargar archivo.",
      });
    } finally {
      setBusyAction(null);
    }
  };

  const submitReview = async (document: DocumentRecord, decision: "approved" | "rejected") => {
    const fallback = decision === "approved" ? DEFAULT_APPROVE_REASON : DEFAULT_REJECT_REASON;
    const reason = (reviewNotes[document.documentId] || fallback).trim();
    setBusyAction(`${decision}:${document.documentId}`);
    try {
      const payload = await dataSource.submitReview({
        documentId: document.documentId,
        decision,
        reason,
      });
      setLastResult(payload);
      setNotice({
        tone: "success",
        message: `${decision === "approved" ? "Aprobado" : "Rechazado"}: ${document.documentName}`,
      });
      await loadStatus();
    } catch (error) {
      setNotice({
        tone: "danger",
        message: error instanceof Error ? error.message : "No se pudo guardar decision.",
      });
    } finally {
      setBusyAction(null);
    }
  };

  const runPipeline = async () => {
    if (ocrThresholdValidation.status !== "valid") {
      setNotice({ tone: "warning", message: ocrThresholdValidation.message });
      return;
    }
    setBusyAction("pipeline");
    try {
      const payload = await dataSource.runPipeline({
        controls: preferences.llamaControls,
        ocrReviewThresholdPercent: ocrThresholdValidation.value,
      });
      setLastResult(payload);
      if (payload.statusPayload) {
        setStatus(payload.statusPayload);
      }
      setNotice({
        tone: "success",
        message: `Ingesta staging finalizada: ${payload.runId ?? "sin run_id"}`,
      });
    } catch (error) {
      setNotice({
        tone: "danger",
        message: error instanceof Error ? error.message : "No se pudo ejecutar ingesta.",
      });
    } finally {
      setBusyAction(null);
    }
  };

  const saveSettings = async () => {
    if (ocrThresholdValidation.status !== "valid") {
      setNotice({ tone: "warning", message: ocrThresholdValidation.message });
      return;
    }
    setBusyAction("settings");
    try {
      const payload = await dataSource.saveSettings({
        ocrReviewThresholdPercent: ocrThresholdValidation.value,
        llamaControls: preferences.llamaControls,
      });
      const savedPercent =
        payload.settings?.ocrReviewThresholdPercent ?? ocrThresholdValidation.value;
      setLastResult({
        ok: payload.ok,
        summary: { ocrReviewThresholdPercent: savedPercent },
      });
      setNotice({
        tone: "success",
        message: "Ajustes guardados.",
      });
      if (payload.status) {
        setStatus(payload.status);
      } else {
        await loadStatus();
      }
    } catch (error) {
      setNotice({
        tone: "danger",
        message: error instanceof Error ? error.message : "No se pudo guardar configuracion.",
      });
    } finally {
      setBusyAction(null);
    }
  };

  const runValidation = async () => {
    setBusyAction("validate");
    try {
      const payload = await dataSource.validateBundle({
        stagingRoot: lastResult?.stagingRoot,
      });
      setLastResult(payload);
      setNotice({
        tone: payload.status === "passed" ? "success" : "warning",
        message: `Validacion ${payload.target === "staging" ? "staging" : "oficial"} ${payload.status}: ${
          payload.errors ?? 0
        } errores.`,
      });
      await loadStatus();
    } catch (error) {
      setNotice({
        tone: "danger",
        message: error instanceof Error ? error.message : "No se pudo validar.",
      });
    } finally {
      setBusyAction(null);
    }
  };

  const promoteStaging = async () => {
    if (!lastResult?.stagingRoot) {
      setNotice({
        tone: "warning",
        message: "Primero ejecuta y valida una ingesta en staging.",
      });
      return;
    }
    setBusyAction("promote");
    try {
      const payload = await dataSource.promoteStaging({
        stagingRoot: lastResult.stagingRoot,
      });
      setLastResult(payload);
      setNotice({
        tone: "success",
        message: `Staging promovido a salida oficial: ${payload.runId ?? "sin run_id"}`,
      });
      await loadStatus();
    } catch (error) {
      setNotice({
        tone: "danger",
        message: error instanceof Error ? error.message : "No se pudo promover staging.",
      });
    } finally {
      setBusyAction(null);
    }
  };

  const handleDocumentSelect = (view: "review" | "inventory", document: DocumentRecord) => {
    setSelectedDocumentId(view, document.documentId);
  };

  // Cuando Platform oculta la nav interna (forcedActiveView/hideInternalNavigation),
  // el sidebar NO se renderiza: el grid de 2 columnas del shell dejaría al
  // workspace metido en la columna de 224px. La variante de 1 columna lo evita
  // sin dejar de ser el MISMO front Legacy.
  const sidebarHidden = hideInternalNavigation || Boolean(forcedActiveView);

  return (
    <div className={sidebarHidden ? "app-shell app-shell--no-sidebar" : "app-shell"}>
      {sidebarHidden ? null : (
        <DashboardSidebar activeView={preferences.activeView} onViewChange={setActiveView} />
      )}
      <main className="workspace">
        <header className="topbar">
          <div>
            <h1>{viewTitles[activeView]}</h1>
            <p>{activeViewSubtitle}</p>
          </div>
          <div className="topbar-actions">
            {sidebarHidden ? null : (
              <div className="view-switcher" aria-label="Cambiar vista">
                {DASHBOARD_VIEWS.map((item) => (
                  <button
                    className={activeView === item.view ? "active" : ""}
                    onClick={() => setActiveView(item.view)}
                    type="button"
                    key={item.view}
                    title={item.title}
                  >
                    {item.switcherLabel}
                  </button>
                ))}
              </div>
            )}
            <button className="ghost-button" onClick={loadStatus} disabled={loading}>
              <RefreshCw size={16} />
              Actualizar
            </button>
            <span className="user-chip">{userChipLabel}</span>
          </div>
        </header>

        {notice ? <DashboardNotice tone={notice.tone} message={notice.message} /> : null}

        {!isStandaloneWorkspaceView ? <DashboardSummary summary={status?.summary ?? null} /> : null}

        {activeView === "operations" ? (
          <>
            <LlamaStatusPanel
              status={status?.llamaFirst ?? null}
              controls={preferences.llamaControls}
              ocrThresholdInput={preferences.ocrThresholdInput}
              ocrThresholdValidation={ocrThresholdValidation}
              settingsBusy={busyAction === "settings"}
              onControlsChange={setLlamaControls}
              onOcrThresholdChange={setOcrThresholdInput}
              onSaveSettings={saveSettings}
            />

            <section className="primary-grid">
              <UploadPanel
                categories={categories}
                form={uploadForm}
                busy={busyAction === "upload"}
                onChange={setUploadForm}
                onSubmit={handleUpload}
              />
              <PipelinePanel
                validation={status?.validation ?? null}
                lastResult={lastResult}
                busyAction={busyAction}
                controls={preferences.llamaControls}
                pipelineBlockedReason={
                  ocrThresholdValidation.status === "valid"
                    ? null
                    : ocrThresholdValidation.message
                }
                onRunPipeline={runPipeline}
                onValidate={runValidation}
                onPromote={promoteStaging}
              />
            </section>
          </>
        ) : null}

        {activeView === "review" ? (
          <ReviewWorkspace
            documents={pendingReview}
            busyAction={busyAction}
            notes={reviewNotes}
            selectedDocument={selectedReviewDocument}
            selectedDocumentId={selectedReviewDocument?.documentId ?? null}
            onSelect={(document) => handleDocumentSelect("review", document)}
            onNoteChange={(documentId, value) =>
              setReviewNotes((current) => ({ ...current, [documentId]: value }))
            }
            onReview={submitReview}
          />
        ) : null}

        {activeView === "inventory" ? (
          <InventoryWorkspace
            documents={filteredDocuments}
            total={documents.length}
            query={query}
            statusFilter={statusFilter}
            ingestionFilter={ingestionFilter}
            ingestionMethodOptions={ingestionMethodOptions}
            selectedDocument={selectedInventoryDocument}
            selectedDocumentId={selectedInventoryDocument?.documentId ?? null}
            onSelect={(document) => handleDocumentSelect("inventory", document)}
            onQueryChange={setQuery}
            onStatusFilterChange={setStatusFilter}
            onIngestionFilterChange={setIngestionFilter}
          />
        ) : null}

        {activeView === "chunking" ? <ChunkingWorkspace api={chunkingApi} /> : null}

        {activeView === "embedding-indexing" ? (
          <EmbeddingIndexingWorkspace
            activeStage={preferences.embeddingIndexing.activeStage}
            embeddingIndexingState={preferences.embeddingIndexing}
            onStageChange={setEmbeddingIndexingActiveStage}
            onEmbeddingIndexingStateChange={setEmbeddingIndexingState}
            api={embeddingIndexingApi}
          />
        ) : null}
      </main>
    </div>
  );
}

function resolveSelectedDocument(
  preferredDocumentId: string | null,
  documents: DocumentRecord[],
) {
  if (preferredDocumentId) {
    const selected = documents.find((document) => document.documentId === preferredDocumentId);
    if (selected) {
      return selected;
    }
  }

  return documents[0] ?? null;
}
