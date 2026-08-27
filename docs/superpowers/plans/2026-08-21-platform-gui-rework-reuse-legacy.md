# Plan — Rework de GUIs de Platform reutilizando la lane legacy (multi-proyecto)

- **Fecha**: 2026-08-21
- **Rama**: main
- **Área**: front (+ ajustes puntuales de back para defectos bloqueantes)
- **Estado**: EXPLORACIÓN CERRADA / LISTO PARA EJECUCIÓN
- **Predecesor**: `docs/superpowers/plans/2026-08-20-fase8-gui-plataforma-plan.md` (Fase 8, CERRADA)

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convertir Platform en la superficie multi-proyecto limpia y auditable para operar el ciclo RAG completo (`documents -> corpus snapshots -> variants -> releases`) reutilizando la lógica visual y operativa madura de legacy, que ya funciona para un corpus, pero parametrizada por `project_id` para soportar proyectos con corpus distintos y releases verificables por `rag_release_id`.

**Architecture:** FastAPI sigue siendo la autoridad de scope, idempotencia, permisos, build y compatibilidad; React solo dispara comandos Platform y consume read-models tipados. El build de release pasa a job durable server-owned con estado consultable bajo demanda y refresh controlado solo cuando la release visible esté `queued`/`running`. La UI de Platform consume adapters propios sobre componentes, flujo y patrones legacy: el patrón probado de legacy para un corpus se reutiliza por `project_id`, sin acoplar Legacy a Platform ni duplicar una segunda orquestación.

**Tech Stack:** Python 3.12, FastAPI, Pydantic 2, PostgreSQL/in-memory repositories, React, TypeScript strict mode, `platformApi`, shared API client, legacy `pipelineState`/`pipelineFlow`/panel primitives, pytest, Vitest, production frontend build.

**Spec:** Este plan reemplaza y consolida `docs/superpowers/plans/2026-08-21-platform-gui-rework-continuation.md`, y deriva de `docs/superpowers/plans/Plan_Ajustado_Plataforma_RAG_MultiProyecto(3).md`.

## Global Constraints

- No borrar ni sustituir documentos fuente; este archivo es el plan definitivo de ejecución.
- No reabrir contratos de Fase 7 ni exponer `actor_id`, `indexing_target_id`, rutas físicas, secretos, chunks raw o vectores al frontend.
- Fail-closed siempre visible: nada de fallbacks silenciosos, listas vacías falsas o success envelopes inventados.
- Platform y Legacy permanecen superficies hermanas; Platform puede reutilizar piezas, pero Legacy no importa tipos Platform.
- Backend owns build authority: el browser nunca orquesta chunking, embedding, indexing ni selección física de target.
- Evitar consulta agresiva para estado de build Platform; usar status bajo demanda y, si hay auto-refresh, que sea adaptativo con backoff, pausa por pestaña oculta, timeout y refresh manual.
- TDD obligatorio por tarea: prueba fallida, implementación mínima correcta, pruebas focalizadas, regresión afectada y cierre documentado.

---

## Idea Central

Platform no debe ser una UI paralela improvisada. Debe reutilizar la lógica visual
y operativa madura de la lane legacy, pero aplicada por `project_id`.

Legacy pipeline ya demuestra que el flujo RAG funciona para un corpus. Platform
debe reciclar esas vistas, estados y patrones para operar muchos proyectos, donde
cada proyecto puede tener un corpus distinto, snapshots distintos, variantes
distintas y releases distintas.

La Platform debe permitir operar el ciclo RAG multi-proyecto completo:
documentos, corpus snapshots, variantes y releases. Ese reuso no puede debilitar
auditoría, aislamiento, trazabilidad ni contratos de Fase 7.

El E2E objetivo no es que Platform pinte una UI bonita aparte: es que desde
Platform se pueda llegar a una release RAG auditada y operable, identificada por
`rag_release_id`, usando el backend y los contratos de Platform.

## Objetivo del plan

- Reusar componentes y patrones legacy donde ya funcionan bien.
- Parametrizar el pipeline visual/operativo legacy por `project_id`, no por un
  corpus global único.
- Mantener Platform y Legacy como superficies separadas.
- Evitar duplicación de UI, hooks, estados, tablas y lógica de flujo.
- Corregir bloqueos reales: build síncrono, listas incompletas, selección masiva
  y UX inconsistente.
- Preservar fail-closed: si algo falta, falla, está bloqueado o requiere revisión,
  se muestra como tal.

## Método de acción

1. Cerrar Fase A primero: job asíncrono durable para `releases/{id}/build`, estado
   consultable y tests backend de contrato.
2. Generalizar carga completa/paginada para `variants` y `releases`, igual que ya
   se hizo en `documents` y `corpus`.
3. Extraer/reusar de legacy la capa de estado, flujo, paneles, tablas y navegación
   que ya está probada.
4. Recomponer las vistas Platform sobre esa capa compartida.
5. Pulir accesibilidad, responsive, estados de error, runbook y verificación final.

## Resultado final esperado

Platform queda como una superficie multi-proyecto limpia, auditable y operable,
con la misma calidad de flujo que legacy, pero sin mezclar contratos ni
responsabilidades.

El operador podrá seleccionar proyecto, revisar documentos, crear snapshots,
crear variantes, construir releases, validar y publicar sin caídas de socket, sin
listas truncadas, sin selección riesgosa y sin sobrecargar el sistema con refresh
innecesario.

La prueba E2E debe demostrar que un proyecto con su corpus propio puede completar
el flujo hasta una release RAG identificada por `rag_release_id`, sin depender del
corpus único de legacy ni de una orquestación frontend paralela.

## 0. Cierre de exploración (2026-08-21)

La exploración ya no está “en abstracto”: este branch deja resueltos los
prerrequisitos mínimos para ejecutar el rework sin volver a redescubrir los
mismos bugs.

### Evidencia cerrada en código

- **D-1 parcial, ya aterrizado en la UI real**:
  - `app/front/src/features/platform/platformApi.ts`
    añade `collectAllPages`, `listAllDocuments` y `listAllCorpusSnapshots`.
  - `app/front/src/features/platform/documents/useDocumentIntakeWorkspace.ts`
    carga el corpus documental completo.
  - `app/front/src/features/platform/corpus/useCorpusSnapshotWorkspace.ts`
    carga todas las revisiones candidatas y todo el historial de snapshots.
- **D-2 parcial, ya aterrizado con política fail-closed**:
  - Intake documental: `Seleccionar todos` ya no auto-incluye revisiones
    `needs_review`; esas quedan para selección explícita del operador.
  - Snapshot builder: ya existe selección masiva (`Seleccionar todas las
    elegibles`) y tampoco auto-incluye `needs_review`.
- **D-3a, desbloqueo de transporte verificado**:
  - `app/back/src/ingestion/gui/server.py` ya convierte excepciones del bridge en
    `500` con envelope (`PIPELINE_BRIDGE_ERROR`) en vez de cortar el socket.
  - `app/back/tests/ingestion/test_gui_server.py` fija la regresión con test
    explícito del caso de excepción.

### Verificación ejecutada en este branch

- Backend: `C:\venvs\chatbot-sst\Scripts\python.exe -m pytest app/back/tests/ingestion/test_gui_server.py -q`
- Frontend focalizado: Vitest de `documents`, `corpus` y `PlatformWorkspace`
- Frontend completo: `npm --prefix app/front run test`
- Frontend build: `npm --prefix app/front run build`

### Qué NO quedó cerrado aún

- **D-3b RESUELTO (2026-08-24, Tasks 1+2)**: `releases/{id}/build` ya es asíncrono
  y durable — encola (`202`), un runner corre el motor con conexión propia en
  Postgres y persiste el estado en `release_build_jobs`, observable por
  `GET /build-status`. Ver ADR-010. Ya no hay build síncrono que cuelgue el socket.
- **La recomposición grande de Platform sobre la lane legacy no empezó aún**:
  este cierre prepara el terreno, no ejecuta las Fases C/D/E.
- **La paginación completa YA se generalizó a las cuatro listas project-aware**:
  `platformApi.ts` expone `listAllVariants`/`listAllReleases` además de
  `listAllDocuments`/`listAllCorpusSnapshots`, y los hooks de `variants` y
  `releases` ya los consumen (`useVariantMatrixWorkspace.ts`,
  `useRagReleaseWorkspace.ts`). Queda por auditar cualquier vista futura que
  vuelva a consumir solo la primera página.
- **La recomposición grande de Platform sobre la lane legacy no empezó** (Fases
  C/D/E): este cierre prepara el terreno, no las ejecuta.

## 1. Problema

Fase 8 construyó las superficies de Platform (Projects, Variants, Documents,
Corpus, Releases) **desde cero**. La lane **Legacy pipeline** ya resuelve bien la
gestión del pipeline RAG de un corpus (ingesta → normalize → chunk → embed →
index → retrieval), con vistas maduras: shell con `view-switcher`, orquestación
por máquina de estados, refresh de runs, paneles de run/estado/catálogo, tablas y
tokens consistentes. Platform reinventó esas piezas peor, en vez de reciclarlas.

La consecuencia práctica (con datos reales de `sst-general`, 55 documentos):

- **Intake lista solo 25 de 55** documentos (`page_size` por defecto = 25; la
  vista no pagina ni sube el tamaño).
- **No hay "seleccionar todos"** en intake ni en snapshot: marcar 55 revisiones a
  mano es inviable.
- **`GET variant-matrix` y `POST releases/{id}/build` responden *socket hang
  up*** — el backend GUI cierra la conexión sin responder.
- Las vistas de Platform "se ven horribles" y no siguen el lenguaje de la lane
  legacy.

La idea rectora del operador: **lo que el legacy hace para un corpus, Platform
debe hacerlo por `project_id`, reutilizando las mismas vistas** — no una segunda
implementación paralela.

## 2. Objetivo

Reutilizar los componentes/máquina-de-estados probados de la lane legacy,
parametrizados por proyecto y alimentados por `platformApi` (contrato de Fase 7),
de modo que Platform ofrezca la misma gestión de pipeline RAG que el legacy, pero
multi-proyecto, con UX y estética consistentes. Cerrar de paso los defectos
bloqueantes que impiden operar con un corpus real.

