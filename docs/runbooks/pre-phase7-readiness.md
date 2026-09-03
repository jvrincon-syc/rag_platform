# Pre-Phase 7 Readiness â€” Gate 0 (baseline congelado)

> **Alcance de esta sesiÃ³n: GATE 0.** No se iniciÃ³ Task 1. No se implementÃ³
> cÃ³digo de aplicaciÃ³n, migraciones ni frontend. No se hizo commit ni push. No se
> tocÃ³ `data/docs_raw`. No se ejecutÃ³ ninguna operaciÃ³n destructiva de base de
> datos (la Ãºnica conexiÃ³n se abriÃ³ en modo `readonly`).
>
> **ExcepciÃ³n autorizada por el operador (esta sesiÃ³n):** el operador levantÃ³
> explÃ­citamente la polÃ­tica por defecto de "no inspecciÃ³n de BD" y autorizÃ³
> correr un probe **read-only** para obtener la evidencia viva de Gate 0. No se
> ejecutaron pytest, build de frontend, `pip check` ni el health checker.
>
> Este runbook registra el **estado real observado**. Termina con exactamente un
> resultado: `GATE 0: PASS` o `GATE 0: BLOCKED`.

Fecha de la sesiÃ³n: 2026-08-18.

> **Re-verificaciÃ³n 2026-08-18 (segunda corrida):** probe read-only re-ejecutado;
> resultado idÃ©ntico â€” PG 18.6, pgvector 0.8.5, 10 tablas de plataforma + 7
> `idx_vec_*`, seed 1 por tabla (1 release, 1 config version, 1 binding), 1 versiÃ³n
> por proyecto (determinista), 0 FKs entrantes a bindings. Gate 0 se mantiene PASS.
> Plan autoritativo de esa sesion: cierre pre-Fase 7 luego absorbido por
> ADR-006, ADR-007, ADR-008 y el plan maestro
> `docs/superpowers/plans/Plan_Ajustado_Plataforma_RAG_MultiProyecto(3).md`.

---

## A. Instrucciones del repositorio y plan autoritativo

LeÃ­dos y obedecidos: `README_REGLAS.md`, `AGENTS.md`, `CLAUDE.md`,
`app/back/AGENTS_back.md`, el cierre pre-Fase 7 luego absorbido por ADRs, el
plan maestro `docs/superpowers/plans/Plan_Ajustado_Plataforma_RAG_MultiProyecto(3).md`
y el baseline archivado `docs/rag-platform/migration-baseline.md`.

ConfirmaciÃ³n: esta sesiÃ³n es Gate 0. No se reinterpretÃ³ la arquitectura congelada.

---

## B. Commit exacto

- `git rev-parse HEAD` â†’ **`079c66559eb6d819c84e74113ef6944b88c7d297`**
- `git log -1 --oneline` â†’ **`079c665 checkpoint de e2e con release id`**

Divergencia registrada (no bloqueante): el plan maestro cita `3bc9a8a` y el
baseline archivado registrÃ³ `9784d2f`; el Ã¡rbol real estÃ¡ mÃ¡s adelante
(`079c665`, incluye Fases 4-6 y la corrida e2e de release). Se usÃ³ el worktree
local real, sin asumir SHA de conversaciones previas.

---

## C. Estado del worktree (NO limpio â€” congelado tal cual)

64 archivos cambiados (115 inserciones, 6836 eliminaciones):

- **Modificados:** manifiestos e inventario normalizado de `sst-general` y ~55
  sidecars `data/projects/sst-general/normalized/**/*.metadata.json`.
- **Borrados:** 2 manifests `_20260814_175849` y 4 planes histÃ³ricos
  (`docs/superpowers/plans/2026-07-*`).
- **Sin seguimiento:** 2 manifests `_20260818_083057`, el plan congelado
  `2026-08-18-...md`, y (creado y borrado en esta sesiÃ³n) el probe temporal.
- Staged: ninguno.

**Solape con Task 1-7:** ningÃºn archivo de cÃ³digo (`app/back/src/**`), migraciÃ³n
(`migrations/**`) ni frontend (`app/front/**`) estÃ¡ modificado. SÃ­ estÃ¡n
modificados sin commit los sidecars `*.metadata.json` del corpus normalizado de
`sst-general` â€” insumo de Task 1 (platform identity) y Task 5 (ownership).
Caveat no bloqueante (Â§DecisiÃ³n, D-4): el corpus normalizado de referencia estÃ¡
sucio respecto a `HEAD`; conviene commitear/stashear antes de que Task 1/5
dependan de esos sidecars. Gate 0 no exige Ã¡rbol limpio.

