import {
  AlertCircle,
  Bot,
  GitBranch,
  Layers3,
  Loader2,
  Radar,
  RefreshCw,
  Rocket,
} from "lucide-react";
import { DashboardNotice } from "../../dashboard/components/DashboardChrome.js";
import { RetrievalProfilesPanel } from "../../retrieval/components/RetrievalProfilesPanel.js";
import { RetrievalSearchPanel } from "../../retrieval/components/RetrievalSearchPanel.js";
import { RetrievalStatusPanel } from "../../retrieval/components/RetrievalStatusPanel.js";
import { RetrievalValidationPanel } from "../../retrieval/components/RetrievalValidationPanel.js";
import { CorpusSnapshotBuilderPanel } from "../corpus/CorpusSnapshotBuilderPanel.js";
import { BuildReport } from "./BuildReport.js";
import { ReleaseDraftForm } from "./ReleaseDraftForm.js";
import { ReleaseHistory } from "./ReleaseHistory.js";
import { ReleaseLifecycle } from "./ReleaseLifecycle.js";
import { useRagReleaseWorkspace } from "./useRagReleaseWorkspace.js";
import type { ReleaseWorkspaceData } from "./useRagReleaseWorkspace.js";
import { useReleaseRetrievalPanel } from "./useReleaseRetrievalPanel.js";

// Composición pura del release lifecycle workspace: estado en el hook, presentación
// en los subcomponentes. Aquí solo layout, topbar, notice y estados globales.
export function RagReleaseWorkspace() {
  const workspace = useRagReleaseWorkspace();
  const loading = workspace.load.status === "loading";

  return (
    <main className="workspace operator-workspace platform-workspace">
      <header className="topbar">
        <div>
          <h1>Ciclo de vida de releases</h1>
          <p>
            De un draft (variante + snapshot + binding lógico) a build, validación,
            publicación y retiro. El backend resuelve la receta; React nunca orquesta
            chunking/embedding/indexing legacy.
          </p>
        </div>
        <div className="topbar-actions">
          <button
            className="ghost-button"
            type="button"
            onClick={workspace.refresh}
            disabled={!workspace.projectId || loading}
          >
            {loading ? <Loader2 className="spin" size={16} /> : <RefreshCw size={16} />}
            Actualizar
          </button>
        </div>
      </header>

      {workspace.notice ? (
        <DashboardNotice tone={workspace.notice.tone} message={workspace.notice.message} />
      ) : null}

      <RagReleaseBody workspace={workspace} />
    </main>
  );
}

function RagReleaseBody({ workspace }: { workspace: ReturnType<typeof useRagReleaseWorkspace> }) {
  const { load } = workspace;
  const retrieval = useReleaseRetrievalPanel();

  if (load.status === "no-project") {
    return (
      <section className="panel">
        <div className="ui-empty">
          <Rocket size={24} />
          <span>Selecciona un proyecto para gestionar sus releases.</span>
        </div>
      </section>
    );
  }

  // Retrieval es independiente del estado de carga de releases (no depende de
  // la release ni del proyecto, ver nota en `useReleaseRetrievalPanel`): un
  // fallo o loading de `load` no debe ocultar un panel que ya cargó bien.
  return (
    <>
      {load.status === "loading" ? (
        <section className="panel">
          <div className="ui-empty">
            <Loader2 className="spin" size={22} />
            <span>Cargando releases y opciones del draft...</span>
          </div>
        </section>
      ) : null}

      {load.status === "error" ? (
        <section className="panel">
          <div className="ui-empty">
            <AlertCircle size={24} />
            <span role="alert">{load.message}</span>
            <button className="secondary-button" type="button" onClick={workspace.refresh}>
              <RefreshCw size={16} />
              Reintentar
            </button>
          </div>
        </section>
      ) : null}

      {load.status === "ready" ? (
        <ReleaseSections workspace={workspace} data={load.data} />
      ) : null}

      <RetrievalDiagnosticsSection retrieval={retrieval} />
    </>
  );
}

