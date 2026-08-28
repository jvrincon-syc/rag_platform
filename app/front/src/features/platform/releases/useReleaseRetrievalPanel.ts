import { useCallback, useEffect, useRef, useState } from "react";
import {
  loadRetrievalProfileStatus,
  loadRetrievalProfiles,
  searchRetrieval,
  validateRetrievalProfile,
} from "../../retrieval/retrievalApi.js";
import type {
  RetrievalProfile,
  RetrievalProfileStatus,
  RetrievalSearchResult,
  RetrievalValidationResult,
} from "../../retrieval/retrievalTypes.js";
import { mapPipelineError } from "../../../shared/api/errorMapping.js";

function errorMessage(caught: unknown): string {
  return mapPipelineError(caught).message;
}

// Diagnostico de retrieval para RAG/Releases. NO esta ligado a la release
// seleccionada (ADR-006: publicar/activar una release nunca toca
// `retrieval_profiles` legacy). Consume los MISMOS endpoints globales
// `/api/retrieval/*` que la lane Legacy, solo para dar contexto de que perfil
// esta activo hoy sirviendo al chatbot, sin inventar un vinculo release->perfil
// que el backend no tiene.
export function useReleaseRetrievalPanel() {
  const [profiles, setProfiles] = useState<RetrievalProfile[]>([]);
  const [profilesLoading, setProfilesLoading] = useState(true);
  const [profilesError, setProfilesError] = useState<string | null>(null);
  const [selectedProfileId, setSelectedProfileId] = useState<string | null>(null);

  const [status, setStatus] = useState<RetrievalProfileStatus | null>(null);
  const [statusLoading, setStatusLoading] = useState(false);
  const [statusError, setStatusError] = useState<string | null>(null);

  const [validationBusy, setValidationBusy] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);
  const [validationResult, setValidationResult] = useState<RetrievalValidationResult | null>(
    null,
  );

  const [query, setQuery] = useState("");
  const [topK, setTopK] = useState(5);
  const [searchBusy, setSearchBusy] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [searchResult, setSearchResult] = useState<RetrievalSearchResult | null>(null);

  // Guarda contra respuestas fuera de orden: si el operador cambia de perfil
  // mientras un validate/search/status del perfil anterior sigue en vuelo, la
  // respuesta tardia no debe pisar el estado del perfil ahora seleccionado.
  const selectedProfileIdRef = useRef(selectedProfileId);
  selectedProfileIdRef.current = selectedProfileId;

  const refreshProfiles = useCallback(async () => {
    setProfilesLoading(true);
    setProfilesError(null);
    try {
      const page = await loadRetrievalProfiles();
      setProfiles(page.items);
      setSelectedProfileId((current) => {
        if (current && page.items.some((profile) => profile.retrievalProfileId === current)) {
          return current;
        }
        return (
          page.items.find((profile) => profile.active)?.retrievalProfileId ??
          page.items[0]?.retrievalProfileId ??
          null
        );
      });
    } catch (caught) {
      setProfilesError(errorMessage(caught));
    } finally {
      setProfilesLoading(false);
    }
  }, []);

  useEffect(() => {
    void refreshProfiles();
  }, [refreshProfiles]);

  const refreshStatus = useCallback(async () => {
    const requestedProfileId = selectedProfileId;
    if (!requestedProfileId) {
      setStatus(null);
      return;
    }
    setStatusLoading(true);
    setStatusError(null);
    try {
      const result = await loadRetrievalProfileStatus(requestedProfileId);
      if (selectedProfileIdRef.current !== requestedProfileId) return;
      setStatus(result);
    } catch (caught) {
      if (selectedProfileIdRef.current !== requestedProfileId) return;
      setStatusError(errorMessage(caught));
    } finally {
      if (selectedProfileIdRef.current === requestedProfileId) {
        setStatusLoading(false);
      }
    }
  }, [selectedProfileId]);

  useEffect(() => {
    setValidationResult(null);
    setValidationError(null);
    setSearchResult(null);
    setSearchError(null);
    void refreshStatus();
  }, [refreshStatus]);

  const validate = useCallback(async () => {
    const requestedProfileId = selectedProfileId;
    if (!requestedProfileId) return;
    setValidationBusy(true);
    setValidationError(null);
    try {
      const result = await validateRetrievalProfile(requestedProfileId);
      if (selectedProfileIdRef.current !== requestedProfileId) return;
      setValidationResult(result);
      await refreshStatus();
    } catch (caught) {
      if (selectedProfileIdRef.current !== requestedProfileId) return;
      setValidationError(errorMessage(caught));
    } finally {
      if (selectedProfileIdRef.current === requestedProfileId) {
        setValidationBusy(false);
      }
    }
  }, [selectedProfileId, refreshStatus]);

  const search = useCallback(async () => {
    const requestedProfileId = selectedProfileId;
    if (!requestedProfileId) return;
    const trimmedQuery = query.trim();
    if (!trimmedQuery) {
      setSearchError("Escribe una consulta antes de buscar evidencia.");
      return;
    }
    setSearchBusy(true);
    setSearchError(null);
    try {
      const result = await searchRetrieval({
        retrievalProfileId: requestedProfileId,
        query: trimmedQuery,
        topK,
      });
      if (selectedProfileIdRef.current !== requestedProfileId) return;
      setSearchResult(result);
    } catch (caught) {
      if (selectedProfileIdRef.current !== requestedProfileId) return;
      setSearchError(errorMessage(caught));
    } finally {
      if (selectedProfileIdRef.current === requestedProfileId) {
        setSearchBusy(false);
      }
    }
  }, [selectedProfileId, query, topK]);

  return {
    profiles,
    profilesLoading,
    profilesError,
    selectedProfileId,
    selectProfile: setSelectedProfileId,
    status,
    statusLoading,
    statusError,
    validationBusy,
    validationError,
    validationResult,
    validate,
    query,
    setQuery,
    topK,
    setTopK,
    searchBusy,
    searchError,
    searchResult,
    search,
  };
}
