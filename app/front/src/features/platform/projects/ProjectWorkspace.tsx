import { useState } from "react";
import { FolderOpen, Loader2, RefreshCw, Wand2 } from "lucide-react";
import { DashboardNotice } from "../../dashboard/components/DashboardChrome.js";
import { ProjectConfigurationForm } from "./ProjectConfigurationForm.js";
import { ProjectList } from "./ProjectList.js";
import { useProjectWorkspace } from "./useProjectWorkspace.js";

// Provisiona/agrega un backend de embedding a un proyecto YA creado (idempotente).
// local/lightning comparten variante BGE (runtime se elige por build); voyage crea la suya.
function ProvisionBackendPanel({
  busy,
  onProvision,
}: {
  busy: boolean;
  onProvision: (backend: "local" | "lightning" | "voyage") => void;
}) {
  const [backend, setBackend] = useState<"local" | "lightning" | "voyage">("local");
  return (
    <section className="panel" aria-label="Provisionar backend de embedding">
      <div className="panel-heading">
        <div>
          <h2>Backend de embedding</h2>
          <span>Agrega o reasegura la variante por defecto para que el proyecto pueda ingerir/buildear.</span>
        </div>
      </div>
      <div className="ui-panel-body">
        <div className="ui-field">
          <label htmlFor="provision-backend">Backend</label>
          <select
            id="provision-backend"
            value={backend}
            disabled={busy}
            onChange={(event) =>
              setBackend(event.target.value as "local" | "lightning" | "voyage")
            }
          >
            <option value="local">Local (BGE en la caja)</option>
            <option value="lightning">Lightning studio (BGE remoto)</option>
            <option value="voyage">Voyage (API)</option>
          </select>
          <span className="ui-field-note">
            local/lightning comparten la variante BGE (el runtime se elige por build);
            voyage crea su propia variante.
          </span>
        </div>
        <div className="ui-actions">
          <button
            className="primary-button"
            type="button"
            disabled={busy}
            onClick={() => onProvision(backend)}
          >
            {busy ? <Loader2 className="spin" size={16} /> : <Wand2 size={16} />}
            Provisionar
          </button>
        </div>
      </div>
    </section>
  );
}

// Composición pura del workspace de proyectos: estado en useProjectWorkspace,
// presentación en ProjectList / ProjectConfigurationForm. Solo orquesta layout,
// notice y los estados loading/empty del detalle.
export function ProjectWorkspace() {
  const workspace = useProjectWorkspace();

  return (
    <main className="workspace operator-workspace platform-workspace">
      <header className="topbar">
        <div>
          <h1>RAG Platform</h1>
          <p>Administración de proyectos y su configuración versionada.</p>
        </div>
        <div className="topbar-actions">
          {workspace.selectedProject && (
            <span className="ui-pill" aria-label="Proyecto seleccionado">
              {workspace.selectedProject.display_name}
            </span>
          )}
          <button
            className="ghost-button"
            type="button"
            onClick={workspace.refresh}
            disabled={workspace.projectsLoading}
          >
            {workspace.projectsLoading ? (
              <Loader2 className="spin" size={16} />
            ) : (
              <RefreshCw size={16} />
            )}
            Actualizar
          </button>
        </div>
      </header>

      {workspace.notice ? (
        <DashboardNotice tone={workspace.notice.tone} message={workspace.notice.message} />
      ) : null}

      <section className="platform-grid">
        <ProjectList
          projects={workspace.projects}
          selectedProjectId={workspace.selectedProjectId}
          loading={workspace.projectsLoading}
          error={workspace.projectsError}
          creating={workspace.creatingProject}
          onSelect={workspace.selectProject}
          onCreate={workspace.createProject}
          onRefresh={workspace.refresh}
        />

        <div className="platform-detail">
          {workspace.selectedProject && workspace.configuration ? (
            <>
              <ProjectConfigurationForm
                key={`${workspace.selectedProject.project_id}:${workspace.configuration.version}`}
                project={workspace.selectedProject}
                configuration={workspace.configuration}
                renaming={workspace.renamingProject}
                saving={workspace.savingConfiguration}
                onRename={workspace.renameProject}
                onSaveConfiguration={workspace.saveConfigurationVersion}
              />
              <ProvisionBackendPanel
                busy={workspace.provisioningBackend}
                onProvision={(backend) => void workspace.provisionBackend(backend)}
              />
            </>
          ) : (
            <section className="panel" aria-label="Detalle del proyecto">
              <div className="panel-heading">
                <div>
                  <h2>Configuración</h2>
                  <span>El detalle aparece al seleccionar un proyecto.</span>
                </div>
              </div>
              <div className="ui-empty">
                {workspace.configLoading ? (
                  <>
                    <Loader2 className="spin" size={22} />
                    <span>Cargando configuración...</span>
                  </>
                ) : workspace.configError ? (
                  <span role="alert">{workspace.configError}</span>
                ) : (
                  <>
                    <FolderOpen size={24} />
                    <span>Selecciona un proyecto de la lista para ver y versionar su configuración.</span>
                  </>
                )}
              </div>
            </section>
          )}
        </div>
      </section>
    </main>
  );
}
