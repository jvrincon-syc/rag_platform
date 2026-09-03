// Superficies de nivel operador. `OperatorSurface` es un tipo separado de
// `AppView`: "platform" nunca es una vista del dashboard legacy, por lo que no
// vive en `dashboardTypes` ni en `dashboardNavigation`.
export type OperatorSurface = "platform" | "legacy";

export type OperatorSurfaceDefinition = {
  surface: OperatorSurface;
  label: string;
  title: string;
};

// "Pipeline de ingesta" (superficie legacy) se retira de la barra: todo el flujo
// vive en Platform. El tipo conserva "legacy" para compatibilidad de rutas/tests.
export const OPERATOR_SURFACES: readonly OperatorSurfaceDefinition[] = [
  { surface: "platform", label: "Platform", title: "RAG Platform" },
];

const OPERATOR_SURFACE_SET = new Set<OperatorSurface>(
  OPERATOR_SURFACES.map((item) => item.surface),
);

export function isOperatorSurface(value: unknown): value is OperatorSurface {
  return typeof value === "string" && OPERATOR_SURFACE_SET.has(value as OperatorSurface);
}
