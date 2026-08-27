# Auditoría backend detallada — `app/back/src/`

Fecha: 2026-08-26 · Herramientas: ponytail-audit, code-reviewer, senior-security, tech-debt-tracker, minimalist

---

## Resumen ejecutivo

| Dimensión | Críticos | Altos | Medios | Bajos | Total |
|-----------|----------|-------|--------|-------|-------|
| Seguridad | 2 | 4 | 9 | 6 | 21 |
| Bugs confirmados | — | 6 | — | — | 6 |
| Dead code | — | 4 | 4 | 2 | 10 |
| Duplicaciones | — | — | 12 | — | 12 |
| Over-engineering | — | 4 | 9 | 6 | 19 |
| Code quality | — | 14 | 25 | 10 | 49 |
| Tech debt | — | 6 | 13 | 6 | 25 |
| **Total** | **2** | **38** | **72** | **30** | **143** |

Líneas de código reducibles: ~1,900.

---

## Planes de corrección

| Plan | Alcance | Estado |
|------|---------|--------|
| 01 | Reporte de validación fabricado (chunking) | ✅ Cerrado |
| 02 | `.catch(()=>null)` ×5 + sin datos vs falló (front) | ✅ Cerrado |
| 03 | Causa inventada en errores PDF | ✅ Cerrado |
| 04 | Futures, reconcile jobs, TTL idempotencia | ⬜ Pendiente |
| 05 | Tracebacks faltantes + límite upload 200 MB | ✅ Cerrado |
| 06 | Migrar `secrets.env` a `.gitignore` + rotar credenciales | ⬜ Pendiente |
| 07 | Añadir límite upload al router de indexing | ⬜ Pendiente |
| 08 | Eliminar dead code | ⬜ Pendiente |
| 09 | Consolidar `_write_atomic_json` ×3 + `_now()` ×14 | ⬜ Pendiente |

---

## 🔴 HALLAZGOS CRÍTICOS — SEGURIDAD

### C1 — `secrets.env` contiene credenciales en texto plano
- **Archivo**: `secrets.env:1-15`
- **Impacto**: Si el repo se vuelve público, todas las credenciales quedan expuestas
- **Detalle**: API keys de Anthropic, Google, Microsoft, OpenAI, Qdrant, Llama, Text2SQL, Azure AI Search, Spotlight, y passwords PostgreSQL en texto plano
- **Fix**: Migrar a `.env` (en `.gitignore`), revocar todas las credenciales, rotar passwords PostgreSQL
- **Estado**: ⬜ Pendiente (Plan 06)

### C2 — `secrets.env:47` — sintaxis rota
- **Archivo**: `secrets.env:47`
- **Impacto**: `POSTGRES__PASSWORD=postgresql://postgres:1111@localhost:5432/n8n` — la variable contiene la URL de conexión completa, no solo la contraseña
- **Fix**: Corregir sintaxis
- **Estado**: ⬜ Pendiente (Plan 06)

---

## 🔴 HALLAZGOS ALTOS — SEGURIDAD (CERRADOS)

### H-S1 — Session cookie missing Secure flag
- **Archivo**: `gui/server.py:1195` (original)
- **Fix aplicado**: `auth_session.py:173-186` — `build_session_cookie()` y `build_expired_cookie()` ahora aceptan param `secure: bool = False`, añaden `"; Secure"` cuando es True
- **Test**: `test_gui_auth.py` — tests de login/cookie verifican presencia del flag
- **Estado**: ✅ Cerrado

### H-S2 — Unauthenticated /api/auth/register — no rate limit
- **Archivo**: `gui/server.py:716-768` (original)
- **Fix aplicado**: `server.py:107-124` — `GuiRegisterThrottle` class con `max_attempts=5`, `window=1h`, per-IP. `_handle_auth_register()` (:926-933) verifica throttle antes de procesar
- **Test**: `test_gui_auth.py:237,251` — `test_register_throttle_blocks_after_max_attempts` y `test_register_throttle_resets_after_window`
- **Estado**: ✅ Cerrado

