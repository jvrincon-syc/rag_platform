import { useState } from "react";
import {
  AlertCircle,
  Bot,
  Cpu,
  GitBranch,
  Layers3,
  Loader2,
  Radar,
  RefreshCw,
  Rocket,
  Scissors,
  Server,
  Zap,
} from "lucide-react";
import { DashboardNotice } from "../../dashboard/components/DashboardChrome.js";
import { RetrievalProfilesPanel } from "../../retrieval/components/RetrievalProfilesPanel.js";
import { RetrievalSearchPanel } from "../../retrieval/components/RetrievalSearchPanel.js";
import { RetrievalStatusPanel } from "../../retrieval/components/RetrievalStatusPanel.js";
import { RetrievalValidationPanel } from "../../retrieval/components/RetrievalValidationPanel.js";
import { CorpusSnapshotBuilderPanel } from "../corpus/CorpusSnapshotBuilderPanel.js";
import type { CustomChunkingParams } from "../platformApi.js";
import type { Variant } from "../platformTypes.js";
import { BuildReport } from "./BuildReport.js";
import { ReleaseDraftForm } from "./ReleaseDraftForm.js";
import { ReleaseHistory } from "./ReleaseHistory.js";
import { ReleaseLifecycle } from "./ReleaseLifecycle.js";
import { useRagReleaseWorkspace } from "./useRagReleaseWorkspace.js";
import type { ReleaseWorkspaceData } from "./useRagReleaseWorkspace.js";
import { useReleaseRetrievalPanel } from "./useReleaseRetrievalPanel.js";
import { describeVariant } from "./variantRecipe.js";

// Encabezado de panel con número de paso: el ciclo RAG ES una secuencia real
// (snapshot → draft → build → publicar), así que numerarlo informa el orden en
// vez de decorar. El número es aria-hidden; el <h2> conserva el nombre accesible.
function StepPanelHeading({
  step,
  title,
  hint,
}: {
  step: number;
  title: string;
  hint: string;
}) {
  return (
    <div className="panel-heading step-heading">
      <span className="step-badge" aria-hidden="true">
        {step}
      </span>
      <div>
        <h2>{title}</h2>
        <span>{hint}</span>
      </div>
    </div>
  );
}

// Configuración del build ANTES de construir: muestra la receta real de la variante
// (embedding + chunking, fijados por la variante) y deja elegir el runtime de BGE
// (local en la caja / Lightning studio) para ESTA corrida. Voyage usa su propio
// motor: ahí el runtime BGE no aplica y se deshabilita, sin fingir que hace algo.
function BuildConfigCard({
  variant,
  runtime,
  onRuntimeChange,
  disabled,
}: {
  variant: Variant | null;
  runtime: "local" | "remote" | null;
  onRuntimeChange: (value: "local" | "remote" | null) => void;
  disabled: boolean;
}) {
  const recipe = variant ? describeVariant(variant) : null;
  const isVoyage = recipe?.embeddingKind === "voyage";

  return (
    <div className="build-config-card">
      <div className="build-recipe" aria-label="Receta de la variante">
        <span className="build-recipe-chip">
          <Cpu size={13} aria-hidden="true" /> {recipe?.embeddingLabel ?? "—"}
        </span>
        <span className="build-recipe-chip">
          <Scissors size={13} aria-hidden="true" /> {recipe?.chunkingLabel ?? "—"}
        </span>
      </div>

      <div className="ui-field build-runtime-selector">
        <label htmlFor="build-embedding-runtime">
          <Server size={13} aria-hidden="true" /> Runtime de embedding (para este build)
        </label>
        <select
          id="build-embedding-runtime"
          value={runtime ?? "global"}
          disabled={disabled || isVoyage}
          onChange={(event) => {
            const next = event.target.value;
            onRuntimeChange(next === "global" ? null : (next as "local" | "remote"));
          }}
        >
          <option value="global">Global del servidor (por defecto)</option>
          <option value="local">Local (modelo en la caja)</option>
          <option value="remote">Lightning studio (remoto)</option>
        </select>
        <span className="ui-hint">
          {isVoyage
            ? "Esta variante es Voyage: usa su propio motor por API; el runtime BGE no aplica."
            : "Local y Lightning studio comparten el mismo espacio BGE; solo cambia dónde corre. No toca el perfil de retrieval activo del chatbot."}
        </span>
      </div>
    </div>
  );
}

