import { useMemo } from "react";
import { StatePanel } from "../../../components/ui/StatePanel.js";
import { DashboardPipelineApp } from "../../dashboard/DashboardPipelineApp.js";
import type { AppView } from "../../dashboard/dashboardTypes.js";
import { usePlatformProjectContext } from "../PlatformProjectContext.js";
import { createPlatformDashboardDataSource } from "./platformDashboardDataSource.js";
import {
  createPlatformChunkingApiClient,
  createPlatformEmbeddingIndexingApiClient,
} from "./platformStageClients.js";

// Host Platform del pipeline Legacy compartido: monta el MISMO
// `DashboardPipelineApp` que la lane Legacy, con datasource/scope propios de
// proyecto. No dibuja tablas/paneles/inspectores de pipeline por su cuenta.
export function PlatformLegacyPipelineWorkspace({ activeView }: { activeView: AppView }) {
  const { projectId, selectedProject } = usePlatformProjectContext();

  // La variante RAG se resuelve/crea a demanda vía
  // `resolveOrCreatePlatformRagVariant`; `preferences.selectedRagVariantId` es
  // solo un cache de display y nunca se pasa aquí como entrada.
  const dataSource = useMemo(() => {
    if (!projectId) return null;
    return createPlatformDashboardDataSource({
      projectId,
      projectName: selectedProject?.display_name ?? projectId,
    });
  }, [projectId, selectedProject?.display_name]);

  // Clientes de etapa project-aware: Chunking/Embedding-Indexing NUNCA usan los
  // endpoints globales bajo Platform (Task 6 Step 4). Memoizados por proyecto.
  const chunkingApi = useMemo(
    () => (projectId ? createPlatformChunkingApiClient(projectId) : undefined),
    [projectId],
  );
  const embeddingIndexingApi = useMemo(
    () => (projectId ? createPlatformEmbeddingIndexingApiClient(projectId) : undefined),
    [projectId],
  );

  if (!projectId || !dataSource) {
    return (
      <section className="panel">
        <StatePanel
          kind="info"
          message="Selecciona un proyecto para abrir el pipeline Legacy con scope Platform."
        />
      </section>
    );
  }

  return (
    <DashboardPipelineApp
      dataSource={dataSource}
      forcedActiveView={activeView}
      scopeSubtitle={`Proyecto ${selectedProject?.display_name ?? projectId}`}
      userChipLabel={selectedProject?.display_name ?? projectId}
      chunkingApi={chunkingApi}
      embeddingIndexingApi={embeddingIndexingApi}
    />
  );
}