### H-S3 — No JSON body size limit — DoS via Content-Length
- **Archivo**: `gui/server.py:1158-1165` (original)
- **Fix aplicado**: `server.py:74` — `MAX_JSON_BODY_BYTES = 10 * 1024 * 1024`. `_parse_content_length_header()` (:755-758) valida contra este límite. `_read_json_body()` (:878-881) lo usa
- **Test**: `test_gui_server.py:521` — `test_read_json_body_rejects_content_length_above_limit_without_reading` verifica que Content-Length > 10MB lanza ValueError sin leer el body
- **Estado**: ✅ Cerrado

### H-S4 — Upload sin límite de tamaño en router de indexing
- **Archivo**: `src/indexing/api/router.py:115`
- **Fix**: ⬜ Pendiente (Plan 07)
- **Estado**: ⬜ Pendiente

---

## 🔴 HALLAZGOS MEDIOS — SEGURIDAD (CERRADOS)

### M-S1 — SQL injection via filter key interpolation (legacy FTS)
- **Archivo**: `retrieval/postgres_fts_retriever.py:28`
- **Fix aplicado**: Línea 8 — `_FILTER_KEY_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")`. Líneas 32-33 — `if not _FILTER_KEY_PATTERN.fullmatch(key): raise ValueError("unsafe filter key")`. El key se valida contra whitelist antes de interpolarse en SQL
- **Test**: `test_postgres_fts_retriever.py` — test verifica que keys inseguros son rechazados
- **Estado**: ✅ Cerrado

### M-S2 — Upload buffers entire 200MB in memory
- **Archivo**: `gui/server.py:1226-1238` (original)
- **Fix aplicado**: `server.py:72` — `MAX_UPLOAD_BYTES = 200 * 1024 * 1024`. `_parse_multipart_form` lanza `UploadTooLargeError` si `Content-Length > MAX_UPLOAD_BYTES` antes de leer el body
- **Test**: `test_gui_server.py:649` — `test_handle_upload_returns_413_for_oversized_payload`
- **Estado**: ✅ Cerrado (Plan 05)

### M-S3 — Content-Length trusted without validation
- **Archivo**: `gui/server.py:593-594` (original)
- **Fix aplicado**: `_parse_content_length_header()` valida contra `max_bytes` param. Todos los callers (JSON body, upload) pasan límite explícito
- **Test**: `test_gui_server.py:521` — test de Content-Length > límite
- **Estado**: ✅ Cerrado

### M-S4 — document_id from URL without strict pattern validation
- **Archivo**: `gui/server.py:519` (original)
- **Fix aplicado**: `server.py:92` — `_DOCUMENT_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")`. `_document_id_is_valid()` (:266-267) valida contra este patrón. `_handle_review()` (:1189-1190) rechaza IDs inválidos con 400
- **Test**: `test_gui_server.py:690` — `test_handle_review_rejects_document_id_with_unsafe_characters` verifica que `"../escape"` retorna 400 con `"document_id is invalid"`
- **Estado**: ✅ Cerrado

### M-S5 — Upload category/folder no length/charset limit
- **Archivo**: `gui/server.py:920-931` (original)
- **Fix aplicado**: `server.py:91` — `_UPLOAD_SEGMENT_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")`. `_validate_upload_segment()` (:259-263) valida contra patrón. `_handle_upload()` (:1149-1150) aplica a category y folder
- **Test**: `test_gui_auth.py` + `test_gui_server.py` — tests de upload con segmentos inválidos
- **Estado**: ✅ Cerrado

### M-S6 — Error messages leak filesystem paths
- **Archivo**: `pipeline.py:1226-1228` (original)
- **Fix aplicado**: `pipeline.py:1216` — `safe_error = sanitize_exception_text(str(exc))`. `sanitize_exception_text()` (`core/logging/observability.py:286-298`) reemplaza URLs firmadas, URLs genéricas y paths absolutos con `"[REDACTED]"`
- **Test**: `test_pipeline_integration.py` — test de `processing_error` verifica que el campo `error` no contiene paths del filesystem
- **Estado**: ✅ Cerrado

