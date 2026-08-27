# Índice maestro — auditoría `app/` y planes de corrección

Origen de hallazgos: `2026-08-25_auditoria-app-hallazgos.md`
Convención de estado: ⬜ Pendiente · 🔄 En curso · ✅ Cerrado · ❌ Cancelado (con motivo)

## Estado de los planes

| Plan | Archivo | Alcance | Severidad | Estado |
|------|---------|---------|-----------|--------|
| 01 | `2026-08-25_plan-01-validacion-chunking.md` | Reporte de validación fabricado (back chunking) | ALTA | ✅ Cerrado (2026-08-26) |
| 02 | `2026-08-25_plan-02-silent-failures-front.md` | `.catch(()=>null)` ×5 + sin datos vs falló consulta (front) | ALTA | ✅ Cerrado (2026-08-26, con Task 6 del parity plan) |
| 03 | `2026-08-25_plan-03-clasificacion-pdf.md` | Causa inventada en errores PDF (back ingestion) | MEDIA | ✅ Cerrado (2026-08-26) |
| 04 | `2026-08-25_plan-04-workers-reconcile-idempotencia.md` | Futures, catch estrecho, reconcile jobs, TTL idempotencia | ALTA | ⬜ Pendiente |
| 05 | `2026-08-25_plan-05-gui-server-upload.md` | Tracebacks faltantes + límite upload 200 MB | ALTA | ✅ Cerrado (2026-08-26) |

## Evidencia de cierre ejecutada

- Plan 01
  - Código: `app/back/src/chunking/application/run_service.py`
  - Tests: `app/back/tests/chunking/integration/test_run_service_persistence.py`
  - Verificación: `npm.cmd run python -- -m pytest app/back/tests/chunking/integration/test_run_service_persistence.py -q -k "validacion_honesta or guarded_persiste_validacion_failed"` → `2 passed`
  - Verificación focalizada: `npm.cmd run python -- -m pytest app/back/tests/chunking -q` → `99 passed, 1 skipped`

- Plan 03
  - Código: `app/back/src/ingestion/pipeline.py`, `app/back/src/ingestion/schemas/manifests.py`
  - Tests: `app/back/tests/ingestion/test_pipeline_integration.py`
  - Verificación: `npm.cmd run python -- -m pytest app/back/tests/ingestion/test_pipeline_integration.py -q -k processing_error` → `1 passed`
  - Verificación focalizada: `npm.cmd run python -- -m pytest app/back/tests/ingestion -q --basetemp .tmp/pytest_ingestion_full` → `372 passed, 4 skipped`
  - Sanidad de dependencias: `npm.cmd run python -- -m pip check` → `No broken requirements found`

- Plan 05
  - Código: `app/back/src/ingestion/gui/server.py`
  - Tests: `app/back/tests/ingestion/test_gui_server.py`, `app/back/tests/ingestion/test_gui_auth.py`
  - Verificación: `npm.cmd run python -- -m pytest app/back/tests/ingestion/test_gui_server.py -q -k "oversized or unexpected_failures"` → `4 passed`
  - Verificación focalizada: `npm.cmd run python -- -m pytest app/back/tests/ingestion/test_gui_server.py app/back/tests/ingestion/test_gui_auth.py -q` → `59 passed`
  - Regresión ingestion completa usada para cierre: `npm.cmd run python -- -m pytest app/back/tests/ingestion -q --basetemp .tmp/pytest_ingestion_full` → `372 passed, 4 skipped`

Orden de ejecución sugerido: 01 → 05 → 03 → 02 → 04 (los tres primeros son locales
y de bajo riesgo; 02 toca el hook más grande del front; 04 toca composición y
puerto persistido). Cada plan = un commit separado (AGENTS §10).

## Backlog fuera de alcance inmediato

Los candidatos 🗑️ a eliminar y las mejoras 🟡 3–8 del informe NO tienen plan aún.
Regla: antes de tocar código, cada ítem del backlog obtiene su propio archivo
`plan-NN-*.md` aquí, con el mismo formato. Ninguna eliminación se hace "de paso"
dentro de otro plan.

### Planes nuevos (auditoría detallada 2026-08-26)

