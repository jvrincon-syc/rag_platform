import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import {
  buildRelease,
  createReleaseDraft,
  getConfiguration,
  getRelease,
  getReleaseBuildStatus,
  listAllCorpusSnapshots,
  listAllReleases,
  listAllVariants,
  publishRelease,
  retireRelease,
  validateRelease,
} from "../platformApi.js";
import { usePlatformProjectContext } from "../PlatformProjectContext.js";
import { usePollingLoop } from "../../embeddingIndexing/shared/usePollingLoop.js";
import { mapPipelineError } from "../../../shared/api/errorMapping.js";
import type { CorpusSnapshot, Release, ReleaseBuildStatus, Variant } from "../platformTypes.js";
import { useIdempotentReleaseAction } from "./useIdempotentReleaseAction.js";

// Estado de servidor + acciones del workspace de release lifecycle. Los componentes
// reciben datos ya resueltos y callbacks; no hacen fetch ni traducen errores ni
// conocen la máquina de estados (solo transiciones válidas → botones contextuales).
// D9: la ÚNICA operación de build es `POST /releases/{id}/build`; React nunca llama
// endpoints legacy de chunking/embedding/indexing.

export type ReleaseWorkspaceData = {
  releases: Release[];
  variants: Variant[];
  snapshots: CorpusSnapshot[];
  bindingKeys: string[];
};

export type ReleaseLoadState =
  | { status: "no-project" }
  | { status: "loading" }
  | { status: "ready"; data: ReleaseWorkspaceData }
  | { status: "error"; message: string };

// Progreso del build asíncrono (ADR-010). El build ya no bloquea el request: se
// encola y se observa por polling. `idle` = nunca se intentó (o release/proyecto
// cambiaron); `queued`/`running` = en curso; `succeeded` muestra el reporte;
// `failed` muestra el error del proveedor sin ocultarlo (fail-closed).
export type BuildProgress =
  | { status: "idle" }
  | { status: "queued" }
  | { status: "running" }
  | { status: "succeeded"; report: ReleaseBuildStatus }
  | { status: "failed"; errorCode: string | null; errorMessage: string | null };

export type ReleaseWorkspaceNotice =
  | { tone: "info" | "success" | "warning" | "danger"; message: string }
  | null;

// Traducción fail-closed de errores de transporte a copia de UI. Nunca oculta un
// bloqueo tras un genérico ni tras un éxito aparente.
function messageFromError(error: unknown): string {
  const mapped = mapPipelineError(error);
  if (mapped.status === 403) {
    return "No autorizado para esta operación.";
  }
  if (mapped.status === 503 && mapped.code === "HTTP_AUTH_NOT_CONFIGURED") {
    return "Problema de configuración del servidor de auth, no de tu sesión.";
  }
  if (mapped.code === "IDEMPOTENCY_KEY_CONFLICT") {
    return "Conflicto de clave de idempotencia: la operación ya está en curso o se envió con otra intención. No se reintenta sola; confirma o abandónala explícitamente.";
  }
  if (mapped.code === "RELEASE_BUILD_TOO_LARGE") {
    return "El build supera el límite permitido. Reduce el snapshot de corpus (menos revisiones) e inténtalo de nuevo.";
  }
  if (mapped.code === "IDEMPOTENT_OPERATION_FAILED") {
    return "La operación idempotente falló de forma definitiva. Requiere un intento nuevo y explícito.";
  }
  // 422 (validación) y el resto: mensaje del backend tal cual, sin ocultarlo.
  return mapped.message;
}

