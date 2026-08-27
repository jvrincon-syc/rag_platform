# Plan 04 — Workers async observables + reconcile de builds + TTL de idempotencia

Estado: ⬜ Pendiente · Severidad: ALTA · Hallazgo origen: #4 del informe

## Checklist de cierre
- [ ] Futures observados (embedding executor, indexing executor, build runner)
- [ ] Catch ampliado en `IndexingRunExecutor.execute`
- [ ] Reconcile de `ReleaseBuildJob` en arranque (puerto + Postgres + memoria)
- [ ] TTL 24 h para reservas `RESERVED` huérfanas
- [ ] Pruebas focalizadas en verde + regresión global
- [ ] Estado ✅ en `2026-08-25_indice-y-cierre.md`

## Hallazgo (verificado en código)
(a) `embedding/api/router.py:190`, `indexing/api/router.py:181`,
`api/dependencies.py:918-921`: Future/hilo lanzado sin observador. Los
`_run_guarded` solo tienen `finally` (embedding `run_service.py:879-884`, indexing
`index_bundle.py:769-774`) ⇒ una excepción no capturada muere dentro del Future sin
log y el run queda "running" para siempre.
(b) `index_bundle.py:683`: catch `(OSError, ValueError, RuntimeError)` deja escapar
`KeyError`/`TypeError`/errores de psycopg ⇒ mismo efecto silencioso.
(c) Sin reconcile de `ReleaseBuildJob`: proceso caído con job RUNNING lo deja
colgado indefinidamente (hilo daemon `release_build_runner.py:116-124`; el protocolo
`ReleaseBuildJobRepository` no lista jobs — `release_build_job_service.py:29-42`).
Contraste: embedding/indexing SÍ reconcilian al arranque (`api/app.py:49-50`).
(d) Reservas `RESERVED` huérfanas bloquean la clave idempotente para siempre
(`idempotency.py:222-227`, limpieza manual declarada).

## Decisiones registradas (2026-08-25)
TTL **24 h fijo** (constante, sin env-var). Reserva vencida ⇒ terminal `FAILED`
(504); el cliente reintenta con clave NUEVA. Nunca re-ejecutar en silencio una
operación cuyo resultado se desconoce.

## Contraste con código (2ª pasada, 2026-08-25)
- Tests unitarios del guard YA EXISTEN con store falso en
  `tests/rag_platform/test_platform_api.py:544-570` (`InMemoryIdempotencyStore`,
  guard construido como `IdempotencyGuard(store=store)`) — los tests de TTL van ahí.
  El constructor ya acepta `clock: Callable[[], datetime]` inyectable
  (`idempotency.py:156-158`): los tests usan reloj fijo para simular vencimiento,
  sin sleeps.
- `tests/rag_platform/test_release_build_job_service.py` tiene cambios SIN COMMIT del
  usuario (2 tests nuevos del runner con `internal_error_id`). Este plan EXTIENDE ese
  archivo para los tests de reconcile; prohibido revertir/pisar ese trabajo.
- `run_one_build` ya maneja sus propias excepciones de forma amplia (incluye los
  cambios sin commit). El guard nuevo del runner cubre SOLO lo de fuera:
  `build_services_factory()` / `fresh.close()` en `_execute_build`
  (`api/dependencies.py:886-914`).
- `ReleaseBuildRunner` tiene UN único punto de construcción: `dependencies.py:916`.
  Wiring de plataforma: bloque `if flags.rag_platform_v1:` en `dependencies.py:422-449`.
- Nota carrera documentada: con TTL 24 h la ventana (owner vivo > 24 h) es
  impracticable; si ocurriera, un `complete()` posterior sobreescribe el terminal
  FAILED — aceptable y registrado aquí.

