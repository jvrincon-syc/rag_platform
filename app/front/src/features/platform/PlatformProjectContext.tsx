import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from "react";

import { usePlatformPreferences } from "./hooks/usePlatformPreferences.js";
import type { PlatformPreferences } from "./platformState.js";
import type { Project } from "./platformTypes.js";

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
};

const PlatformProjectContext = createContext<PlatformProjectContextValue | null>(null);

export function PlatformProjectProvider({ children }: { children: ReactNode }) {
  const {
    preferences,
    setSelectedProject,
    setSelectedRagVariant,
    setSelectedCorpusSnapshot,
    setSelectedRagRelease,
  } = usePlatformPreferences(null);
  const [knownProjects, setKnownProjectsState] = useState<Project[]>([]);

  const setKnownProjects = useCallback((projects: Project[]) => {
    setKnownProjectsState(Array.isArray(projects) ? projects : []);
  }, []);

  const upsertProject = useCallback((project: Project) => {
    setKnownProjectsState((current) => [
      project,
      ...current.filter((item) => item.project_id !== project.project_id),
    ]);
  }, []);

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