function ReleaseSections({
  workspace,
  data,
}: {
  workspace: ReturnType<typeof useRagReleaseWorkspace>;
  data: ReleaseWorkspaceData;
}) {
  const publishedReleases = data.releases.filter((release) => release.state === "published");

  return (
    <>
      <section className="panel" aria-label="Snapshot de corpus">
        <div className="panel-heading">
          <div>
            <h2>Snapshot de corpus</h2>
            <span>Congela revisiones aprobadas antes de crear una release.</span>
          </div>
        </div>
        <div className="ui-panel-body">
          <CorpusSnapshotBuilderPanel />
        </div>
      </section>

      <section className="panel" aria-label="Mapa de variantes y releases">
        <div className="panel-heading">
          <div>
            <h2>Mapa RAG del proyecto</h2>
            <span>
              Recorre primero las variantes del proyecto y luego sus releases. Publicada =
              usable por API chatbot.
            </span>
          </div>
        </div>
        <div className="ui-panel-body">
          <dl className="ui-metrics release-overview-metrics">
            <div>
              <dt>
                <GitBranch size={14} aria-hidden="true" /> Variantes RAG
              </dt>
              <dd>{data.variants.length}</dd>
            </div>
            <div>
              <dt>
                <Layers3 size={14} aria-hidden="true" /> Releases
              </dt>
              <dd>{data.releases.length}</dd>
            </div>
            <div>
              <dt>
                <Bot size={14} aria-hidden="true" /> Publicadas para chatbot
              </dt>
              <dd>{publishedReleases.length}</dd>
            </div>
            <div>
              <dt>Release en gestión</dt>
              <dd>{workspace.selectedRelease?.rag_release_id ?? "Sin selección"}</dd>
            </div>
          </dl>

          <p className="ui-note release-overview-note">
            <Bot size={16} aria-hidden="true" />
            La API chatbot no elige una release activa global: cualquier release publicada puede
            responder si el cliente envía su <code>rag_release_id</code>.
          </p>
        </div>
      </section>

      <section className="release-grid">
        <div className="release-aside">
          <section className="panel" aria-label="Variantes y releases del proyecto">
            <div className="panel-heading">
              <div>
                <h2>Variantes y releases</h2>
                <span>
                  Cada bloque representa una <code>rag_variant_id</code> y debajo muestra sus
                  releases y su estado operativo.
                </span>
              </div>
            </div>
            <div className="ui-panel-body">
              <ReleaseHistory
                releases={data.releases}
                variants={data.variants}
                selectedReleaseId={workspace.selectedReleaseId}
                onSelect={workspace.selectRelease}
              />
            </div>
          </section>

          <section className="panel" aria-label="Nuevo draft de release">
            <div className="panel-heading">
              <div>
                <h2>Nuevo draft</h2>
                <span>Congela variante, snapshot y binding lógico en una release reproducible.</span>
              </div>
            </div>
            <div className="ui-panel-body">
              <ReleaseDraftForm
                variants={data.variants}
                snapshots={data.snapshots}
                bindingKeys={data.bindingKeys}
                variantId={workspace.draftVariantId}
                snapshotId={workspace.draftSnapshotId}
                bindingKey={workspace.draftBindingKey}
                creating={workspace.creating}
                canCreate={workspace.canCreateDraft}
                onVariantChange={workspace.setDraftVariantId}
                onSnapshotChange={workspace.setDraftSnapshotId}
                onBindingKeyChange={workspace.setDraftBindingKey}
                onCreate={workspace.createDraft}
              />
            </div>
          </section>
        </div>

        <div className="release-main">
          <section className="panel" aria-label="Gestión de la release seleccionada">
            <div className="panel-heading">
              <div>
                <h2>Gestión de la release seleccionada</h2>
                <span>
                  {workspace.selectedRelease
                    ? `${workspace.selectedRelease.rag_variant_id} · ${workspace.selectedRelease.rag_release_id}`
                    : "Selecciona una release para ver sus transiciones, disponibilidad para chatbot y contexto congelado."}
                </span>
              </div>
            </div>
            <div className="ui-panel-body">
              <ReleaseLifecycle
                release={workspace.selectedRelease}
                busyAction={workspace.busyAction}
                onBuild={workspace.build}
                onValidate={workspace.validate}
                onPublish={workspace.publish}
                onRetire={workspace.retire}
              />
            </div>
          </section>

          <section className="panel" aria-label="Informe de build">
            <div className="panel-heading">
              <div>
                <h2>Informe de build</h2>
                <span>Resultado del último build de la release seleccionada.</span>
              </div>
            </div>
            <div className="ui-panel-body">
              <BuildReport
                progress={workspace.buildProgress}
                polling={workspace.buildPolling}
                statusError={workspace.buildStatusError}
              />
            </div>
          </section>
        </div>
      </section>
    </>
  );
}

// Zona propia, visualmente "apagada" (fondo neutral, no --panel blanco) para
// leerse como contexto secundario: nunca parte del ciclo de vida de la
// release de arriba. ADR-006: build/publish/retire de una release JAMAS crea
// ni cambia un perfil de retrieval; esto es un espejo de solo lectura del
// perfil que hoy sirve al chatbot para el proyecto, no de esta release.
function RetrievalDiagnosticsSection({
  retrieval,
}: {
  retrieval: ReturnType<typeof useReleaseRetrievalPanel>;
}) {
  return (
    <section className="retrieval-diagnostics" aria-label="Diagnostico de retrieval">
      <div className="retrieval-diagnostics-heading">
        <span className="ui-pill">
          <Radar size={13} aria-hidden="true" /> Diagnóstico global · fuera del ciclo de vida
        </span>
        <h2>Retrieval</h2>
        <p>
          Perfil que responde hoy al chatbot para este proyecto, no el de esta release: construir
          o publicar una release nunca lo activa ni lo cambia.
        </p>
      </div>

      <div className="retrieval-diagnostics-grid">
        <div className="retrieval-diagnostics-profiles">
          <RetrievalProfilesPanel
            profiles={retrieval.profiles}
            loading={retrieval.profilesLoading}
            error={retrieval.profilesError}
            selectedProfileId={retrieval.selectedProfileId}
            onSelectProfile={retrieval.selectProfile}
          />
        </div>
        <div className="retrieval-diagnostics-status">
          <RetrievalStatusPanel
            retrievalProfileId={retrieval.selectedProfileId}
            status={retrieval.status}
            loading={retrieval.statusLoading}
            error={retrieval.statusError}
          />
        </div>
        <div className="retrieval-diagnostics-validation">
          <RetrievalValidationPanel
            status={retrieval.status}
            validationBusy={retrieval.validationBusy}
            validationError={retrieval.validationError}
            validationResult={retrieval.validationResult}
            onValidate={() => void retrieval.validate()}
          />
        </div>
        <div className="retrieval-diagnostics-search">
          <RetrievalSearchPanel
            retrievalProfileId={retrieval.selectedProfileId}
            status={retrieval.status}
            query={retrieval.query}
            onQueryChange={retrieval.setQuery}
            topK={retrieval.topK}
            onTopKChange={retrieval.setTopK}
            searchBusy={retrieval.searchBusy}
            searchError={retrieval.searchError}
            searchResult={retrieval.searchResult}
            onSearch={() => void retrieval.search()}
          />
        </div>
      </div>
    </section>
  );
}
