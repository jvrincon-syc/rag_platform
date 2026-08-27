import { loadIndexingRun } from "../indexingApi.js";
import { indexingRunIsTerminal } from "../indexingState.js";
import { usePollingLoop } from "../../embeddingIndexing/shared/usePollingLoop.js";
import type { PipelineUiError } from "../../../shared/api/apiTypes.js";
import type { IndexingRun } from "../indexingTypes.js";

export type IndexingRunPollingState = {
  run: IndexingRun | null;
  polling: boolean;
  error: PipelineUiError | null;
  timedOut: boolean;
};

// Cargador del run inyectable (default = global). Platform puede pasar un
// loader project-aware para que el polling no pegue a endpoints globales
// mientras aparenta scope de proyecto (audit 2026-08-25).
export type IndexingRunLoader = typeof loadIndexingRun;

// Polls a non-terminal indexing run until it reaches a terminal state, using the
// shared abortable, visibility-aware polling loop.
export function useIndexingRunPolling(
  runId: string | null,
  options?: { intervalMs?: number; enabled?: boolean; loadRun?: IndexingRunLoader },
): IndexingRunPollingState {
  const loadRun = options?.loadRun ?? loadIndexingRun;
  const { value, polling, error, timedOut } = usePollingLoop<IndexingRun>({
    resourceId: runId,
    enabled: options?.enabled,
    intervalMs: options?.intervalMs,
    fetchOnce: (signal) => loadRun(runId as string, { signal }),
    isTerminal: (run) => indexingRunIsTerminal(run.status),
  });

  return { run: value, polling, error, timedOut };
}