---

## D. Inventario de migraciones (repo vs vivo)

### Repositorio (`migrations/*.sql`)

30 archivos. Ãšltima: **`20260812_03_extend_chunk_bundles_with_platform_provenance.sql`**.
Plataforma presente: `20260810_01..08`, `20260812_01..03`. Las migraciones que el
plan crearÃ¡ (`20260818_01/02/03`) **NO existen todavÃ­a** (correcto).

Sin tabla de ledger canÃ³nica: `scripts/indexing/prepare_postgres_indexing.py`
reaplica todos los `*.sql` cada corrida con DDL idempotente. El estado vivo se
inspecciona por catÃ¡logo, no por tabla de versiones.

### PostgreSQL vivo (observado por probe read-only)

- Servidor: **PostgreSQL 18.6** (x86_64-windows).
- ExtensiÃ³n `vector` (pgvector): **0.8.5**.
- `search_path`: `"$user", public`.
- Tablas de plataforma presentes (10/10): `rag_projects`,
  `project_configuration_versions`, `document_processing_profiles`,
  `chunking_profiles`, `project_embedding_profiles`,
  `project_indexing_target_bindings`, `indexing_targets`, `rag_variants`,
  `corpus_snapshots`, `rag_releases`.
- Tablas `idx_vec_*` presentes (7): `idx_vec_llama_bge_m3_v1`,
  `idx_vec_llama_cohere_embed_v4_v1`, `idx_vec_llama_first_local_v1`,
  `idx_vec_llama_voyage_4_v1`, `idx_vec_local_bge_m3_v1`,
  `idx_vec_local_cohere_embed_v4_v1`, `idx_vec_local_voyage_4_v1`.

**ReconciliaciÃ³n repoâ†”vivo:** el esquema vivo coincide con las suposiciones de
las migraciones del repo â€” `rag_releases` con `target_binding_key` y **sin**
`configuration_version`; `project_indexing_target_bindings` en forma legacy
`PK(project_id, binding_key)` sin `configuration_version`. Es exactamente el
estado que Tasks 3/4 esperan alterar. Sin diferencia material sin reconciliar.

---

## E. Feature flags efectivas

ResoluciÃ³n: `core/feature_flags.py::FeatureFlags.from_env` lee `SST_FEATURE_*` de
`os.environ`; default de `rag_platform_v1` = `False`. En el shell de la sesiÃ³n:
todas ausentes.

| Flag | Env | Default | Efectivo |
| --- | --- | --- | --- |
| `SST_FEATURE_RAG_PLATFORM_V1` | `<unset>` | `False` | **`False`** |
| `SST_FEATURE_EMBEDDING_V2` | `<unset>` | `True` | `True` |
| `SST_FEATURE_INDEXING_BUNDLE_FIRST` | `<unset>` | `True` | `True` |
| `SST_FEATURE_RETRIEVAL_V1` | `<unset>` | `True` | `True` |

---

## F. Baseline PostgreSQL

- Variable DSN del repo: `RAG_PLATFORM_POSTGRES_DSN`
  (`indexing/infrastructure/postgres/settings.py:25`).
- DSN sanitizado (sin secreto):

```
host = localhost
port = 5432
database = rag_platform
user = <REDACTED>
password = <REDACTED>
```

- ConexiÃ³n: exitosa, en modo **readonly** (sin capacidad de escritura).
- Servidor **PostgreSQL 18.6**, pgvector **0.8.5** (ver Â§D-vivo).

---

## G. Inventario de seed/catÃ¡logo de plataforma (observado)

Conteos reales (`SELECT count(*)`):

| Tabla | Filas |
| --- | ---: |
| `rag_projects` | 1 |
| `project_configuration_versions` | 1 |
| `document_processing_profiles` | 1 |
| `chunking_profiles` | 1 |
| `project_embedding_profiles` | 1 |
| `project_indexing_target_bindings` | 1 |
| `indexing_targets` | 7 |
| `rag_variants` | 1 |
| `corpus_snapshots` | 1 |
| `rag_releases` | 1 |

