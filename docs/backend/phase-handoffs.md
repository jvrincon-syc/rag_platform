# Handoffs entre fases backend

## PropÃ³sito

Este documento describe cÃ³mo se transfiere el control y los datos entre las
fases operativas implementadas en la rama actual, desde `docs_raw` hasta
retrieval. La meta es dejar explÃ­citos los contratos de entrada/salida, los
gates y los consumidores inmediatos.

## Flujo extremo a extremo

| Fase | Entrada principal | TransformaciÃ³n | Salida principal | Gate antes de pasar | Siguiente consumidor |
| --- | --- | --- | --- | --- | --- |
| Inventario/ingesta | `data/docs_raw` o ruta staging | fingerprint, lectura, OCR/parse, normalizaciÃ³n, clasificaciÃ³n, extracciÃ³n, validaciÃ³n | Markdown y artefactos Schema 2.0 + `_manifests/` en `data/docs_normalized` o staging | validaciÃ³n estructural y estado documental (`processed` o `needs_review`) | `chunking`, revisiÃ³n humana, indexaciÃ³n filtrada |
| RevisiÃ³n/promociÃ³n | candidate root + manifest de validaciÃ³n estructural | promociÃ³n controlada del candidato validado; `review_decisions.json` puede existir como soporte operativo, pero no es gate tÃ©cnico actual | candidato promovido a `data/docs_normalized` | validaciÃ³n estructural aprobada | `chunking`, `indexing`, GUI |
| Chunking | `docs_normalized` aprobado | parser estructural + parent builder + child builder + validaciÃ³n | chunk bundles e Ã­ndices de inspecciÃ³n | bundle vÃ¡lido y correlaciÃ³n con documento normalizado | `embedding`, inspecciÃ³n HTTP/GUI |
| Embedding | chunk bundle + perfil verificado | lectura de chunks, batch embedding, validaciÃ³n y readiness | embedding bundle + readiness checks | perfil compatible, motor disponible, documentos habilitados | `indexing` |
| Indexing | embedding bundle + perfil/target | construcciÃ³n de nodos, persistencia de rows activas, activaciÃ³n/rollback | indexing runs, nodes, vector rows, targets activos | bundle listo, target compatible, persistencia confirmada si PostgreSQL | `retrieval` |
| Retrieval | retrieval profile + target activo + query | query embedding, vector search, lexical fallback, parent expansion | evidencia recuperada y estado de readiness/validaciÃ³n | perfil activo y validado; fallback lÃ©xico permitido si vector falla | capa de respuesta/chat futura o consumidor HTTP |

## Fase 1: `docs_raw` -> `docs_normalized`

### Entry points

- [run_pipeline.py](../../scripts/ingestion/run_pipeline.py)
- [server.py](../../app/back/src/ingestion/gui/server.py)
- [pipeline.py](../../app/back/src/ingestion/pipeline.py)

### Artefactos de salida

- `*.md`
- `*.metadata.json`
- `*.pages.json`
- `*.ocr.json`
- `*.tables.json`
- `*.forms.json`
- manifests bajo `_manifests/`

### Gate

- validaciÃ³n estructural por `validate_normalized_tree`
- warnings materiales o ausencia de evidencia crÃ­tica empujan a
  `needs_review`
- la promociÃ³n es atÃ³mica y separada de la normalizaciÃ³n base
- `needs_review` no bloquea por sÃ­ solo `promote_candidate`; el gate real en
  `HEAD` es que la validaciÃ³n estructural haya pasado

## Fase 2: `docs_normalized` -> chunk bundles

### Entry points

- [app.py](../../app/back/src/chunking/api/app.py)
- [run_service.py](../../app/back/src/chunking/application/run_service.py)

### Salida

- bundles parent-child
- manifiestos `*.api-run.json`
- material de inspecciÃ³n y validaciÃ³n de chunking

### Gate

- el documento fuente debe existir en `docs_normalized`
- las referencias de spans y blocks deben ser coherentes con el documento
  normalizado

## Fase 3: chunk bundles -> embedding bundles

### Entry points

- `POST /api/embedding/runs` dentro de
  [router.py](../../app/back/src/embedding/api/router.py)
- [verify_profile.py](../../scripts/embedding/verify_profile.py)

### Salida

- corridas de embedding
- embedding bundles
- readiness checks

### Gate

- perfil de embedding verificado
- semÃ¡ntica del engine compatible con el perfil
- bundle de chunking vigente y elegible

## Fase 4: embedding bundles -> indexaciÃ³n durable o en memoria

