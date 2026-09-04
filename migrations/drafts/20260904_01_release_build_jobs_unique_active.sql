-- ============================================================================
-- DRAFT — NO APLICAR AUTOMÁTICAMENTE. Revisión manual del operador (PR-1.4).
--
-- Vive en `migrations/drafts/` a propósito: el aplicador
-- (`scripts/indexing/prepare_postgres_indexing.py`) hace `migrations/*.sql` NO
-- recursivo, así que este archivo NO se recoge. Para aplicarlo, muévelo a
-- `migrations/` con el siguiente número de secuencia tras validarlo contra una
-- BD desechable.
--
-- Qué hace: refuerza a nivel de esquema el invariante "un solo build activo por
-- release" que PR-1.4 ya impone en la capa de aplicación
-- (`EnqueueReleaseBuildUseCase`). El índice único parcial impide que dos filas
-- `queued`/`running` coexistan para la misma `rag_release_id`, cerrando la
-- ventana de carrera entre dos requests concurrentes que pasen el chequeo de
-- aplicación antes de que ninguno haya insertado.
--
-- Nota de aplicación: si la tabla tiene tráfico y se quiere cero-downtime, crea
-- el índice con CREATE UNIQUE INDEX CONCURRENTLY FUERA de una transacción (el
-- aplicador actual envuelve cada migración en una transacción, incompatible con
-- CONCURRENTLY). Para una BD pequeña/parada, la forma transaccional de abajo basta.
--
-- Prerrequisito de datos: no deben existir ya dos filas activas para la misma
-- release (si PR-1.4 estuvo desplegado, no las habrá). Verificar antes:
--   SELECT rag_release_id, count(*) FROM release_build_jobs
--   WHERE state IN ('queued','running') GROUP BY 1 HAVING count(*) > 1;
-- ============================================================================

CREATE UNIQUE INDEX IF NOT EXISTS ux_release_build_jobs_one_active
    ON release_build_jobs (rag_release_id)
    WHERE state IN ('queued', 'running');
