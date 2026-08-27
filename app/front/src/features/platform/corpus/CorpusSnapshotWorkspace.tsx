import { CorpusSnapshotBuilderPanel } from "./CorpusSnapshotBuilderPanel.js";

// Wrapper de rollback durante la migración (plan 2026-08-25, Task 5): la ruta
// "review" de Platform ya no monta este workspace (usa el pipeline Legacy real
// vía `PlatformLegacyPipelineWorkspace`); el constructor de snapshot vive ahora
// en `RAG / Releases` a través de `CorpusSnapshotBuilderPanel`. Se conserva
// este archivo solo para no perder su cobertura de tests mientras Task 7 limpia
// las pantallas de reemplazo inalcanzables.
export function CorpusSnapshotWorkspace() {
  return (
    <main className="workspace operator-workspace platform-workspace">
      <header className="topbar">
        <div>
          <h1>Snapshots de corpus</h1>
          <p>Congela un conjunto reproducible de revisiones normalizadas del proyecto.</p>
        </div>
      </header>
      <CorpusSnapshotBuilderPanel />
    </main>
  );
}