### No-objetivos

- No reabrir el contrato backend de Fase 7 (auth, scope, sin fuga de target
  físico, idempotencia).
- No fusionar las dos superficies: `Legacy pipeline` sigue existiendo y
  etiquetada; Platform es la superficie multi-proyecto.
- No implementar SSO/OIDC, chat, ni administración de retrieval de producción.
- No reescribir el backend de plataforma salvo los arreglos puntuales del §5.

## 3. Inventario de reutilización (auditoría previa)

Qué ya existe y es reutilizable (evitar duplicación):

| Legacy / compartido | Qué aporta | Reuso en Platform |
| --- | --- | --- |
| `features/embeddingIndexing/shared/{pipelineState,pipelineFlow,usePollingLoop}` | Máquina de estados del pipeline + patrones de refresh/visibilidad legacy | Reusar estados, transiciones y disciplina de abort/visibilidad; Platform no copia polling agresivo ni orquesta etapas legacy |
| `features/{embedding,indexing,retrieval,chunking}/components/*` | Paneles de run, estado, catálogo, tablas densas | Vistas por etapa del pipeline, alimentadas con datos scope-aware |
| `features/dashboard/{DashboardApp,components/DashboardChrome}` | Shell, `DashboardNotice`, `view-switcher`, `user-chip` | Lenguaje de shell ya adoptado por `OperatorApp` |
| `components/ui/{MetricCard,StatePanel,StatusBadge}` | Estados y badges compartidos (extraídos en Task 12) | Ya en uso; ampliar adopción |
| `shared/api/*` + `platformApi.ts` | Cliente HTTP tipado, envelope único, cookie same-origin | Fuente de datos de todas las vistas |

### Funcionalidades textuales de Pipeline Legacy observadas con Playwright y código

Este inventario es parte del contrato funcional visible que Platform debe reutilizar
por proyecto. No describe capacidades nuevas ni exige forzar Platform a verse como
Legacy; documenta las funcionalidades operacionales que ya existían en la lane
`Legacy pipeline` y que se perdieron o quedaron fragmentadas en la GUI actual de
RAG Platform.

**Elementos Globales**
- Sidebar propia de `SST Pipeline`.
- Navegación: `Operacion`, `Revision`, `Inventario`, `Chunking`, `Embedding/Indexing`.
- Topbar con título de pantalla, run/schema actual, switcher rápido y botón `Actualizar`.
- Métricas generales: `Total`, `Procesados`, `En revisión`, `Fallidos`, `Aprobados`, `Rechazados`.
- Notices de éxito/error/warning para acciones del operador.

**1. Operación**
- Resumen del estado documental del pipeline.
- Panel de proveedor de ingesta PDF:
  - Modo `Local`.
  - Modo `Llama`.
  - Estado de configuración LlamaCloud.
  - Tier/version/provider.
- Configuración de servicios Llama:
  - `Parse`.
  - `Classify`.
  - `Extract`.
  - Orden permitido, por ejemplo `Classify > Parse > Extract`.
- Configuración de calidad:
  - `Umbral OCR`.
  - Guardado de ajustes.
- Carga de nuevo documento:
  - Selección `.pdf`, `.md`, `.markdown`.
  - Categoría.
  - Carpeta destino.
  - Subir documento.
- Acciones del pipeline:
  - Ejecutar ingesta local en staging o enviar a LlamaCloud.
  - Validar salida oficial o staging.
  - Promover staging.
- Resumen de validación:
  - Estado.
  - Ruta de manifest.
  - Resultado JSON de última acción.

**2. Revisión**
- Lista de documentos pendientes de decisión manual.
- Columnas de revisión:
  - Documento.
  - Categoría.
  - Motivos.
  - Decisión.
- Campo de nota/motivo por documento.
- Acciones:
  - `Aprobar`.
  - `Rechazar`.
  - `Ver detalle`.
- Inspector lateral:
  - Nombre y ruta del documento.
  - `document_id`.
  - Categoría.
  - Tipo.
  - Tamaño.
  - Proveedor/método de ingesta.
  - OCR/confianza.
  - Fecha.
  - Motivos de revisión.
  - Detalles auditables.
  - Decisión registrada si existe.

**3. Inventario**
- Tabla completa del inventario normalizado.
- Búsqueda por documento.
- Filtro por estado:
  - Procesados.
  - En revisión.
  - Fallidos.
  - Aprobados.
  - Rechazados.
- Filtro por ingesta:
  - Local.
  - Llama.
  - Sin ingesta.
  - Método específico.
- Columnas:
  - Ruta del documento.
  - Tipo.
  - Ingesta.
  - Confiabilidad.
  - Categoría.
  - Tamaño.
  - Estado.
  - Decisión de revisión.
  - Fecha.
- Acción `Revisar evidencia`.
- Inspector lateral reutilizado para ver procedencia, motivos, OCR, decisión y metadata.

**4. Chunking**
- Lanzar corrida de chunking.
- Scope:
  - `Documentos`.
  - `Corpus`.
- Selección de perfil de chunking.
- Entrada de `Document IDs` cuando el scope es documentos.
- Opción `Forzar reprocesado`.
- `Idempotency-Key` editable.
- Acción para regenerar idempotency key.
- Acción `Iniciar chunking`.
- Panel de perfil activo:
  - Perfil.
  - Children min.
  - Target.
  - Max.
  - Overlap.
  - Overlap min/max.
- Métricas:
  - Corrida activa.
  - Estado.
  - Progreso.
  - Validation.
- Estado de corrida:
  - Status.
  - Perfil.
  - Documentos solicitados.
  - Progreso.
  - Warnings.
  - Links a corrida, documentos y validación.
- Validación de chunking:
  - Estado.
  - Revisados.
  - Errores.
  - Warnings.
- Tabla de documentos chunked o persistidos.
- Inspección parent-child:
  - Selección de documento.
  - Lista de parents.
  - Texto resumido del parent.
  - Páginas fuente.
  - Lista de children.
  - Token count.
  - Overlap previo/siguiente.
  - Warnings de overlap cero.

**5. Embedding/Indexing**
Es una pantalla grande con flujo interno de 4 etapas.

**5.1 Embedding**
- Catálogo de perfiles de embedding.
- Perfil habilitado/bloqueado con motivo visible.
- Selección de perfil.
- Selección de `chunk bundle`.
- Ejecutar embedding sobre un bundle.
- Ejecutar embedding de todo el corpus.
- Progreso de batch del corpus.
- Estado del run:
  - Run id.
  - Status.
  - Polling.
  - Children embebidos / solicitados.
  - Warnings.
  - Error summary.
- Inspector de embedding bundle:
  - Bundle id.
  - Dimensión.
  - Número de vectores.
  - Estado.
  - Validación.
  - Readiness.
  - Tabla de chunks del bundle.
  - Checks de validación.
  - Bloqueos para indexing.

**5.2 Indexing**
- Muestra `embedding bundle` actual.
- Target resuelto por servidor.
- Ejecutar indexing de un bundle.
- Ejecutar indexing de todo el corpus.
- Progreso de batch.
- Estado del run:
  - Validación.
  - Activación.
  - Run id.
  - Documentos committed / solicitados.
  - Warnings.
  - Run interrumpido.
- Tabla de documentos indexados:
  - Documento.
  - Estado.
  - Elegibilidad.
  - Vectores.
  - Commit/indexado.
- Panel de errores:
  - Documento.
  - Código de error.
  - Status.
  - `internal_error_id`.

**5.3 Activation**
- Activación como etapa separada del indexing.
- Selección de política de fallback léxico:
  - Permitir cuando vector no disponible.
  - Nunca.
  - Siempre.
- Acción `Activar`.
- Readiness de retrieval:
  - Filas activas.
  - Motivos de bloqueo.
- Resultado de activación:
  - Filas activadas.
  - `retrieval_profile_id`.

**5.4 Retrieval**
- Catálogo de perfiles de retrieval.
- Selección de perfil.
- Estado activo/inactivo.
- Validación y runtime.
- Estado de retrieval:
  - Perfil.
  - Validación.
  - Fallback léxico.
  - Runtime.
  - Motor disponible/no disponible.
  - Vector retrieval habilitado.
  - Fallback permitido.
  - Readiness.
  - Documentos activos.
- Validación de retrieval:
  - Acción `Validar perfil`.
  - Query sintética interna.
  - Candidatos encontrados.
  - Dimensión.
  - Versión del validador.
  - Motivos de bloqueo.
- Búsqueda de evidencia:
  - Campo de consulta.
  - `Top K`.
  - Acción `Buscar evidencia`.
  - Resultados con:
    - Documento.
    - Tipo de evidencia.
    - Fuente vector/léxico.
    - Score.
    - Páginas.
    - Texto recuperado.

**Conclusión de reutilización:** Legacy no era solo una vista bonita; tenía un
flujo operacional completo desde ingesta/configuración hasta retrieval
verificable. RAG Platform debe absorber estas capacidades por proyecto, no
reemplazarlas por pantallas CRUD separadas.

Qué reinventó Platform y hay que **reemplazar por lo anterior**: tablas y formularios
propios en `platform/{documents,corpus,variants,releases}` que no siguen el patrón
de run-panels/tablas del legacy.

## 4. Estrategia

1. **Generalizar, no duplicar.** Extraer de la lane legacy los componentes de
   etapa (chunk/embed/index/retrieval) y la orquestación a una capa reutilizable
   que acepte un **contexto de proyecto** (`project_id` + scope) en vez de asumir
   el corpus legacy único. Donde el componente hoy asume la lane global, se le
   inyecta el contexto por props/hook.
2. **Platform compone.** Los workspaces de Platform pasan a **componer** esos
   componentes generalizados, alimentándolos con `platformApi` (datos
   project-aware). Se eliminan las tablas/formularios ad-hoc de Fase 8 que no
   aportan.
3. **Arreglar el data-layer una vez.** Paginación real + "seleccionar todos" +
   estados vacíos/carga viven en los componentes compartidos de lista/tabla, así
   ambos lanes se benefician.
