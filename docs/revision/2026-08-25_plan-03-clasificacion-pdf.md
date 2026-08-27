# Plan 03 — Clasificación honesta de errores PDF (ingestión)

Estado: ✅ Cerrado (2026-08-26) · Severidad: MEDIA · Hallazgo origen: #3 del informe

## Checklist de cierre
- [x] Implementado
- [x] Regresión `test_pipeline_integration.py` en verde con contrato honesto actualizado
- [x] Test nuevo de excepción inesperada en verde
- [x] Estado ✅ en `2026-08-25_indice-y-cierre.md`

## Hallazgo (verificado en código)
`app/back/src/ingestion/pipeline.py:1197-1207` — en el catch-all por documento,
todo `.pdf` recibe razón `pdf_extractor_unconfigured` aunque el extractor ESTÉ
configurado (bug de código, disco lleno, PDF corrupto, permisos). El diagnóstico
real solo queda en `"error": str(exc)`; la causa reportada a la cola de revisión
(`needs_review.json`) es inventada → viola AGENTS §5 y §3.3.

## Decisión registrada (2026-08-25)
PDF con error inesperado ⇒ `needs_review` + razón honesta `processing_error`
(sigue yendo a cola humana, pero con causa verdadera).

## Contraste con código (2ª pasada, 2026-08-25)
- La señal canónica de extractor ausente ya existe: `"No PDF extractor configured"`
  es uno de los `fallback_signals` de `_read_document` (`pipeline.py:776-780`) y es
  el mensaje exacto de `MissingPdfExtractor` (`readers/pdf_digital_reader.py:30-32`).
  El helper nuevo debe reusar ESA cadena, no inventar otra heurística.
- Grep total (src + tests + scripts + front): `pdf_extractor_unconfigured` solo
  aparece en `pipeline.py:1203` y en el set de razones aceptadas del test
  `test_pipeline_integration.py:95-101`. Cero consumidores externos de la cadena.
- Con el fix, el test existente SIGUE pasando sin tocarlo: el fake PDF del entorno
  de test dispara el RuntimeError "No PDF extractor configured" real.

## Cambios propuestos
| Archivo | Cambio |
|---|---|
| `ingestion/pipeline.py` | Helper `_is_missing_pdf_extractor_error(exc) -> bool`: True si `"No PDF extractor configured" in str(exc)`. En el except (:1197): la rama pdf queda condicionada a ese helper; cualquier otra excepción ⇒ `["processing_error"]`. El estado se mantiene `needs_review` para PDFs (:1207 sin cambios). |
| idem | `_failure_recommendation` (:832-837): caso `processing_error` ⇒ "Revisar el log del pipeline: fallo inesperado procesando el documento." (hoy sugiere configurar extractor, incorrecto para esta causa). |
| `tests/ingestion/test_pipeline_integration.py` | Test nuevo: reader que lanza `ValueError("disk full")` para un `.pdf` ⇒ reasons == `["processing_error"]` (NO `pdf_extractor_unconfigured`), status `needs_review`, campo `"error"` preservado en el ítem. |

## No hacer
- No cambiar el estado a `failed` (decisión registrada: va a revisión humana).
- No capturar tipos específicos de excepción de terceros (frágil); la señal por
  mensaje reusa el contrato ya existente en `_read_document`.

## Verificación

    python -m pytest app/back/tests/ingestion -q    # desde la RAÍZ del repo
    # (pyproject.toml:44-46 define pythonpath/testpaths relativos a rootdir)

Ejecución 2026-08-26:
- `npm.cmd run python -- -m pytest app/back/tests/ingestion/test_pipeline_integration.py -q -k processing_error` → `1 passed`
- `npm.cmd run python -- -m pytest app/back/tests/ingestion/test_pipeline_integration.py -q` → `21 passed`
- `npm.cmd run python -- -m pytest app/back/tests/ingestion -q -m "not corpus"` → `370 passed, 2 skipped, 4 deselected`
- `npm.cmd run python -- -m pytest app/back/tests/ingestion -q --basetemp .tmp/pytest_ingestion_full` → `372 passed, 4 skipped`
- `npm.cmd run python -- -m pip check` → `No broken requirements found`

Nota de cierre:
- La aserción histórica de `test_pipeline_processes_markdown_and_tracks_pdf_needing_review` se ajustó para aceptar `processing_error` cuando el fixture dispara un PDF corrupto real (`No /Root object!`), porque el contrato honesto ya no puede inventar `pdf_extractor_unconfigured` en ese caso.
- El test `corpus` de Llama Cloud ahora se salta honestamente cuando `LlamaParse` no es accesible en el entorno, en lugar de degradar la suite completa como si fuera una regresión del pipeline local.

Nota (3ª pasada): el front no referencia `pdf_extractor_unconfigured` ni
`processing_error` en ningún archivo — cero impacto UI.

## Evidencia de cierre (2026-08-26)

- Código modificado:
  - `app/back/src/ingestion/pipeline.py`
    - helper `_is_missing_pdf_extractor_error(...)`
    - clasificación honesta `processing_error` para fallos PDF inesperados
    - recomendación operativa actualizada en `_failure_recommendation`
  - `app/back/src/ingestion/schemas/manifests.py`
    - `ReviewItem.error` permite persistir el error real del documento
- Pruebas añadidas o ajustadas:
  - `app/back/tests/ingestion/test_pipeline_integration.py`
    - `test_pipeline_marks_unexpected_pdf_failures_as_processing_error`
    - ajuste de la aserción histórica para aceptar contrato honesto ante PDF corrupto real
- Resultado observable del fix:
  - `needs_review.json` deja de inventar `pdf_extractor_unconfigured` para fallos ajenos al extractor
  - el item de revisión conserva la causa real en el campo `error`

## Riesgos y rollback
Bajo. Único productor/consumidor de la cadena verificado. Los operadores verán
razones más precisas en la cola de revisión; ningún flujo filtra por la cadena
exacta fuera del test que sigue pasando. Rollback por commit aislado.