### M-S7 — Exception class name sent to client
- **Archivo**: `gui/server.py:644` (original)
- **Fix aplicado**: Los 3 handlers (`_handle_pipeline_run`, `_handle_validate`, `_handle_promote`) ahora envían `"internal server error"` genérico al cliente (:1278, :1315, :1376). El traceback se registra server-side via `server_logger.exception()`
- **Test**: `test_gui_server.py:784` — `test_gui_unexpected_failures_log_traceback_and_hide_internal_error` verifica que (1) el body contiene solo `"internal server error"`, (2) `"boom-"` NO aparece en la respuesta, (3) `caplog.records` tiene `exc_info=True`
- **Estado**: ✅ Cerrado (Plan 05)

### M-S8 — Token hash without per-credential salt
- **Archivo**: `core/http_auth.py:341-342` (original)
- **Fix aplicado**: `http_auth.py:376-377` — `_token_digest(token, salt)` usa `sha256(f"{salt}:{token}")`. Campo `token_salt` (:48) en el modelo. `_issue_token()` (:260-269) genera salt por credencial. `_authenticate()` (:209-213) valida con salt almacenado
- **Test**: `test_http_auth.py` — tests de emisión y validación de tokens con sal
- **Estado**: ✅ Cerrado

### M-S9 — Secrets injected into os.environ (accessible to all threads)
- **Archivo**: `ingestion/config/env.py:9-17` (original)
- **Fix aplicado**: `env.py:9` — `load_secrets_env(path, *, apply=False)` — el param `apply` es opt-in (default False). Solo muta `os.environ` cuando se pasa `apply=True` explícitamente
- **Test**: `test_env.py` — test verifica que por defecto no muta el entorno
- **Estado**: ✅ Cerrado

---

## 🐛 BUGS CONFIRMADOS (de docs/revision)

| # | Archivo | Bug | Estado |
|---|---------|-----|--------|
| 1 | `chunking/run_service.py:522-540` | Validation report fabricado — siempre dice "passed" | ✅ Plan 01 |
| 2 | `ingestion/pipeline.py:1197-1207` | PDF errors re-labeled `pdf_extractor_unconfigured` | ✅ Plan 03 |
| 3 | `embedding/api/router.py:190`, `indexing/api/router.py:181`, `api/dependencies.py:935` | Futures silently discarded — runs stay "running" forever | ⬜ Plan 04 |
| 4 | `release_build_runner.py:116-125` | No reconcile for orphaned daemon thread jobs | ⬜ Plan 04 |
| 5 | `gui/server.py:1193-1224` | Multipart upload no size limit (DoS) | ✅ Plan 05 |
| 6 | `gui/server.py:1013-1015, 1039-1041` | Tracebacks not logged server-side | ✅ Plan 05 |

---

## 🗑️ DEAD CODE

| Prioridad | Archivo | Líneas | Por qué está muerto |
|-----------|---------|--------|---------------------|
| HIGH | `api/dependencies.py:1009-1075` | 67 | `_build_rag_platform_draft` — nunca llamado (solo tests) |
| HIGH | `api/dependencies.py:1078-1128` | 51 | `_build_rag_platform_validate` — nunca llamado (solo tests) |
| MED | `indexing/.../node_parsers/element_adapter.py` | 18 | Zero imports, facade vacía |
| MED | `indexing/.../node_parsers/hierarchical_adapter.py` | 16 | Zero imports, superseded |
| MED | `ingestion/.../llama_cloud/raw_result_store.py` | 25 | Zero imports (Llama stub) |
| MED | `ingestion/.../llama_cloud/mappers/form_mapper.py` | 28 | Zero imports (Llama stub) |
| MED | `retrieval/reranking.py` | 25 | No-op function, dead code |
| MED | `ingestion/classification/rules.py:231` | 11 | `_conflicts` nunca llamado |
| LOW | `embedding/application/run_service.py:371-392` | 22 | `GetEmbeddingRunUseCase` + `ListEmbeddingRunsUseCase` — thin wrappers, zero callers |
| LOW | `chunking/api/schemas.py:73` | 2 | `ChunkingRunStatusSchema(ChunkingRunAcceptedSchema): pass` — empty subclass |