4. **Desbloquear el backend** (§5) antes de confiar la UI de variante/release: sin
   eso, la vista se rehace sobre una API que se cae.

## 5. Defectos a resolver (raíz, no síntoma)

### D-1 · Paginación del read-model (25 de 55)
- Causa: `listDocuments(pid, undefined)` usa `DEFAULT_PAGE_SIZE=25`; la UI no
  pagina ni sube `page_size` (máx `MAX_PAGE_SIZE=100`).
- Arreglo: read-model paginado en la vista (controles página/tamaño) **o** carga
  incremental hasta agotar `total_pages`. Aplica a Documents, Corpus, Releases,
  Variants (cualquier lista scope-aware). Corpus > 100 exige paginación real, no
  solo subir el tamaño.

### D-2 · "Seleccionar todos" / selección masiva
- Falta en intake (normalize) y snapshot builder.
- Arreglo: acción de selección masiva sobre el conjunto **cargado** (respetando
  paginación: "seleccionar todos en esta página" vs "todos los N"), en el
  componente de tabla compartido. Mantener el gate fail-closed de `needs_review`
  (una revisión que exige decisión no se auto-incluye en "todos").

### D-3 · `variant-matrix` y `releases/build` → *socket hang up*
- Síntoma: el bridge GUI (`ThreadingHTTPServer` → `AsgiBridge` → FastAPI) cierra
  la conexión sin responder.
- Hipótesis a diagnosticar (backend):
  - `GET variant-matrix`: excepción no manejada en el `AsgiBridge` o en la
    serialización de celdas para el proyecto real (p. ej. binding/perfil ausente,
    o el bridge no traduce una excepción a envelope y muere el handler).
  - `POST releases/{id}/build`: el build corre el **motor real de forma
    síncrona** dentro del request HTTP de un servidor de un solo hilo → bloquea
    hasta timeout/caída del socket.
- Arreglo decidido: (a) mantener el `AsgiBridge` endurecido para que toda
  excepción se convierta en respuesta con envelope (nunca cerrar el socket);
  (b) ejecutar el build **asíncrono/encolado** con estado durable; (c) exponer
  `GET build-status` para consulta bajo demanda; (d) si la UI necesita
  auto-refresh, hacerlo solo mientras la release visible esté `queued`/`running`,
  con backoff, pausa al ocultar pestaña, timeout, cancelación al cambiar de
  release/proyecto y botón manual de refresh. Esto evita consulta agresiva y no
  exige WebSockets/SSE real, que hoy no encaja bien porque `AsgiBridge` bufferiza
  las respuestas ASGI.
- **Este defecto es prerrequisito**: la UI de Variants/Releases no se puede
  rehacer con confianza mientras la API se cae.

### D-4 · Estética/UX de las vistas Platform
- Se resuelve estructuralmente al reusar los componentes legacy (§4), no con
  parches cosméticos.

## 6. Decisiones Técnicas Grandes

La versión definitiva combina este plan con
`2026-08-21-platform-gui-rework-continuation.md`, pero corrige la decisión de
progreso del build: **no se implementa consulta agresiva de 1s para Platform**.

La arquitectura final es:

1. `POST /api/platform/releases/{id}/build` no ejecuta el build en el request:
   reserva o reusa un job idempotente, valida permisos/scope server-side y
   responde `202 Accepted` con un snapshot de job.
2. El backend ejecuta el build en un runner server-owned. El navegador nunca
   orquesta chunking, embedding, indexing, targets físicos ni etapas internas.
3. `GET /api/platform/releases/{id}/build-status` devuelve el último snapshot
   durable para recarga, diagnóstico y pruebas.
4. El estado del job es consultable bajo demanda. Si se habilita auto-refresh, es
   adaptativo: solo para la release visible en `queued`/`running`, con backoff,
   pausa al ocultar pestaña, timeout, abort al cambiar de contexto y botón manual
   de refresh.
5. El frontend nunca envía `indexing_target_id`, paths físicos, `actor_id`,
   secretos ni autoridad física. El backend deriva proyecto, variante, snapshot,
   binding lógico, target real y permisos.
6. La UI no orquesta chunking, embedding ni indexing legacy; solo dispara comandos
   de Platform y muestra estado.
7. La paginación se resuelve correctamente para documents, corpus, variants y
   releases.
8. `needs_review` nunca entra por selección masiva automática.
9. Se reusa la lane legacy para estados, paneles, tablas, navegación, tokens,
   errores y disciplina de abort/visibilidad; **no** se copia una segunda lógica
   paralela de flujo.

Esta decisión es la opción más conservadora para el estado actual del repo:
evita bloquear el servidor, evita sobrecargar con refresh innecesario, no requiere
WebSockets, no fuerza SSE sobre un `AsgiBridge` que hoy bufferiza respuestas, y
conserva un contrato auditable e idempotente.

## 7. Estructura de archivos definitiva

### Backend

- Crear `app/back/src/rag_platform/domain/release_build_job.py`: entidad/DTO de
  job, estado, versión, timestamps, error y reporte.
- Crear `app/back/src/rag_platform/application/release_build_job_service.py`:
  casos de uso `StartReleaseBuildJobUseCase` y `GetReleaseBuildJobStatusUseCase`.
- Modificar `app/back/src/rag_platform/application/release_build_service.py`:
  conservar la lógica durable por revisión; mover la invocación al runner.
- Modificar `app/back/src/rag_platform/application/services.py`: exponer los
  nuevos casos de uso en `RagPlatformServices`.
- Modificar `app/back/src/api/dependencies.py`: cablear repositorios/runners en
  modo in-memory y Postgres.
- Crear `app/back/src/rag_platform/infrastructure/in_memory/release_build_jobs.py`:
  repo determinístico y runner drenable para tests.
- Crear `app/back/src/rag_platform/infrastructure/postgres/release_build_jobs.py`:
  persistencia durable de job, versión y latest-by-release.
- Modificar `app/back/src/rag_platform/api/schemas.py`: agregar
  `ReleaseBuildJobSchema` y mapper desde snapshot.
- Modificar `app/back/src/rag_platform/api/router.py`: cambiar `POST /build` a
  `202` y agregar `GET /build-status`. Agregar `GET /build-status/wait` solo si
  la implementación demuestra que reduce carga frente a refresh adaptativo simple.
- Modificar `app/back/tests/rag_platform/test_platform_api.py`: contratos HTTP
  de enqueue, replay, status, refresh controlado si aplica, error y scope.
- Crear `app/back/tests/rag_platform/test_release_build_jobs.py`: contrato de
  dominio/aplicación del job.
- Modificar `app/back/tests/ingestion/test_gui_server.py`: regresión del bridge
  para que errores sigan llegando como envelope, no socket cortado.

### Frontend

- Modificar `app/front/src/features/platform/platformApi.ts`: agregar
  `listAllVariants`, `listAllReleases`, `startReleaseBuild`,
  `getReleaseBuildStatus` y, solo si existe endpoint wait, `waitReleaseBuildStatus`.
- Modificar `app/front/src/features/platform/platformTypes.ts`: exponer los
  aliases generados del nuevo schema de job.
- Crear `app/front/src/features/platform/shared/useAdaptiveBuildStatusRefresh.ts`:
  hook de refresh controlado, abortable, visibility-aware, con backoff, timeout y
  botón manual. Puede usar `GET build-status` o `GET build-status/wait` si ese
  endpoint se implementa.
- Crear `app/front/src/features/platform/shared/platformPipelineState.ts`: adapter
  de documentos/corpus/variants/releases/job a estado de pipeline compartido.
- Crear `app/front/src/features/platform/shared/platformPipelinePanels.tsx`:
  composición de paneles/tokens legacy con datos Platform.
- Modificar `app/front/src/features/platform/releases/useRagReleaseWorkspace.ts`:
  cambiar build síncrono por enqueue + status visible + refresh terminal
  controlado; cargar releases, variants y snapshots completos.
- Modificar `app/front/src/features/platform/releases/BuildReport.tsx` y
  `ReleaseLifecycle.tsx`: renderizar `queued/running/succeeded/failed` sin fingir
  que el build muta directamente el lifecycle.
- Modificar `app/front/src/features/platform/variants/useVariantMatrixWorkspace.ts`:
  dejar de depender de página 1 para variants.
- Modificar `app/front/src/features/platform/documents/DocumentIntakeWorkspace.tsx`,
  `corpus/CorpusSnapshotWorkspace.tsx`, `variants/VariantMatrixWorkspace.tsx`,
  `releases/RagReleaseWorkspace.tsx` y `PlatformWorkspace.tsx`: recomponer con
  paneles compartidos donde reduzca duplicación real.
- Modificar `app/front/src/styles/platform.css`: solo tokens/ajustes compartidos;
  sin parches visuales por pantalla que dupliquen legacy.

### Documentación

- Crear o modificar `docs/runbooks/platform-release-build.md`: flujo operativo,
  estados, errores, reintentos, recuperación y verificación.
- Mantener este archivo como plan fuente; no crear planes paralelos para la misma
  ejecución.

## 8. Tareas ejecutables

> **For agentic workers:** REQUIRED SUB-SKILL: usar
> `superpowers:subagent-driven-development` o `superpowers:executing-plans`.
> Cada tarea exige TDD: prueba fallida, implementación mínima, prueba focalizada,
> regresión afectada y revisión de seguridad/trazabilidad.

### Task 1: Fase A backend, contrato de job asíncrono durable

**Archivos:** `release_build_job.py`, `release_build_job_service.py`,
`test_release_build_jobs.py`, `test_platform_api.py`.

**Interfaces producidas:**

```python
class ReleaseBuildJobState(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
```

```python
@dataclass(frozen=True)
class ReleaseBuildJobSnapshot:
    job_id: str
    rag_release_id: str
    project_id: str
    state: ReleaseBuildJobState
    version: int
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None
    report: dict[str, object] | None
    error: dict[str, object] | None
```

> **Task 1 CERRADA (2026-08-24).** Operador corrió los tests en verde
> (`test_release_build_job_service.py` 11/11; `test_platform_api.py` 47 passed).

