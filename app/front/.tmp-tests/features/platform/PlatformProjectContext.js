import { jsx as _jsx } from "react/jsx-runtime";
import { createContext, useCallback, useContext, useMemo, useState } from "react";
import { usePlatformPreferences } from "./hooks/usePlatformPreferences.js";
const PlatformProjectContext = createContext(null);
export function PlatformProjectProvider({ children }) {
    const { preferences, setSelectedProject, setSelectedRagVariant, setSelectedCorpusSnapshot, setSelectedRagRelease, } = usePlatformPreferences(null);
    const [knownProjects, setKnownProjectsState] = useState([]);
    const setKnownProjects = useCallback((projects) => {
        setKnownProjectsState(Array.isArray(projects) ? projects : []);
    }, []);
    const upsertProject = useCallback((project) => {
        setKnownProjectsState((current) => [
            project,
            ...current.filter((item) => item.project_id !== project.project_id),
        ]);
    }, []);
    const projectId = preferences.selectedProjectId;
    const selectedProject = useMemo(() => knownProjects.find((project) => project.project_id === projectId) ?? null, [knownProjects, projectId]);
    const value = useMemo(() => ({
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
    }), [
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
    ]);
    return (_jsx(PlatformProjectContext.Provider, { value: value, children: children }));
}
export function usePlatformProjectContext() {
    const context = useContext(PlatformProjectContext);
    if (!context) {
        throw new Error("usePlatformProjectContext debe usarse dentro de PlatformProjectProvider.");
    }
    return context;
}
