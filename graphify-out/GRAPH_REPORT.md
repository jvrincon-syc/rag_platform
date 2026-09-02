# Graph Report - src  (2026-09-02)

## Corpus Check
- 355 files · ~150,958 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 6971 nodes · 15800 edges · 337 communities (255 shown, 55 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 1191 edges (avg confidence: 0.95)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Document Classification
- Platform Events & Actors
- Indexing Activation & Bundles
- RAG Release Build & Reuse
- Chunk Provenance & PG Settings
- Embedding Ports & Registry
- Normalized Artifacts & Platform Ports
- Observability & Pipeline Events
- Platform Metadata Enrichment
- Artifact Reuse & Build Ledger
- RAG Platform Wiring
- Platform Rebuild & Readiness
- HTTP Envelope & Feature Flags
- Bundle Activation Vectors
- Profile Readiness & Verification
- HTTP Contract & Indexing Router
- Embedding Bundle Repository
- API Auth & Project Access
- Retrieval & Citations
- Engine Registry & Providers
- Text Normalization & Readers
- Schema2 Chunk Assembly
- Community 22
- Community 23
- Community 24
- Community 25
- Community 26
- Community 27
- Community 28
- Community 29
- Community 30
- Community 31
- Community 32
- Community 33
- Community 34
- Community 35
- Community 36
- Community 37
- Community 38
- Community 39
- Community 40
- Community 41
- Community 42
- Community 43
- Community 44
- Community 45
- Community 46
- Community 47
- Community 48
- Community 49
- Community 50
- Community 51
- Community 52
- Community 53
- Community 54
- Community 55
- Community 56
- Community 57
- Community 58
- Community 59
- Community 60
- Community 61
- Community 62
- Community 63
- Community 64
- Community 65
- Community 66
- Community 67
- Community 68
- Community 69
- Community 70
- Community 71
- Community 72
- Community 73
- Community 74
- Community 75
- Community 76
- Community 77
- Community 78
- Community 79
- Community 80
- Community 81
- Community 82
- Community 83
- Community 84
- Community 85
- Community 86
- Community 87
- Community 88
- Community 89
- Community 90
- Community 91
- Community 92
- Community 93
- Community 94
- Community 95
- Community 96
- Community 97
- Community 98
- Community 99
- Community 100
- Community 101
- Community 102
- Community 103
- Community 104
- Community 105
- Community 106
- Community 107
- Community 108
- Community 109
- Community 110
- Community 111
- Community 112
- Community 113
- Community 114
- Community 115
- Community 116
- Community 117
- Community 118
- Community 119
- Community 120
- Community 121
- Community 122
- Community 123
- Community 124
- Community 125
- Community 126
- Community 127
- Community 128
- Community 129
- Community 130
- Community 131
- Community 132
- Community 133
- Community 134
- Community 135
- Community 136
- Community 137
- Community 138
- Community 139
- Community 140
- Community 141
- Community 142
- Community 143
- Community 144
- Community 145
- Community 146
- Community 147
- Community 148
- Community 149
- Community 150
- Community 151
- Community 152
- Community 153
- Community 154
- Community 155
- Community 156
- Community 157
- Community 158
- Community 159
- Community 160
- Community 161
- Community 162
- Community 163
- Community 164
- Community 165
- Community 166
- Community 167
- Community 168
- Community 169
- Community 170
- Community 171
- Community 172
- Community 173
- Community 174
- Community 175
- Community 176
- Community 177
- Community 178
- Community 179
- Community 180
- Community 181
- Community 182
- Community 183
- Community 184
- Community 185
- Community 186
- Community 187
- Community 188
- Community 189
- Community 190
- Community 191
- Community 192
- Community 193
- Community 194
- Community 195
- Community 196
- Community 197
- Community 198
- Community 199
- Community 200
- Community 201
- Community 202
- Community 203
- Community 204
- Community 205
- Community 206
- Community 207
- Community 208
- Community 209
- Community 210
- Community 211
- Community 212
- Community 213
- Community 214
- Community 215
- Community 216
- Community 217
- Community 218
- Community 219
- Community 220
- Community 221
- Community 222
- Community 223
- Community 224
- Community 225
- Community 226
- Community 227
- Community 228
- Community 229
- Community 230
- Community 231
- Community 232
- Community 233
- Community 234
- Community 235
- Community 236
- Community 237
- Community 238
- Community 239
- Community 240
- Community 241
- Community 242
- Community 243
- Community 244
- Community 245
- Community 246
- Community 247
- Community 248
- Community 249
- Community 250
- Community 251
- Community 252
- Community 253
- Community 254
- Community 255
- Community 256
- Community 257
- Community 259
- Community 260
- Community 261
- Community 262
- Community 263
- Community 264
- Community 265
- Community 266
- Community 267
- Community 268
- Community 269
- Community 270
- Community 271
- Community 272
- Community 273
- Community 274
- Community 275
- Community 277
- Community 278
- Community 279
- Community 280
- Community 281
- Community 282
- Community 283
- Community 284
- Community 285
- Community 286
- Community 287
- Community 288
- Community 289
- Community 290
- Community 291
- Community 292
- Community 293
- Community 294
- Community 295
- Community 296
- Community 297
- Community 298
- Community 299
- Community 300
- Community 301
- Community 302
- Community 303
- Community 304
- Community 305
- Community 306
- Community 307
- Community 308
- Community 309
- Community 310
- Community 311

## God Nodes (most connected - your core abstractions)
1. `PlatformId` - 352 edges
2. `StrictModel` - 299 edges
3. `PlatformActor` - 121 edges
4. `IdentityKind` - 90 edges
5. `PlatformAccessPolicy` - 86 edges
6. `build_pipeline_services()` - 82 edges
7. `_build_rag_platform_services()` - 80 edges
8. `EmbeddingProfile` - 64 edges
9. `RagPlatformServices` - 63 edges
10. `ResolvedIndexingProfile` - 54 edges

## Surprising Connections (you probably didn't know these)
- `create_app()` --uses--> `InvalidIdentity`  [INFERRED]
  api/app.py → rag_platform/domain/identity.py
- `PipelineServices` --uses--> `DispatchChatbotQuestionUseCase`  [INFERRED]
  api/dependencies.py → chatbot/application/service.py
- `PipelineServices` --uses--> `ConsumerScope`  [INFERRED]
  api/dependencies.py → core/consumer_scope.py
- `PipelineServices` --uses--> `FeatureFlags`  [INFERRED]
  api/dependencies.py → core/feature_flags.py
- `PipelineServices` --uses--> `ConfiguredBearerAuth`  [INFERRED]
  api/dependencies.py → core/http_auth.py

## Import Cycles
- None detected.

## Communities (337 total, 55 thin omitted)

### Community 0 - "Document Classification"
Cohesion: 0.02
Nodes (162): ClassificationPolicy, ClassifyProjectDocumentUseCase, Protocol, Política de clasificación documental de plataforma (Fase 2). Define el puerto…, Puerto: clasifica un documento en un resultado neutral de plataforma. Las…, Clasifica un documento y valida su tipo contra el catálogo del proyecto. Es…, Clasifica y valida contra el catálogo; devuelve el resultado validado. Args:…, Caso de uso de creación de corpus snapshots (Fase 2). Congela una lista… (+154 more)

### Community 1 - "Platform Events & Actors"
Cohesion: 0.03
Nodes (132): JsonlEventSink, Protocol, Protocol for durable JSONL event sinks., Persist one structured event., Scope one durable document commit., TransactionManager, Frontera de actor de confianza para la superficie de plataforma (Fase 7). El…, CorpusSnapshotRepository (+124 more)

### Community 2 - "Indexing Activation & Bundles"
Cohesion: 0.02
Nodes (119): EmbeddingBundleStale, The embedding bundle no longer matches its source chunk bundle., ActivationResult, _now(), datetime, Roll one lane back to a validated bundle. Raises: IndexingActivationBlocked:…, Outcome of one activation., Activate one indexed bundle. Raises: IndexingActivationBlocked: When any… (+111 more)

### Community 3 - "RAG Release Build & Reuse"
Cohesion: 0.02
Nodes (76): _build_rag_platform_draft(), Cablea ``CreateRagReleaseDraftUseCase`` (postgres o in-memory). El…, PhysicalDistanceMetric, Devuelve el normalizado reutilizable por identidad exacta, o ``None``., Devuelve el embedding bundle sellado reutilizable, o ``None`` (Fase 4). Cierra…, Devuelve el normalizado con la identidad exacta, o ``None``., Registra un normalizado recién construido., Devuelve el snapshot con ese ``manifest_hash``, o ``None`` (idempotencia). (+68 more)

### Community 4 - "Chunk Provenance & PG Settings"
Cohesion: 0.03
Nodes (101): Page and character provenance carried by every chunk., One parent chunk read back from a persisted bundle., SourceParentChunk, SourceSpanRecord, field_serializer, IndexingReadiness, Whether one embedding bundle may be written into a target., PostgresIndexingSettings (+93 more)

### Community 5 - "Embedding Ports & Registry"
Cohesion: 0.04
Nodes (78): ChunkBundleRepository, EmbeddingBundleRepository, EmbeddingEngineRegistry, EmbeddingProfileRepository, EmbeddingRunRepository, Protocol, Application ports for embedding engines, repositories and artifacts., Durable read/write access to ``embedding_runs``. (+70 more)

### Community 6 - "Normalized Artifacts & Platform Ports"
Cohesion: 0.03
Nodes (73): NormalizedArtifactBuilder, NormalizedArtifactRepository, ProjectRawStorage, ProjectRepository, Protocol, Puertos de aplicación de la plataforma RAG (Fase 1). Aquí viven los contratos…, Persistencia de documentos lógicos y sus revisiones inmutables (Fase 2)., Devuelve el documento lógico o ``None``. (+65 more)

### Community 7 - "Observability & Pipeline Events"
Cohesion: 0.03
Nodes (80): measure_duration_ms(), Measure elapsed milliseconds using ``time.perf_counter``., emit_pipeline_event(), BaseException, JsonScalar, Logger, Emit one sanitized structured event for a bundle-first pipeline step., Insert a run, returning the stored row. (+72 more)

### Community 8 - "Platform Metadata Enrichment"
Cohesion: 0.05
Nodes (89): Classification, apply_platform_metadata(), PlatformContextResolutionError, PlatformMetadataContext, InventoryRecord, RuntimeError, Enriquecimiento aditivo del metadata sidecar con contexto de plataforma. La…, Resuelve la identidad de plataforma de cada documento seleccionado o falla… (+81 more)

### Community 9 - "Artifact Reuse & Build Ledger"
Cohesion: 0.04
Nodes (72): ChunkBundleReuseRepository, Protocol, RagBuildRunRepository, Reuso de artefactos por identidad exacta y ledger de build (Fase 3). La…, Consulta de chunk bundles sellados por identidad física exacta (§4.4)., Devuelve el bundle sellado con esa identidad exacta, o ``None``. La identidad…, Consulta de embedding bundles sellados por identidad física exacta (§4)., Devuelve el embedding bundle sellado con esa identidad exacta, o ``None``. La… (+64 more)

### Community 10 - "RAG Platform Wiring"
Cohesion: 0.03
Nodes (56): _build_rag_platform_services(), Resuelve el tope de documentos por build desde el entorno (fail-closed).…, Cablea la superficie tipada única de plataforma para Fase 7 (Task 3 + Task 4).…, _resolve_max_build_documents(), ProjectConfigurationRepository, Deriva las raíces de almacenamiento aisladas de un proyecto., Devuelve las raíces bajo ``data/projects/{project_id}/``., Devuelve el binding permitido o ``None`` si no está en la allowlist. (+48 more)

### Community 11 - "Platform Rebuild & Readiness"
Cohesion: 0.04
Nodes (60): _build_rag_platform_rebuild(), Cablea el rebuild pure-platform (Fase 4 Stage 3) en el composition root.…, EmbeddingIndexingReadinessEvaluator, Decide whether a sealed bundle may be handed to Indexing., ChunkBundleNotFound, The source chunk bundle is not registered in the durable ledger., canonical_json(), Serialize a payload deterministically for hashing. Args: payload: Any JSON-… (+52 more)

### Community 12 - "HTTP Envelope & Feature Flags"
Cohesion: 0.04
Nodes (77): http_error(), HTTPException, Build an ``HTTPException`` already carrying the shared envelope., ConsumerScope, Server-controlled consumer scope for activation and rollback. Until…, The scope a mutation is authorized to act on, resolved server-side., FeatureFlags, Explicit feature flags for the bundle-first rollout. The legacy paths stay… (+69 more)

### Community 13 - "Bundle Activation Vectors"
Cohesion: 0.04
Nodes (54): Composed, Identifier, Activate one bundle and supersede prior active rows of the same documents., Deactivate the current bundle and reactivate a validated previous one., Count active rows for one bundle in one lane., Insert inactive vector rows for one embedding bundle., Immutable embedding profile resolved for one corpus lane., ResolvedIndexingProfile (+46 more)

### Community 14 - "Profile Readiness & Verification"
Cohesion: 0.03
Nodes (52): Return the readiness verdict and every blocking reason., Return one profile or raise ``EmbeddingProfileNotFound``., Return every registered profile, including blocked ones., Promote one profile after an explicit compatibility verification., ProfileVerificationRequest, ProfileVerificationResult, ValidationCheck, Prove the profile revision against the engine or an explicit attestation. (+44 more)

### Community 15 - "HTTP Contract & Indexing Router"
Cohesion: 0.04
Nodes (74): ErrorBodySchema, ErrorEnvelopeSchema, Shared HTTP contract helpers: error envelope and page envelope. The envelope…, Body of the shared error envelope., Every non-2xx response uses this envelope., activate_bundle(), create_run(), get_activate_use_case() (+66 more)

### Community 16 - "Embedding Bundle Repository"
Cohesion: 0.03
Nodes (49): Insert or update an unsealed bundle., Persist the sealed bundle; refuses to overwrite a sealed row., Return one bundle or raise ``EmbeddingBundleNotFound``., Return an existing bundle for the deterministic identity tuple., Update the operational readiness projection of a sealed bundle. Sealing freezes…, EmbeddingBundleNotFound, The embedding bundle does not exist., EmbeddingBundle (+41 more)

### Community 17 - "API Auth & Project Access"
Cohesion: 0.05
Nodes (67): get_authenticated_principal(), Return the already-authenticated principal bound to the request., Authorize the authenticated principal for a single project., require_project_access(), create_run(), get_bundle(), get_bundle_indexing_readiness(), get_bundle_validation() (+59 more)

### Community 18 - "Retrieval & Citations"
Cohesion: 0.03
Nodes (48): _build_source_url(), Construct a public URL for the raw document, if configured., _resolve_document_name(), Return the closest child nodes by full-text rank., Return parent evidence keyed by ``parent_node_id``., Reorder ``candidates`` by true relevance to ``query``; return top_n., Insert or update one retrieval profile., Return one profile or raise ``RetrievalProfileNotFound``. (+40 more)

### Community 19 - "Engine Registry & Providers"
Cohesion: 0.07
Nodes (47): _engine_error_reason(), indexing_profile_from(), Registry that binds one durable embedding profile to exactly one engine. The…, Translate a provider runtime failure into a sanitized domain error. Provider…, Adapt a durable embedding profile to the legacy provider constructor., translate_engine_error(), EmbeddingBatch, EmbeddingCapabilities (+39 more)

### Community 20 - "Text Normalization & Readers"
Cohesion: 0.08
Nodes (50): normalize_indexable_text(), normalize_text(), RemovedSpan, BaseModel, ReadResult, _append_once(), _document_confidence(), _engine_version() (+42 more)

### Community 21 - "Schema2 Chunk Assembly"
Cohesion: 0.08
Nodes (53): Presence and non-invented OCR provenance from validated sidecars., ValidatedSidecars, Build a normalized chunking bundle from already loaded Schema 2 artifacts., Schema2BundleAssembler, NormalizedDocumentFactory, Any, Document, MetadataArtifact (+45 more)

### Community 22 - "Community 22"
Cohesion: 0.03
Nodes (68): $ref, title, type, $ref, minLength, title, type, minLength (+60 more)

### Community 23 - "Community 23"
Cohesion: 0.06
Nodes (43): BuiltBundle, EmbeddingBundleBuilder, EmbeddingBundleValidator, _now(), datetime, Build, validate and gate sealed embedding bundles. The builder is the only…, Embed one chunk bundle and seal the resulting artifacts atomically., Embed, stage, validate, promote and seal one bundle. Raises:… (+35 more)

### Community 24 - "Community 24"
Cohesion: 0.06
Nodes (41): IndexingPort, Protocol, Index a normalized, approved document., NodeRepository, NormalizedDocumentRepository, ProfileRegistry, ProfileResolver, BaseNode (+33 more)

### Community 25 - "Community 25"
Cohesion: 0.05
Nodes (51): _build_chatbot_webhook_dispatcher(), _build_faq_resolver(), _build_idempotency_store(), build_pipeline_services(), build_pipeline_services_from_env(), _default_gui_auth_registry_path(), _emit_startup_observability(), PipelineServices (+43 more)

### Community 26 - "Community 26"
Cohesion: 0.07
Nodes (52): dispatch_question(), _emit_request_event(), get_actor(), get_dispatch_use_case(), list_rag_releases(), _parse_id(), Exception, Request (+44 more)

### Community 27 - "Community 27"
Cohesion: 0.05
Nodes (42): LexicalFallbackNotAllowed, Exception, Domain errors for retrieval, each carrying its public code., The retrieval profile does not exist., Vector retrieval is blocked and the profile forbids lexical-only answers., Base class for retrieval domain errors with a stable public code., RetrievalDomainError, RetrievalProfileNotFound (+34 more)

### Community 28 - "Community 28"
Cohesion: 0.06
Nodes (37): _open_postgres_connection(), Resolve the requested persistence mode from the environment.…, Open a psycopg2 connection, failing closed on any driver error., _resolve_persistence_mode(), create_app(), FastAPI, Path, build_run_service() (+29 more)

### Community 29 - "Community 29"
Cohesion: 0.06
Nodes (26): Return every registered chunk bundle., Persist one chunk bundle identity so downstream FKs can reference it., Return one registered chunk bundle or raise ``ChunkBundleNotFound``., ChunkBundleRef, Durable identity of one registered chunk bundle. ``project_id`` es…, FilesystemChunkBundleCatalogRepository, HybridChunkBundleRepository, _is_metadata_artifact() (+18 more)

### Community 30 - "Community 30"
Cohesion: 0.08
Nodes (35): ChunkingError, ChunkingProfileError, ChunkInvariantError, ValueError, Raised when chunks cannot preserve their required provenance., Base error for invalid chunking domain data., Raised when a chunking profile is internally inconsistent., Enum (+27 more)

### Community 31 - "Community 31"
Cohesion: 0.07
Nodes (30): ParentSegment, Contiguous subset of one parent text with stable relative offsets., Protocol, Counts canonical tokens without exposing a tokenizer implementation., Return the canonical token count for non-empty chunk text., Builds validated structural chunks from a normalized document., StructuralChunkerPort, TokenCounterPort (+22 more)

### Community 32 - "Community 32"
Cohesion: 0.08
Nodes (37): ChatbotReleaseRetrievalPort, ChatbotWebhookDeliveryPort, Protocol, Ports used by the chatbot dispatch use case., Delivers the question + chunks payload to the downstream webhook., Deliver one payload and return safe transport metadata., Search one published release without relying on the active legacy lane., Return release-scoped evidence or fail closed when the lane is ambiguous. (+29 more)

### Community 33 - "Community 33"
Cohesion: 0.07
Nodes (29): _env_bool(), _env_int(), LlamaSettings, load_llama_settings(), Any, field_validator, model_validator, ParsedItemsPage (+21 more)

### Community 34 - "Community 34"
Cohesion: 0.08
Nodes (48): get_project_configuration(), get_release_build_status(), get_variant_matrix(), list_chunking_profiles(), list_processing_profiles(), normalize_project_documents(), Rutas HTTP de la plataforma RAG multi-proyecto (Fase 7). Adaptador HTTP…, submit_revision_review_decision() (+40 more)

### Community 35 - "Community 35"
Cohesion: 0.12
Nodes (45): ArtifactHash, BundleManifest, compute_content_hash(), detect_extension(), detect_mime_type(), infer_category(), iter_files(), datetime (+37 more)

### Community 36 - "Community 36"
Cohesion: 0.12
Nodes (18): BaseHTTPRequestHandler, HTTPStatus, build_session_cookie(), parse_cookie(), _is_health_check_route(), Phase1GuiHandler, BaseException, Devuelve la metadata pública de la sesión vigente o 401. (+10 more)

### Community 37 - "Community 37"
Cohesion: 0.11
Nodes (19): ChildChunkBuilder, ChunkingProfile, Sentence-like text unit with stable token and character ranges., Builds retrieval children with bounded semantic overlap., Fold the section heading into a child's context prefix (opt-in). Only profiles…, SentenceUnit, ParentChunkBuilder, ChunkingProfile (+11 more)

### Community 38 - "Community 38"
Cohesion: 0.08
Nodes (29): ChatbotReleaseLane, ChatbotReleaseRetrievalResult, One published release resolved to exactly one retrieval lane., The release lane plus the evidence retrieved inside that release only., ChatbotReleaseLaneUnavailable, The release does not resolve exactly one active retrieval lane., _cosine(), _evidence_from_node() (+21 more)

### Community 39 - "Community 39"
Cohesion: 0.06
Nodes (31): AuthenticatedPrincipal, BearerCredential, ConfiguredBearerAuth, HttpAuthNotConfigured, HttpProjectScopeForbidden, PersistedBearerCredential, PersistedBearerRegistry, project_in_scope() (+23 more)

### Community 40 - "Community 40"
Cohesion: 0.08
Nodes (35): build_chatbot_runtime(), build_chatbot_runtime_from_env(), ChatbotRuntime, create_chatbot_runtime_app(), FastAPI, Path, ASGI application factory for dedicated SST chatbot traffic., Resolve settings from env vars and build the dedicated chatbot runtime. (+27 more)

### Community 41 - "Community 41"
Cohesion: 0.06
Nodes (28): Protocol, Persistencia durable del estado de los intentos de build asíncrono., Inserta un job nuevo (estado inicial ``queued``)., Persiste una transición de estado del job (running/succeeded/failed)., Devuelve el job por id o lanza ``ReleaseBuildJobNotFound``., Devuelve el job más reciente de la release, o ``None`` si no hay ninguno., ReleaseBuildJobRepository, Enum (+20 more)

### Community 42 - "Community 42"
Cohesion: 0.06
Nodes (26): DefaultEmbeddingEngineRegistry, _mock_revision(), Return ``unknown_revision``: the Voyage API exposes no model revision., Return the deterministic mock revision., Resolve engines by exact durable profile, with no provider fallback., Return the engine allowed to embed documents for this profile., Return the engine allowed to embed queries for this profile. With…, Return operational availability without raising. (+18 more)

### Community 43 - "Community 43"
Cohesion: 0.07
Nodes (23): RagVariantRepository, Persistencia de variantes RAG con unicidad de receta mientras activas., Devuelve la variante activa con ese fingerprint, o ``None``., Inserta una variante o lanza ``DuplicateVariantRecipe``., Devuelve la variante por id o lanza ``RagVariantNotFound``., Devuelve las variantes del proyecto en orden estable (por id)., Devuelve la variante o lanza ``RagVariantNotFound``., Devuelve la variante o lanza un error de dominio si no existe. (+15 more)

### Community 44 - "Community 44"
Cohesion: 0.07
Nodes (36): Logging helpers for backend modules., _configure_logger(), configure_structured_logging(), _extra_fields(), get_logger(), _has_named_handler(), _json_default(), Logger (+28 more)

### Community 45 - "Community 45"
Cohesion: 0.10
Nodes (34): HTMLParser, _form_labels_from_markdown(), _forms_from_markdown_pages(), _HtmlTableParser, _llama_page_metadata(), _page_parse_confidence(), _page_warnings(), parsed_document_to_read_result() (+26 more)

### Community 46 - "Community 46"
Cohesion: 0.06
Nodes (26): execute_normalize_pipeline(), Path, Adaptador infra del puerto ``ProjectDocumentNormalizer``., Registra en el read-model cada revisión cuyo markdown quedó en disco.…, Corre ``run_pipeline`` raw→normalized con promote atómico y devuelve el…, RunPipelineProjectNormalizer, _as_metric(), PostgresSealedEmbeddingBundleRepository (+18 more)

### Community 47 - "Community 47"
Cohesion: 0.08
Nodes (23): ChunkingProfileNotFound, ProcessingProfileNotFound, El perfil de procesamiento referenciado por la receta no existe., El perfil de chunking referenciado por la receta no existe., ChunkingProfile, DocumentProcessingProfile, Receta de procesamiento (parseo/normalización) con fingerprint inmutable.…, Receta de chunking con fingerprint inmutable. Un cambio de chunking reindexa… (+15 more)

### Community 48 - "Community 48"
Cohesion: 0.10
Nodes (30): _choose(), classify_document(), _classify_legacy(), _confidence(), _conflicts(), _field_text(), _first_prediction(), _normalize() (+22 more)

### Community 49 - "Community 49"
Cohesion: 0.06
Nodes (39): properties, anyOf, default, title, anyOf, default, title, title (+31 more)

### Community 50 - "Community 50"
Cohesion: 0.07
Nodes (27): ChunkingProfileRepository, ProcessingProfileRepository, ChunkingProfile, Persistencia de perfiles de procesamiento por proyecto., Devuelve el perfil o lanza ``ProcessingProfileNotFound``., Devuelve los perfiles de procesamiento del proyecto (orden estable)., Persistencia de perfiles de chunking por proyecto., Devuelve el perfil o lanza ``ChunkingProfileNotFound``. (+19 more)

### Community 51 - "Community 51"
Cohesion: 0.13
Nodes (29): FormControl, FormLabel, CandidateRegion, CoverageAnalyzer, CoverageAssessment, _is_logo_like(), _page_area(), Any (+21 more)

### Community 52 - "Community 52"
Cohesion: 0.14
Nodes (34): load_runtime_llama_settings(), load_secrets_env(), Path, AsgiBridge, Any, Serve an ASGI application from the existing ``http.server`` GUI backend. The…, Call an ASGI application synchronously from a blocking HTTP handler., build_status_payload() (+26 more)

### Community 53 - "Community 53"
Cohesion: 0.15
Nodes (35): ChangeHistoryEntry, _augment_split_sst_suffix(), _code_field(), extract_document_control(), _extract_history(), _field_from_candidates(), _field_from_primary_page(), _find_candidates() (+27 more)

### Community 54 - "Community 54"
Cohesion: 0.08
Nodes (19): IndexingMaterializationRepository, Marca una materialización como ``FAILED`` con un código observable., Repositorio del lifecycle inmutable de materializaciones (ADR-007 §3)., Devuelve la materialización sellada con esa identidad, o ``None``., Abre una materialización en estado ``WRITING``., Sella una materialización ``WRITING`` fijando checksum y conteos., IndexingMaterialization, Materialización física de vectores de un bundle en un target (ADR-007 §3).… (+11 more)

### Community 55 - "Community 55"
Cohesion: 0.11
Nodes (25): PageRasterizer, BBox, Path, RuntimeError, RasterizationCapabilityError, RasterRegion, _render_with_pdfium(), _append_unique_lines() (+17 more)

### Community 56 - "Community 56"
Cohesion: 0.06
Nodes (36): properties, anyOf, default, title, anyOf, default, title, estimated (+28 more)

### Community 57 - "Community 57"
Cohesion: 0.06
Nodes (36): properties, anyOf, default, title, anyOf, default, title, estimated (+28 more)

### Community 58 - "Community 58"
Cohesion: 0.10
Nodes (33): create_run(), get_run(), get_validation(), _http_error(), list_children(), list_parents(), list_profiles(), list_run_documents() (+25 more)

### Community 59 - "Community 59"
Cohesion: 0.06
Nodes (35): anyOf, default, title, properties, pattern, title, type, pattern (+27 more)

### Community 60 - "Community 60"
Cohesion: 0.07
Nodes (21): _build_rag_platform_validate(), NullTransactionManager, Cablea ``ValidateRagReleaseUseCase`` (postgres o in-memory)., Transaction manager used when no database connection is configured., Return a no-op scope., PsycopgTransactionManager, Commit on success, roll back on any exception., Scope one durable commit around a psycopg connection. (+13 more)

### Community 61 - "Community 61"
Cohesion: 0.15
Nodes (9): Builds semantic structural blocks from normalized markdown plus sidecars., StructuralParser, NormalizedDocumentBundle, Pre-structural normalized document consumed before Task 3 block creation., MarkdownAdapter, MarkdownRegion, A contiguous content region with original markdown coordinates., Extracts structural markdown regions without turning pages into boundaries. (+1 more)

### Community 62 - "Community 62"
Cohesion: 0.06
Nodes (34): items, title, type, properties, $ref, anyOf, default, title (+26 more)

### Community 63 - "Community 63"
Cohesion: 0.14
Nodes (31): _adapt_inventory(), _adapt_metadata(), _adapt_ocr(), _adapt_pages(), _adapt_path(), adapt_v1_to_v2(), _is_absolute(), _legacy_confidence() (+23 more)

### Community 64 - "Community 64"
Cohesion: 0.11
Nodes (18): IdempotencyRecord, IdempotencyStatus, Enum, str, Estado durable de un registro de idempotencia., Registro durable de una petición de mutación idempotente. ``result_json`` solo…, Resultado de un intento de reserva. ``fresh`` indica que este llamador ganó la…, Reserva atómicamente ``record`` o devuelve el existente. Debe ser atómica… (+10 more)

### Community 65 - "Community 65"
Cohesion: 0.15
Nodes (7): ChunkingRunService, ChunkingRunState, Any, Path, Application service for local chunking runs and persisted inspection., Return the canonical local structural chunking profile., Return v1's recipe with opt-in section-context propagation enabled. Identical…

### Community 66 - "Community 66"
Cohesion: 0.11
Nodes (23): HttpAuthError, HttpAuthInvalidCredentials, HttpAuthPrincipalExists, HttpAuthRequired, Exception, The request supplied a bearer token that is not configured., A local GUI registration tried to reuse an existing principal id., Base error for the HTTP authentication boundary. (+15 more)

### Community 67 - "Community 67"
Cohesion: 0.07
Nodes (31): anyOf, default, default, minimum, title, type, properties, anyOf (+23 more)

### Community 68 - "Community 68"
Cohesion: 0.10
Nodes (21): ListProjectEmbeddingEnginesUseCase, ProjectEmbeddingEngineReader, Protocol, Caso de uso read-only: motores de embedding materializados por proyecto. Expone…, Puerto de solo lectura del read-model de motores por proyecto., Devuelve los motores con artefactos materializados del proyecto. Args:…, Orden determinista y estable, independiente del adaptador., Lista los motores de embedding materializados de un proyecto. (+13 more)

### Community 69 - "Community 69"
Cohesion: 0.15
Nodes (21): LayoutBlock, LayoutPage, model_validator, _as_iterable(), _bbox_from_coordinates(), _bbox_from_object(), _cropbox(), _extract_text() (+13 more)

### Community 70 - "Community 70"
Cohesion: 0.07
Nodes (30): anyOf, default, minLength, title, type, type, properties, block_id (+22 more)

### Community 71 - "Community 71"
Cohesion: 0.07
Nodes (18): _bge_revision(), _hub_snapshot_revision(), Read the resolved Hugging Face commit of a BGE runtime. FlagEmbedding exposes…, Resolve the cached Hugging Face snapshot commit for one model name., EmbeddingProvider, DistanceMetric, Protocol, Return the configured retry budget for retryable provider errors. (+10 more)

### Community 72 - "Community 72"
Cohesion: 0.11
Nodes (16): ChunkingProfile, Return the deterministic chunk bundle for one document and profile., ChunkBundle, Validated parent-child output for a single normalized document., Return a deterministic fingerprint of the complete chunk output., Return the complete canonical bundle payload for traceability., Ensure every parent references structural blocks from the input document., ElementAwareNodeParserAdapter (+8 more)

### Community 73 - "Community 73"
Cohesion: 0.07
Nodes (28): title, type, title, type, minLength, title, type, anyOf (+20 more)

### Community 74 - "Community 74"
Cohesion: 0.07
Nodes (27): additionalProperties, properties, required, title, type, title, type, minLength (+19 more)

### Community 75 - "Community 75"
Cohesion: 0.08
Nodes (27): items, title, type, items, $ref, items, title, type (+19 more)

### Community 76 - "Community 76"
Cohesion: 0.07
Nodes (27): additionalProperties, properties, required, title, type, title, type, minLength (+19 more)

### Community 77 - "Community 77"
Cohesion: 0.08
Nodes (27): items, title, type, minLength, title, type, items, $ref (+19 more)

### Community 78 - "Community 78"
Cohesion: 0.10
Nodes (15): Return one target or raise ``LookupError``., InMemoryIndexingTargetRepository, Deterministic ``indexing_targets`` double., Return one target or raise ``LookupError``., Return every registered target., PostgresIndexingTargetRepository, Read ``indexing_targets``, the authority over physical vector tables., Return one target or raise ``LookupError``. (+7 more)

### Community 79 - "Community 79"
Cohesion: 0.17
Nodes (16): ChunkingDocumentNotFoundError, ChunkingIdempotencyConflictError, ChunkingParentNotFoundError, ChunkingProfileNotFoundError, ChunkingRunRequest, ValueError, Raised when a requested document id is unknown., Raised when a requested parent id is unknown. (+8 more)

### Community 80 - "Community 80"
Cohesion: 0.16
Nodes (8): build_expired_cookie(), GuiAuthCoordinator, GuiSession, GuiSessionStore, datetime, Sesión GUI local por cookie opaca para usuarios locales con contraseña., Store en memoria de proceso de sesiones GUI, thread-safe., Une directorio local de usuarios, bearer interno y cookie GUI.

### Community 81 - "Community 81"
Cohesion: 0.08
Nodes (24): properties, anyOf, default, title, title, type, anyOf, default (+16 more)

### Community 82 - "Community 82"
Cohesion: 0.08
Nodes (24): anyOf, default, properties, anyOf, default, title, anyOf, default (+16 more)

### Community 83 - "Community 83"
Cohesion: 0.08
Nodes (24): properties, default, title, type, anyOf, default, title, $ref (+16 more)

### Community 84 - "Community 84"
Cohesion: 0.08
Nodes (24): LlamaCloudMetadata, additionalProperties, title, type, additionalProperties, properties, required, title (+16 more)

### Community 85 - "Community 85"
Cohesion: 0.08
Nodes (24): anyOf, default, title, minLength, title, type, title, type (+16 more)

### Community 86 - "Community 86"
Cohesion: 0.08
Nodes (24): properties, estimated, measured, unavailable, enum, title, type, anyOf (+16 more)

### Community 87 - "Community 87"
Cohesion: 0.15
Nodes (13): EvidenceBuilder, Any, Vector-primary fusion: dense remains the authority, lexical refines. Rules: 1.…, reciprocal_rank_fusion(), RetrievedCandidate, vector_primary_hybrid_fusion(), ParentExpansionService, _cosine() (+5 more)

### Community 88 - "Community 88"
Cohesion: 0.09
Nodes (22): additionalProperties, corpus_version, document_id, document_name, extraction_method, handwriting, ocr_confidence, page_count (+14 more)

### Community 89 - "Community 89"
Cohesion: 0.09
Nodes (23): additionalProperties, title, type, additionalProperties, required, title, type, $defs (+15 more)

### Community 90 - "Community 90"
Cohesion: 0.09
Nodes (23): minLength, title, type, anyOf, default, title, anyOf, default (+15 more)

### Community 91 - "Community 91"
Cohesion: 0.14
Nodes (18): IdempotencyKey, build_release(), publish_release(), Ejecuta un comando de release una sola vez por clave/fingerprint. Centraliza la…, retire_release(), _run_idempotent(), validate_release(), RetireReleaseRequestSchema (+10 more)

### Community 92 - "Community 92"
Cohesion: 0.09
Nodes (22): minLength, title, type, minLength, title, type, $ref, minLength (+14 more)

### Community 93 - "Community 93"
Cohesion: 0.09
Nodes (22): anyOf, default, $ref, anyOf, default, $ref, title, OcrWord (+14 more)

### Community 94 - "Community 94"
Cohesion: 0.13
Nodes (20): BinaryIO, _copy_request_body_to_tempfile(), _field_value(), JsonBodyTooLargeError, _multipart_boundary(), _parse_content_disposition(), _parse_content_length_header(), _parse_multipart_form() (+12 more)

### Community 95 - "Community 95"
Cohesion: 0.18
Nodes (21): paginate(), Return one page of an already-materialized sequence., list_profiles(), list_runtime(), list_targets(), _get(), ItemT, create_release_draft() (+13 more)

### Community 96 - "Community 96"
Cohesion: 0.13
Nodes (7): BgeEmbeddingProvider, BgeRuntimeModel, _chunks(), _load_bge_model(), DistanceMetric, Protocol, Encode texts with FlagEmbedding.

### Community 97 - "Community 97"
Cohesion: 0.18
Nodes (18): ProviderAuthenticationError, ProviderError, ProviderJobFailedError, ProviderMalformedResultError, ProviderQuotaError, ProviderRateLimitError, ProviderTimeoutError, ProviderUnsupportedFeatureError (+10 more)

### Community 98 - "Community 98"
Cohesion: 0.10
Nodes (20): anyOf, default, $ref, FormLabel, additionalProperties, properties, title, type (+12 more)

### Community 99 - "Community 99"
Cohesion: 0.11
Nodes (20): items, minLength, title, type, items, items, title, type (+12 more)

### Community 100 - "Community 100"
Cohesion: 0.10
Nodes (20): anyOf, default, title, anyOf, default, title, detected, not_detected (+12 more)

### Community 101 - "Community 101"
Cohesion: 0.10
Nodes (20): anyOf, default, title, anyOf, default, title, detected, not_detected (+12 more)

### Community 102 - "Community 102"
Cohesion: 0.28
Nodes (4): FilesystemChunkBundleRepository, Any, Path, Persist chunk bundles under one filesystem root with fail-closed promotion.

### Community 103 - "Community 103"
Cohesion: 0.11
Nodes (11): ProviderEngineAdapter, Normalization, Adapt an existing indexing embedding provider to the engine port. Every…, Return the provider name the engine implements., Return the model the engine loaded., Return the dense vector dimension produced by the engine., Return the normalization the engine applies to its vectors., Return whether the engine can embed queries. (+3 more)

### Community 104 - "Community 104"
Cohesion: 0.11
Nodes (19): properties, anyOf, default, minimum, title, type, anyOf, default (+11 more)

### Community 105 - "Community 105"
Cohesion: 0.11
Nodes (19): enum, title, type, document_type, acta, anexo, capacitacion, formulario (+11 more)

### Community 106 - "Community 106"
Cohesion: 0.11
Nodes (19): properties, anyOf, default, minimum, title, type, anyOf, default (+11 more)

### Community 107 - "Community 107"
Cohesion: 0.11
Nodes (19): additionalProperties, required, title, type, $defs, ConfidenceMetric, Evidence, Observation (+11 more)

### Community 108 - "Community 108"
Cohesion: 0.12
Nodes (12): operational_settings(), Load operational settings from the environment, semantics from the profile.…, EmbeddingSettings, _env_bool(), _env_int(), _env_optional_int(), Any, field_validator (+4 more)

### Community 109 - "Community 109"
Cohesion: 0.14
Nodes (6): _local_snapshot(), OnnxBgeQueryEngine, Normalization, ONNX query-embedding engine for BGE-M3 dense vectors. The BGE-M3 dense query…, Embeds queries with BGE-M3's ONNX dense pass; matches the durable bge profile., Load the ONNX session + tokenizer now (cheap: ~1s) so the first query pays…

### Community 110 - "Community 110"
Cohesion: 0.27
Nodes (15): _block_bbox(), _block_id(), _block_text(), _boilerplate_region(), BoilerplateMatch, BoilerplateResult, build_indexable_text(), detect_boilerplate() (+7 more)

### Community 111 - "Community 111"
Cohesion: 0.11
Nodes (18): anyOf, default, properties, anyOf, default, minimum, title, type (+10 more)

### Community 112 - "Community 112"
Cohesion: 0.12
Nodes (18): type, additionalProperties, title, type, properties, fingerprints, run_id, summary (+10 more)

### Community 113 - "Community 113"
Cohesion: 0.18
Nodes (12): AsgiResponse, One buffered ASGI response., Forward one request into the ASGI app and buffer the response., load_review_decisions(), Path, ReviewDecision, save_review_decision(), _write_json_atomic() (+4 more)

### Community 114 - "Community 114"
Cohesion: 0.12
Nodes (17): properties, title, type, minLength, title, type, bottom, coordinate_system (+9 more)

### Community 115 - "Community 115"
Cohesion: 0.13
Nodes (17): required, corpus_version, document_id, document_name, generated_at, pipeline_version, schema_version, source_relpath (+9 more)

### Community 116 - "Community 116"
Cohesion: 0.12
Nodes (17): properties, title, type, minLength, title, type, bottom, coordinate_system (+9 more)

### Community 117 - "Community 117"
Cohesion: 0.12
Nodes (17): properties, title, type, minLength, title, type, bottom, coordinate_system (+9 more)

### Community 118 - "Community 118"
Cohesion: 0.15
Nodes (13): _hash_key(), idempotency_request_fingerprint(), IdempotencyGuard, IdempotencyResult, _now(), Any, datetime, Idempotencia durable de mutaciones de release (Fase 7). Las mutaciones de… (+5 more)

### Community 119 - "Community 119"
Cohesion: 0.12
Nodes (16): minLength, title, type, title, type, properties, control_id, control_type (+8 more)

### Community 120 - "Community 120"
Cohesion: 0.12
Nodes (16): title, type, properties, minLength, title, type, items, title (+8 more)

### Community 121 - "Community 121"
Cohesion: 0.12
Nodes (15): additionalProperties, additionalProperties, required, title, type, $defs, ConfidenceMetric, InventoryRecord (+7 more)

### Community 122 - "Community 122"
Cohesion: 0.12
Nodes (16): items, title, type, additionalProperties, type, items, conflicts, review_reasons (+8 more)

### Community 123 - "Community 123"
Cohesion: 0.13
Nodes (16): $defs, Evidence, MeasuredValue, Observation, additionalProperties, type, status, value (+8 more)

### Community 124 - "Community 124"
Cohesion: 0.13
Nodes (16): additionalProperties, required, title, type, $defs, BBox, Evidence, additionalProperties (+8 more)

### Community 125 - "Community 125"
Cohesion: 0.12
Nodes (16): properties, minimum, title, type, byte_size, relpath, schema_version, sha256 (+8 more)

### Community 126 - "Community 126"
Cohesion: 0.15
Nodes (16): required, required, artifact_hashes, byte_size, document_id, document_status, normalized_base, processing_fingerprint (+8 more)

### Community 127 - "Community 127"
Cohesion: 0.16
Nodes (8): Decisión operacional de revisión, independiente de la membresía en un snapshot., Persiste una decisión del operador., Devuelve la última decisión por revisión para un proyecto., RevisionReviewDecisionRecord, InMemoryRevisionReviewDecisionRepository, Decisiones operacionales de revisión en memoria (Task 3, tests/dry-run)., PostgresRevisionReviewDecisionRepository, Reads and writes ``source_document_revision_review_decisions`` (Task 3).

### Community 128 - "Community 128"
Cohesion: 0.17
Nodes (8): Preload BGE-M3 so the first real chat request pays no cold load. No-op unless a…, BgeReranker, BgeScoringModel, Protocol, BGE-M3 cross-score reranker: real relevance judgment over the deduped pool.…, Score query/passage pairs (FlagEmbedding ``BGEM3FlagModel`` API)., Reorders a deduped candidate pool by BGE-M3's combined relevance score., Force the (shared) BGE-M3 load now so the first real request pays no ~13s cold…

### Community 129 - "Community 129"
Cohesion: 0.13
Nodes (15): properties, detected, not_detected, not_evaluated, status, value_raw, enum, title (+7 more)

### Community 130 - "Community 130"
Cohesion: 0.14
Nodes (15): failed, needs_review, pending, processed, enum, title, type, enum (+7 more)

### Community 131 - "Community 131"
Cohesion: 0.13
Nodes (15): $ref, $ref, anyOf, default, title, properties, deskew, handwriting (+7 more)

### Community 132 - "Community 132"
Cohesion: 0.13
Nodes (15): $ref, minLength, title, type, anyOf, default, title, properties (+7 more)

### Community 133 - "Community 133"
Cohesion: 0.13
Nodes (15): properties, title, type, minLength, title, type, normalized_base, processing_fingerprint (+7 more)

### Community 134 - "Community 134"
Cohesion: 0.19
Nodes (15): patch, create_project(), get_project(), update_project(), update_project_configuration(), CreateProjectRequestSchema, project_to_schema(), ProjectSchema (+7 more)

### Community 135 - "Community 135"
Cohesion: 0.22
Nodes (9): _digest(), Any, Path, PhysicalDistanceMetric, Recomputa los checksums del artefacto sellado y los compara. Returns: ``True``…, Adaptador de sellado content-addressed de embeddings por proyecto., Sella un embedding bundle de forma atómica e idempotente. Args: project_id:…, SealedEmbeddingStore (+1 more)

### Community 136 - "Community 136"
Cohesion: 0.18
Nodes (9): CrossEncoderScorer, LightCrossEncoderReranker, Protocol, Lightweight cross-encoder reranker (bge-reranker-base) as a fast alternative to…, Score query/passage pairs (FlagEmbedding ``FlagReranker`` API)., Reorders a deduped candidate pool by a single cross-encoder's relevance score., Force the model load now so the first real request pays no cold load., Return the local HF-cache snapshot dir for ``model_name``, or the name… (+1 more)

### Community 137 - "Community 137"
Cohesion: 0.14
Nodes (8): ArtifactRefs, Relative artifact locations plus their checksums., Return the vector artifact path, relative to the artifact root., Return the chunk map path, relative to the artifact root., Return the manifest path, relative to the artifact root., Return sha256 checksums keyed by artifact file name., Return the stored numpy dtype name., Return the stored vector shape as ``"rows x columns"``.

### Community 138 - "Community 138"
Cohesion: 0.19
Nodes (9): EmbeddingProviderUnavailableError, RuntimeError, Embedding provider runtime is not configured., CohereEmbeddingProvider, EmbeddingProfileMismatchError, ValueError, Embedding profile is incompatible with the target store., Embedding provider name is not registered. (+1 more)

### Community 139 - "Community 139"
Cohesion: 0.14
Nodes (14): PlatformArtifactProvenance, additionalProperties, description, properties, title, type, rag_variant_id, semantic_recipe_fingerprint (+6 more)

### Community 140 - "Community 140"
Cohesion: 0.14
Nodes (14): PageBlock, RemovedSpan, extraction_method, text, additionalProperties, required, title, type (+6 more)

### Community 141 - "Community 141"
Cohesion: 0.15
Nodes (14): items, title, type, items, type, headers, rows, warnings (+6 more)

### Community 142 - "Community 142"
Cohesion: 0.14
Nodes (13): get_actor_provider(), get_idempotency_store(), get_platform_services(), Request, Devuelve la superficie de aplicaciÃ³n de plataforma cableada., Devuelve el proveedor de actor derivado del principal autenticado., Devuelve el almacÃ©n durable de idempotencia (autoridad: PostgreSQL)., get_actor() (+5 more)

### Community 143 - "Community 143"
Cohesion: 0.22
Nodes (9): Artefacto de chunking sellado, content-addressed y propiedad del proyecto. Su…, SealedChunkBundle, _digest(), Any, Path, Adaptador de sellado content-addressed por proyecto., Sella un chunk bundle de forma atómica e idempotente. Args: project_id:…, SealedChunkStore (+1 more)

### Community 144 - "Community 144"
Cohesion: 0.20
Nodes (9): FaqMatch, FaqResolver, normalize(), Path, Direct-FAQ resolver: a fast lexical/fuzzy shortcut checked BEFORE the BGE…, A resolved FAQ hit: the curated answer plus audit metadata., Frontmatter normalization: lowercase, trim, strip diacritics + punctuation,…, Fuzzy/lexical FAQ lookup over the curated question set. (+1 more)

### Community 145 - "Community 145"
Cohesion: 0.26
Nodes (8): PageTraceResolution, Resolved page traces or a fail-closed provenance warning., Resolve Markdown character ranges to source pages without guessing., Prefer explicit page markers, then require unique sequential text alignment., SourceSpanResolver, PageTrace, Literal page content and its character range in normalized Markdown., PageRecord

### Community 146 - "Community 146"
Cohesion: 0.18
Nodes (3): _deterministic_vector(), DeterministicEmbeddingProvider, DistanceMetric

### Community 147 - "Community 147"
Cohesion: 0.26
Nodes (9): ProviderUsage, Protocol, UsageLedger, _add_usage(), JsonlUsageLedger, Any, Path, summarize_usage_ledger() (+1 more)

### Community 148 - "Community 148"
Cohesion: 0.17
Nodes (13): $defs, Evidence, FormGroup, additionalProperties, title, type, additionalProperties, required (+5 more)

### Community 149 - "Community 149"
Cohesion: 0.15
Nodes (13): minLength, title, type, minimum, title, type, properties, document_id (+5 more)

### Community 150 - "Community 150"
Cohesion: 0.15
Nodes (13): items, title, type, items, title, type, items, title (+5 more)

### Community 151 - "Community 151"
Cohesion: 0.21
Nodes (11): create_app(), _error_response(), FastAPI, FastAPI application exposing Chunking, Embedding, Indexing and Retrieval. Every…, Build the bundle-first HTTP application around already-wired services., get_http_authenticator(), Request, Return the configured bearer authenticator bound to the application. (+3 more)

### Community 152 - "Community 152"
Cohesion: 0.18
Nodes (7): InMemoryNodeRepository, PostgresNodeRepository, BaseNode, Durable-node repository double for tests., Replace nodes by ref document id., PostgreSQL adapter for parent and child node metadata/text., Replace durable nodes for one normalized document.

### Community 153 - "Community 153"
Cohesion: 0.18
Nodes (7): InMemoryNormalizedDocumentRepository, PostgresNormalizedDocumentRepository, IngestionOrigin, Normalized document repository double for tests., Record normalized document provenance., PostgreSQL adapter for normalized bundle provenance., Upsert normalized document provenance and artifact references.

### Community 154 - "Community 154"
Cohesion: 0.17
Nodes (12): properties, minimum, title, type, byte_size, relpath, sha256, title (+4 more)

### Community 155 - "Community 155"
Cohesion: 0.17
Nodes (11): additionalProperties, run_id, required, $schema, title, type, bundles, documents (+3 more)

### Community 156 - "Community 156"
Cohesion: 0.17
Nodes (12): RunDocument, title, type, minLength, title, type, disposition, document_id (+4 more)

### Community 157 - "Community 157"
Cohesion: 0.17
Nodes (3): Normalization, Embeds queries by calling the studio's /embed; matches the durable bge profile., RemoteBgeQueryEngine

### Community 158 - "Community 158"
Cohesion: 0.36
Nodes (5): Path, Loads a validated Schema 2 bundle rooted in ``docs_normalized``., Create a source constrained to one normalized-document root., Return a pre-structural bundle after validating all available sidecars., Schema2NormalizedDocumentSource

### Community 159 - "Community 159"
Cohesion: 0.24
Nodes (8): Image, _has_signature_cue(), BBox, Observation, Path, _render_pdf_pages(), _signature_bbox(), RenderedPage

### Community 160 - "Community 160"
Cohesion: 0.20
Nodes (9): EmbeddingProfileOrchestrator, InactiveProfileError, ProfileLaneMismatchError, IngestionOrigin, ValueError, The selected profile exists but is not active., Resolve and validate indexing profiles before durable writes., Return an active profile only when it matches the normalized lane. (+1 more)

### Community 161 - "Community 161"
Cohesion: 0.40
Nodes (4): FilesystemBundleLoader, Any, Path, Load validated bundles from ``data/chunks`` or the configured chunk root.

### Community 162 - "Community 162"
Cohesion: 0.27
Nodes (5): CreditBudget, CreditBudgetExceededError, CreditUsage, RuntimeError, New provider jobs would exceed the configured credit budget.

### Community 163 - "Community 163"
Cohesion: 0.18
Nodes (11): title, type, minLength, title, type, properties, normalized_base, processing_fingerprint (+3 more)

### Community 164 - "Community 164"
Cohesion: 0.18
Nodes (11): PlatformDocumentIdentity, additionalProperties, description, required, title, type, processing_profile_fingerprint, processing_profile_id (+3 more)

### Community 165 - "Community 165"
Cohesion: 0.18
Nodes (11): OcrPage, handwriting, page_number, additionalProperties, required, title, type, confidence (+3 more)

### Community 166 - "Community 166"
Cohesion: 0.22
Nodes (11): enum, enum, title, type, failed, needs_review, pending, processed (+3 more)

### Community 167 - "Community 167"
Cohesion: 0.18
Nodes (11): TableRecord, bbox, page_number, additionalProperties, required, title, type, extractor (+3 more)

### Community 168 - "Community 168"
Cohesion: 0.27
Nodes (9): promote_atomically(), Any, Path, Escritura determinista de artefactos con promoción atómica staging→final.…, Escribe filas JSONL ordenadas y ASCII, con salto de línea final. Bytes…, Escribe un JSON indentado, ordenado y ASCII, con salto de línea final., Promueve pares ``(staged, final)`` con ``os.replace``, dejando el marker al…, write_json() (+1 more)

### Community 169 - "Community 169"
Cohesion: 0.20
Nodes (6): EmbeddingBundleArtifactStore, Atomic filesystem store for vector artifacts and chunk maps., Write artifacts into an isolated staging directory., Atomically publish staged artifacts; never overwrites a sealed bundle., Read back the dense vectors of a published bundle., Read the published manifest of one bundle.

### Community 170 - "Community 170"
Cohesion: 0.20
Nodes (10): additionalProperties, required, title, type, $defs, ArtifactHash, byte_size, relpath (+2 more)

### Community 171 - "Community 171"
Cohesion: 0.20
Nodes (10): $defs, ErrorItem, additionalProperties, required, title, type, schema_version, error_type (+2 more)

### Community 172 - "Community 172"
Cohesion: 0.20
Nodes (10): minLength, title, type, items, $ref, title, type, properties (+2 more)

### Community 173 - "Community 173"
Cohesion: 0.20
Nodes (10): additionalProperties, required, title, type, BBox, bottom, coordinate_system, top (+2 more)

### Community 174 - "Community 174"
Cohesion: 0.20
Nodes (10): enum, required, text, blank_area, checkbox, label_id, other, radio (+2 more)

### Community 175 - "Community 175"
Cohesion: 0.20
Nodes (10): DocumentControl, additionalProperties, required, title, type, code, effective_date, publication_date (+2 more)

### Community 176 - "Community 176"
Cohesion: 0.20
Nodes (10): enum, title, type, hybrid, hybrid_llamaparse, llamaparse, markdown, ocr (+2 more)

### Community 177 - "Community 177"
Cohesion: 0.20
Nodes (9): additionalProperties, document_id, pages, schema_version, required, $schema, title, type (+1 more)

### Community 178 - "Community 178"
Cohesion: 0.20
Nodes (10): additionalProperties, required, title, type, BBox, bottom, coordinate_system, top (+2 more)

### Community 179 - "Community 179"
Cohesion: 0.20
Nodes (10): items, $ref, items, title, type, pages, words, items (+2 more)

### Community 180 - "Community 180"
Cohesion: 0.20
Nodes (9): additionalProperties, document_id, page_count, pages, schema_version, required, $schema, title (+1 more)

### Community 181 - "Community 181"
Cohesion: 0.20
Nodes (10): enum, title, type, hybrid, hybrid_llamaparse, llamaparse, markdown, ocr (+2 more)

### Community 182 - "Community 182"
Cohesion: 0.20
Nodes (10): items, title, type, type, details, reasons, items, minItems (+2 more)

### Community 183 - "Community 183"
Cohesion: 0.20
Nodes (9): additionalProperties, document_id, schema_version, tables, required, $schema, title, type (+1 more)

### Community 184 - "Community 184"
Cohesion: 0.22
Nodes (5): InMemoryReadinessCheckRepository, Deterministic ``readiness_checks`` double., Persist one readiness check idempotently., Return the most recent check for one subject., Return every recorded check in insertion order.

### Community 186 - "Community 186"
Cohesion: 0.36
Nodes (7): check_ocr_environment(), _env_flag(), _env_value(), OcrDoctorReport, _parse_languages(), _parse_tesseract_version(), BaseModel

### Community 187 - "Community 187"
Cohesion: 0.22
Nodes (9): artifact_hashes, document_id, document_status, normalized_base, processing_fingerprint, required_artifacts, source_hash, source_relpath (+1 more)

### Community 188 - "Community 188"
Cohesion: 0.22
Nodes (8): additionalProperties, generated_at, items, run_id, required, $schema, title, type

### Community 189 - "Community 189"
Cohesion: 0.22
Nodes (9): anyOf, default, title, properties, minLength, title, type, document_id (+1 more)

### Community 190 - "Community 190"
Cohesion: 0.22
Nodes (9): failed, needs_review, pending, processed, default, enum, title, type (+1 more)

### Community 191 - "Community 191"
Cohesion: 0.22
Nodes (9): additionalProperties, required, title, type, Classification, document_type, document_type_confidence, topic (+1 more)

### Community 192 - "Community 192"
Cohesion: 0.22
Nodes (9): PageRecord, ocr_confidence, page_number, additionalProperties, required, title, type, text_normalized (+1 more)

### Community 193 - "Community 193"
Cohesion: 0.22
Nodes (9): items, $ref, title, properties, items, schema_version, const, title (+1 more)

### Community 194 - "Community 194"
Cohesion: 0.22
Nodes (9): document_id, generated_at, items, run_id, schema_version, source_relpath, required, required (+1 more)

### Community 195 - "Community 195"
Cohesion: 0.22
Nodes (9): additionalProperties, title, type, additionalProperties, title, type, $defs, ArtifactHash (+1 more)

### Community 196 - "Community 196"
Cohesion: 0.22
Nodes (9): type, required_artifacts, warnings, items, title, type, items, title (+1 more)

### Community 197 - "Community 197"
Cohesion: 0.36
Nodes (6): EligibilityResult, IndexingEligibilityService, _ingestion_origin(), _normalized_hash(), Result of evaluating whether a normalized document can be indexed., Decide whether a normalized record can proceed to indexing.

### Community 199 - "Community 199"
Cohesion: 0.25
Nodes (8): enum, title, type, failed, needs_review, pending, processed, document_status

### Community 200 - "Community 200"
Cohesion: 0.25
Nodes (7): additionalProperties, document_id, schema_version, required, $schema, title, type

### Community 201 - "Community 201"
Cohesion: 0.25
Nodes (8): FormControl, additionalProperties, required, title, type, bbox, control_id, control_type

### Community 202 - "Community 202"
Cohesion: 0.32
Nodes (8): detected, estimated, measured, not_detected, not_evaluated, unavailable, enum, enum

### Community 203 - "Community 203"
Cohesion: 0.25
Nodes (8): minLength, title, type, document_id, source_relpath, properties, title, type

### Community 204 - "Community 204"
Cohesion: 0.25
Nodes (8): TableCell, text, additionalProperties, required, title, type, column_index, row_index

### Community 205 - "Community 205"
Cohesion: 0.29
Nodes (8): create_corpus_snapshot(), _eligibility_decisions(), Traduce las decisiones de elegibilidad del request o falla con 422., CorpusSnapshotDocumentSchema, CorpusSnapshotSchema, CreateCorpusSnapshotRequestSchema, Congela un snapshot inmutable; el server valida elegibilidad fail-closed.…, snapshot_to_schema()

### Community 206 - "Community 206"
Cohesion: 0.29
Nodes (6): IndexingTargetCatalog, IndexingTargetView, Protocol, Vista mínima de un indexing target del catálogo global (estructural)., Catálogo global de indexing targets. Lo satisface el repositorio de targets de…, Devuelve todos los indexing targets registrados.

### Community 207 - "Community 207"
Cohesion: 0.29
Nodes (4): NormalizedDocumentPlatformContext, Platform provenance carried with, but not defining, chunk identity., Expose semantic audit provenance without changing chunk identity., Expose semantic audit provenance without changing chunk identity.

### Community 208 - "Community 208"
Cohesion: 0.57
Nodes (6): _digest(), _portable(), processing_fingerprint(), Any, _secret_key(), validation_fingerprint()

### Community 209 - "Community 209"
Cohesion: 0.29
Nodes (4): GuiRegisterThrottle, datetime, In-memory per-client throttle for unauthenticated GUI registrations., timedelta

### Community 210 - "Community 210"
Cohesion: 0.43
Nodes (4): Any, Path, RawResultStore, _redact()

### Community 211 - "Community 211"
Cohesion: 0.29
Nodes (3): Any, model_validator, Migrate historical flat provenance without accepting ambiguity.

### Community 212 - "Community 212"
Cohesion: 0.29
Nodes (7): Observation, status, value, additionalProperties, required, title, type

### Community 213 - "Community 213"
Cohesion: 0.33
Nodes (7): upload_project_document(), document_row_to_schema(), ProjectDocumentRevisionSchema, Fila de documento del proyecto para la GUI. **Nunca** expone rutas físicas., Mapea la revisión recién subida a la fila del read-model. Un raw recién…, uploaded_revision_to_schema(), UploadFile

### Community 214 - "Community 214"
Cohesion: 0.33
Nodes (6): DistanceMetric, IngestionOrigin, Resolve a legacy indexing profile into the durable profile contract., Return a deterministic, validated vector table name for a profile id., resolved_profile_from_indexing_profile(), vector_table_name()

### Community 215 - "Community 215"
Cohesion: 0.33
Nodes (3): HierarchicalNodeParserAdapter, BaseNode, Document

### Community 216 - "Community 216"
Cohesion: 0.33
Nodes (6): additionalProperties, required, title, type, ConfidenceMetric, kind

### Community 217 - "Community 217"
Cohesion: 0.33
Nodes (6): additionalProperties, required, title, type, ConfidenceMetric, kind

### Community 218 - "Community 218"
Cohesion: 0.33
Nodes (5): EmbeddingProfileReader, Any, Protocol, Puerto estrecho para leer un perfil de embedding global (ADR-005). Solo se…, Devuelve el perfil de embedding o lanza si no existe.

### Community 219 - "Community 219"
Cohesion: 0.40
Nodes (4): FtsQuery, PostgresFtsRetriever, Any, Legacy full-text retriever over ``llama_index_documents``. Superseded on the…

### Community 220 - "Community 220"
Cohesion: 0.40
Nodes (3): BgeModelCache, Process-wide cache of loaded BGE runtimes, keyed by Hugging Face model name.…, Return the cached runtime for ``model_name``, loading it at most once.

### Community 223 - "Community 223"
Cohesion: 0.50
Nodes (4): promote_candidate(), PromotionError, Path, RuntimeError

### Community 224 - "Community 224"
Cohesion: 0.40
Nodes (4): additionalProperties, $schema, title, type

### Community 225 - "Community 225"
Cohesion: 0.40
Nodes (5): items, title, type, $ref, artifact_hashes

### Community 226 - "Community 226"
Cohesion: 0.40
Nodes (5): type, required_artifacts, items, title, type

### Community 227 - "Community 227"
Cohesion: 0.40
Nodes (5): type, warnings, items, title, type

### Community 228 - "Community 228"
Cohesion: 0.40
Nodes (5): const, default, title, type, identity_version

### Community 229 - "Community 229"
Cohesion: 0.40
Nodes (5): type, warnings, items, title, type

### Community 230 - "Community 230"
Cohesion: 0.40
Nodes (5): $ref, additionalProperties, title, type, feature_observations

### Community 231 - "Community 231"
Cohesion: 0.40
Nodes (5): type, warnings, items, title, type

### Community 232 - "Community 232"
Cohesion: 0.40
Nodes (4): additionalProperties, $schema, title, type

### Community 233 - "Community 233"
Cohesion: 0.40
Nodes (5): $defs, ReviewItem, additionalProperties, title, type

### Community 234 - "Community 234"
Cohesion: 0.40
Nodes (5): row_span, default, minimum, title, type

### Community 235 - "Community 235"
Cohesion: 0.40
Nodes (4): _is_unique_violation(), Exception, Best-effort detection of a PostgreSQL unique-violation (SQLSTATE 23505).…, Inserta o confirma la fila sellada por su identidad física exacta. Idempotente…

### Community 236 - "Community 236"
Cohesion: 0.50
Nodes (3): _NullTransactionManager, Transaction manager for in-memory wiring and dry-run., Return a no-op scope.

### Community 237 - "Community 237"
Cohesion: 0.50
Nodes (4): minLength, title, type, document_id

### Community 238 - "Community 238"
Cohesion: 0.50
Nodes (4): schema_version, const, title, type

### Community 239 - "Community 239"
Cohesion: 0.50
Nodes (4): source_hash, pattern, title, type

### Community 240 - "Community 240"
Cohesion: 0.50
Nodes (4): minLength, title, type, error_type

### Community 241 - "Community 241"
Cohesion: 0.50
Nodes (4): retryable, default, title, type

### Community 242 - "Community 242"
Cohesion: 0.50
Nodes (4): run_id, minLength, title, type

### Community 243 - "Community 243"
Cohesion: 0.50
Nodes (4): schema_version, const, title, type

### Community 244 - "Community 244"
Cohesion: 0.50
Nodes (4): source_relpath, anyOf, default, title

### Community 245 - "Community 245"
Cohesion: 0.50
Nodes (4): stage, minLength, title, type

### Community 246 - "Community 246"
Cohesion: 0.50
Nodes (4): minLength, title, type, document_name

### Community 247 - "Community 247"
Cohesion: 0.50
Nodes (4): anyOf, default, title, engine_version

### Community 248 - "Community 248"
Cohesion: 0.50
Nodes (4): minimum, title, type, file_size

### Community 249 - "Community 249"
Cohesion: 0.50
Nodes (4): estimated, measured, unavailable, enum

### Community 250 - "Community 250"
Cohesion: 0.50
Nodes (4): anyOf, default, title, legacy_path

### Community 251 - "Community 251"
Cohesion: 0.50
Nodes (4): sample_size, anyOf, default, title

### Community 252 - "Community 252"
Cohesion: 0.50
Nodes (4): minLength, title, type, generated_at

### Community 253 - "Community 253"
Cohesion: 0.50
Nodes (4): run_id, minLength, title, type

### Community 254 - "Community 254"
Cohesion: 0.50
Nodes (4): minimum, title, type, column_index

### Community 255 - "Community 255"
Cohesion: 0.50
Nodes (3): PhysicalNode, Un nodo de indexación con identidad **física** namespaced por proyecto.…, Return whether this node is a child that expands from a parent.

### Community 259 - "Community 259"
Cohesion: 0.67
Nodes (3): anyOf, title, detected_extension

### Community 260 - "Community 260"
Cohesion: 0.67
Nodes (3): anyOf, default, ocr_confidence

### Community 261 - "Community 261"
Cohesion: 0.67
Nodes (3): source_relpath, title, type

## Knowledge Gaps
- **1188 isolated node(s):** `additionalProperties`, `minimum`, `title`, `type`, `title` (+1183 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 3117 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **55 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `StrictModel` connect `Chunk Provenance & PG Settings` to `Document Classification`, `Platform Events & Actors`, `Indexing Activation & Bundles`, `RAG Release Build & Reuse`, `Embedding Ports & Registry`, `Community 134`, `Observability & Pipeline Events`, `Platform Metadata Enrichment`, `Normalized Artifacts & Platform Ports`, `RAG Platform Wiring`, `Platform Rebuild & Readiness`, `HTTP Envelope & Feature Flags`, `Bundle Activation Vectors`, `Profile Readiness & Verification`, `HTTP Contract & Indexing Router`, `Embedding Bundle Repository`, `API Auth & Project Access`, `Artifact Reuse & Build Ledger`, `Engine Registry & Providers`, `Community 147`, `Text Normalization & Readers`, `Schema2 Chunk Assembly`, `Community 23`, `Community 24`, `Retrieval & Citations`, `Community 26`, `Community 29`, `Community 32`, `Community 33`, `Community 34`, `Community 35`, `Community 39`, `Community 41`, `Community 42`, `Community 43`, `Community 45`, `Community 47`, `Community 48`, `Community 50`, `Community 51`, `Community 54`, `Community 55`, `Community 58`, `Community 60`, `Community 63`, `Community 64`, `Community 66`, `Community 68`, `Community 197`, `Community 69`, `Community 205`, `Community 78`, `Community 143`, `Community 213`, `Community 91`, `Community 95`, `Community 108`, `Community 110`, `Community 118`, `Community 255`?**
  _High betweenness centrality (0.166) - this node is a cross-community bridge._
- **Why does `PlatformId` connect `RAG Release Build & Reuse` to `Document Classification`, `Platform Events & Actors`, `Chunk Provenance & PG Settings`, `Normalized Artifacts & Platform Ports`, `Community 134`, `Community 135`, `Artifact Reuse & Build Ledger`, `RAG Platform Wiring`, `Platform Rebuild & Readiness`, `Community 143`, `Community 25`, `Community 26`, `Community 29`, `Community 34`, `Community 41`, `Community 43`, `Community 46`, `Community 47`, `Community 50`, `Community 54`, `Community 60`, `Community 68`, `Community 91`, `Community 95`, `Community 235`, `Community 127`?**
  _High betweenness centrality (0.058) - this node is a cross-community bridge._
- **Why does `ResolvedIndexingProfile` connect `Bundle Activation Vectors` to `Community 160`, `Indexing Activation & Bundles`, `Chunk Provenance & PG Settings`, `Embedding Ports & Registry`, `Engine Registry & Providers`, `Community 214`, `Community 24`?**
  _High betweenness centrality (0.022) - this node is a cross-community bridge._
- **Are the 114 inferred relationships involving `PlatformId` (e.g. with `_parse_id()` and `_parse_id()`) actually correct?**
  _`PlatformId` has 114 INFERRED edges - model-reasoned connections that need verification._
- **Are the 62 inferred relationships involving `PlatformActor` (e.g. with `dispatch_question()` and `get_actor()`) actually correct?**
  _`PlatformActor` has 62 INFERRED edges - model-reasoned connections that need verification._
- **Are the 62 inferred relationships involving `IdentityKind` (e.g. with `_build_rag_platform_draft()` and `_build_rag_platform_services()`) actually correct?**
  _`IdentityKind` has 62 INFERRED edges - model-reasoned connections that need verification._
- **Are the 30 inferred relationships involving `PlatformAccessPolicy` (e.g. with `ListProjectCorpusSnapshotsUseCase` and `CreateCorpusSnapshotUseCase`) actually correct?**
  _`PlatformAccessPolicy` has 30 INFERRED edges - model-reasoned connections that need verification._