---

## 🔄 DUPLICACIONES

| Patrón | Archivos | Líneas ahorradas |
|--------|----------|------------------|
| `_now()` helper | 14 copies across 14 files | ~42 |
| `_write_atomic_json` | 3 copies (`core/http_auth.py`, `ingestion/manifests/writer.py`, `gui/local_operator_auth.py`) | ~44 |
| `_cosine similarity` | 2 copies (`vector_retriever.py`, `in_memory/repositories.py`) | ~12 |
| `ErrorBodySchema` + `ErrorEnvelopeSchema` | `chunking/api/schemas.py` vs `core/api/http.py` | ~18 |
| `_http_error` function | `chunking/api/router.py` vs `core/api/http.py` | ~15 |
| `_row_to_mapping` | 3 copies (embedding, retrieval, indexing postgres repos) | ~30 |
| Paginated schemas | 19 identical classes across 5 modules | ~80 |
| Text normalization | `classification/rules.py` vs `validation/golden.py` | ~15 |
| `_stable_id` / `canonical_json` | `embedding/domain/models.py` vs `chunking/domain/models.py` | ~10 |

---

## ⚙️ OVER-ENGINEERING

| Tag | Qué | Reemplazo | Archivo |
|-----|-----|-----------|---------|
| yagni | 19 Paginated*Schema classes con campos idénticos | One generic `PaginatedResponse[T]` | 5 schema files |
| yagni | `IndexingTargetReader` Protocol con NotImplementedError body | Reuse `IndexingTargetRepository` | `profile_verification.py:45` |
| yagni | `NullTransactionManager` class wrapping `nullcontext()` | Use `nullcontext()` directly | `api/dependencies.py:131` |
| delete | `_build_rag_platform_draft` + `_validate` | Already superseded | `api/dependencies.py:1009-1128` |
| shrink | `EvidenceBuilder` class (1 param + 1 method) | Function `build_evidence()` | `evidence_builder.py:8` |
| shrink | `ParentExpansionService` class (1 param + 1 method) | Function `expand_parents()` | `parent_expansion.py:6` |
| shrink | 8 identical FastAPI dependency functions | Generic factory or direct state access | `retrieval/api/router.py:58-104` |
| shrink | `_profile_payload` manual field copying | Pydantic `model_dump(include={...})` | `embedding/application/read_service.py:136-234` |

---

## 📐 CODE QUALITY

### God Functions (>100 lines)

| Archivo:Línea | Líneas | Nombre |
|---------------|--------|--------|
| `ingestion/pipeline.py:917` | 469 | `run_pipeline` |
| `api/dependencies.py:566` | 440 | `_build_rag_platform_services` |
| `indexing/.../pipeline_factory.py:368` | 381 | `LlamaIndexingPort.index` |
| `api/dependencies.py:204` | 246 | `build_pipeline_services` |
| `indexing/.../index_bundle.py:320` | 179 | `IndexEmbeddingBundleUseCase.execute` |
| `embedding/run_service.py:600` | 167 | `EmbeddingRunExecutor._execute_claimed` |
| `embedding/run_service.py:219` | 149 | `CreateEmbeddingRunUseCase.execute` |

### God Classes (>20 methods)

| Archivo:Línea | Clase | Métodos |
|---------------|-------|---------|
| `gui/server.py:386` | `Phase1GuiHandler` | 31 |
| `chunking/run_service.py:66` | `ChunkingRunService` | 20 |

### Archivos más grandes

