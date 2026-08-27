# Plan 01 — Validación de chunking honesta (fail-closed)

Estado: ✅ Cerrado (2026-08-26) · Severidad: ALTA · Hallazgo origen: #1 del informe

## Checklist de cierre
- [x] Implementado
- [x] Pruebas de regresión añadidas y en verde
- [x] Verificación focalizada ejecutada
- [x] Estado ✅ en `2026-08-25_indice-y-cierre.md`

## Hallazgo (verificado en código)
`app/back/src/chunking/application/run_service.py:522-540` — `_persist_validation`
escribe `"status": "passed"`, `"errors": 0`, `"checks": []` incondicionalmente aunque
el run haya fallado o termine `completed_with_warnings`. El endpoint
`GET /api/chunking/runs/{run_id}/validation` (`api/router.py:157` → `get_validation:310`)
sirve ese reporte inventado al GUI y al front (`chunkingApi.ts`). Además, runs
fallidos no generan archivo alguno: la única llamada está en la ruta de éxito
(`execute_run:245`), así que el guard `_execute_run_guarded` (:355-371) marca
`failed` pero nunca deja validación auditable.

## Decisión registrada (2026-08-25)
Runs fallidos SÍ escriben archivo con `status: "failed"` (fail-closed total:
siempre hay reporte auditable).

## Contraste con código (2ª y 3ª pasada, 2026-08-25)
- Contrato confirmado sin fricción: el front mapea snake_case → camelCase en
  `chunkingApi.ts:202-213` (`toValidation`: `payload.run_id`, `payload.documents_checked`).
  Mantener las claves JSON exactas del back es suficiente; no hay que tocar front.
- **Existen DOS productores de `{run_id}.validation.json`**:
  1. Orchestrator por documento: `chunking/infrastructure/filesystem_run_repository.py:44-59`
     (schema `{run_id, document_id, status, parent_count, child_count}`, valores reales
     de `result.validation.*`) — YA ES HONESTO, NO SE TOCA. Sin colisión de nombres
     (espacios de run_id distintos: id del engine vs sha256 del run API).
  2. Run service API: `chunking/application/run_service.py:522-540` — el fabricado.
     Este plan cambia SOLO el #2.
- `tests/retrieval/test_pipeline_api.py:527` aserta `"passed"` pero es el endpoint de
  validación RETRIEVAL — sin relación; ningún test aserta el contenido fabricado del
  run service (verificado por grep).
- Efecto cruzado esperado en front: hoy un run fallido da 404 →
  `loadChunkingValidationOptional` devuelve null → UI muestra "pendiente". Tras el fix
  responderá 200 con `status="failed"` → la UI mostrará "failed". Es el comportamiento
  deseado; `ChunkingRunPanel.tsx:125` pinta el string crudo, sin cambio necesario.

## Cambios propuestos
| Archivo | Cambio |
|---|---|
| `chunking/application/run_service.py` | `_persist_validation(state)` deriva el reporte del estado real: check `documents_completed` (passed si `completed_documents == requested_documents`; detail `"{completados}/{solicitados}"`), check `run_status_ok` (passed si el estado es terminal de éxito). `status` = `"passed"` solo si ambos checks pasan; `"failed"` en caso contrario. `errors` = documentos faltantes (+1 si el run terminó failed/interrupted). `warnings` = `len(state.warnings)`. Claves JSON EXACTAS a las actuales: `run_id / status / documents_checked / errors / warnings / checks`. |
| idem | Invocar `_persist_validation(state)` también desde `_execute_run_guarded` (dentro del except, tras marcar `failed` y persistir manifest) para que todo run tenga validación honesta. |
| `tests/chunking/integration/test_run_service_persistence.py` | (a) Run exitoso ⇒ archivo con `status="passed"`, `errors=0`, checks con `documents_completed` passed. (b) Run que lanza excepción ⇒ archivo existe con `status="failed"`, `errors >= 1`, y el manifest sigue en `failed`. |

## No hacer
- No cambiar nombres/claves del payload ni añadir campos nuevos (contrato estable).
- No mover la lógica a otro módulo: es responsabilidad directa del run service.

## Verificación

    python -m pytest app/back/tests/chunking -q    # desde la RAÍZ del repo
    # (pyproject.toml:44-46 define pythonpath/testpaths relativos a rootdir)

Verificación ejecutada el 2026-08-26:
- `npm.cmd run python -- -m pytest app/back/tests/chunking/integration/test_run_service_persistence.py -q -k "validacion_honesta or guarded_persiste_validacion_failed"` → `2 passed`
- `npm.cmd run python -- -m pytest app/back/tests/chunking -q` → `99 passed, 1 skipped`

## Evidencia de cierre (2026-08-26)

- Código modificado:
  - `app/back/src/chunking/application/run_service.py`
    - `_execute_run_guarded` ahora persiste validación también en la ruta `failed`
    - `_persist_validation` calcula `status`, `errors` y `checks` desde el estado real del run
- Pruebas añadidas:
  - `app/back/tests/chunking/integration/test_run_service_persistence.py`
    - `test_execute_run_persiste_validacion_honesta_para_corrida_exitosa`
    - `test_execute_run_guarded_persiste_validacion_failed_cuando_explota_el_chunking`
- Resultado observable del fix:
  - el endpoint `GET /api/chunking/runs/{run_id}/validation` deja de servir un JSON fabricado
  - un run fallido ya no responde 404 para validación; responde con un reporte auditable `status="failed"`

## Riesgos y rollback
Bajo: cambia solo el CONTENIDO del JSON, no su forma ni su transporte.
Consumidores auditados: router chunking, bridge GUI (`gui/chunking_adapter.py:128`),
front `toValidation` — todos leen claves existentes.
Rollback: revertir el commit del plan (aislado).