Proyecto presente: **`proj_sst-general`** (bootstrap/e2e).

> **CorrecciÃ³n de un supuesto del operador:** se indicÃ³ "la BD no tiene datos",
> pero el probe muestra un **seed mÃ­nimo de un solo elemento por tabla** (incluida
> **1 release**). Se registra el estado real. Como cada proyecto tiene exactamente
> una versiÃ³n de configuraciÃ³n, este estado es el caso determinista mÃ¡s simple (no
> hay ambigÃ¼edad histÃ³rica que resolver).

---

## H. Mapeo histÃ³rico release â†’ configuraciÃ³n (decisiÃ³n dura) â€” RESUELTO

- `rag_releases`: 1 fila, proyecto `proj_sst-general`. La tabla **no** tiene
  `configuration_version` (solo `target_binding_key`).
- `project_configuration_versions` para `proj_sst-general`: **1**.

Como el proyecto tiene **exactamente 1** versiÃ³n de configuraciÃ³n, el mapeo de la
Ãºnica release a esa versiÃ³n es **determinista** (no existe otra versiÃ³n que
pudiera haber usado). Regla del plan: "1 configuration version â†’ mapeo puede ser
determinista si no hay evidencia contradictoria" â€” satisfecha. **NO se usÃ³
`max(version)`**; no hay nada que fabricar. **No es blocker.**

Insumo para Task 4: el backfill de `configuration_version` para la release
existente es determinista (= la Ãºnica versiÃ³n del proyecto); la migraciÃ³n de
enforcement `20260818_03` puede `VALIDATE` tras ese backfill determinista.

---

## I. Mapeo histÃ³rico binding â†’ configuraciÃ³n â€” RESUELTO

- `project_indexing_target_bindings`: forma legacy confirmada en vivo â€”
  columnas `project_id, binding_key, indexing_target_id, embedding_profile_id`,
  sin `configuration_version`.
- `bindings_vs_versions`: `proj_sst-general` â†’ bindings=**1**, versions=**1**.

Exactamente 1 versiÃ³n â†’ migraciÃ³n determinista permitida (camino (a) de Task 3).
NingÃºn proyecto con `versions>1`. NingÃºn proyecto con `versions=0 & bindings>0`.
**No es blocker.**

---

## J. Foreign keys entrantes a `project_indexing_target_bindings` â€” RESUELTO

Query de catÃ¡logo `pg_constraint` (contype='f', confrelid=bindings): **0 filas**.
No hay FK entrante en el esquema vivo (coincide con el repo). â†’ La estrategia
delete+reinsert de Task 3 es **viable**. **No es blocker.**

---

## K. Esquema actual de `rag_releases` (observado)

Columnas de pin observadas: solo `target_binding_key`. `configuration_version`:
**AUSENTE**. Columna tipo `resolved_indexing_target_id`: **AUSENTE**. Confirma
que el contrato pinned-configuration del plan es aditivo. La Ãºnica fila viva no
satisface aÃºn el contrato (no persiste `configuration_version`); se pinnearÃ¡ por
backfill determinista (Â§H). No se modificÃ³ ninguna fila.

---

## L. `find_binding` y consumidores de `CreateRagVariantRequest` (inventario)

- `TargetBindingResolver.find_binding()` (`project_repositories.py:387-389`):
  `(self, project_id: PlatformId, binding_key: str)` â€” **NO** toma
  `configuration_version`.
- `CreateRagVariantRequest` (`recipe_service.py:52-66`): `variant_slug (req),
  project_id (req), processing_profile_id (req), chunking_profile_id (req),
  embedding_profile_id (req), target_binding_key (req),
  allow_unverifiable_revision=False`. **NO** tiene `configuration_version`.
- `CreateRagVariantUseCase.execute(request, *, actor_id)` (`recipe_service.py:89-91`)
  reconstruye prefijos: `f"proj_{request.project_id}"` (112-114), `f"pp_{...}"`,
  `f"cp_{...}"` (115-122), `f"ragv_{request.variant_slug}"` (173-176). Confirma
  el bug de doble prefijo que el plan corrige con `platform_id_body`.
- Consumidores que romperÃ¡ el nuevo campo requerido: `seed_project.py:248`,
  `test_recipe_identity.py:154`.
