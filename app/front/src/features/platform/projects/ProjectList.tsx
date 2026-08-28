import { useState, type FormEvent } from "react";
import { FolderPlus, Loader2, Plus, RefreshCw, X } from "lucide-react";
import type {
  CorpusOrganizationPolicy,
  CreateProjectRequest,
  DocumentTypeTemplate,
  Project,
} from "../platformTypes.js";
import { POLICY_OPTIONS, TEMPLATE_OPTIONS } from "./projectOptions.js";

function projectStateClass(state: string): string {
  if (state === "active") return "project-state active";
  if (state === "error") return "project-state error";
  return "project-state pending";
}

// Presentación pura: lista de proyectos + alta mínima. El estado de formulario es
// local (campos del alta); nada de fetch ni de negocio vive aquí.
export function ProjectList({
  projects,
  selectedProjectId,
  loading,
  error,
  creating,
  onSelect,
  onCreate,
  onRefresh,
}: {
  projects: Project[];
  selectedProjectId: string | null;
  loading: boolean;
  error: string | null;
  creating: boolean;
  onSelect: (projectId: string) => void;
  onCreate: (body: CreateProjectRequest) => Promise<boolean>;
  onRefresh: () => void;
}) {
  const [formOpen, setFormOpen] = useState(false);
  const [slug, setSlug] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [policy, setPolicy] = useState<CorpusOrganizationPolicy>("source-folders-v1");
  const [template, setTemplate] = useState<DocumentTypeTemplate>("generic");

  const canSubmit = slug.trim().length > 0 && displayName.trim().length > 0 && !creating;

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!canSubmit) {
      return;
    }
    const ok = await onCreate({
      project_slug: slug.trim(),
      display_name: displayName.trim(),
      corpus_organization_policy: policy,
      document_type_template: template,
    });
    if (ok) {
      setSlug("");
      setDisplayName("");
      setPolicy("source-folders-v1");
      setTemplate("generic");
      setFormOpen(false);
    }
  }

  return (
    <section className="panel" aria-label="Proyectos">
      <div className="panel-heading">
        <div>
          <h2>Proyectos</h2>
          <span>Selecciona un proyecto para ver y versionar su configuración.</span>
        </div>
        <div className="topbar-actions">
          <button
            className="ghost-button"
            type="button"
            onClick={onRefresh}
            disabled={loading}
            title="Recargar la lista de proyectos"
          >
            {loading ? <Loader2 className="spin" size={16} /> : <RefreshCw size={16} />}
            Actualizar
          </button>
          <button
            className="primary-button"
            type="button"
            onClick={() => setFormOpen((open) => !open)}
            aria-expanded={formOpen}
            aria-controls="new-project-form"
          >
            {formOpen ? <X size={16} /> : <Plus size={16} />}
            {formOpen ? "Cancelar" : "Nuevo proyecto"}
          </button>
        </div>
      </div>

      <div className="ui-panel-body">
        {formOpen ? (
          <form className="platform-create-form" id="new-project-form" onSubmit={handleSubmit}>
            <div className="ui-field">
              <label htmlFor="new-project-slug">Slug</label>
              <input
                id="new-project-slug"
                value={slug}
                placeholder="mi-proyecto"
                autoComplete="off"
                onChange={(event) => setSlug(event.target.value)}
              />
              <span className="ui-field-note">Identidad inmutable del proyecto.</span>
            </div>
            <div className="ui-field">
              <label htmlFor="new-project-name">Nombre visible</label>
              <input
                id="new-project-name"
                value={displayName}
                placeholder="Mi proyecto"
                autoComplete="off"
                onChange={(event) => setDisplayName(event.target.value)}
              />
            </div>
            <div className="platform-row">
              <div className="ui-field">
                <label htmlFor="new-project-policy">Política de organización</label>
                <select
                  id="new-project-policy"
                  value={policy}
                  onChange={(event) => setPolicy(event.target.value as CorpusOrganizationPolicy)}
                >
                  {POLICY_OPTIONS.map((option) => (
                    <option value={option.value} key={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </div>
              <div className="ui-field">
                <label htmlFor="new-project-template">Plantilla de tipos</label>
                <select
                  id="new-project-template"
                  value={template}
                  onChange={(event) => setTemplate(event.target.value as DocumentTypeTemplate)}
                >
                  {TEMPLATE_OPTIONS.map((option) => (
                    <option value={option.value} key={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>
            <div className="ui-actions">
              <button className="primary-button" type="submit" disabled={!canSubmit}>
                {creating ? <Loader2 className="spin" size={16} /> : <FolderPlus size={16} />}
                Crear proyecto
              </button>
            </div>
          </form>
        ) : null}

        {error ? (
          <p className="ui-field-note error" role="alert">
            {error}
          </p>
        ) : null}

        {loading && projects.length === 0 ? (
          <div className="ui-empty compact">
            <Loader2 className="spin" size={20} />
            <span>Cargando proyectos...</span>
          </div>
        ) : projects.length === 0 ? (
          <div className="ui-empty compact">
            <FolderPlus size={22} />
            <span>Aún no hay proyectos. Crea el primero para empezar a configurarlo.</span>
          </div>
        ) : (
          <ul className="project-list" aria-label="Lista de proyectos">
            {projects.map((project) => {
              const active = project.project_id === selectedProjectId;
              return (
                <li key={project.project_id}>
                  <button
                    type="button"
                    className={active ? "project-card active" : "project-card"}
                    aria-current={active ? "true" : undefined}
                    onClick={() => onSelect(project.project_id)}
                  >
                    <div className="project-card-header">
                      <span className="project-card-name">{project.display_name}</span>
                      <span className={projectStateClass(project.state)}>{project.state}</span>
                    </div>
                    <span className="project-card-slug">{project.project_id}</span>
                    <div className="project-card-meta">
                      <span>config v{project.configuration.version}</span>
                    </div>
                  </button>
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </section>
  );
}
