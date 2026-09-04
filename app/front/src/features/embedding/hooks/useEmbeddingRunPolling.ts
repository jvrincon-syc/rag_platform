import { loadEmbeddingRun } from "../embeddingApi.js";
import { embeddingRunIsTerminal } from "../embeddingState.js";
import { usePollingLoop } from "../../../shared/hooks/usePollingLoop.js";
import type { PipelineUiError } from "../../../shared/api/apiTypes.js";
import type { EmbeddingRun } from "../embeddingTypes.js";

export type EmbeddingRunPollingState = {
  run: EmbeddingRun | null;
  polling: boolean;
  error: PipelineUiError | null;
  timedOut: boolean;
};

// Cargador del run inyectable (default = global). Platform puede pasar un
// loader project-aware para que el polling no pegue a endpoints globales
// mientras aparenta scope de proyecto (audit 2026-08-25).
export type EmbeddingRunLoader = typeof loadEmbeddingRun;

// Polls a non-terminal embedding run until it reaches a terminal state, using
// the shared abortable, visibility-aware polling loop.
export function useEmbeddingRunPolling(
  embeddingRunId: string | null,
  options?: { intervalMs?: number; enabled?: boolean; loadRun?: EmbeddingRunLoader },
): EmbeddingRunPollingState {
  const loadRun = options?.loadRun ?? loadEmbeddingRun;
  const { value, polling, error, timedOut } = usePollingLoop<EmbeddingRun>({
    resourceId: embeddingRunId,
    enabled: options?.enabled,
    intervalMs: options?.intervalMs,
    fetchOnce: (signal) => loadRun(embeddingRunId as string, { signal }),
    isTerminal: (run) => embeddingRunIsTerminal(run.status),
  });

  return { run: value, polling, error, timedOut };
}