## Cambios propuestos
| Archivo | Cambio |
|---|---|
| `embedding/application/run_service.py` | `submit()`: `future.add_done_callback(...)` que hace `logger.error("embedding_worker_future_failed", extra={"embedding_run_id": ...}, exc_info=error)` si el Future terminó con excepción. |
| `indexing/application/bundle_first/index_bundle.py` | (a) mismo done-callback en `submit()`. (b) `execute()`: ampliar :683 a `except Exception` (la rama domain-errors permanece PRIMERO; conserva `logger.exception` + `_fail` con código interno estable). |
| `rag_platform/infrastructure/release_build_runner.py` | `submit()` envuelve el target del hilo en try/except: `logger.exception("release_build_worker_crashed", extra={"build_job_id": ...})` + callback opcional `on_worker_error: Callable[[str, BaseException], None]`. Respeta el docstring/mecánica actual del módulo. |
| `rag_platform/application/release_build_job_service.py` | Puerto `ReleaseBuildJobRepository` += `list_non_terminal() -> list[ReleaseBuildJob]`. Clase `ReleaseBuildJobReconciler(jobs=..., now=...)`: cada job `queued/running` ⇒ FAILED con `error_code="RELEASE_BUILD_INTERRUPTED"` y `error_message` sin rutas ni secretos. Nombre alineado con el patrón existente `IndexingRunReconciler`; capa aplicación pura (solo protocolo), igual que el resto del paquete. |
| `rag_platform/infrastructure/postgres/release_repositories.py` | `list_non_terminal()`: `SELECT … WHERE state IN ('queued','running')` parametrizado, sin DDL. |
| `rag_platform/infrastructure/in_memory/repositories.py` | `list_non_terminal()`: filtro sobre dict bajo lock. |
| `api/dependencies.py` | Al construir `RagPlatformServices`: pasar `on_worker_error` que marca el job FAILED (`"RELEASE_BUILD_WORKER_CRASHED"`) vía repo si no era terminal (repo accesible en scope: `release_build_jobs`, :860-866); exponer reconciler como campo NUEVO de `PipelineServices` (p. ej. `release_build_reconciler: object \| None = None`) asignado dentro del bloque `flags.rag_platform_v1` (:422-449). |
| `api/app.py` | lifespan: tras los reconciles existentes (:49-50), invocar reconcile de build jobs si `services.rag_platform is not None and services.release_build_reconciler is not None`. |
| `rag_platform/application/idempotency.py` | `IdempotencyGuard(store=..., reserved_ttl_seconds=_DEFAULT_RESERVED_TTL_SECONDS)` con constante `24 * 3600`. En replay con status RESERVED: edad = clock − created_at (datetime naive tratado como UTC, defensivo); si edad > TTL ⇒ `store.fail(key_hash, response_status=504)` + log warning + raise error nuevo; si vigente ⇒ comportamiento actual (409 IN_PROGRESS). Actualizar docstring del "ponytail" (:226-227) reflejando la política implementada. |
| `rag_platform/domain/errors.py` | `IdempotencyReservationExpired(RagPlatformError)` con code `"IDEMPOTENCY_RESERVATION_EXPIRED"`, http_status 409 — mapeado automático por el handler genérico (`api/app.py:132-144`). |
| Tests | `tests/indexing/**`: excepción inesperada (p. ej. KeyError del use case falso) ⇒ run failed + warning con código interno. `tests/embedding/**`: done-callback no rompe submit; excepción loggeada (caplog). `tests/rag_platform/test_release_build_job_service.py` (EXTENDER, no pisar): reconcile marca solo non-terminal y es idempotente. `tests/rag_platform/test_platform_api.py` (sección guard, :535+): RESERVED vencida (clock fijo +25 h) ⇒ raise IdempotencyReservationExpired + store quedó FAILED(504); RESERVED vigente ⇒ IN_PROGRESS; usar `InMemoryIdempotencyStore` existente y clock inyectable del guard. |

Nota (3ª pasada): ambos módulos de executors ya importan `Future` y definen logger
de módulo — el done-callback no requiere imports nuevos.

## No hacer
- No añadir backoff/retries de embedding aquí (backlog 🟡.3).
- No migrar DDL ni tocar esquema (solo lecturas de estados existentes).
- No introducir env-var para el TTL ni para el límite del queue.

## Verificación

    python -m pytest app/back/tests/indexing app/back/tests/embedding app/back/tests/rag_platform -q    # desde la RAÍZ del repo
    # (pyproject.toml:44-46 define pythonpath/testpaths relativos a rootdir)

## Riesgos y rollback
Medio: toca composición (`PipelineServices`) y puerto persistido (protocolo +
2 adaptadores), pero sin DDL. Orden de commits sugerido (cada uno reversible):
(1) done-callbacks + catch ampliado, (2) reconcile de build jobs, (3) TTL idempotencia.
