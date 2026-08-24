-- Fase 8 rework (plan 2026-08-21 §D-3b): build de release ASÍNCRONO durable.
-- El build síncrono corría el motor dentro del request HTTP y bloqueaba el
-- handler (socket hang up en el proxy). Este job durable deja que el request
-- encole y responda 202, y que un worker corra el motor fuera del hilo del
-- request; el estado sobrevive a refresh y a reinicio del proceso.
-- Tabla independiente y aditiva: NO altera `rag_releases` ni el ledger
-- `rag_build_runs` (ese audita artefactos por etapa; esto es el estado de ciclo
-- de vida del intento async). Idempotente (IF NOT EXISTS), reaplicable por el
-- aplicador `prepare_postgres_indexing.py`.

-- ---------------------------------------------------------------------------
-- release_build_jobs: un registro por intento de build asíncrono de una release.
-- `state` es el ciclo de vida observable por la GUI (polling). Los tres enteros
-- del reporte (`revisions_built`/`reused_stages`/`built_stages`) se llenan solo
-- al terminar con éxito; `error_code`/`error_message` solo al fallar. Nunca se
-- persiste texto de documento, vectores, secretos ni rutas absolutas.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS release_build_jobs (
    build_job_id TEXT PRIMARY KEY,
    rag_release_id TEXT NOT NULL REFERENCES rag_releases(rag_release_id),
    project_id TEXT NOT NULL REFERENCES rag_projects(project_id),
    state TEXT NOT NULL CHECK (
        state IN ('queued', 'running', 'succeeded', 'failed')
    ),
    revisions_built INTEGER CHECK (revisions_built IS NULL OR revisions_built >= 0),
    reused_stages INTEGER CHECK (reused_stages IS NULL OR reused_stages >= 0),
    built_stages INTEGER CHECK (built_stages IS NULL OR built_stages >= 0),
    error_code TEXT,
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Lectura principal de la GUI: el job más reciente de una release.
CREATE INDEX IF NOT EXISTS ix_release_build_jobs_release_created
    ON release_build_jobs (rag_release_id, created_at DESC);
