import { History } from "lucide-react";
import { StatePanel } from "../../../components/ui/StatePanel.js";
import type { HistoryState } from "./useCorpusSnapshotWorkspace.js";

// Historial de snapshots del proyecto (read-model rehidratable). Los estados
// no-felices (loading/empty/error) pasan por StatePanel para ser consistentes con
// el resto de la plataforma. Marca el snapshot seleccionado (persistido como ID de
// navegación) para que sobreviva a un refresh. `manifest_hash` es la firma
// inmutable de procedencia del snapshot.
export function SnapshotHistory({
  state,
  selectedSnapshotId,
  onSelect,
}: {
  state: HistoryState;
  selectedSnapshotId: string | null;
  onSelect: (snapshotId: string) => void;
}) {
  if (state.status === "idle" || state.status === "loading") {
    return <StatePanel kind="loading" message="Cargando historial..." />;
  }

  if (state.status === "error") {
    return <StatePanel kind="error" message={state.message} />;
  }

  if (state.status === "empty") {
    return (
      <StatePanel
        kind="info"
        icon={<History size={22} />}
        message="Este proyecto aún no tiene snapshots. Crea el primero desde el constructor."
      />
    );
  }

  return (
    <ul className="ui-list" aria-label="Historial de snapshots de corpus">
      {state.snapshots.map((snapshot) => {
        const active = snapshot.corpus_snapshot_id === selectedSnapshotId;
        return (
          <li key={snapshot.corpus_snapshot_id}>
            <button
              type="button"
              className={active ? "ui-list-item active" : "ui-list-item"}
              aria-current={active ? "true" : undefined}
              onClick={() => onSelect(snapshot.corpus_snapshot_id)}
            >
              <strong>
                <code>{snapshot.corpus_snapshot_id}</code>
              </strong>
              <span>
                {snapshot.document_count} doc(s) · manifest{" "}
                <code title="Firma inmutable de procedencia">{snapshot.manifest_hash}</code>
              </span>
              <small>{snapshot.created_at}</small>
            </button>
          </li>
        );
      })}
    </ul>
  );
}