- [x] Tests de aplicación → `app/back/tests/rag_platform/test_release_build_job_service.py`:
  enqueue deja `queued`; get-status latest-by-release / `None` sin builds; enqueue y
  status fuera de scope fallan cerrado; runner marca `running → succeeded|failed`
  (nunca colgado en `running`).
- [x] Tests HTTP: `POST /build` responde el job encolado, `GET /build-status` está
  cubierto por el read-model; los tests de `/build` de `test_platform_api.py` (header
  obligatorio + release inexistente + replay) siguen verdes (47 passed).
- [x] Repo in-memory + Postgres (`InMemory/PostgresReleaseBuildJobRepository`) con
  latest-by-release (`created_at desc, id`); migración `20260824_01_create_release_build_jobs.sql`.
- **Modelo real (desviación honesta vs el borrado del plan):** `ReleaseBuildJob`
  (`domain/build_jobs.py`) con `build_job_id` (no `ReleaseBuildJobSnapshot`/`job_id`).
  **Sin campo `version` monotónico** — el latest se resuelve por `created_at`; más
  simple (ponytail) y suficiente para el polling. La idempotencia NO se re-implementa
  en la tabla del job: la garantiza el store `platform_idempotency` existente (replay
  del mismo `Idempotency-Key` → mismo `build_job_id`, sin re-encolar).
- Archivos: `domain/build_jobs.py`, `application/release_build_job_service.py`,
  `domain/errors.py` (`RELEASE_BUILD_JOB_NOT_FOUND`), repos in-memory/Postgres, migración.

### Task 2: Runner, wiring y persistencia durable

**Archivos:** `dependencies.py`, `services.py`, `router.py`,
`release_build_service.py`, repos Postgres/in-memory.

> **Task 2 CERRADA (2026-08-24).** Wiring + flip de contrato + runner + ADR-010.
> Backend verde (operador: `test_release_build_job_service.py` + `test_platform_api.py`
> 47 passed; `test_gui_server.py` verde en el pase de Task A/2b).

- [x] Wiring de `RagPlatformServices` (+4 campos: `enqueue_release_build`,
  `get_release_build_status`, `submit_release_build`, `release_build_jobs`) en el
  ÚNICO sitio de construcción (`dependencies.py:851`); job repo cableado en ambas
  ramas (memoria/Postgres).
- [x] `POST /api/platform/releases/{id}/build` → **encola** y responde
  `ReleaseBuildAcceptedSchema` (`{build_job_id, rag_release_id, state:"queued"}`);
  el guard de idempotencia asegura replay = mismo job sin re-encolar.
- [x] `GET /releases/{id}/build-status` → `ReleaseBuildStatusSchema | null`. **No** se
  añadió `/build-status/wait`: el refresh adaptativo usa **status bajo demanda**
  (polling con `usePollingLoop`), la alternativa que el plan permitía documentar.
- [x] El build real corre SOLO en el runner (`infrastructure/release_build_runner.py`):
  en Postgres con **conexión propia** (bundle fresco por build vía `build_services_factory`),
  no comparte la conexión del request ni la bloquea; traduce excepciones a
  `error_code`/`error_message`; no guarda secretos/chunks/vectores.
- [x] Persistencia Postgres: latest-by-release, estado, timestamps
  (`created_at`/`updated_at`), reporte resumido (revisions_built/reused/built) y error
  sanitizado. **Sin `version`** (desviación ponytail); idempotencia reusada del store
  existente (no duplicada en la tabla del job).
- [x] **ADR-010** (`docs/adr/ADR-010-async-durable-release-build.md`) por el cambio de
  contrato de `/build`.
- Archivos: `application/services.py`, `api/dependencies.py`, `api/router.py`,
  `api/schemas.py`, `infrastructure/release_build_runner.py`.

### Task 3: Carga completa/paginada para variants/releases y build UX controlada

**Archivos:** `platformApi.ts`, `platformTypes.ts`,
`useAdaptiveBuildStatusRefresh.ts`, `useRagReleaseWorkspace.ts`, tests de Platform.

> **Task 3 IMPLEMENTADA y verificada por tests (2026-08-24).** Operador corrió
> `npm --prefix app/front test` (70/70 verde) + `run build` (OK) + backend
> (`test_release_build_job_service.py`, `test_platform_api.py` 47 passed).
> **Falta solo el gate final:** verificación Playwright runtime cuando la app esté
> levantada (ver más abajo). NO se avanza a Task 4 hasta hacerla.

- [x] Tests de API: `listAllVariants`/`listAllReleases` recorren todas las páginas
  (`collectAllPages`); `buildRelease` (encola) y `getReleaseBuildStatus` pegan a los
  endpoints correctos (cubierto en `platformApi.test.mjs` + guards).
- [x] Refresh controlado del build: **reusa `usePollingLoop` legacy** (no se creó
  `useAdaptiveBuildStatusRefresh` — ponytail: el loop legacy ya da abort, pausa por
  `document.hidden`, no-solapamiento, intervalo fijo 2500 ms y parada en terminal).
  Sin backoff exponencial (desviación honesta: el no-solape acota la carga). Solo
  activo mientras la release visible está `queued`/`running`; un request activo;
  cancela al cambiar release/proyecto; botón manual; error visible; sin `setInterval`
  rígido.
- [x] `useRagReleaseWorkspace.build()` encola, guarda el job, muestra estado, arranca
  el polling controlado, refresca la release al terminal y conserva la Idempotency-Key
  por intención (D7).
- [x] Releases y variants ya consumen `listAllReleases`/`listAllVariants` (no página 1).
- [x] Ejecutados por el operador: `npm --prefix app/front run test` (verde) + `run build` (OK).
- [x] **Gate final — Playwright runtime (codex, 2026-08-24):** ejecutado con la app
  arriba; capturas/consola en `.playwright-cli/`. Derivó además el inventario funcional
  de la lane Legacy que Platform debe reusar por proyecto (§3, insumo de Task 4).
- [x] **Auditoría de cierre (2026-08-24) — 2 defectos hallados y resueltos:**
  - **Bug fail-closed (front):** `useRagReleaseWorkspace` no surfaceaba `buildPoll.error`;
    un fallo persistente de `build-status` (401/403/404/red) quedaba invisible hasta el
    timeout de 5 min mostrando "encolado". Fix: se expone `buildStatusError` y `BuildReport`
    lo muestra ("última consulta de estado falló … reintentando") mientras `queued`/`running`.
  - **Bug seguridad (back):** `release_build_runner.py`, rama `except Exception`, guardaba
    `f"{type(exc).__name__}: {exc}"` verbatim y ese texto llegaba al browser vía build-status
    (riesgo de fuga de ruta física / secreto, invariante Fase 7). Fix: patrón `internal_error_id`
    legacy — log completo server-side + `error_code=RELEASE_BUILD_INTERNAL_ERROR` + mensaje con
    id opaco; nunca el `str(exc)` crudo. Test añadido: `test_runner_excepcion_inesperada_no_filtra_detalle_al_cliente`.
- [x] **Verificación del operador (2026-08-24) — VERDE:** `pytest app/back/tests/rag_platform`
  = **284 passed** (incluye el nuevo `test_runner_excepcion_inesperada_no_filtra_detalle_al_cliente`);
  `test_gui_server.py` 36 passed; front **70/70** + build OK. El único rojo fue
  `test_dos_reservas_concurrentes_reales_solo_un_dueno` (marker `postgres_live`), **no**
  relacionado con el rework: reventaba con `SST_POSTGRES_DSN` placeholder (`host=x`
  inalcanzable). Endurecido para **skipear** cuando Postgres no es alcanzable (probe de
  conexión → `pytest.skip`), acorde a la intención del marker. `npm --prefix app/front run lint`
  no existe (CLAUDE.md); omitido.

> **Task 3 CERRADA (2026-08-24).** Full-data loading (4 listas), build asíncrono con
> UX controlada (enqueue 202 + polling terminal + refresh manual, sin polling agresivo),
> gate Playwright runtime (codex) y 2 defectos de auditoría resueltos (fail-closed de
> polling + no-fuga de detalle en error de build). Verificación del operador en verde.

### Phase 0: mapa de reuso y hallazgos arquitectónicos (2026-08-24)

**Estado verificado del repo.**

- Rama local: `main`.
- HEAD local: `40abea2f3e19fb6f9b54c32b5bc1ac91ecb26113`.
- Working tree: sucio antes de Phase 0. Cambios existentes en
  `release_build_runner.py`, tests backend de build/idempotencia, release UI y
  este plan; artefactos no trackeados bajo `data/projects/sst-general/*` y
  `e2e_retrieval_report.md`. Phase 1 debe trabajar sobre ese estado sin revertirlo.
- El plan fuente actual ya marca Tasks 1-3 cerradas; el siguiente trabajo real es
  Task 4, pero dividido por el prompt en Phase 0/1 antes de recomponer pantallas.

**Matriz obligatoria de reuso Legacy -> Platform.**

