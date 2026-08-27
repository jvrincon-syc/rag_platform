# Plan 02 — Sin datos ≠ falló la consulta (front embedding/indexing)

Estado: ✅ Cerrado (2026-08-26) · Severidad: ALTA · Hallazgo origen: #2 del informe

> **Cierre (2026-08-26).** Ejecutado como prerequisito de Task 6 del parity plan
> `docs/superpowers/plans/2026-08-25-rag-platform-legacy-pipeline-parity.md`
> (coordinación de archivos compartidos: `useEmbeddingIndexingPipeline.ts`). Verde
> del operador: `npm --prefix app/front run test` (115/115) + `run build` OK. Los
> 5 `.catch(()=>null)` ahora escriben estados de error dedicados; paneles pintan
> `notice-danger` en vez de omitir; tests nuevos de `EmbeddingBundleInspector` e
> `IndexingErrorsPanel` + caso de readiness-error en `ActivationPanel`.

## Checklist de cierre
- [x] Implementado
- [x] Tests de componentes nuevos/actualizados en verde
- [x] `npm test && npm run test:components` en verde
- [x] Estado ✅ en `2026-08-25_indice-y-cierre.md`

## Hallazgo (verificado en código)
`app/front/src/features/embeddingIndexing/useEmbeddingIndexingPipeline.ts`:
`.catch(() => null)` en :252 (overview → `bundleFirstEnabled`), :471 (bundle
validation), :472 (bundle readiness), :730 (errores del run de indexing), :731
(retrieval readiness). Un fallo HTTP deja esos datos en `null` y la UI trata la
ausencia como estado normal. Caso grave: `IndexingErrorsPanel.tsx:36-41` pinta
"Sin errores registrados para este run." con CheckCircle2 verde cuando la carga de
errores FALLÓ (`errorsPage === null` y error nunca seteado porque el catch lo tragó).

## Decisión registrada (2026-08-25)
Distinguir explícitamente "sin datos" de "falló la consulta"; renderizar el error.

## Contraste con código (2ª pasada, 2026-08-25)
- `IndexingErrorsPanel` ya renderiza `notice-danger` cuando recibe `error` y el
  workspace ya le pasa `error={indexing.errorsError}` (`EmbeddingIndexingWorkspace.tsx:131-135`):
  el bug está SOLO en el hook (el catch traga el fallo antes de llegar al estado).
- Las ramas de limpieza del hook ya resetean datos (`:483-493` bundle NOT_FOUND,
  `:707-713` indexing NOT_FOUND); falta añadir ahí el reset de los NUEVOS estados de error.
- `ActivationPanel.tsx:113-130`: omite readiness en silencio cuando es `null`
  (mismo patrón a corregir con prop `readinessError`).
- `EmbeddingBundleInspector.tsx:125,144`: mismas omisiones silenciosas para
  validation/readiness.
- (3ª pasada) El efecto de bundle SÍ resetea su error al inicio (`setEmbeddingBundleError(null)`
  en :465), pero el efecto de indexing detail (:719-726) NO resetea
  `documentsError`/`errorsError` al comenzar: un error de un intento previo seguiría
  visible junto a datos frescos. El fix debe resetear TODOS los estados de error al
  inicio de cada efecto, espejando el patrón del efecto de bundle.

## Cambios propuestos
| Archivo | Cambio |
|---|---|
| `features/embeddingIndexing/useEmbeddingIndexingPipeline.ts` | Nuevos estados: `bundleValidationError`, `bundleReadinessError` (slice embedding), `overviewError` (slice indexing) e `indexingReadinessError` (slice activation). Efecto :458: `bundle + chunks` por Promise.all (contenido principal); validation/readiness se cargan EN PARALELO con catch individual que escribe el mensaje en su estado de error. Efecto :719: igual — fallo de `loadIndexingRunErrors` setea `indexingErrorsError` (estado YA existente y YA cableado al panel); fallo de retrieval readiness setea `indexingReadinessError`. Fallo de overview setea `overviewError`. Reset de TODOS los estados de error (incluidos `documentsError`/`errorsError` preexistentes) al inicio de cada efecto y dentro de ambas ramas NOT_FOUND — espejo del patrón :465. Exponer los campos nuevos en el return tipado. |
| `features/embedding/components/EmbeddingBundleInspector.tsx` | Props opcionales `validationError?: string \| null` y `readinessError?: string \| null`: renderizan `.notice.notice-danger` (role="alert") en su sección correspondiente. La sección se omite SOLO cuando dato=`null` SIN error (dato realmente no disponible aún). |
| `features/indexing/components/ActivationPanel.tsx` | Prop opcional `readinessError?: string \| null` → `notice-danger` encima del bloque readiness existente. |
| `features/embeddingIndexing/EmbeddingIndexingWorkspace.tsx` | Cablear las props nuevas hook→paneles y mostrar un aviso danger superior cuando `indexing.overviewError` (afecta al feature flag bundle-first mostrado por `IndexingRunPanel`). |
| `features/embedding/components/EmbeddingBundleInspector.test.tsx` (nuevo) y `features/indexing/components/IndexingErrorsPanel.test.tsx` (nuevo) | Casos: (a) con validationError/readinessError ⇒ alerta visible; (b) IndexingErrorsPanel con `error` ⇒ nota verde ausente y alerta presente; (c) éxito con 0 errores ⇒ nota verde presente. Seguir el estilo de los `.test.tsx` existentes (vitest + testing-library). |

## No hacer
- No reintentar automáticamente ni silenciar 404 legítimos: mientras un run corre,
  "validación aún no disponible" sigue siendo estado pendiente, no error.
- No tocar `usePollingLoop` ni la lógica de polling (verificada correcta).
- No dividir el hook en este plan (monolito queda en backlog 🟡.4); solo cambios
  aditivos de estados y efectos de carga.

## Verificación

    cd app/front && npm test && npm run test:components

## Riesgos y rollback
Medio-bajo: el hook es el archivo más grande del front (944 líneas), pero los
cambios son aditivos (estados nuevos + catches individuales) sin reordenar lógica
existente. Rollback por commit aislado.