// Chunking con hiperparámetros a medida (#2): crea una variante `structural-custom`
// con la política de tokens/overlap dada. Campos vacíos = defaults canónicos (v1). El
// backend valida los invariantes (min<=target<=max, overlap en rango) antes de crear.
function CustomChunkingForm({
  creating,
  onCreate,
}: {
  creating: boolean;
  onCreate: (params: CustomChunkingParams) => void;
}) {
  const [open, setOpen] = useState(false);
  const [backend, setBackend] = useState<"local" | "lightning" | "voyage">("local");
  const [values, setValues] = useState<Record<string, string>>({});
  const [sectionContext, setSectionContext] = useState(false);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  // Vacío = usar el default canónico (null). Un valor NO numérico es un error de
  // formulario que bloquea el POST (PR-4 4.4): antes `Number("abc")` caía en NaN
  // y se convertía en `null` en silencio, indistinguible de "vacío a propósito".
  const parseField = (key: string): number | null | "invalid" => {
    const raw = (values[key] ?? "").trim();
    if (!raw) return null;
    const parsed = Number(raw);
    return Number.isFinite(parsed) ? parsed : "invalid";
  };

  const NUM_FIELDS: { key: string; label: string; placeholder: string }[] = [
    { key: "child_min_tokens", label: "Child min", placeholder: "250" },
    { key: "child_target_tokens", label: "Child target", placeholder: "350" },
    { key: "child_max_tokens", label: "Child max", placeholder: "450" },
    { key: "overlap_min_tokens", label: "Overlap min", placeholder: "30" },
    { key: "overlap_max_tokens", label: "Overlap max", placeholder: "60" },
    { key: "overlap_ratio", label: "Overlap ratio", placeholder: "0.12" },
  ];

  if (!open) {
    return (
      <div className="custom-chunking-toggle">
        <button className="ghost-button" type="button" onClick={() => setOpen(true)}>
          <Scissors size={15} /> Chunking avanzado (crear variante a medida)
        </button>
      </div>
    );
  }

  return (
    <form
      className="custom-chunking-form"
      onSubmit={(event) => {
        event.preventDefault();
        const parsed: Record<string, number | null> = {};
        const nextErrors: Record<string, string> = {};
        for (const f of NUM_FIELDS) {
          const value = parseField(f.key);
          if (value === "invalid") {
            nextErrors[f.key] = "Debe ser un número, o déjalo vacío para usar el default.";
          } else {
            parsed[f.key] = value;
          }
        }
        setFieldErrors(nextErrors);
        if (Object.keys(nextErrors).length > 0) {
          // Fail-closed: nunca envía la variante con un valor inventado (null)
          // cuando el operador tecleó algo no numérico por error.
          return;
        }
        onCreate({
          embedding_backend: backend,
          child_min_tokens: parsed.child_min_tokens ?? null,
          child_target_tokens: parsed.child_target_tokens ?? null,
          child_max_tokens: parsed.child_max_tokens ?? null,
          overlap_min_tokens: parsed.overlap_min_tokens ?? null,
          overlap_max_tokens: parsed.overlap_max_tokens ?? null,
          overlap_ratio: parsed.overlap_ratio ?? null,
          include_section_context: sectionContext,
        });
      }}
    >
      <div className="ui-field">
        <label htmlFor="custom-chunk-backend">Embedding de la variante</label>
        <select
          id="custom-chunk-backend"
          value={backend}
          disabled={creating}
          onChange={(event) =>
            setBackend(event.target.value as "local" | "lightning" | "voyage")
          }
        >
          <option value="local">BGE-M3 (local/lightning)</option>
          <option value="voyage">Voyage</option>
        </select>
      </div>

      <div className="custom-chunking-grid">
        {NUM_FIELDS.map((f) => (
          <div className="ui-field" key={f.key}>
            <label htmlFor={`custom-chunk-${f.key}`}>{f.label}</label>
            <input
              id={`custom-chunk-${f.key}`}
              inputMode="decimal"
              placeholder={`${f.placeholder} (def.)`}
              value={values[f.key] ?? ""}
              disabled={creating}
              aria-invalid={fieldErrors[f.key] ? true : undefined}
              onChange={(event) => {
                setValues((current) => ({ ...current, [f.key]: event.target.value }));
                setFieldErrors((current) => {
                  if (!current[f.key]) return current;
                  const { [f.key]: _removed, ...rest } = current;
                  return rest;
                });
              }}
            />
            {fieldErrors[f.key] ? (
              <span className="ui-field-note" role="alert">
                {fieldErrors[f.key]}
              </span>
            ) : null}
          </div>
        ))}
      </div>

      <label className="custom-chunking-check">
        <input
          type="checkbox"
          checked={sectionContext}
          disabled={creating}
          onChange={(event) => setSectionContext(event.target.checked)}
        />
        Incluir contexto de sección (v2)
      </label>

      <div className="platform-actions">
        <button className="primary-button" type="submit" disabled={creating}>
          {creating ? <Loader2 className="spin" size={16} /> : <Scissors size={16} />}
          Crear variante
        </button>
        <button
          className="ghost-button"
          type="button"
          onClick={() => setOpen(false)}
          disabled={creating}
        >
          Cerrar
        </button>
      </div>
      <span className="ui-hint">
        Vacío = default canónico. min ≤ target ≤ max; overlap dentro de rango. La
        variante aparecerá en el selector de arriba.
      </span>
    </form>
  );
}