| Legacy component | Responsabilidad actual | Acoplamiento API/controlador | Reuso directo | Extracción/generalización requerida | Destino Platform | Reemplaza | Riesgo Legacy |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `DashboardApp` | Shell legacy, topbar, refresh, summary, filtros y orquestación de ingesta/review/inventory | Alto: llama `dashboardApi`, preferencias legacy y acciones de ingesta | No | No reutilizar como controlador; extraer solo patrones de shell/notice/summary cuando ya sean props | Ninguno directo | No aplica | Alto si se toca |
| `DashboardChrome` / `DashboardNotice` / `DashboardSummary` | Notice, métricas y paneles de operación | Bajo/medio: mostly props, `LlamaStatusPanel`/`PipelinePanel` sí son legacy | Parcial | Reusar `DashboardNotice`/`MetricCard`; separar paneles legacy si se necesitan | Todas las vistas Platform | Notices/resúmenes ad-hoc | Bajo para notice/summary |
| `DashboardSidebar` | Navegación legacy SST Pipeline | Bajo: props `activeView/onViewChange`, labels legacy | No para Platform nav | Mantener legacy; Platform usa su sub-nav limitada | Ninguno | No aplica | Bajo |
| `InventoryWorkspace` / `InventoryPanel` | Inventario con búsqueda, filtros, tabla densa e inspector | Medio: tipo `DocumentRecord` legacy y status/ingesta legacy | No directo | Extraer contrato neutral `DocumentInventoryItem` + filtros + inspector prop-driven | Platform Documents | `RevisionTable` como UX central | Medio |
| `ReviewWorkspace` / `DocumentInspector` | Revisión manual e inspector auditable | Medio: `DocumentRecord`, decisiones legacy | Parcial | Generalizar inspector y chips; mantener acciones de review separadas por adapter | Documents / Corpus warnings | Inspectores duplicados | Medio |
| `ChunkingWorkspace` | Pantalla completa de chunking legacy con launch, run, documentos e inspector parent-child | Alto: `chunkingApi`, preferencias e idempotency legacy | No directo | Reusar lenguaje visual/paneles; no comandos Platform por etapa | Releases build visualization, no acciones separadas | Panel build actual insuficiente | Medio/alto |
| `EmbeddingIndexingWorkspace` | Orquestador de embedding, indexing, activation, retrieval legacy | Alto: `useEmbeddingIndexingPipeline` llama APIs legacy | No como controlador | Reusar `PipelineHeader`, `PipelineSummary`, panels prop-driven; Platform adapter propio | Releases unified build | `BuildReport` simple | Alto si se mezcla |
| `PipelineHeader` / `PipelineStepper` | Stepper por etapas y refresh | Bajo: props + stage status | Sí, con tipos ampliados | Generalizar stage labels/order para `normalize/chunking/embedding/indexing` | Releases | Nueva visualización build | Bajo |
| `PipelineSummary` | IDs resumen de pipeline legacy | Bajo: props pero nombres legacy | Parcial | Crear variante summary genérica o component con slots/labels | Releases / Variants | Resúmenes ad-hoc | Bajo |
| `pipelineState` / `pipelineFlow` | Derivación pura de limpieza de IDs y avance/polling terminal | Bajo: funciones puras; stages legacy específicos | Parcial | Añadir adapter Platform separado; no forzar stages legacy | Shared Platform adapter | Lógica duplicada futura | Bajo |
| `usePollingLoop` | Polling abortable, no solapado, pausa en tab oculta, terminal y timeout | Bajo: genérico, usa `mapPipelineError` | Sí | Ninguna para Phase 1; ya usado por releases | Releases build-status | Cualquier polling nuevo | Bajo |
| `EmbeddingCatalogPanel` | Catálogo de perfiles embedding | Bajo/medio: props con tipos legacy | Parcial | Adapter de perfiles Platform, ocultando targets físicos | Variants | Matriz CRUD dura | Bajo |
| `EmbeddingRunPanel` | Selección bundle + lanzamiento embedding legacy | Medio: props legacy y comandos legacy | Solo presentación parcial | Separar selector/progreso de comandos; no botones Platform por etapa | Releases/Variants | Build panel simple | Medio |
| `EmbeddingBundleInspector` | Inspector de bundle, chunks, validation/readiness | Medio: tipos embedding legacy | Parcial | Reusar layout solo si Platform expone read-model seguro; no raw chunks/vectores | Releases later | No reemplazo Phase 1 | Medio |
| `IndexingRunPanel` | Estado/run indexing y comandos legacy | Medio: props legacy, target resuelto textual | Parcial | Reusar estado visual; ocultar target físico en Platform | Releases | Build panel simple | Medio |
| `IndexingDocumentsTable` | Tabla de documentos indexados/elegibilidad/vectores | Bajo/medio: prop-driven con tipos legacy | Parcial | Adapter seguro si hay read-model; no exponer vectores raw | Releases later | No reemplazo Phase 1 | Medio |
| `IndexingErrorsPanel` | Errores por documento con `internal_error_id` | Bajo: prop-driven | Sí con adapter | Usar solo códigos/IDs opacos sanitizados | Releases activity/errors | Errores genéricos | Bajo |
| `ActivationPanel` | Activación legacy/retrieval profile | Alto semántico: activación legacy no es publicación Platform | No para Platform publish | Reusar solo patrón de readiness/bloqueos; no mezclar semántica | Releases validate/publish readiness | Lifecycle plano | Alto |
| Retrieval panels | Perfil/status/validación/búsqueda evidencia legacy | Alto: APIs retrieval globales | D en Task 4 | Diferir vista Retrieval dedicada; solo lenguaje visual si aplica | Ninguno ahora | No aplica | Alto |

**Matriz Platform actual.**

| Platform surface | Clasificación | Motivo |
| --- | --- | --- |
| `Projects` | KEEP | Es el punto estructural aceptable; carga proyectos/config y selecciona proyecto. |
| `PlatformWorkspace` | ADAPT | Debe poseer `ProjectContext` y envolver todas las vistas, no solo sub-nav local. |
| `platformApi` / `platformTypes` | KEEP | Es el contrato correcto; no llamar APIs legacy desde Platform. |
| `usePlatformPreferences` / `platformState` | ADAPT | La persistencia pura sirve, pero debe exponerse mediante contexto compartido. |
| `Documents` | REPLACE UX | Mantiene capacidades correctas (upload/normalize/fail-closed), pero la UX central debe pasar a inventario + inspector. |
| `RevisionTable`, `RawUploadPanel`, `NormalizationPanel` | DELETE AFTER MIGRATION / ADAPT | Conservar funciones válidas mientras migra; luego eliminar tablas/paneles duplicados. |
| `Variants` | REPLACE UX | Debe ser catálogo/receta, no matriz administrativa como experiencia principal. |
| `VariantMatrixTable` | DELETE AFTER MIGRATION | Puede quedar como adapter interno temporal, no como UX final. |
| `Corpus` | REPLACE UX | Selección e historial son correctos, pero deben recomponerse con inventario/selección legacy. |
| `SnapshotBuilder`, `SnapshotHistory` | ADAPT | Mantener reglas `needs_review`, mejorar con patrón inventory/inspector. |
| `Releases` | REPLACE/RECOMPOSE UX | La lógica async/build es correcta; la visualización debe ser pipeline unificado. |
| `BuildReport` / `ReleaseLifecycle` / `ReleaseHistory` | ADAPT | Mantener comandos Platform; sustituir presentación por pipeline + feed seguro cuando exista data. |
| `platform.css` | ADAPT | Usar tokens compartidos; retirar parches por pantalla al migrar. |

**Diseño seleccionado para contexto de proyecto (Phase 1).**

- `PlatformWorkspace` será dueño de un provider `PlatformProjectProvider`.
- El provider reusa la reconciliación pura actual (`platformState`) y la
  persistencia existente (`platformPersistence`), pero expone `projectId`,
  preferencias y setters mediante `usePlatformProjectContext`.
- `Projects` seguirá cargando el catálogo y, en Phase 1, podrá reconciliar contra
  IDs vivos mediante el contexto.
- `Documents`, `Variants`, `Corpus` y `Releases` leerán el mismo contexto en vez
  de instanciar `usePlatformPreferences(null)` cada uno.
- Legacy no importa este contexto. El contexto no guarda sesión, idempotency,
  payloads, documentos, secretos ni estado de requests.

**Build progress data-flow.**

1. `POST /api/platform/releases/{rag_release_id}/build` encola un
   `ReleaseBuildJob` durable y responde `build_job_id/state`.
2. `ReleaseBuildRunner` corre el build fuera del request y actualiza
   `queued -> running -> succeeded|failed`.
3. Persistencia durante el build: `release_build_jobs` guarda job id, release id,
   project id, estado, timestamps, conteos finales y error sanitizado.
4. `BuildRagReleaseUseCase` sí registra pasos `normalize/chunk/embed/index` en
   `rag_build_steps`, pero esos pasos se escriben dentro del loop de build, no se
   exponen en `GET /build-status` y no están ligados a `build_job_id`; agregarlos
   solo por release mezclaría reintentos.
5. Stages incrementales: existen en el ledger interno, pero el snapshot HTTP no
   trae `current_stage`, `completed_units`, `total_units`, `%`, `message` ni
   `recent_events`.
6. Conteos antes del estado terminal: no están disponibles en `ReleaseBuildJob`;
   solo se llenan al éxito. No se puede derivar un porcentaje real sin consultar/
   agregar una agregación segura.
7. Fuente de eventos segura: no existe read-model de eventos de producto; los logs
   del runner son server-side y no deben exponerse.
8. Cambio mínimo si se requiere porcentaje real: extender únicamente
   `GET /build-status`/`ReleaseBuildStatusSchema` con campos derivados y
   sanitizados desde `release_build_jobs` + `rag_build_steps`, asociando el run de
   ledger al `build_job_id` aceptado:
   `current_stage`, `completed_units`, `total_units`, `progress_percent`,
   `message`, `recent_events`. No crear endpoints por etapa ni exponer logs.
   Hasta entonces la UI debe usar progreso indeterminado.

**Riesgos.**

- El working tree ya trae cambios de cierre de Task 3; no revertir ni reescribir
  esos archivos sin revisar.
- `DashboardApp`, `ChunkingWorkspace` y `EmbeddingIndexingWorkspace` son
  controladores legacy; reutilizarlos directamente acoplaría Platform a APIs
  globales.
- `Activation` y `Publish` tienen semánticas distintas; solo se reusa lenguaje de
  readiness, no el comando.
- El build-status actual no permite porcentaje honesto; inventar porcentajes por
  estado queda prohibido.

### Phase 1: contexto compartido mínimo y regresiones Legacy (2026-08-24)

**Contrato cerrado.**

- `PlatformWorkspace` posee un `PlatformProjectProvider` único para las cinco
  vistas permitidas: `Projects`, `Documents`, `Variants`, `Corpus`, `Releases`.
- `PlatformProjectContext` reusa `usePlatformPreferences(null)` y expone solo
  estado de navegación: `projectId`, preferencias, setters y metadatos de
  proyectos conocidos. No guarda sesión, idempotency keys, payloads documentales,
  rutas físicas, chunks raw, vectores ni requests en curso.
