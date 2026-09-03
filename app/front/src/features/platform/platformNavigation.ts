import { DASHBOARD_VIEWS } from "../dashboard/dashboardNavigation.js";

// Vistas dentro de la superficie Platform. Tipo separado de `OperatorSurface`
// (platform | legacy) y de `AppView` (dashboard legacy): una vista de plataforma
// no es una pantalla del dashboard. El array es la fuente única para la sub-nav.
//
// Parity plan 2026-08-25 (Task 5): las 5 entradas de pipeline (`operations` a
// `embedding-indexing`) se DERIVAN de `DASHBOARD_VIEWS`, la misma fuente que usa
// la lane Legacy — nunca una copia a mano de labels/títulos que pueda driftear.
// Solo `projects` y `releases` son entradas propias de Platform (no existen en
// Legacy).
export type PlatformView =
  | "projects"
  | "operations"
  | "review"
  | "inventory"
  | "chunking"
  | "embedding-indexing"
  | "releases";

export type PlatformViewDefinition = {
  view: PlatformView;
  label: string;
  title: string;
};

// Las 5 entradas de pipeline vienen de `DASHBOARD_VIEWS` (mismos labels/títulos
// que Legacy; `sidebarLabel` porque el switcher de Platform es una nav ancha,
// no el switcher abreviado interno de Legacy). Orden = secuencia real del
// operador: alta/config del proyecto → intake/normalize (operación) → decisión
// de elegibilidad (revisión) → inventario → etapas de build (chunking /
// embedding-indexing) → gestión RAG / releases.
// Chunking y Embedding/Indexing ya no son vistas propias: su configuración vive
// dentro del build de release (RAG / Releases). Se excluyen de la sub-nav.
const HIDDEN_PIPELINE_VIEWS = new Set<PlatformView>(["chunking", "embedding-indexing"]);

const PIPELINE_VIEWS: readonly PlatformViewDefinition[] = DASHBOARD_VIEWS.filter(
  (item) => !HIDDEN_PIPELINE_VIEWS.has(item.view as PlatformView),
).map((item) => ({
  view: item.view,
  label: item.sidebarLabel,
  title: item.title,
}));

export const PLATFORM_VIEWS: readonly PlatformViewDefinition[] = [
  { view: "projects", label: "Projects", title: "Proyectos y configuración versionada" },
  ...PIPELINE_VIEWS,
  { view: "releases", label: "RAG / Releases", title: "Gestión RAG: build y ciclo de vida de releases" },
];

const PLATFORM_VIEW_SET = new Set<PlatformView>(PLATFORM_VIEWS.map((item) => item.view));

export function isPlatformView(value: unknown): value is PlatformView {
  return typeof value === "string" && PLATFORM_VIEW_SET.has(value as PlatformView);
}