// Activación explícita: pone los vectores de la release en vivo (is_active=true) y
// crea el retrieval profile release-scoped. Es un paso SEPARADO de publicar (publish
// nunca activa); sin este paso el chatbot ve 0 filas activas (NO_ACTIVE_VECTOR_ROWS).
function ActivateLivePanel({
  published,
  activating,
  onActivate,
}: {
  published: boolean;
  activating: boolean;
  onActivate: () => void;
}) {
  return (
    <div className="activate-live">
      <button
        className="primary-button"
        type="button"
        onClick={onActivate}
        disabled={activating}
      >
        {activating ? <Loader2 className="spin" size={16} /> : <Zap size={16} />}
        Activar en vivo
      </button>
      <span className="ui-hint">
        Pone los vectores de esta release en vivo y crea su retrieval profile (paso
        aparte de publicar). Sin esto el chatbot recupera 0 resultados.
        {published
          ? ""
          : " Recomendado tras publicar, pero funciona en cuanto la release está construida."}
      </span>
    </div>
  );
}

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
  const retrieval = useReleaseRetrievalPanel({ projectId: workspace.projectId ?? undefined });

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
  // la release seleccionada, ver nota en `useReleaseRetrievalPanel`), pero SÍ
  // depende del proyecto activo para filtrar perfiles por tenant.
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
  const selectedVariant = workspace.selectedRelease
    ? (data.variants.find(
        (variant) => variant.rag_variant_id === workspace.selectedRelease?.rag_variant_id,
      ) ?? null)
    : null;

  return (
    <>
      <section className="panel" aria-label="Snapshot de corpus">
        <StepPanelHeading
          step={1}
          title="Snapshot de corpus"
          hint="Congela las revisiones aprobadas: la foto inmutable del corpus que la release construirá."
        />
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
          <section className="panel" aria-label="Nuevo draft de release">
            <StepPanelHeading
              step={2}
              title="Nuevo draft"
              hint="Elige embedding y chunking (la receta) + snapshot y binding. Queda una release reproducible."
            />
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
              <CustomChunkingForm
                creating={workspace.creatingChunkingVariant}
                onCreate={(params) => void workspace.createCustomChunkingVariant(params)}
              />
            </div>
          </section>

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
        </div>

        <div className="release-main">
          <section className="panel" aria-label="Gestión de la release seleccionada">
            <StepPanelHeading
              step={3}
              title="Configurar y construir"
              hint={
                workspace.selectedRelease
                  ? `${workspace.selectedRelease.rag_variant_id} · ${workspace.selectedRelease.rag_release_id}`
                  : "Selecciona una release para configurar su build y ver sus transiciones."
              }
            />
            <div className="ui-panel-body">
              <BuildConfigCard
                variant={selectedVariant}
                runtime={workspace.buildEmbeddingRuntime}
                onRuntimeChange={workspace.setBuildEmbeddingRuntime}
                disabled={workspace.busyAction !== null}
              />
              <ReleaseLifecycle
                release={workspace.selectedRelease}
                busyAction={workspace.busyAction}
                onBuild={workspace.build}
                onValidate={workspace.validate}
                onPublish={workspace.publish}
                onRetire={workspace.retire}
              />
              {workspace.selectedRelease ? (
                <ActivateLivePanel
                  published={workspace.selectedRelease.state === "published"}
                  activating={workspace.activating}
                  onActivate={() => void workspace.activate()}
                />
              ) : null}
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