### Entry points

- [run_indexing.py](../../scripts/indexing/run_indexing.py)
- `POST /api/indexing/runs` dentro de
  [router.py](../../app/back/src/indexing/api/router.py)

### Salida

- indexing runs
- nodos parent/child persistidos
- filas vectoriales activas
- activaciÃ³n o rollback del target

### Gate

- bundle de embeddings listo para indexaciÃ³n
- target compatible con el perfil
- `--persist-confirmed` y `RAG_PLATFORM_POSTGRES_DSN` cuando la persistencia real es
  PostgreSQL

## Fase 5: indexaciÃ³n -> retrieval

### Entry points

- `POST /api/retrieval/profiles`
- `POST /api/retrieval/profiles/{id}/activate`
- `POST /api/retrieval/profiles/{id}/validate`

### Salida

- readiness del lane de retrieval
- evidencia recuperada
- fallback lÃ©xico explÃ­citamente observable

### Gate

- perfil de retrieval activo y validado
- filas vectoriales activas para el corpus/target/perfil
- si no hay vector search disponible, solo puede contestar el camino lÃ©xico si
  `lexical_fallback_policy` lo permite

## Superficies HTTP y CLI

El repo expone dos superficies distintas:

- **GUI/HTTP de ingesta**: `ingestion.gui.server` con bridge ASGI hacia parte de
  la API bundle-first.
- **FastAPI bundle-first**: [api/app.py](../../app/back/src/api/app.py) para
  `embedding`, `indexing` y `retrieval`.

Los CLIs siguen siendo la fuente mÃ¡s directa para inventario, pipeline,
preparaciÃ³n PostgreSQL, verificaciÃ³n de perfiles y benchmarks.

## Plataforma RAG: cuatro semÃ¡nticas separadas (ADR-006)

La plataforma multi-proyecto introduce estados que **no** son sinÃ³nimos entre sÃ­
ni de la activaciÃ³n legacy. El handoff entre fases debe preservar la distinciÃ³n:

| Concepto | Confirma | No implica |
| --- | --- | --- |
| `promoted` | promociÃ³n tÃ©cnica del normalizado (gate legacy: validaciÃ³n estructural) | que la revisiÃ³n sea releaseable |
| `release_eligible` | la revisiÃ³n puede entrar a un corpus snapshot | promociÃ³n ni publicaciÃ³n |
| `PUBLISHED` | el catÃ¡logo de plataforma acepta la release | activaciÃ³n de retrieval ni cambio de consumidor |
| activaciÃ³n legacy (`is_active`) | quÃ© release consulta el chatbot | nada de lo anterior; no se toca en este plan |

Una revisiÃ³n `needs_review` exige decisiÃ³n de elegibilidad versionada antes de
entrar a un snapshot. Detalle en
[identity-and-reuse-contract.md](../rag-platform/identity-and-reuse-contract.md)
y baseline en [migration-baseline.md](../rag-platform/migration-baseline.md).

## Coexistencia legacy tras Fase 6 (publicaciÃ³n de catÃ¡logo)

La lane de plataforma se activa con `SST_FEATURE_RAG_PLATFORM_V1` (**off por
defecto**, independiente de los flags bundle-first). Con el flag off el runtime
legacy es byte-idÃ©ntico; con el flag on el composition root registra los servicios
de plataforma **sin** modificar el wiring de retrieval.

`PublishRagReleaseUseCase` (`rag_platform/application/publication_service.py`)
publica una release como transiciÃ³n `VALIDATED â†’ PUBLISHED`; **no** escribe
`is_active`, **no** crea/actualiza `retrieval_profiles` y **no** usa el scope
legacy `chatbot/sst-default`. `ActivateIndexedBundleUseCase`,
`RollbackIndexedBundleUseCase` y `/api/retrieval` permanecen como la lane legacy.

Nota de alcance: seleccionar una release publicada distinta como consumidor de
retrieval **no** es un rollback de filas vectoriales (`is_active`) y **no** forma
parte de este plan; es trabajo de una fase posterior de reconexiÃ³n del consumidor.

## Puntos de acoplamiento a vigilar

- La ingesta y la GUI comparten mucha orquestaciÃ³n en archivos grandes.
- El boundary entre GUI heredada y FastAPI bundle-first existe, pero no
  unifica toda la operaciÃ³n backend.
- `docs_normalized` sigue siendo el contrato compartido mÃ¡s importante entre
  Fase 1 y el resto del pipeline.

