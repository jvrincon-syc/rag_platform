# Informe de auditoría — `app/` (back + front)

Fecha: 2026-08-25 · Método: exploración exhaustiva por subagentes (back y front por
separado) + verificación directa de cada hallazgo crítico leyendo el código real.
Rutas relativas a `app/`. Este documento es el registro de hallazgos; las acciones
viven en los planes 01–05 enlazados desde `2026-08-25_indice-y-cierre.md`.

## 🔴 Bugs silenciosos graves

| # | Ubicación | Problema |
|---|-----------|----------|
| 1 | `back/src/chunking/application/run_service.py:522-540` | Reporte de validación fabricado: `_persist_validation` escribe `"status": "passed"`, `"errors": 0`, `"checks": []` incondicionalmente, aunque el run haya fallado o termine con advertencias. El endpoint `GET /api/chunking/runs/{id}/validation` sirve datos inventados → viola la regla fail-closed del repo (AGENTS §3.2) y la trazabilidad (§3.3). |
| 2 | `front/src/features/embeddingIndexing/useEmbeddingIndexingPipeline.ts:252,471,472,730,731` | Cinco `.catch(() => null)`: un fallo HTTP deja validación/readiness como "sin datos" y el panel de errores de indexing puede mostrar "Sin errores registrados" en verde cuando la carga falló (`IndexingErrorsPanel.tsx:36-41`). Viola AGENTS §9 (no ocultar errores para mejorar apariencia). |
| 3 | `back/src/ingestion/pipeline.py:1197-1207` | Cualquier excepción en un PDF se re-etiqueta como `needs_review` con causa inventada `pdf_extractor_unconfigured`; el diagnóstico real se pierde para auditoría. |
| 4 | Futures descartados: `embedding/api/router.py:190`, `indexing/api/router.py:181`, `api/dependencies.py:919` + catch estrecho `(OSError, ValueError, RuntimeError)` en `index_bundle.py:683` | Excepciones de workers async desaparecen sin log; runs quedan "running" para siempre. No hay reconcile de `ReleaseBuildJob` (crash = job colgado para siempre; hilo daemon en `release_build_runner.py:116-124`) ni expiración de reservas `RESERVED` huérfanas (`idempotency.py:222-227`, "ponytail" declarado en código). |
| 5 | `back/src/ingestion/gui/server.py:1013-1015,1039-1041,1089-1091` y `:1193-1224` | Handlers que devuelven `str(exc)` al cliente sin loggear traceback server-side, y upload multipart sin límite de tamaño (DoS trivial contra el puerto local). |

## ✅ Cierres ejecutados (2026-08-26)

### Hallazgo #1 — Cerrado por Plan 01
- Código: `app/back/src/chunking/application/run_service.py`
  - `_execute_run_guarded` ahora persiste validación también en la ruta de fallo.
  - `_persist_validation` dejó de inventar `"passed"` y deriva `status/errors/checks` del `ChunkingRunState` real.
- Pruebas: `app/back/tests/chunking/integration/test_run_service_persistence.py`
  - `test_execute_run_persiste_validacion_honesta_para_corrida_exitosa`
  - `test_execute_run_guarded_persiste_validacion_failed_cuando_explota_el_chunking`
- Verificación ejecutada:
  - `npm.cmd run python -- -m pytest app/back/tests/chunking/integration/test_run_service_persistence.py -q -k "validacion_honesta or guarded_persiste_validacion_failed"` → `2 passed`
  - `npm.cmd run python -- -m pytest app/back/tests/chunking -q` → `99 passed, 1 skipped`

### Hallazgo #3 — Cerrado por Plan 03
- Código:
  - `app/back/src/ingestion/pipeline.py`
    - helper `_is_missing_pdf_extractor_error(...)`
    - catch-all PDF honesto: `processing_error` para fallos inesperados
    - recomendación operativa actualizada para `processing_error`
  - `app/back/src/ingestion/schemas/manifests.py`
    - `ReviewItem.error` preserva el error real en `needs_review.json`
- Pruebas:
  - `app/back/tests/ingestion/test_pipeline_integration.py`
    - `test_pipeline_marks_unexpected_pdf_failures_as_processing_error`
  - suite ajustada para aceptar contrato honesto cuando el fixture dispara PDF corrupto real
- Verificación ejecutada:
  - `npm.cmd run python -- -m pytest app/back/tests/ingestion/test_pipeline_integration.py -q -k processing_error` → `1 passed`
  - `npm.cmd run python -- -m pytest app/back/tests/ingestion -q --basetemp .tmp/pytest_ingestion_full` → `372 passed, 4 skipped`
  - `npm.cmd run python -- -m pip check` → `No broken requirements found`

### Hallazgo #5 — Cerrado por Plan 05
- Código:
  - `app/back/src/ingestion/gui/server.py`
    - `MAX_UPLOAD_BYTES = 200 * 1024 * 1024`
    - `UploadTooLargeError`
    - `_parse_multipart_form` rechaza `Content-Length` > 200 MB antes de leer el body
    - `_handle_pipeline_run`, `_handle_validate`, `_handle_promote` registran traceback server-side y devuelven 500 genérico
- Pruebas: `app/back/tests/ingestion/test_gui_server.py`
  - regresiones para upload 413
  - regresiones para traceback logging + 500 genérico
