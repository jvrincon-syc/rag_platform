# Documentacion corta de RAG Platform

Para evitar overflow, empieza por este indice y abre solo el README del area
afectada. No cargues `data/`, `memory/`, `.tmp/`, `.venv*` ni
`node_modules/` salvo solicitud explicita.

## Areas

- `rag-platform/README.md`: identidad vigente, baseline de plataforma y
  convenciones de nombres tecnicos heredados.
- `backend/README.md`: mapa transversal del backend, handoffs entre fases,
  variables criticas y deuda visible.
- `ingestion/README.md`: ingesta local, Schema 2.0, gates y consumo downstream.
- `llama_first/README.md`: via experimental Llama Cloud/LlamaIndex, flags y
  bloqueos.
- `chunking/`: contrato del chunking local y su API HTTP.
- `embedding/README.md`: operacion de perfiles, runs y bundles de embeddings.
- `indexing/README.md`: indexacion bundle-first, targets, activacion y rollback.
- `retrieval/README.md`: perfiles de retrieval, readiness y busqueda.
- `observability/README.md`: logs, eventos, correlacion y runbooks.
- `adr/`: decisiones de arquitectura vigentes.
- `runbooks/`: acciones operativas breves.
- `rules/`: politicas obligatorias; leerlas cuando el cambio toque calidad,
  seguridad, ramas o revision.

## Identidad y bibliografia

- `bibliography.md`: catalogo breve de documentos canonicos, ADRs, runbooks y
  referencias operativas.
- `rag-platform/README.md`: punto de entrada para la transicion editorial de
  `chatbot-sst` a `RAG Platform`.

## Fuentes de verdad

- Codigo y scripts: `app/back/src`, `app/back/tests`, `scripts`, `package.json`.
- Configuracion versionada: `pyproject.toml`, `requirements*.txt`,
  `constraints/llama-first.txt`, `secrets.example.env`.
- AGENTS: `AGENTS.md`, `app/back/AGENTS_back.md`,
  `app/front/AGENTS_front.md`.
- Flujo transversal y gaps del backend: `docs/backend/`.
- Salidas generadas o sensibles: `data/`, `secrets.env`, `manual-test-temp/`
  y cualquier `pytest-*` temporal.
- Planes historicos: `memory/` y el historial de git.

## Poda

Los planes temporales y reportes historicos absorbidos por ADRs, READMEs o
runbooks ya no deben mantenerse como documentacion viva paralela. En
`docs/superpowers/plans/` permanecen solo el plan maestro y los planes que
siguen siendo referencia operativa activa. Si necesitas evidencia historica
exacta, usa el historial de git en vez de cargar multiples Markdown.
