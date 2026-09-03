# RAG Platform

## Identidad vigente

La identidad documental y funcional de este repositorio es **RAG Platform**.
El nombre anterior `chatbot-sst` debe tratarse como legado historico.

## Identificadores tecnicos vigentes

Estos nombres deben presentarse como la identidad actual del repo y su runtime
operativo:

- slug actual del repositorio en GitHub: `rag_platform`
- entorno virtual de referencia en Windows: `C:\venvs\rag_platform`
- paquete npm raiz: `rag_platform`
- distribucion Python: `rag-platform`
- paquete runtime: `chatbot_runtime`
- cookie de sesion GUI: `chatbot_sst_gui_session`
- claves de persistencia local: `rag-platform.dashboard.preferences.v2`,
  `rag-platform.platform.preferences.v1` y `rag-platform.chunking.workspace.v1`

`chatbot` sigue siendo un nombre valido solo para la API/consumer de dispatch.

## Autoridades documentales

- Identidad y reutilizacion: [identity-and-reuse-contract.md](./identity-and-reuse-contract.md)
- Baseline reproducible: [migration-baseline.md](./migration-baseline.md)
- Operacion raw/normalized por proyecto: [raw-normalized-catalog-runbook.md](./raw-normalized-catalog-runbook.md)
- Decision arquitectonica base: [../adr/ADR-006-rag-platform-project-variant-release.md](../adr/ADR-006-rag-platform-project-variant-release.md)
- Ownership puro por proyecto: [../adr/ADR-008-pure-platform-project-ownership-not-null.md](../adr/ADR-008-pure-platform-project-ownership-not-null.md)
- Aislamiento retrieval por proyecto: [../adr/ADR-009-retrieval-per-project-tenant-isolation.md](../adr/ADR-009-retrieval-per-project-tenant-isolation.md)

## Estado del plan

La carpeta `docs/superpowers/plans/` ya no es el lugar para acumular planes
cerrados o reemplazados. Se conserva solo:

- el plan maestro multi-proyecto que todavia sirve como referencia de alcance;
- los planes recientes que siguen siendo contexto operativo activo;
- el historial completo en git para cualquier reconstruccion historica.