- Verificación ejecutada:
  - `npm.cmd run python -- -m pytest app/back/tests/ingestion/test_gui_server.py -q -k "oversized or unexpected_failures"` → `4 passed`
  - `npm.cmd run python -- -m pytest app/back/tests/ingestion/test_gui_server.py app/back/tests/ingestion/test_gui_auth.py -q` → `59 passed`
  - `npm.cmd run python -- -m pytest app/back/tests/ingestion -q --basetemp .tmp/pytest_ingestion_full` → `372 passed, 4 skipped`

## 🗑️ Candidatos a eliminar (backlog, requieren mini-plan propio)

**Back (cero referencias verificadas):**
1. `indexing/infrastructure/llama_index/node_parsers/hierarchical_adapter.py` y `element_adapter.py` — archivos completos muertos.
2. `leaves()` en `pipeline_factory.py:836-837`.
3. Cluster legacy de retrieval autodeclarado "remove once legacy retired": `vector_retriever.py`, `postgres_fts_retriever.py`, `reranking.py`, `evidence_builder.py`, `parent_expansion.py`, `fusion.py` (+ sus tests). Nota: `postgres_fts_retriever.py:28` interpola key de filtro en SQL — muerto hoy, riesgo si se reusa.
4. `_build_rag_platform_draft/_validate` (`api/dependencies.py:992-1111`) + campos alias write-only (`:177-181`) — solo tests los leen.
5. `src/evaluation/` completo — sin consumidor productivo (mover a tests/scripts si se conserva).
6. Test-doubles viviendo en `src/`: `InMemoryChunkBundleReuseRepository`, `InMemorySealedEmbeddingBundleRepository`, `InMemoryIndexingMaterializationRepository` (`in_memory/repositories.py:487-796`) y `MockOcrEngine`.

**Front (residuos del refactor de variants):**
7. `getVariantMatrix` (`platformApi.ts:116`) + tipo `VariantMatrixCell` (`platformTypes.ts:26`) — huérfanos confirmados por grep.
8. `platform.css:74-202` — ~130 líneas del bloque "Matriz de variantes" muertas; también `.platform-bulk-actions` (`:297-314`), `.document-select-actions` (`:477-483`), `.operator-empty*` (`operator.css:224-260,306`).
9. `tsconfig.test.json:49` — referencia al hook eliminado `useVariantMatrixWorkspace.ts`.
10. `setSelectedRagVariant` (`usePlatformPreferences.ts:49-55`) — escritura muerta; y maquinaria de scope en `platformState.ts:26-76` que siempre recibe `null`.
11. Copia de `NormalizationPanel.tsx:125` ("Crea una variante en la matriz…") apunta a pantalla eliminada → dead-end UX: hoy no hay forma de crear variantes desde la GUI.

## 🟡 A mejorar (priorizado, backlog)

1. Emitir validación real en chunking o marcar needs_review (#1 arriba → Plan 01).
2. Distinguir "sin datos" de "falló la consulta" en el front; renderizar el error (#2 → Plan 02).
3. Reconcile de arranque para ReleaseBuildJob (#4 → Plan 04) + **backoff en retries de embedding** (`pipeline_factory.py:521-560`, reintenta sin espera ante rate-limit).
4. Monolitos a partir: `api/dependencies.py` (1338 líneas, god composition root), `gui/server.py` (~1670), `pipeline.py` (1377), `postgres/repositories.py` (~995), hooks `useEmbeddingIndexingPipeline.ts` (944) y `useChunkingWorkspace.ts` (513, además sin AbortController en cadenas run→parents→children).
5. Violaciones application→infrastructure (AGENTS §3.6): `bundle_first/ports.py:21` (un puerto importa `AppendOnlyVectorRecord` de Postgres), `engine_registry.py:41-47`, `structural_parser.py:9`, `child_chunk_builder.py:17`, `parent_chunk_builder.py:9`, `run_service.py:14-17` (chunking), `run_service.py:41` + `bundle_builder.py:37-40` (embedding), `activation.py:23`, `llama_orchestrator.py:20`; además `llama_index.core` importado en capa aplicación (`indexing/application/repositories.py:6`).
6. Duplicación: `ErrorBodySchema` ×2 (`chunking/api/schemas.py:148` vs `core/api/http.py:27`), paginación ×3 (`core/api/http.py:67` + dos locales en `chunking/run_service.py`), set de document types duplicado (`adapters.py:34-50` vs `pipeline.py:286-302`), stores sellados copy-paste (`sealed_chunk_store` vs `sealed_embedding_store`), `messageFromError` ×4 en hooks Platform, `chunkingApi`/`dashboardApi` ignoran `shared/api/apiClient`, `DashboardNotice` importado cross-feature, `formatBytes/formatDateTime` duplicados.
7. Keys con índice en filas eliminables (`ProjectConfigurationForm.tsx:155,232`) + pseudo-TODOs camuflados como docstrings/string literals (`api/dependencies.py:670,694`, `retrieval/reranking.py:22-25`, `in_memory/repositories.py:57-58`) — invisibles para tooling de TODOs, sin issue registrada.
8. Upload GUI sin límite y handlers sin traceback (#5 → Plan 05).

## ✅ Puntos positivos verificados

- Cero `except:` pelados en todo `app/back`.
- Cero `pytest.mark.skip` incondicionales, cero `MagicMock` (los doubles son fakes explícitos).
- Cero `console.log` productivos, cero `any`/`as any` en producción front.
- Sin imports circulares activos (grafo embedding↔indexing denso pero acíclico).
- Stores sellados (`sealed_*_store`), runner de builds y `http_auth` con fail-closed ejemplar.
- Polling de front correctamente centralizado en `usePollingLoop` (no duplicado).
