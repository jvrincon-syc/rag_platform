# RAG Platform

## Identidad vigente

La identidad documental y funcional de este repositorio es **RAG Platform**.
El nombre anterior `chatbot-sst` debe tratarse como legado editorial.

## Identificadores tecnicos que siguen vivos

Algunos nombres heredados continuan porque existen literalmente en el codigo,
en artefactos generados o en persistencia local. No deben presentarse como
marca del producto, pero si respetarse cuando el documento hable de rutas,
paquetes o claves reales:

- slug actual del repositorio en GitHub: `chatbot-sst`
- entorno virtual de referencia en Windows: `C:\venvs\chatbot-sst`
- paquete runtime: `chatbot_runtime`
- cookie de sesion GUI: `chatbot_sst_gui_session`
- claves de persistencia local: `chatbot-sst.dashboard.preferences.v2` y
  `chatbot-sst.platform.preferences.v1`

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