- `Projects` conserva la responsabilidad de cargar el catálogo de proyectos y
  alimenta el contexto con `setKnownProjects`/`upsertProject`.
- `Documents`, `Variants`, `Corpus` y `Releases` leen el `projectId` compartido
  desde `usePlatformProjectContext`; ya no instancian preferencias de plataforma
  de forma independiente.
- La sub-nav de Platform muestra un chip accesible `Proyecto activo`. Si Projects
  ya cargó metadata, muestra `display_name`; si no, muestra el `project_id`
  persistido; si no hay selección, muestra estado vacío explícito.
- Legacy queda protegido con regresiones: `DashboardApp` mantiene navegables
  `Review`, `Inventario`, `Chunking` y `Embedding/Indexing`; `usePollingLoop`
  conserva no-solape de solicitudes mientras una consulta sigue pendiente.

**Archivos principales.**

- Nuevo: `app/front/src/features/platform/PlatformProjectContext.tsx`.
- Actualizados: `PlatformWorkspace.tsx`, hooks de
  `projects/documents/variants/corpus/releases`, tests de workspaces Platform y
  `platform.css`.
- Nuevas regresiones Legacy: `DashboardApp.test.tsx` y `usePollingLoop.test.tsx`.

**Verificación ejecutada.**

- Focalizada: `npm.cmd exec vitest run src/features/platform/PlatformWorkspace.test.tsx src/features/platform/projects/ProjectWorkspace.test.tsx src/features/platform/documents/DocumentIntakeWorkspace.test.tsx src/features/platform/variants/VariantMatrixWorkspace.test.tsx src/features/platform/corpus/CorpusSnapshotWorkspace.test.tsx src/features/platform/releases/RagReleaseWorkspace.test.tsx src/features/dashboard/DashboardApp.test.tsx src/features/embeddingIndexing/shared/usePollingLoop.test.tsx`
  = **8 files / 37 tests passed**.
- Regresión frontend: `npm.cmd --prefix app/front run test`
  = **componentes 16 files / 73 tests passed** más tests node/tsc verdes.
- Build: `npm.cmd --prefix app/front run build` = verde.
- `npm.cmd --prefix app/front run lint` no existe en `app/front/package.json`;
  queda como gap de tooling del repo, documentado sin inventar equivalente.

> **Phase 1 CERRADA (2026-08-24).** Queda listo el cimiento compartido de
> selección de proyecto para recomponer pantallas en Phase 2-5. No se abrió una
> vista Retrieval dedicada, no se agregó backend y no se inventó progreso de build.

**Orden propuesto Phase 1-6.**

1. Phase 1: CERRADA. Regresiones Legacy + `PlatformProjectContext` mínimo; sin
   cambios UX grandes.
2. Phase 2: Documents con inventario/inspector neutral y adapters Platform.
3. Phase 3: Variants como catálogo/receta con adapters de perfiles seguros.
4. Phase 4: Corpus con selección tipo inventory y `needs_review` explícito.
5. Phase 5: Releases como lifecycle + pipeline unificado; progreso indeterminado
   hasta ampliar `build-status` con datos reales.
6. Phase 6: eliminar presentación Platform duplicada, normalizar tokens/estados y
   pulir a11y/responsive.

### Phase 2: Documents — inventario neutral config-driven + adapter Platform (2026-08-24)

**Contrato cerrado (respuestas del operador).**

- Modelo neutral = **superset de capacidades de presentación** de Legacy, NO el
  schema pobre de Platform. Campos ricos **opcionales**:
  `id, displayName, documentType, status, normalizationStatus, reviewStatus,
  ingestionStatus?, confidence?, size?, source?, createdAt?, updatedAt?, metadata?`.
- Componente **único config-driven**: `columns`, `filters`, `rowActions`,
  `bulkActions`, `inspectorSections`, `decisionActions?` (capability-driven).
- Platform: `columns = [document, type, normalization, review, date]`,
  `decisionActions = undefined`. Legacy (Phase 6): superset con
  `ingestion/confidence/size` y sus decisiones actuales.
- Dependencia: `DocumentRecord → LegacyAdapter` y
  `ProjectDocumentRevision → PlatformAdapter` → **Neutral Inventory UI** (una sola).
  Legacy no importa tipos Platform; Platform no llama APIs Legacy.

**Hallazgos que fijan el diseño (verificados en código).**

- `ProjectDocumentRevisionSchema` expone solo: `source_document_revision_id`,
  `logical_document_id`, `source_relpath`, `file_size`, `raw_registered`,
  `normalized_registered`, `review_state`, `processing_status`, `uploaded_at`.
- Platform **no** expone category/ingestion/OCR/reasons/decision. No se inventan,
  no se llaman APIs Legacy, no se pone "unknown" como dato semántico: las columnas
  ausentes se ocultan por config (o `N/D` solo si UX lo exige).
- Platform **no** tiene endpoint de decisión → inspector Platform **read-only**
  para decisiones (`decisionActions = undefined`); nada de botones deshabilitados
  "coming soon". `needs_review` visible y fail-closed; selección masiva ya lo
  excluye. approve/reject Platform = **gap de contrato deferido** (tarea futura).

> **Corrección 2026-08-25:** esta conclusión queda superada por el plan
> `docs/superpowers/plans/2026-08-25-rag-platform-legacy-pipeline-parity.md`.
> RAG Platform es una plataforma operacional multiproyecto, no un visor
> read-only. Si falta persistencia para `Aprobar`/`Rechazar`, eso es un gap del
> contrato Platform que debe resolverse con el endpoint mínimo de decisión de
> revisión; no se debe convertir la pantalla de revisión/inventario en
> read-only. La etiqueta read-only solo aplica a bindings/targets físicos
> administrados por servidor o artefactos inmutables.
- Paneles/inspector/chips legacy (`DocumentWorkspaces.tsx`) son prop-driven; el
  neutral se **deriva** de ellos en archivos NUEVOS, sin editar Legacy todavía.

**Archivos.**

- Nuevo neutral (`components/ui/inventory/` o `features/documentsShared/`):
  view model `DocumentInventoryItem` (superset opcional), `InventoryToolbar.tsx`,
  `InventoryTable.tsx` (columnas por config), `DocumentInspector.tsx`
  (`inspectorSections` + `decisionActions?`), chips sobre `StatusBadge`.
- Nuevo Platform: `documents/documentInventoryAdapter.ts`
  (`ProjectDocumentRevision → DocumentInventoryItem` + config de columnas Platform).
- Modificar: `documents/DocumentIntakeWorkspace.tsx` recompuesto sobre el neutral,
  conservando upload/normalize/selección/needs_review/summary.
- Conservar: `RawUploadPanel.tsx`, `NormalizationPanel.tsx` (capacidad Platform).
- Borrar tras equivalencia probada + tests verdes: `documents/RevisionTable.tsx`.
- **No** tocar `DashboardApp`/`DocumentWorkspaces` (migran en Phase 6).

**Phase 2 DoD (operador).**

1. Extraer presentación neutral sin cambiar comportamiento Legacy.
2. Adapter Platform → neutral view model.
3. Migrar Platform Documents al nuevo inventario; upload/normalize intactos.
4. Eliminar `RevisionTable` solo con equivalencia funcional comprobada.
5. Tests Legacy verdes; sin modificar `DocumentWorkspaces` salvo extracción visual
   mínima indispensable (idealmente cero: se derivan archivos nuevos).

**Deferrals.** Columnas category/ingestion/OCR/reasons: N/A en Platform.
approve/reject Platform: fuera de scope (sin backend en Task 4).

> **Phase 2 CERRADA (2026-08-24).** Documents recompuesto sobre el inventario
> neutral config-driven (search + filtro por estado + tabla + inspector read-only),
> conservando upload/normalize/selección/needs_review. `RevisionTable` borrado.
> Adapter Platform honesto (campos ausentes = `undefined`, sin inventar). Legacy
> intacto. Verificación del operador VERDE: `npm --prefix app/front run test`
> (todo verde tras corregir 3 fallos: 1 aserción ambigua + columna que duplicaba
> ruta→ahora ruta+id) y `run build` OK; backend 284 passed / 1 skipped sin cambios.
> **Nota de tooling:** correr vitest desde la raíz del repo (`npx --prefix app/front
> vitest`) da falsos `window is not defined` (sin jsdom); el runner válido es
> `npm --prefix app/front run test` (`test:components`). Legacy migra en Phase 6.

### Phase 3: Variants — catálogo/receta (CERRADA 2026-08-25)

**Hallazgo (verificado en código).** La matriz Platform YA tiene UX de
catálogo/receta: `VariantMatrixTable.tsx` renderiza cada celda como tarjeta-receta
(`variant-cell`) con Processing/Chunking/Embedding (`CellDimensions`),
`target_binding_key` lógico, badge `Config v{n}` y estado construible/bloqueada con
`blocked_reason` en TEXTO (a11y). El "REPLACE UX" es MENOR que en Documents.

**Modelos.** `Variant` = `rag_variant_id`, `state`, `processing_profile_id`,
`chunking_profile_id`, `embedding_profile_id`. `VariantMatrixCell` = `cell_id`,
`buildable`, `blocked_reason`, `target_binding_key`, `configuration_version`, 3
profile ids. **Gap de campo (como Phase 2):** Platform NO expone provider/model/dim
de los perfiles (el legacy `EmbeddingCatalogPanel` sí, vía `EmbeddingProfile`). No
inventar: se muestran los profile_id tal cual, sin backend nuevo.

**Alcance Phase 3 (refinamiento, no reescritura):**
1. Lista "Variantes existentes" (`VariantMatrixWorkspace.tsx` → `ExistingVariants`):
   pasar del `<small>` apretado (`processing · chunking · embedding`) a
   tarjetas-receta reusando el layout `variant-cell-dims` (Processing/Chunking/
   Embedding en filas) + `state` vía `StatusBadge` compartido (tone success si
   "ready"/activa, neutral si no). Patrón visual tomado del legacy
   `EmbeddingCatalogPanel` (tarjeta perfil + chip de estado).
