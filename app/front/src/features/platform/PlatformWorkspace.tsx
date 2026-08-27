import { useState } from "react";
import { ProjectWorkspace } from "./projects/ProjectWorkspace.js";
import { RagReleaseWorkspace } from "./releases/RagReleaseWorkspace.js";
import { PlatformLegacyPipelineWorkspace } from "./legacyPipeline/PlatformLegacyPipelineWorkspace.js";
import { PLATFORM_VIEWS, type PlatformView } from "./platformNavigation.js";
import {
  PlatformProjectProvider,
  usePlatformProjectContext,
} from "./PlatformProjectContext.js";

// Contenedor de la superficie Platform: posee la sub-nav (estado de sesion, no
// persistido) y monta el workspace activo. Reusa `.view-switcher` del shell.
export function PlatformWorkspace() {
  const [view, setView] = useState<PlatformView>("projects");

  return (
    <PlatformProjectProvider>
      <PlatformWorkspaceContent view={view} setView={setView} />
    </PlatformProjectProvider>
  );
}

function PlatformWorkspaceContent({
  view,
  setView,
}: {
  view: PlatformView;
  setView: (view: PlatformView) => void;
}) {
  const { projectId, selectedProject } = usePlatformProjectContext();
  const projectLabel = selectedProject?.display_name ?? projectId ?? "Sin proyecto seleccionado";

  return (
    <div className="platform-surface">
      <div className="platform-nav-row">
        <nav className="view-switcher platform-views" aria-label="Vista de plataforma">
          {PLATFORM_VIEWS.map((item) => (
            <button
              key={item.view}
              type="button"
              className={view === item.view ? "active" : ""}
              aria-current={view === item.view ? "page" : undefined}
              onClick={() => setView(item.view)}
              title={item.title}
            >
              {item.label}
            </button>
          ))}
        </nav>
        <span className="ui-pill platform-project-chip" aria-label="Proyecto activo">
          <span>Proyecto activo</span>
          <strong>{projectLabel}</strong>
        </span>
      </div>
      <PlatformView view={view} />
    </div>
  );
}

function PlatformView({ view }: { view: PlatformView }) {
  switch (view) {
    case "projects":
      return <ProjectWorkspace />;
    // El pipeline (Operación/Revisión/Inventario/Chunking/Embedding-Indexing)
    // monta el MISMO `DashboardPipelineApp` que Legacy, con datasource y scope
    // de proyecto Platform (parity plan 2026-08-25, Task 5). Nunca una pantalla
    // de reemplazo propia.
    case "operations":
      return <PlatformLegacyPipelineWorkspace activeView="operations" />;
    case "review":
      return <PlatformLegacyPipelineWorkspace activeView="review" />;
    case "inventory":
      return <PlatformLegacyPipelineWorkspace activeView="inventory" />;
    case "chunking":
      return <PlatformLegacyPipelineWorkspace activeView="chunking" />;
    case "embedding-indexing":
      return <PlatformLegacyPipelineWorkspace activeView="embedding-indexing" />;
    case "releases":
      return <RagReleaseWorkspace />;
  }
}
