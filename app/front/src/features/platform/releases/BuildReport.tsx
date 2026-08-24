import { Hammer, Loader2, XOctagon } from "lucide-react";
import type { BuildProgress } from "./useRagReleaseWorkspace.js";

// Estado del build asíncrono de la release seleccionada (ADR-010). El build ya no
// bloquea el request: se encola y se observa por polling. Este panel refleja el
// job sin ocultar el fallo del proveedor ni fingir un éxito (fail-closed):
//   idle → nunca se intentó · queued/running → en curso · succeeded → reporte
//   (revisiones/etapas) · failed → error_code + error_message.
export function BuildReport({
  progress,
  polling,
}: {
  progress: BuildProgress;
  polling: boolean;
}) {
  if (progress.status === "idle") {
    return (
      <div className="ui-empty">
        <Hammer size={22} />
        <span>Ejecuta un build sobre una release en draft para ver el informe.</span>
      </div>
    );
  }

  if (progress.status === "queued" || progress.status === "running") {
    const label = progress.status === "queued" ? "Build encolado" : "Build en ejecución";
    return (
      <div className="ui-empty" role="status" aria-live="polite">
        <Loader2 className="spin" size={22} aria-hidden="true" />
        <span>
          {label}: el servidor lo está procesando{polling ? " (consultando estado…)" : ""}. Esta
          vista se actualiza sola hasta que termine.
        </span>
      </div>
    );
  }

  if (progress.status === "failed") {
    return (
      <div className="ui-empty" role="alert">
        <XOctagon size={22} aria-hidden="true" />
        <span>
          Build fallido{progress.errorCode ? ` (${progress.errorCode})` : ""}:{" "}
          {progress.errorMessage ?? "el servidor no entregó detalle."}
        </span>
      </div>
    );
  }

  const { report } = progress;
  return (
    <dl className="build-report" aria-label="Informe de build">
      <div className="build-report-tile">
        <dt>Revisiones construidas</dt>
        <dd>{report.revisions_built ?? 0}</dd>
      </div>
      <div className="build-report-tile">
        <dt>Etapas construidas</dt>
        <dd>{report.built_stages ?? 0}</dd>
      </div>
      <div className="build-report-tile">
        <dt>Etapas reutilizadas</dt>
        <dd>{report.reused_stages ?? 0}</dd>
      </div>
    </dl>
  );
}