2. Estados no-felices de la matriz/lista → usar `StatePanel`/`StatusBadge`
   compartidos (hoy `.ui-empty` ad-hoc) para consistencia con Documents.
3. Invariantes intactos: crear variante SOLO con `cell_id + variant_slug` (D8);
   `STALE_VARIANT_MATRIX_CELL` fail-closed (refresca matriz + limpia selección);
   `target_binding_key` es lógico (mostrar OK); nunca target físico/actor.
4. Sin backend, sin exponer provider/model/dim (deferido, gap de contrato).

**Archivos implementados:** `VariantMatrixTable.tsx` (estados→`StatePanel`),
`VariantMatrixWorkspace.tsx` (`ExistingVariants`→tarjetas-receta con `VariantCard`
local + `StatusBadge`), `VariantMatrixWorkspace.test.tsx`.
**Deferrals:** provider/model/dim de perfiles (Platform no los expone).

> **Estado (2026-08-24): Phase 3 IMPLEMENTADA, pendiente runtime Playwright con
> servicios funcionales.** TDD focalizado agregado para variantes existentes como
> tarjetas-receta; `createVariant` conserva body exacto `{cell_id, variant_slug}`.
> Verificación automatizada ejecutada: `npm.cmd exec vitest run
> src/features/platform/variants/VariantMatrixWorkspace.test.tsx` = 5 passed;
> `npm.cmd --prefix app/front run test` = verde (`tsc`, tests node y 18 component
> files / 87 tests); `npm.cmd --prefix app/front run build` = verde. OpenAPI/types:
> no requerido (sin cambios backend/schema). Playwright final: frontend abre en
> `http://127.0.0.1:5174/`, pero runtime Platform queda bloqueado por
> `GET /api/auth/session` HTTP 500; repetir con backend/auth operativo antes de
> avanzar a Task 4. Legacy no fue modificado.

> **Cierre runtime (2026-08-25): Phase 3 VERIFICADA con frontend y backend
> operativos.** Se retomo el cierre pendiente con Playwright usando
> `prueba3` / `holamundo123`, proyecto `SST General` (`proj_sst-general`) y la
> vista `Variants`. El error visible `pipeline bridge failed: AttributeError`
> fue reproducido antes del fix: `GET
> /api/platform/projects/proj_sst-general/variant-matrix` devolvia `500` con
> envelope `PIPELINE_BRIDGE_ERROR`, mientras `GET
> /api/platform/projects/proj_sst-general/variants?page=1&page_size=100`
> devolvia `200`.
>
> **Raiz corregida.** Los adaptadores Postgres de perfiles no cumplian el puerto
> usado por `GetVariantMatrixUseCase`: `PostgresProcessingProfileRepository` y
> `PostgresChunkingProfileRepository` implementaban `get(...)`, pero no
> `list_for_project(...)`; la implementacion in-memory si lo tenia, por eso el
> hueco solo aparecia en runtime Postgres. Se agregaron `list_for_project(...)`
> y mapeadores `_row_to_profile(...)` compartidos en
> `app/back/src/rag_platform/infrastructure/postgres/project_repositories.py`.
>
> **Ajuste UI adicional.** La barra lateral de operador cortaba la tarjeta de
> sesion y el boton `Cerrar sesion` porque `.operator-shell` reservaba un rail
> demasiado angosto (`88px`, y `72px` en el breakpoint intermedio). Se ajusto
> `app/front/src/styles/operator.css` para reservar
> `minmax(176px, 12vw) minmax(0, 1fr)`, mantener el layout movil en
> `max-width: 760px` y permitir wrapping del usuario en
> `.operator-session-card strong`. Se agrego la regresion
> `app/front/src/features/operator/operatorLayoutCss.test.mjs` al script de
> test frontend.
>
> **TDD y verificacion.**
> - Red primero: `app/back/tests/rag_platform/test_postgres_project_repositories.py`
>   fallo con `AttributeError` para ambos repos Postgres; el test CSS fallo por
>   el rail insuficiente.
> - Green focalizado: `npm.cmd run python -- -m pytest
>   app/back/tests/rag_platform/test_postgres_project_repositories.py -q` =
>   2 passed; `node app/front/src/features/operator/operatorLayoutCss.test.mjs`
>   = ok.
> - Regresion backend afectada:
>   `npm.cmd run python -- -m pytest
>   app/back/tests/rag_platform/test_variant_matrix.py
>   app/back/tests/rag_platform/test_project_queries.py
>   app/back/tests/rag_platform/test_platform_api.py::test_variant_matrix_vacia_ok
>   app/back/tests/rag_platform/test_platform_api.py::test_list_processing_profiles_vacio_ok
>   app/back/tests/rag_platform/test_platform_api.py::test_list_chunking_profiles_vacio_ok -q`
>   = 16 passed.
> - Frontend completo: `npm.cmd --prefix app/front run test` = 87 tests passed
>   (se requirio reintento elevado por `spawn EPERM` de esbuild en Windows).
> - Build frontend: `npm.cmd --prefix app/front run build` = verde.
> - OpenAPI/types: no requerido; no hubo cambio de contrato HTTP ni schema.
>
> **Playwright final.** Tras reiniciar el backend en `127.0.0.1:8765` para cargar
> el codigo nuevo, la vista `Variants` dejo de mostrar `pipeline bridge failed`;
> `variant-matrix` y `variants` devolvieron `200 OK`. La medicion de layout a
> `1280x720` confirmo `cardOverflowsRail: false`,
> `logoutOverflowsRail: false` y `surfaceOverlapsRail: false`. El unico error de
> consola restante fue `401 Unauthorized` de `/api/auth/session` antes del login,
> esperado.
>
> **Ajuste visual posterior en Platform Documents (2026-08-25).** Se alineo el
> lenguaje de color de `review_state` en RAG Platform Documents con la ayuda
> visual que ya existia en Legacy Documents: `needs_review` y `pending` usan tono
> `warning`, `approved` y `processed` usan `success`, `rejected` usa `danger`, y
> estados no reconocidos quedan `neutral`. La etiqueta sigue siendo el valor crudo
> del contrato Platform para conservar auditoria; no se traduce ni se inventa
> metadata. El cambio quedo acotado al adapter neutral
> `app/front/src/features/platform/documents/documentInventoryAdapter.ts` y a su
> regresion `documentInventoryAdapter.test.tsx`.
>
> **Evidencia del ajuste visual.**
> - Red TDD confirmado: el test nuevo fallo porque `pending` se renderizaba con
>   `tone: "neutral"` en vez de `tone: "warning"`.
> - Green focalizado: `npm.cmd exec vitest run
>   src/features/platform/documents/documentInventoryAdapter.test.tsx` = 6 passed.
> - Regresion Documents: `npm.cmd exec vitest run
>   src/features/platform/documents/DocumentIntakeWorkspace.test.tsx
>   src/features/platform/documents/documentInventoryAdapter.test.tsx` =
>   15 passed.
> - Frontend completo: `npm.cmd --prefix app/front run test` = 87 tests passed.
> - Build frontend: `npm.cmd --prefix app/front run build` = verde.
> - Playwright no se repitio para este ajuste porque frontend/backend quedaron
>   detenidos por orden del operador; el cambio es de mapeo visual cubierto por
>   adapter + render de Documents + build. OpenAPI/types no requerido.
>
> **Cierre operativo.** No se hizo commit ni push. Se limpiaron artefactos
> temporales nuevos de Playwright sin tocar snapshots versionados. A pedido del
> operador, despues de la verificacion se detuvieron frontend y backend; se
> confirmo que no quedaron procesos `LISTENING` en `127.0.0.1:5173` ni en
> `127.0.0.1:8765`.

### Phase 4: Corpus — reuso del inventario neutral + polish visual (EN CURSO 2026-08-25)

**Hallazgo.** `SnapshotBuilder.tsx` es una tabla-selección bespoke (`CandidateRow`)
que DUPLICA el inventario-con-selección ya resuelto en Phase 2 (`DocumentInventory`).
La única pieza propia de Corpus es la **decisión de elegibilidad por fila
`needs_review`** (`approved_after_review` / `operator_waiver`). El hook
`useCorpusSnapshotWorkspace` es correcto y se conserva.

**Clasificación.** `useCorpusSnapshotWorkspace`=KEEP; `SnapshotBuilder`=REPLACE
(reusar `DocumentInventory`, borrar `CandidateRow`); `SnapshotHistory`=ADAPT
(`StatePanel`); `CorpusSnapshotWorkspace`=ADAPT (compone).

**Diseño.** Corpus compone `DocumentInventory` (Phase 2) alimentado por
`documentInventoryAdapter.toInventoryItems`, con columnas Corpus = doc columns +
**columna de elegibilidad** (factory que cierra sobre `decisions`,
`selectedRevisionIds`, `onSetDecision`; select solo en filas seleccionadas +
`needs_review`). Sin tocar el componente neutral (columns ya acepta render
arbitrario; NO se implementa el `rowActions` diferido). Botón "Crear snapshot" +
`disabledReason` (gate `pendingReviewIds`) fuera del inventario.

**Polish visual (pedido del operador: intuitivo, llamativo, dinámico, joven, con
ayudas de color).** Se ELEVA el lenguaje visual COMPARTIDO (no one-off) para que
todas las pantallas Platform se beneficien: pills de estado con color+texto (a11y),
barra contextual de selección con conteo (aparece al seleccionar, no botones
deshabilitados estáticos), micro-interacciones sutiles (hover/selección/chips),
jerarquía clara. Todo con tokens compartidos; sin romper Legacy; `prefers-reduced-
motion` respetado. Inspiración: patrones de data-table/bulk-select 2025-2026.

**Invariantes.** `needs_review` nunca auto-incluida; crear bloqueado hasta resolver
decisiones; body `createCorpusSnapshot` sin cambios; sin target físico/actor;
errores 403/409/422 fail-closed. Sin backend. Deferrals: field-gap
category/ingestion/OCR.

### Task 4: Reuso real de la lane legacy sin acoplarla a Platform

