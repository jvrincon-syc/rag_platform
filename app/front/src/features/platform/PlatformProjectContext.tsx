import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from "react";

import { usePlatformPreferences } from "./hooks/usePlatformPreferences.js";
import type { PlatformPreferences, PlatformSelectionScope } from "./platformState.js";
import type { Project } from "./platformTypes.js";

export type ProjectArtifactIds = {
  variantIds: readonly string[];
  corpusSnapshotIds: readonly string[];
  releaseIds: readonly string[];
};

export type PlatformProjectContextValue = {
  preferences: PlatformPreferences;
  projectId: string | null;
  selectedProject: Project | null;
  knownProjects: Project[];
  setSelectedProject: (projectId: string | null) => void;
  setSelectedRagVariant: (variantId: string | null) => void;
  setSelectedCorpusSnapshot: (snapshotId: string | null) => void;
  setSelectedRagRelease: (releaseId: string | null) => void;
  setKnownProjects: (projects: Project[]) => void;
  upsertProject: (project: Project) => void;
  // Reporta los IDs vivos de variante/snapshot/release del proyecto dado (p. ej.
  // tras la carga de RagReleaseWorkspace) para que el provider pode selecciones
  // obsoletas. Un reporte de un proyecto que ya no es el seleccionado se ignora
  // (condición de carrera al cambiar de proyecto).
  reportProjectArtifacts: (projectId: string, artifacts: ProjectArtifactIds) => void;
};

const PlatformProjectContext = createContext<PlatformProjectContextValue | null>(null);

export function PlatformProjectProvider({
  children,
  initialKnownProjects,
}: {
  children: ReactNode;
  initialKnownProjects?: Project[];
}) {
  const [knownProjects, setKnownProjectsState] = useState<Project[]>(initialKnownProjects ?? []);
  const [projectArtifacts, setProjectArtifacts] = useState<ProjectArtifactIds | null>(null);

  // D9 (PR-4 4.3): scope reconciliado en vivo, ya no `null`. `projectIds` es la
  // única lista siempre conocida (via `listProjects`); los tres sub-scopes de
  // artefactos quedan `undefined` hasta que algún workspace los reporte para el
  // proyecto activo (`resolvePlatformPreferences` preserva sin evidencia).
  const scope = useMemo<PlatformSelectionScope>(
    () => ({
      projectIds: knownProjects.map((project) => project.project_id),
      variantIds: projectArtifacts?.variantIds,
      corpusSnapshotIds: projectArtifacts?.corpusSnapshotIds,
      releaseIds: projectArtifacts?.releaseIds,
    }),
    [knownProjects, projectArtifacts],
  );

  const {
    preferences,
    setSelectedProject: setSelectedProjectPreference,
    setSelectedRagVariant,
    setSelectedCorpusSnapshot,
    setSelectedRagRelease,
  } = usePlatformPreferences(scope);

  const setKnownProjects = useCallback((projects: Project[]) => {
    setKnownProjectsState(Array.isArray(projects) ? projects : []);
  }, []);

  const upsertProject = useCallback((project: Project) => {
    setKnownProjectsState((current) => [
      project,
      ...current.filter((item) => item.project_id !== project.project_id),
    ]);
  }, []);

  // Cambiar de proyecto invalida cualquier artefacto reportado para el proyecto
  // anterior: sin esto, la nueva selección heredaría (por un instante) el scope
  // del proyecto saliente.
  const setSelectedProject = useCallback(
    (projectId: string | null) => {
      setProjectArtifacts(null);
      setSelectedProjectPreference(projectId);
    },
    [setSelectedProjectPreference],
  );

  const reportProjectArtifacts = useCallback(
    (projectId: string, artifacts: ProjectArtifactIds) => {
      setProjectArtifacts((current) => {
        if (projectId !== preferences.selectedProjectId) {
          return current;
        }
        return artifacts;
      });
    },
    [preferences.selectedProjectId],
  );

  const projectId = preferences.selectedProjectId;
  const selectedProject = useMemo(
    () => knownProjects.find((project) => project.project_id === projectId) ?? null,
    [knownProjects, projectId],
  );

  const value = useMemo<PlatformProjectContextValue>(
    () => ({
      preferences,
      projectId,
      selectedProject,
      knownProjects,
      setSelectedProject,
      setSelectedRagVariant,
      setSelectedCorpusSnapshot,
      setSelectedRagRelease,
      setKnownProjects,
      upsertProject,
      reportProjectArtifacts,
    }),
    [
      preferences,
      projectId,
      selectedProject,
      knownProjects,
      setSelectedProject,
      setSelectedRagVariant,
      setSelectedCorpusSnapshot,
      setSelectedRagRelease,
      setKnownProjects,
      upsertProject,
      reportProjectArtifacts,
    ],
  );

  return (
    <PlatformProjectContext.Provider value={value}>{children}</PlatformProjectContext.Provider>
  );
}

export function usePlatformProjectContext(): PlatformProjectContextValue {
  const context = useContext(PlatformProjectContext);
  if (!context) {
    throw new Error("usePlatformProjectContext debe usarse dentro de PlatformProjectProvider.");
  }
  return context;
}