export function useRagReleaseWorkspace() {
  // scope = null: solo lee la selección de proyecto vigente y persiste la release
  // elegida (D6: solo IDs de navegación).
  const { preferences, projectId, setSelectedRagRelease } = usePlatformProjectContext();
  const selectedReleaseId = preferences.selectedRagReleaseId;
  const preferredVariantId = preferences.selectedRagVariantId;
  const preferredSnapshotId = preferences.selectedCorpusSnapshotId;

  const idempotent = useIdempotentReleaseAction();

  const [load, setLoad] = useState<ReleaseLoadState>(
    projectId ? { status: "loading" } : { status: "no-project" },
  );
  // Release cuyo build se está observando por polling. `nonce` se incrementa en
  // cada build para reiniciar el polling aun sobre la MISMA release (reintento).
  const [buildTarget, setBuildTarget] = useState<{ releaseId: string; nonce: number } | null>(null);
  // Último build-status CONOCIDO (terminal o null) de la release seleccionada,
  // fuera de la máquina de polling activo: solo alimenta el informe de lectura,
  // ver el efecto de siembra más abajo.
  const [seededStatus, setSeededStatus] = useState<ReleaseBuildStatus | null>(null);
  const [notice, setNotice] = useState<ReleaseWorkspaceNotice>(null);
  const [creating, setCreating] = useState(false);
  // Intención de mutación en vuelo sobre la release seleccionada (deshabilita las
  // acciones y evita doble envío). null = ninguna.
  const [busyAction, setBusyAction] = useState<null | "build" | "validate" | "publish" | "retire">(
    null,
  );

  // Selección local del draft (estado de formulario, no persistido). Se siembra con
  // las preferencias de navegación y un fallback al primer elemento cargado.
  const [draftVariantId, setDraftVariantId] = useState<string | null>(null);
  const [draftSnapshotId, setDraftSnapshotId] = useState<string | null>(null);
  const [draftBindingKey, setDraftBindingKey] = useState<string | null>(null);

  // Un único AbortController vivo: cambiar de proyecto o refrescar abortan la carga
  // en vuelo para evitar condiciones de carrera entre proyectos.
  const controllerRef = useRef<AbortController | null>(null);

  // Polling del estado del build asíncrono, reusando el loop legacy compartido
  // (abortable, pausa con la pestaña oculta, no solapa peticiones, corta en
  // terminal y por timeout). `resourceId` incluye el nonce: cambiar de release,
  // de proyecto (buildTarget→null) o relanzar el build reinicia el loop, y su
  // cleanup aborta la petición en vuelo. Sin `setInterval` agresivo.
  const buildReleaseId = buildTarget?.releaseId ?? null;
  const buildPoll = usePollingLoop<ReleaseBuildStatus | null>({
    resourceId: buildTarget ? `${buildTarget.releaseId}:${buildTarget.nonce}` : null,
    intervalMs: 2500,
    fetchOnce: (signal) => getReleaseBuildStatus(buildReleaseId as string, { signal }),
    // `null` (aún sin job) no es terminal: se sigue consultando hasta encontrarlo.
    isTerminal: (status) =>
      status !== null && (status.state === "succeeded" || status.state === "failed"),
  });

  const buildProgress = useMemo<BuildProgress>(() => {
    // Build activo en esta sesión (recién lanzado o retomado por estar
    // queued/running): fuente de verdad = el polling en curso.
    if (buildTarget) {
      const status = buildPoll.value;
      if (status?.state === "succeeded") {
        return { status: "succeeded", report: status };
      }
      if (status?.state === "failed") {
        return {
          status: "failed",
          errorCode: status.error_code ?? null,
          errorMessage: status.error_message ?? null,
        };
      }
      return status?.state === "running" ? { status: "running" } : { status: "queued" };
    }
    // Sin build activo: usa el último estado conocido (histórico) sembrado al
    // seleccionar la release, si lo hay.
    if (seededStatus?.state === "succeeded") {
      return { status: "succeeded", report: seededStatus };
    }
    if (seededStatus?.state === "failed") {
      return {
        status: "failed",
        errorCode: seededStatus.error_code ?? null,
        errorMessage: seededStatus.error_message ?? null,
      };
    }
    return { status: "idle" };
  }, [buildTarget, buildPoll.value, seededStatus]);

  const fetchAll = useCallback(async (pid: string, signal: AbortSignal) => {
    setLoad({ status: "loading" });
    // Un reintento exitoso (Actualizar/Reintentar) debe retirar el aviso de
    // fallo anterior; si no, "HTTP 500" queda pegado en pantalla aunque los
    // datos ya hayan cargado bien.
    setNotice(null);
    try {
      // Los tres listados recorren TODAS las páginas: releases, variantes y
      // snapshots son la evidencia del ciclo RAG y ninguna puede quedar truncada
      // en la primera página (25 ítems).
      const [allReleases, allVariants, allSnapshots, configuration] = await Promise.all([
        listAllReleases(pid, { signal }),
        listAllVariants(pid, { signal }),
        listAllCorpusSnapshots(pid, { signal }),
        getConfiguration(pid, { signal }),
      ]);
      if (signal.aborted) {
        return;
      }
      setLoad({
        status: "ready",
        data: {
          releases: Array.isArray(allReleases) ? allReleases : [],
          variants: Array.isArray(allVariants) ? allVariants : [],
          snapshots: Array.isArray(allSnapshots) ? allSnapshots : [],
          // `target_binding_key` es una clave LÓGICA; nunca el `indexing_target_id`
          // físico. Se leen de la configuración versionada (read-only).
          bindingKeys: Array.isArray(configuration.target_bindings)
            ? configuration.target_bindings.map((binding) => binding.binding_key)
            : [],
        },
      });
    } catch (error) {
      if (signal.aborted) {
        return;
      }
      const message = messageFromError(error);
      setLoad({ status: "error", message });
      setNotice({ tone: "danger", message });
    }
  }, []);

  const runLoad = useCallback(
    (pid: string) => {
      controllerRef.current?.abort();
      const controller = new AbortController();
      controllerRef.current = controller;
      void fetchAll(pid, controller.signal);
    },
    [fetchAll],
  );

  // Al cambiar de proyecto se recarga todo y se reinicia el draft/notice/report. La
  // selección de proyecto obsoleta limpia el estado local antes de recargar.
  useEffect(() => {
    setNotice(null);
    // Cambiar de proyecto cancela cualquier polling de build en curso (buildTarget
    // →null desmonta el loop) y libera la acción en vuelo.
    setBuildTarget(null);
    setBusyAction(null);
    setDraftVariantId(null);
    setDraftSnapshotId(null);
    setDraftBindingKey(null);
    if (!projectId) {
      controllerRef.current?.abort();
      controllerRef.current = null;
      setLoad({ status: "no-project" });
      return;
    }
    runLoad(projectId);
    return () => {
      controllerRef.current?.abort();
    };
  }, [projectId, runLoad]);

  const data = load.status === "ready" ? load.data : null;

  // Siembra las selecciones del draft cuando llegan los datos: preferencia de
  // navegación si sigue siendo válida, si no el primer elemento disponible.
  useEffect(() => {
    if (!data) {
      return;
    }
    setDraftVariantId((current) => {
      if (current && data.variants.some((v) => v.rag_variant_id === current)) {
        return current;
      }
      const preferred = data.variants.find((v) => v.rag_variant_id === preferredVariantId);
      return preferred?.rag_variant_id ?? data.variants[0]?.rag_variant_id ?? null;
    });
    setDraftSnapshotId((current) => {
      if (current && data.snapshots.some((s) => s.corpus_snapshot_id === current)) {
        return current;
      }
      const preferred = data.snapshots.find((s) => s.corpus_snapshot_id === preferredSnapshotId);
      return preferred?.corpus_snapshot_id ?? data.snapshots[0]?.corpus_snapshot_id ?? null;
    });
    setDraftBindingKey((current) => {
      if (current && data.bindingKeys.includes(current)) {
        return current;
      }
      return data.bindingKeys[0] ?? null;
    });
  }, [data, preferredVariantId, preferredSnapshotId]);

  const selectedRelease = useMemo(() => {
    if (!data || !selectedReleaseId) {
      return null;
    }
    return data.releases.find((release) => release.rag_release_id === selectedReleaseId) ?? null;
  }, [data, selectedReleaseId]);

  // Reemplaza (o inserta al frente) una release en la lista tras una mutación, sin
  // recargar toda la página.
  const applyRelease = useCallback((updated: Release) => {
    setLoad((current) => {
      if (current.status !== "ready") {
        return current;
      }
      const releases = current.data.releases.some((r) => r.rag_release_id === updated.rag_release_id)
        ? current.data.releases.map((r) =>
            r.rag_release_id === updated.rag_release_id ? updated : r,
          )
        : [updated, ...current.data.releases];
      return { status: "ready", data: { ...current.data, releases } };
    });
  }, []);

  // Fallo de una mutación: un `INVALID_RELEASE_TRANSITION` resincroniza el estado
  // real (refetch) en vez de forzar la transición; el resto se surfacea fail-closed.
  const handleMutationError = useCallback(
    async (error: unknown, releaseId: string) => {
      const mapped = mapPipelineError(error);
      if (mapped.code === "INVALID_RELEASE_TRANSITION") {
        try {
          const fresh = await getRelease(releaseId);
          applyRelease(fresh);
          setNotice({
            tone: "warning",
            message: `Transición inválida: el estado real de la release es "${fresh.state}". Se resincronizó; no se forzó la transición.`,
          });
          return;
        } catch (refetchError) {
          setNotice({ tone: "danger", message: messageFromError(refetchError) });
          return;
        }
      }
      setNotice({ tone: "danger", message: messageFromError(error) });
    },
    [applyRelease],
  );

  const createDraft = useCallback(async (): Promise<boolean> => {
    if (!projectId || !draftVariantId || !draftSnapshotId || !draftBindingKey) {
      return false;
    }
    setCreating(true);
    setNotice(null);
    try {
      // Body EXACTO del contrato: solo claves lógicas, nunca IDs físicos.
      const release = await createReleaseDraft({
        corpus_snapshot_id: draftSnapshotId,
        rag_variant_id: draftVariantId,
        target_binding_key: draftBindingKey,
      });
      applyRelease(release);
      setSelectedRagRelease(release.rag_release_id);
      setBuildTarget(null);
      setNotice({
        tone: "success",
        message: `Draft ${release.rag_release_id} (release #${release.release_number}) creado en estado "${release.state}".`,
      });
      return true;
    } catch (error) {
      setNotice({ tone: "danger", message: messageFromError(error) });
      return false;
    } finally {
      setCreating(false);
    }
  }, [projectId, draftVariantId, draftSnapshotId, draftBindingKey, applyRelease, setSelectedRagRelease]);

  const build = useCallback(async () => {
    if (!selectedRelease || busyAction) {
      return;
    }
    const releaseId = selectedRelease.rag_release_id;
    setBusyAction("build");
    setNotice(null);
    try {
      // El build ya no bloquea: encola el job (ADR-010). Un reintento de la MISMA
      // intención reusa la Idempotency-Key (replay server-side, mismo build_job_id).
      const accepted = await idempotent.run(`build:${releaseId}`, (options) =>
        buildRelease(releaseId, options),
      );
      setNotice({
        tone: "info",
        message: `Build encolado (job ${accepted.build_job_id}); ejecutándose en el servidor.`,
      });
      // Arranca (o reinicia, vía nonce) el polling; busyAction sigue en "build"
      // hasta que el job alcance un estado terminal (lo libera el efecto terminal).
      setBuildTarget((prev) => ({ releaseId, nonce: (prev?.nonce ?? 0) + 1 }));
    } catch (error) {
      // Fallo al ENCOLAR (no del job): libera la acción; el estado se surfacea
      // fail-closed (409 de idempotencia/transición incluidos).
      await handleMutationError(error, releaseId);
      setBusyAction(null);
    }
  }, [selectedRelease, busyAction, idempotent, handleMutationError]);

  // Reacción al estado terminal del polling: libera la acción, surfacea el
  // resultado (éxito/fallo/timeout) y, al éxito, resincroniza la release. Nunca
  // oculta un fallo del proveedor tras un genérico ni tras un éxito aparente.
  useEffect(() => {
    if (!buildTarget) {
      return;
    }
    const status = buildPoll.value;
    const succeeded = status?.state === "succeeded";
    const failed = status?.state === "failed";
    if (succeeded || failed || buildPoll.timedOut) {
      setBusyAction((current) => (current === "build" ? null : current));
    }
    if (succeeded) {
      setNotice({
        tone: "success",
        message: `Build completado: ${status?.revisions_built ?? 0} revisión(es), ${status?.built_stages ?? 0} etapa(s) construida(s), ${status?.reused_stages ?? 0} reutilizada(s).`,
      });
    } else if (failed) {
      setNotice({
        tone: "danger",
        message: `Build fallido${status?.error_code ? ` (${status.error_code})` : ""}: ${status?.error_message ?? "el servidor no entregó detalle."}`,
      });
    } else if (buildPoll.timedOut) {
      setNotice({
        tone: "warning",
        message:
          "El seguimiento del build venció sin estado terminal. El build sigue del lado del servidor; usa Actualizar para reconsultar.",
      });
    }
  }, [buildTarget, buildPoll.value, buildPoll.timedOut]);

  // Al terminar OK, resincroniza la release seleccionada (p. ej. manifest hash)
  // sin volcar a "loading": el informe del build permanece visible.
  useEffect(() => {
    if (!buildTarget || buildPoll.value?.state !== "succeeded") {
      return;
    }
    let cancelled = false;
    void (async () => {
      try {
        const fresh = await getRelease(buildTarget.releaseId);
        if (!cancelled) {
          applyRelease(fresh);
        }
      } catch {
        // Fail-closed: el resultado del build ya es visible; no lo ocultamos si el
        // refresco puntual de la release falla.
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [buildTarget, buildPoll.value, applyRelease]);

  // Al seleccionar una release (o al hidratar una selección persistida en la
  // carga inicial) se consulta UNA VEZ su build-status. Sin esto, el Informe
  // de build siempre mostraba "idle" para cualquier release que no se
  // hubiera construido en la sesión actual del navegador, aunque ya tuviera
  // un build succeeded/failed real en el servidor -- la release parecía "no
  // seleccionable" porque nada visible cambiaba al elegirla.
  // Terminado (succeeded/failed) o null (nunca se intentó) → solo informativo
  // (`seededStatus`): NO se promueve a `buildTarget`, para no disparar el
  // efecto de "build recién completado" (notice + resync de la release) por
  // el solo hecho de mirar una release ya construida.
  // En curso (queued/running) → sí se promueve a `buildTarget`: hay un build
  // real avanzando (p. ej. de otra pestaña, o tras un reload) y corresponde
  // retomar el polling activo con sus efectos normales.
  useEffect(() => {
    setSeededStatus(null);
    if (!selectedReleaseId || buildTarget) {
      return;
    }
    let cancelled = false;
    const controller = new AbortController();
    void (async () => {
      try {
        const status = await getReleaseBuildStatus(selectedReleaseId, { signal: controller.signal });
        if (cancelled) {
          return;
        }
        if (status && (status.state === "queued" || status.state === "running")) {
          setBuildTarget({ releaseId: selectedReleaseId, nonce: 0 });
        } else {
          setSeededStatus(status);
        }
      } catch {
        // Fail-closed silencioso: esta consulta puntual no bloquea la
        // selección; "Actualizar" o Construir siguen disponibles.
      }
    })();
    return () => {
      cancelled = true;
      controller.abort();
    };
  }, [selectedReleaseId, buildTarget]);

  const validate = useCallback(async () => {
    if (!selectedRelease || busyAction) {
      return;
    }
    const releaseId = selectedRelease.rag_release_id;
    setBusyAction("validate");
    setNotice(null);
    try {
      const updated = await idempotent.run(`validate:${releaseId}`, (options) =>
        validateRelease(releaseId, options),
      );
      applyRelease(updated);
      setNotice({ tone: "success", message: `Release validada (estado "${updated.state}").` });
    } catch (error) {
      await handleMutationError(error, releaseId);
    } finally {
      setBusyAction(null);
    }
  }, [selectedRelease, busyAction, idempotent, applyRelease, handleMutationError]);

  const publish = useCallback(async () => {
    if (!selectedRelease || busyAction) {
      return;
    }
    const releaseId = selectedRelease.rag_release_id;
    setBusyAction("publish");
    setNotice(null);
    try {
      const updated = await idempotent.run(`publish:${releaseId}`, (options) =>
        publishRelease(releaseId, options),
      );
      applyRelease(updated);
      setNotice({ tone: "success", message: `Release publicada (estado "${updated.state}").` });
    } catch (error) {
      await handleMutationError(error, releaseId);
    } finally {
      setBusyAction(null);
    }
  }, [selectedRelease, busyAction, idempotent, applyRelease, handleMutationError]);

  const retire = useCallback(
    async (reason: string): Promise<boolean> => {
      if (!selectedRelease || busyAction) {
        return false;
      }
      const trimmed = reason.trim();
      if (trimmed.length === 0) {
        setNotice({ tone: "warning", message: "Retirar exige un motivo explícito." });
        return false;
      }
      const releaseId = selectedRelease.rag_release_id;
      setBusyAction("retire");
      setNotice(null);
      try {
        const updated = await idempotent.run(`retire:${releaseId}`, (options) =>
          retireRelease(releaseId, { reason: trimmed }, options),
        );
        applyRelease(updated);
        setNotice({ tone: "success", message: `Release retirada (estado "${updated.state}").` });
        return true;
      } catch (error) {
        await handleMutationError(error, releaseId);
        return false;
      } finally {
        setBusyAction(null);
      }
    },
    [selectedRelease, busyAction, idempotent, applyRelease, handleMutationError],
  );

  const selectRelease = useCallback(
    (releaseId: string) => {
      setSelectedRagRelease(releaseId);
      // Cambiar de release cancela el polling del build anterior (buildTarget→null
      // desmonta el loop y aborta la petición en vuelo) y libera la acción.
      setBuildTarget(null);
      setBusyAction(null);
      setNotice(null);
    },
    [setSelectedRagRelease],
  );

  const refresh = useCallback(() => {
    if (projectId) {
      runLoad(projectId);
    }
  }, [projectId, runLoad]);

  const canCreateDraft =
    !creating && draftVariantId !== null && draftSnapshotId !== null && draftBindingKey !== null;

  return {
    projectId,
    load,
    selectedReleaseId,
    selectedRelease,
    buildProgress,
    buildPolling: buildPoll.polling,
    // Fail-closed: si la consulta de estado del build falla (401/403/404/red), el
    // loop reintenta pero el error debe verse. No se oculta tras "encolado" hasta
    // el timeout. `null` mientras la última consulta fue exitosa.
    buildStatusError: buildPoll.error?.message ?? null,
    notice,
    creating,
    busyAction,
    canCreateDraft,
    draftVariantId,
    draftSnapshotId,
    draftBindingKey,
    setDraftVariantId,
    setDraftSnapshotId,
    setDraftBindingKey,
    createDraft,
    build,
    validate,
    publish,
    retire,
    selectRelease,
    refresh,
  };
}
