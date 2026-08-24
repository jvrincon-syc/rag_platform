# ADR-010 — Build de release asíncrono y durable

- **Estado**: Aceptada (2026-08-24)
- **Fase**: 8 (rework de GUIs de plataforma; plan `docs/superpowers/plans/2026-08-21-platform-gui-rework-reuse-legacy.md`, §D-3b)
- **Relacionada**: ADR-006 (proyecto/variante/release), ADR-009 (aislamiento por proyecto)

## Contexto

`POST /api/platform/releases/{id}/build` corría el motor de build **síncrono
dentro del request HTTP**. El servidor GUI (`ingestion.gui.server`) es un
`ThreadingHTTPServer` que reenvía a FastAPI vía un bridge ASGI. Dos problemas
observados con datos reales (`sst-general`, 55 documentos):

1. El build largo bloqueaba el hilo del request hasta que el proxy (Vite) cerraba
   la conexión: *socket hang up*, sin respuesta observable.
2. La app FastAPI se cablea con **una sola conexión psycopg2 compartida**; ese
   build síncrono, más peticiones concurrentes, chocaban sobre la misma conexión
   (psycopg2 no es thread-safe).

El endurecimiento del bridge (excepción → `500 PIPELINE_BRIDGE_ERROR`) y un lock
de proceso serializaron las lecturas, pero no eliminan la necesidad de sacar el
build del hilo del request.

## Decisión

El build de release pasa a ser **asíncrono y durable**:

- `POST /releases/{id}/build` **encola** un `ReleaseBuildJob` durable en estado
  `queued` y responde de inmediato (`ReleaseBuildAcceptedSchema`:
  `build_job_id`, `state`). Ya **no** devuelve el `ReleaseBuildReport` síncrono.
- Un worker en un hilo daemon transiciona el job `running → succeeded|failed` y
  persiste el resultado (los tres enteros del reporte al éxito; `error_code`/
  `error_message` al fallo). Nunca deja el job colgado en `running`.
- En modo Postgres el worker usa una **conexión propia** (un bundle de servicios
  fresco por build, cerrado al terminar): no comparte la conexión del request, no
  la bloquea, y el estado va a la misma tabla durable `release_build_jobs`. En
  modo memoria reutiliza los repos compartidos (thread-safe por lock).
- `GET /releases/{id}/build-status` expone el último job (scope-aware) para que la
  GUI observe el progreso por **polling** (reusando el patrón `usePollingLoop`).
- La idempotencia HTTP existente se preserva: un replay del mismo
  `Idempotency-Key` devuelve el **mismo** `build_job_id` sin re-encolar.

Estado durable en la tabla nueva `release_build_jobs` (migración
`20260824_01`), aditiva: no altera `rag_releases` ni el ledger `rag_build_runs`.

## Consecuencias

- **Cambio de contrato**: `POST /build` cambia de `200 ReleaseBuildReportSchema`
  (síncrono) a `ReleaseBuildAcceptedSchema` (encolado) + nuevo
  `GET /build-status`. El OpenAPI se regenera; el frontend consume el nuevo flujo
  (encolar + polling). El caso de uso `BuildRagReleaseUseCase.execute` no cambia
  (lo invoca el worker), así que sus tests directos siguen válidos.
- El lifecycle de la release (`draft → validated → …`) no cambia; el job async es
  un intento operacional sobre la release, no un estado del lifecycle.
- **Techo (ponytail)**: un hilo daemon por build y un bundle fresco por build en
  Postgres. Si los builds se vuelven frecuentes o el proceso necesita sobrevivir
  reinicios a mitad de build, evoluciona a una cola/worker persistente y un pool
  de conexiones dedicado. El estado ya es durable, así que ese cambio no altera
  el contrato observable.

## Alternativas descartadas

- **Mantener síncrono y subir timeouts**: no elimina el bloqueo del hilo ni el
  choque de conexión; degrada toda la GUI durante un build.
- **Correr el build bajo el lock del bridge**: lo serializa correctamente pero
  bloquea todas las lecturas (incluido el polling de estado) durante el build.
- **Endpoints async duplicados junto al síncrono**: deja dos caminos y exige
  migración posterior (re-trabajo); se prefirió un cambio de contrato limpio.