**Archivos:** `pipelineState.ts`, `pipelineFlow.ts`,
`platformPipelineState.ts`, `platformPipelinePanels.tsx`, workspaces Platform.

- [ ] Escribir regresión de legacy antes de tocar compartidos: embedding/indexing
  siguen renderizando y sus hooks siguen usando `usePollingLoop`.
- [ ] Extraer solo contratos neutrales: stages, badges, severidad, progreso,
  errores y paneles. No importar estado de Platform dentro de legacy.
- [ ] Implementar adapters Platform que consumen datos Platform y producen estado
  compartido. El adapter conserva `project_id`, `rag_release_id`, `job_id` y
  `version` para auditoría.
- [ ] Parametrizar el flujo reutilizado por `project_id`: no asumir corpus global
  único, no leer preferencias legacy de corpus, y no cruzar documentos/snapshots
  entre proyectos.
- [ ] Recomponer Documents, Corpus, Variants y Releases reemplazando bloques
  visuales duplicados por paneles compartidos. No tocar lógica que ya quedó verde
  salvo para conectar el adapter.
- [ ] Añadir o actualizar el E2E de Platform para probar el flujo con
  `rag_release_id`: seleccionar proyecto, usar su corpus/snapshot, crear variante,
  construir release y verificar que el estado/resultados pertenecen a esa release.
- [ ] Ejecutar:

```bash
npm --prefix app/front run test
npm --prefix app/front run build
```

### Task 5: Runbook, accesibilidad y cierre

**Archivos:** runbook, CSS Platform, tests UI.

- [ ] Documentar flujo operativo:
  `draft -> build queued/running -> succeeded -> validate -> publish`.
- [ ] Documentar recuperación: recargar página usa `GET build-status`; si el
  refresh controlado vence o falla, la UI muestra estado actual, permite refresh
  manual y no valida ni publica.
- [ ] Probar botones y estados con roles accesibles: busy deshabilita acciones,
  errores se anuncian, estados terminales quedan visibles.
- [ ] Ejecutar verificación mínima final:

```bash
npm run python -- -m pytest app/back/tests/ingestion/test_gui_server.py -q
npm run python -- -m pytest app/back/tests/rag_platform -q
npm --prefix app/front run test
npm --prefix app/front run build
```

## 9. Riesgos y mitigaciones

- **Sobrecarga por consulta periódica:** mitigado con refresh controlado, un
  request vivo como máximo (no-solape: cada consulta se espera antes de agendar la
  siguiente), solo para release visible en `queued`/`running`, pausa por
  visibilidad y timeout global. Intervalo **fijo** (2500 ms), sin backoff
  exponencial: el reuso de `usePollingLoop` legacy prioriza simplicidad y el
  no-solape ya acota la carga. Prohibido usar `setInterval` rígido para Platform
  build status.
- **SSE/WebSockets prematuros:** descartados por ahora. `AsgiBridge` bufferiza
  ASGI; forzar streaming real sería más riesgoso que status bajo demanda +
  refresh adaptativo.
- **Acoplar legacy a Platform:** mitigado con adapters Platform-owned. Legacy no
  importa tipos Platform; Platform consume contratos compartidos.
- **Cambio de contrato de build:** mitigado con `202 + ReleaseBuildJobSchema`,
  idempotencia explícita, runbook y tests HTTP.
- **Persistencia inconsistente:** mitigado con `version` monotónica, latest
  by-release, replay idempotente y error sanitizado.
- **Corpus grande:** `collectAllPages` sirve para hasta miles con cota; selección
  masiva debe distinguir "página visible" de "todos los elegibles cargados".

## 10. Definition of Done

- Platform gestiona el pipeline RAG completo por `project_id` reutilizando piezas
  legacy sin duplicar tablas/formularios ad-hoc innecesarios.
- El flujo probado en legacy para un corpus queda soportado en Platform para
  múltiples proyectos con corpus distintos, sin depender del corpus global legacy.
- Documents, Corpus, Variants y Releases cargan todas las páginas requeridas o
  muestran paginación explícita; no vuelven a quedarse en los primeros 25.
- La selección masiva respeta `needs_review`: nunca auto-incluye revisiones que
  requieren decisión explícita.
- `variant-matrix` y `releases/build` responden siempre con envelope o snapshot
  estructurado; nunca socket cortado como comportamiento esperado.
- Build no bloquea el request HTTP; estado y errores son observables, auditables
  y recuperables tras recarga.
- No hay consulta agresiva de Platform build status; solo status bajo demanda,
  refresh manual y auto-refresh adaptativo mientras la release visible esté
  `queued`/`running`.
- La lane legacy queda intacta y sus tests siguen verdes.
- Contratos de Fase 7 siguen cerrados: sin fuga de `actor_id`,
  `indexing_target_id`, rutas físicas, secretos, chunks raw ni vectores.
- El E2E de Platform pasa con una release identificada por `rag_release_id`,
  demostrando que build/validate/publish operan sobre el proyecto y corpus
  correctos.
- Runbook actualizado y verificación focalizada + build frontend ejecutados.

## 11. Verificación final requerida

```bash
npm run python -- -m pytest app/back/tests/rag_platform -q
npm run python -- -m pytest app/back/tests/ingestion/test_gui_server.py -q
npm --prefix app/front run lint
npm --prefix app/front run test
npm --prefix app/front run build
```

E2E manual en modo Postgres con `sst-general` (55 documentos): listar completo,
seleccionar elegibles, normalizar, snapshot, variante, build, validate y publish
sin caída de socket, sin consulta agresiva y sin fuga de datos sensibles.

## 12. Self-review del plan

- Cobertura de `continuation.md`: se incorporan job asíncrono, status durable,
  full-data loading, reuso legacy, runbook y verificación final.
- Corrección frente a la preocupación de sobrecarga: el plan reemplaza consulta
  agresiva por status bajo demanda y refresh adaptativo.
- Cobertura de este plan original: se preservan D-1, D-2, D-3, D-4, no-objetivos,
  fail-closed, trazabilidad y separación Legacy/Platform.
- No quedan marcadores de conflicto ni planes paralelos requeridos para ejecutar.

## 13. Instrucciones para el agente ejecutor

**Punto de partida (ya en el branch, NO rehacer):** desbloqueo D-1 (paginación
completa en las 4 listas project-aware), D-2 (selección masiva fail-closed en
intake y snapshot) y D-3a (bridge nunca cuelga el socket: excepción → `500`
`PIPELINE_BRIDGE_ERROR`). El agente **empieza en la Task 1** (build asíncrono
durable, D-3b) y sigue el orden 1 → 5.

**Ciclo de trabajo (obligatorio, de `docs/rules/TESTING_AND_QUALITY.md`):**
INVESTIGAR → DEFINIR contrato → ESCRIBIR prueba fallida → IMPLEMENTAR mínimo →
PRUEBAS focalizadas → REGRESIÓN → REVISAR (seguridad/trazabilidad/rendimiento) →
DOCUMENTAR. Una Task por vez; no abrir la siguiente hasta cerrar la anterior en
verde.

**Guardarraíles duros (no negociables):**
- Antes de tocar código, leer el `AGENTS_*.md` del área (`app/back/AGENTS_back.md`
  o `app/front/AGENTS_front.md`) y las reglas de `docs/rules/`.
- No reabrir invariantes de Fase 7: el frontend nunca envía `actor_id`,
  `indexing_target_id`, `target_bindings`, nombres de tabla ni rutas físicas;
  `target_binding_key` es lógica; la variante se crea solo con `cell_id +
  variant_slug`; auth por cookie same-origin; scope enforced server-side.
- Reusar, no duplicar: extraer/generalizar los componentes de la lane legacy
  (`features/{embedding,indexing,retrieval,chunking,embeddingIndexing,dashboard}`)
  con un contexto de proyecto opcional cuyo default preserve el comportamiento
  legacy. Regresión legacy verde ANTES de recomponer Platform (Task 4).
- Fail-closed visible: `401/403/409/422/503` son estados de producto, nunca se
  silencian ni se convierten en lista vacía; `needs_review` exige decisión
  explícita.
- No `commit`/`push` sin autorización explícita del operador.
- Tests de front `.test.tsx` (Vitest) y `.test.mjs` (tsc+node); backend `pytest`.
  El agente NO ejecuta la suite completa contra Postgres del operador: escribe y
  corre lo focalizado que pueda, y **entrega los comandos para que el operador los
  corra**, esperando su salida antes de cerrar.

**Diagnóstico primero de D-3b (Task 1):** reproducir el *socket hang up* real de
`variant-matrix` y `releases/build` con el traceback que ahora deja el envelope
`PIPELINE_BRIDGE_ERROR` en el log del backend; confirmar la causa (hipótesis:
excepción no manejada en el serializado de la matriz para datos reales; build
síncrono que bloquea el handler). Recién con la causa confirmada, implementar el
contrato de job asíncrono durable (Tasks 1-2). Si el cambio altera el contrato de
`releases/build`, registrar ADR en `docs/adr/`.

**Verificación de cierre (Task 5 + §11):** correr lo declarado en §11 y el E2E
manual en modo Postgres con `sst-general` (55 documentos). Sin caídas de socket,
sin polling agresivo, sin fuga de datos, lane legacy intacta y etiquetada.

---

> **Correction 2026-08-26 (superseded by the parity plan):** The previous Phase 8
> direction reused neutral Platform replacements and relabeled them as Legacy
> views. It also treated missing review-decision wiring as a reason to make
> Platform inspectors read-only. The corrected implementation
> (`docs/superpowers/plans/2026-08-25-rag-platform-legacy-pipeline-parity.md`,
> Tasks 3–7, cerradas 2026-08-26) mounts the actual Legacy pipeline UI through
> `DashboardPipelineApp` and a project-scoped Platform datasource. Platform is
> operational: `Aprobar`/`Rechazar` persist through the Platform review-decision
> contract (`POST …/document-revisions/{id}/review-decision`), snapshot creation
> moved to `RAG / Releases`, chunking/embedding-indexing run the real Legacy
> screens with project-aware stage clients (o estado no-disponible explícito), and
> read-only language now applies only to server-owned physical target bindings or
> immutable release artifacts.