- Callers de `find_binding` (cambio atÃ³mico de firma): `recipe_service.py:142`,
  `release_service.py:156`, `release_build_service.py:185`; adaptadores/protocol
  `project_repositories.py:387`, `in_memory/repositories.py:153`,
  `context.py:107`; resolvers de test `test_release_membership_integrity.py:56`,
  `test_release_incremental_build.py:49`.

---

## M. Baseline seed/runtime de chunking (gap Task 2 confirmado)

- `seed_project.py:99-100`: `--chunking-slug` y `--chunking-strategy`, default
  `"structural"`. `:170`: `chunking_id = f"cp_{args.chunking_slug}"` â†’ `cp_structural`.
- `:150-154`: `INSERT ... ON CONFLICT (chunking_profile_id) DO NOTHING`.
- `:153`: `sanitized_config_json` = `'{}'::jsonb`.
- `:134`: fingerprint = `_fingerprint("chunking", args.chunking_strategy)` â€” excluye config.
- `:107-110`: `_fingerprint()` SHA256 inline; **no existe** helper
  `compute_chunking_profile_fingerprint`.
- `release_build_resolver.py:104-109` `_SUPPORTED_CHUNKING_STRATEGIES` (4 alias);
  `:559-567` `_runtime_chunking_profile()` colapsa todas a
  `RuntimeChunkingProfile.local_structural_v1()`.

Consistente con el seed vivo: `chunking_profiles=1` (un solo perfil `cp_structural`).
Gap Task 2 confirmado. No corregido en Gate 0.

---

## N. Baseline lane legacy PostgreSQL (gap Task 5 confirmado)

- DSN `RAG_PLATFORM_POSTGRES_DSN` (`settings.py:25`), cargado en `run_indexing.py:172`.
- `:232-320`: conecta **despuÃ©s** de leer inventario, **sin** inspecciÃ³n de
  ownership. `:262`: lee solo `_manifests/inventory.json`; nunca `*.metadata.json`.
- `:232-260`: falla CLOSED si falta manifiesto, pero el ownership de documento
  **falla OPEN** (sin check de sidecar). Gap Task 5 confirmado. No corregido en Gate 0.

---

## O. Baseline SQL vectorial (gap Task 6 confirmado)

Identificadores de tabla `idx_vec_*` construidos con **f-string** en todos:

| MÃ©todo | Archivo:lÃ­nea | `indexing_target_id` | ConstrucciÃ³n |
| --- | --- | --- | --- |
| `replace_document_vectors` | `vector_repository.py:77` (`:90`) | **NO** | f-string `DELETE FROM {table}` |
| `append_bundle_vectors` | `:112` (`:134`) | SÃ | f-string `INSERT INTO {table}` |
| `activate_bundle` | `:172` (`:186`) | SÃ | f-string `UPDATE {table}` |
| `count_active_rows` | `:232` (`:246`) | SÃ | f-string `SELECT ... {table}` |
| `rollback_to_bundle` | `:265` (`:280`) | SÃ | f-string `UPDATE {table}` |
| `create_vector_table_sql` | `sql.py:13` (`:18`) | **NO** | f-string `CREATE TABLE {table}`, retorna `str` |

`IndexingTarget` (`domain/bundle_first.py:69-74`) expone `postgres_schema` +
`vector_table`; `ResolvedIndexingProfile` (`domain/profiles.py:17-27`) expone
solo `vector_table`; ambos con `Field(pattern=r"^idx_vec_[a-z0-9_]+$")`. Gap
Task 6 confirmado. No corregido en Gate 0.

---

## P. PolÃ­tica de `data/docs_raw`

`data/docs_raw` existe como fuente inmutable; no se leyÃ³ contenido innecesario;
no se alterÃ³.

**DATA POLICY: CONFIRMED â€” data/docs_raw was not modified.**

---

## Q. PolÃ­tica de ejecuciÃ³n

- **Ejecutado (autorizado por el operador):** probe read-only `gate0_probe.py`
  (conexiÃ³n `readonly`, solo `SELECT`/`SHOW`), luego eliminado (no commiteado).
- **NO ejecutado:** pytest, build de frontend, `pip check`, health checker
  pre-Fase 7. Sus comandos se entregarÃ¡n al operador task por task.

---

## R. PolÃ­tica de Git

- No se creÃ³ ningÃºn commit. No se hizo push.

---