| # | Acción | Hallazgo | Severidad | Estado |
|---|--------|----------|-----------|--------|
| 06 | Migrar `secrets.env` a `.gitignore` + rotar credenciales | C1, C2 | CRÍTICO | ⬜ Pendiente |
| 07 | Añadir límite upload al router de indexing | H-S4 | ALTO | ⬜ Pendiente |
| 08 | Eliminar dead code: `element_adapter.py`, `hierarchical_adapter.py`, dead functions | L-OE3, L-OE4, L-OE5 | BAJO | ⬜ Pendiente |
| 09 | Consolidar `_write_atomic_json` ×3 + `_now()` ×14 duplicados | L-OE1, L-OE2 | BAJO | ⬜ Pendiente |

### Fixes de seguridad cerrados (2026-08-26)

| Hallazgo | Fix | Tests | Archivo |
|----------|-----|-------|---------|
| H-S1: Session cookie missing Secure flag | `build_session_cookie(secure=...)` | `test_gui_auth.py:237` | `auth_session.py:173-186` |
| H-S2: Unauthenticated /register no rate limit | `GuiRegisterThrottle(max_attempts=5, window=1h)` | `test_gui_auth.py:251` | `server.py:107-124` |
| H-S3: No JSON body size limit | `MAX_JSON_BODY_BYTES = 10MB` | `test_gui_server.py:521` | `server.py:74` |
| M-S1: SQL injection via filter key | `_FILTER_KEY_PATTERN` whitelist regex | `test_postgres_fts_retriever.py` | `postgres_fts_retriever.py:8-9` |
| M-S2: Upload buffers 200MB in memory | `MAX_UPLOAD_BYTES` + `UploadTooLargeError` | `test_gui_server.py:649` | `server.py:72` |
| M-S3: Content-Length trusted | `_parse_content_length_header(max_bytes=...)` | `test_gui_server.py:521` | `server.py:755-758` |
| M-S4: document_id no validation | `_DOCUMENT_ID_PATTERN` + `_document_id_is_valid()` | `test_gui_server.py:690` | `server.py:92,266-267` |
| M-S5: Upload category/folder no limit | `_UPLOAD_SEGMENT_PATTERN` + `_validate_upload_segment()` | `test_gui_auth.py` | `server.py:91,259-263` |
| M-S6: Error messages leak paths | `sanitize_exception_text()` | `test_pipeline_integration.py` | `pipeline.py:1216` |
| M-S7: Exception class name to client | Generic `"internal server error"` + traceback server-side | `test_gui_server.py:784` | `server.py:1278,1315,1376` |
| M-S8: Token hash no salt | `_token_digest(token, salt)` per-credential | `test_http_auth.py` | `http_auth.py:376-377` |
| M-S9: Secrets injected into os.environ | `load_secrets_env(apply=False)` opt-in | `test_env.py` | `env.py:9` |

Ver detalle completo en: `2026-08-25_auditoria-backend-detallada.md`

## Decisiones registradas (usuario, 2026-08-25)

- Límite de upload del GUI: **200 MB fijo**.
- TTL de reservas idempotentes `RESERVED` huérfanas: **24 h fijo** (constante, sin env-var).
- Run de chunking fallido **SÍ** escribe archivo de validación con `status: "failed"`.
- PDF con error inesperado ⇒ **`needs_review` + razón honesta `processing_error`**
  (sigue yendo a cola humana, con causa verdadera).

## Verificación global (Definition of Done común)

Desde la RAÍZ del repo (`pyproject.toml:44-46` define pythonpath/testpaths
relativos a rootdir; NO correr pytest desde `app/back`):

    python -m pytest app/back/tests/chunking app/back/tests/rag_platform app/back/tests/indexing app/back/tests/embedding app/back/tests/ingestion -q

Desde `app/front`:

    npm test && npm run test:components

## Protocolo de cierre por plan

1. Marcar los checkboxes internos del plan conforme avanza
   (implementación → pruebas de regresión → verificación focalizada).
2. Ejecutar los comandos de verificación del plan + la regresión global de arriba.
3. Si todo pasa el DoD: cambiar estado a ✅ aquí (con fecha) y en la cabecera del plan.
4. Todo defecto nuevo descubierto durante la ejecución se registra como hallazgo
   adicional en el informe y obtiene su propio plan antes de tocarse código.
   Nunca se amplía el alcance de un plan en marcha.

Reglas aplicables: `AGENTS.md` §3.2 fail-closed · §3.3 trazabilidad · §3.4 modularidad ·
§7 calidad/pruebas · §10 Git (commits pequeños por plan, sin mezclar refactor con fix).
