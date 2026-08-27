# Plan 05 — GUI server: tracebacks server-side + límite de upload

Estado: ✅ Cerrado (2026-08-26) · Severidad: ALTA · Hallazgo origen: #5 del informe

## Checklist de cierre
- [x] Traceback en los 3 handlers que devuelven 500
- [x] Límite 200 MB con respuesta 413
- [x] Test de regresión en verde
- [x] Estado ✅ en `2026-08-25_indice-y-cierre.md`

## Hallazgo (verificado en código)
`app/back/src/ingestion/gui/server.py`:
- `:1013-1015` `_handle_pipeline_run`, `:1039-1041` `_handle_validate`,
  `:1089-1091` `_handle_promote` — `except Exception` ⇒ 500 con `str(exc)` al
  cliente SIN `logger.exception` server-side: la causa real no queda en logs y el
  diagnóstico depende del texto filtrado al cliente.
- `:1193-1224` `_parse_multipart_form` lee `Content-Length` completo a memoria sin
  tope ⇒ DoS trivial contra el puerto local (un solo request gigante).

## Decisiones registradas (2026-08-25)
Límite fijo **200 MB**. Respuesta HTTP **413** al excederlo.

## Contraste con código (2ª pasada, 2026-08-25)
- `_parse_multipart_form` tiene UNA única llamada: `_handle_upload` (:894). El
  límite es local y no afecta otras rutas.
- `_handle_upload` ya captura `ValueError` ⇒ 400 (:916-920) para rutas inválidas:
  la excepción nueva debe ser subclase (`UploadTooLargeError(ValueError)`) y
  capturarse ANTES para mapear a 413 sin tocar ese camino existente.
- `PromotionError` (:1086-1088) permanece 409 SIN traceback: es resultado controlado
  de negocio, no bug. Solo las ramas `except Exception` ganan log con traceback.
- Patrón de logging del módulo ya existe: `server_logger` con extras
  `request_id/stage/event` (p. ej. :965-977); los handlers tienen
  `getattr(self, "_request_id", None)` disponible.

## Cambios propuestos
| Archivo | Cambio |
|---|---|
| `ingestion/gui/server.py` | En los 3 handlers: antes de `_send_error(HTTPStatus.INTERNAL_SERVER_ERROR, ...)`, añadir `server_logger.exception(...)` con extras consistentes (`request_id`, `stage`: "pipeline"/"validation"/"promotion", `event`: p. ej. `"pipeline_run_failed"`). El mensaje al cliente sigue siendo genérico (sin detalle interno sensible). |
| idem | Constante `MAX_UPLOAD_BYTES = 200 * 1024 * 1024` junto a `ALLOWED_UPLOAD_SUFFIXES` (:71) + `class UploadTooLargeError(ValueError)` con mensaje claro ("upload excede el límite de 200 MB"). `_parse_multipart_form` la lanza si `length > MAX_UPLOAD_BYTES` ANTES de leer el body. `_handle_upload` la captura primero ⇒ `_send_error(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, ...)`; el `ValueError` genérico de rutas (:916-920) queda intacto ⇒ 400. |
| `tests/ingestion/test_gui_server.py` | (a) multipart con Content-Length > límite ⇒ respuesta 413 y body no consumido. (b) handler de pipeline con excepción simulada ⇒ 500 y registro vía `caplog` con traceback presente. Seguir los fixtures existentes del archivo (server en hilo + requests reales, como en :603+). |

## No hacer
- No reescribir el parser a streaming/chunked (fuera de alcance; backlog si hace falta).
- No límites por campo ni por número de partes.
- No cambiar contratos JSON de las respuestas existentes.

## Verificación

    python -m pytest app/back/tests/ingestion/test_gui_server.py app/back/tests/ingestion/test_gui_auth.py -q    # desde la RAÍZ del repo
    # (pyproject.toml:44-46 define pythonpath/testpaths relativos a rootdir)

Ejecución 2026-08-26:
- `npm.cmd run python -- -m pytest app/back/tests/ingestion/test_gui_server.py -q -k "oversized or unexpected_failures"` → `4 passed`
- `npm.cmd run python -- -m pytest app/back/tests/ingestion/test_gui_server.py app/back/tests/ingestion/test_gui_auth.py -q` → `59 passed`
- `npm.cmd run python -- -m pytest app/back/tests/ingestion -q -m "not corpus"` → `370 passed, 2 skipped, 4 deselected`
- `npm.cmd run python -- -m pytest app/back/tests/ingestion -q --basetemp .tmp/pytest_ingestion_full` → `372 passed, 4 skipped`
- `npm.cmd run python -- -m pip check` → `No broken requirements found`

Nota de cierre:
- El test `corpus` de Llama Cloud ahora se salta honestamente cuando `LlamaParse` no es accesible en el entorno, en lugar de fallar como si fuera una regresión local del GUI server.

Notas (3ª pasada):
- `server_logger = logging.getLogger(__name__)` (:87): los asserts de log usan
  `caplog` estándar (propagación por defecto activa).
- El harness existente construye requests directos con headers `Content-Length`
  (patrón en `test_gui_server.py` y `test_gui_auth.py`); el test 413 sigue ese
  mismo estilo, sin servidor real adicional.

## Evidencia de cierre (2026-08-26)

- Código modificado:
  - `app/back/src/ingestion/gui/server.py`
    - `MAX_UPLOAD_BYTES = 200 * 1024 * 1024`
    - `UploadTooLargeError`
    - `_parse_multipart_form` rechaza uploads > 200 MB antes de leer el body
    - `_handle_pipeline_run`, `_handle_validate`, `_handle_promote` registran traceback server-side y devuelven error 500 genérico
- Pruebas añadidas:
  - `app/back/tests/ingestion/test_gui_server.py`
    - regresiones para 413 por upload sobredimensionado
    - regresiones para logging con traceback y respuesta 500 sin filtrar `str(exc)`
- Resultado observable del fix:
  - el GUI local ya no acepta bodies arbitrariamente grandes por `Content-Length`
  - los fallos inesperados quedan auditados en logs server-side sin exponer detalle interno al cliente

## Riesgos y rollback
Muy bajo. Cambio local al GUI server; el front recibe un 413 nuevo pero esperado
(sin contrato roto). Rollback por commit aislado.