## DecisiÃ³n Gate 0

Todos los bloqueos previos se resolvieron con evidencia viva real:

1. **Acceso a BD:** resuelto â€” probe read-only ejecutado con autorizaciÃ³n del
   operador; esquema y datos observados directamente.
2. **Release â†’ config (Â§H):** resuelto â€” 1 release y 1 versiÃ³n de configuraciÃ³n
   por proyecto â†’ mapeo determinista, sin fabricaciÃ³n.
3. **Binding â†’ config (Â§I):** resuelto â€” 1 binding, 1 versiÃ³n â†’ migraciÃ³n
   determinista permitida (camino (a) de Task 3).
4. **FKs entrantes a bindings (Â§J):** resuelto â€” 0 filas â†’ delete+reinsert viable.
5. **Esquema vivo vs migraciones (Â§D):** resuelto â€” el esquema vivo coincide con
   las suposiciones del repo; `rag_releases` sin `configuration_version` y
   bindings en forma legacy, exactamente lo que Tasks 3/4 alterarÃ¡n.

Caveats registrados (no bloqueantes):

- **D-4 worktree de datos:** ~55 sidecars `*.metadata.json` de `sst-general`
  modificados sin commit; commitear/stashear antes de que Task 1/5 dependan de ellos.
- **Insumo Task 4:** backfill determinista de `configuration_version` para la
  release existente (= Ãºnica versiÃ³n del proyecto); la migraciÃ³n `20260818_03`
  puede `VALIDATE` tras Ã©l.

No se fabricÃ³ procedencia, no se usÃ³ `max(configuration_version)`, no se copiaron
bindings a versiones histÃ³ricas, no se adivinÃ³ quÃ© usÃ³ ninguna release.

---

## Addendum post-Gate-0 (2026-08-18, durante Gate 2)

Al aplicar la primera migraciÃ³n de Gate 2 (`20260818_01`) se descubriÃ³ que el
aplicador `scripts/indexing/prepare_postgres_indexing.py` **no puede reaplicar todas
las migraciones**: `20260810_08_pure_platform_project_not_null.sql` falla con
`NotNullViolation` porque existe una fila `chunk_bundles` legacy con `project_id`
NULL (`legacy-chunk-bundle-...`), en una BD que ADR-008 declara pure-platform. El
aplicador corre en una sola transacciÃ³n, asÃ­ que **hizo rollback completo (sin
cambios)**. `20260818_01` se aplicÃ³ por eso de forma **quirÃºrgica** (una sola
migraciÃ³n, transacciÃ³n propia) y quedÃ³ verificada. ImplicaciÃ³n: las migraciones
`20260818_02/03` (Task 4) tambiÃ©n deberÃ¡n aplicarse quirÃºrgicamente. **DecisiÃ³n de
operador pendiente** sobre la fila legacy huÃ©rfana (reset/rebuild dev ADR-007 o
limpieza puntual con evidencia). No modifica el resultado de Gate 0.

**ActualizaciÃ³n (2026-08-18): el operador autorizÃ³ reset/rebuild dev (ADR-007).**
Se truncaron las 41 tablas de datos (incluida la fila `chunk_bundles` con
`project_id` NULL) y `prepare_postgres_indexing.py` re-aplicÃ³ todas las
migraciones limpio (`status=prepared`), esquema en head con `20260818_01`. El
re-apply-all vuelve a funcionar; las migraciones de Task 4 ya no requieren apply
quirÃºrgico. La BD quedÃ³ **sin seed de plataforma** (proj_sst-general se re-siembra
con `seed_project.py` cuando se necesite).

# GATE 0: PASS

---

## Addendum Task 6 (2026-08-18)

- Script canÃƒÂ³nico del health checker pre-Fase 7:
  `scripts/rag_platform/check_pre_phase7_health.py`
- Comando del operador:

```powershell
npm run python -- scripts/rag_platform/check_pre_phase7_health.py --json
```

- CategorÃƒÂ­as reportadas por el checker:
  - `ownership`
  - `orphans`
  - `releases`
  - `runs`
  - `materializations`
  - `vectors`
  - `project_mismatches`
- Contrato operativo:
  - es **read-only**;
  - devuelve `status="blocked"` si alguna categorÃƒÂ­a tiene hallazgos;
  - no repara, no backfillea, no elimina y no muta filas.