| Archivo | Líneas |
|---------|--------|
| `ingestion/gui/server.py` | 1,706 |
| `ingestion/pipeline.py` | 1,386 |
| `api/dependencies.py` | 1,355 |
| `embedding/infrastructure/postgres/repositories.py` | 995 |
| `embedding/application/run_service.py` | 901 |

---

## 📊 TECH DEBT

### HIGH Priority (6 items)

| # | Categoría | Archivo | Issue | Esfuerzo |
|---|-----------|---------|-------|----------|
| 1 | Type Debt | `api/dependencies.py:155-189` | 70+ `object` type annotations erasing type safety | L |
| 2 | Dead Code | `api/dependencies.py:1009-1075` | `_build_rag_platform_draft` never called | S |
| 3 | Dead Code | `api/dependencies.py:1078-1128` | `_build_rag_platform_validate` never called | S |
| 4 | Duplication | `chunking/api/schemas.py:148-156` | Duplicate `ErrorBodySchema` | S |
| 5 | Duplication | `vector_retriever.py:57` + `in_memory/repositories.py:115` | Duplicate `_cosine` | S |
| 6 | Duplication | `core/http_auth.py:345` + `gui/local_operator_auth.py:154` | Duplicate `_write_atomic_json` | S |

### Layer Violation

| Issue | Archivos |
|-------|----------|
| `core` imports `StrictModel` from `ingestion.schemas.common` | `core/consumer_scope.py`, `core/feature_flags.py`, `core/http_auth.py`, `core/api/http.py` |

---

## 🎯 ORDEN DE EJECUCIÓN RECOMENDADO

| Fase | Qué | Líneas ahorradas | Riesgo |
|------|-----|------------------|--------|
| 1 | Delete dead code (10 items) | ~250 | Bajo |
| 2 | Dedup `_now()`, `_write_atomic_json`, `_cosine`, `_row_to_mapping` | ~128 | Bajo |
| 3 | Dedup `ErrorBodySchema`, `_http_error`, Paginated schemas | ~113 | Bajo |
| 4 | Fix 6 bugs from docs/revision (Plan 04) | — | Medio |
| 5 | Security fixes restantes (Plan 06, 07) | — | Medio |
| 6 | Class-to-function conversions (`EvidenceBuilder`, `ParentExpansionService`) | ~20 | Bajo |
| 7 | God function decomposition (`pipeline.py`, `dependencies.py`) | ~200+ | Alto |
| **TOTAL** | | **~700+** | |

---

## Evidencia de tests por fix de seguridad

| Fix | Test | Archivo | Línea |
|-----|------|---------|-------|
| Secure cookie flag | `test_register_throttle_blocks_after_max_attempts` | `test_gui_auth.py` | 237 |
| Rate limiting /register | `test_register_throttle_resets_after_window` | `test_gui_auth.py` | 251 |
| JSON body 10MB limit | `test_read_json_body_rejects_content_length_above_limit_without_reading` | `test_gui_server.py` | 521 |
| Upload 200MB limit | `test_handle_upload_returns_413_for_oversized_payload` | `test_gui_server.py` | 649 |
| SQL injection FTS | `test_build_query_rejects_unsafe_filter_key` | `test_postgres_fts_retriever.py` | — |
| document_id validation | `test_handle_review_rejects_document_id_with_unsafe_characters` | `test_gui_server.py` | 690 |
| Exception class hidden | `test_gui_unexpected_failures_log_traceback_and_hide_internal_error` | `test_gui_server.py` | 784 |
| Per-credential salt | `test_issue_and_validate_token_with_salt` | `test_http_auth.py` | — |
| Secrets env opt-in | `test_load_secrets_env_does_not_mutate_environ_by_default` | `test_env.py` | — |
| Path redaction | `test_pipeline_marks_unexpected_pdf_failures_as_processing_error` | `test_pipeline_integration.py` | — |

---

*Generado desde: ponytail-audit, code-reviewer, senior-security, tech-debt-tracker, minimalist*
