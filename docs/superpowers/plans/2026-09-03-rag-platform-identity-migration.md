# RAG Platform Identity Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert repository, package, runtime, and operator documentation identity from legacy `rag_platform` to canonical `rag_platform` while preserving chatbot dispatch as a product capability and auditing dead-code risk with Graphify.

**Architecture:** Treat `rag_platform` as the repository/platform identity and keep `chatbot` only where it names the downstream dispatch API capability. Update root package metadata, Python distribution metadata, Docker/runtime names, local storage keys, runbooks, and migration docs without altering immutable corpus paths or project IDs such as `sst-general`.

**Tech Stack:** Python 3.12, pytest, npm scripts, Vite frontend metadata, Docker Compose, Graphify static graph.

**Spec:** User request from 2026-09-03: rename repo identity/path from `rag_platform/rag_platform` to `rag_platform`, update documentation, account for GitHub repo rename, and identify dead/unused code with Graphify.

## Global Constraints

- Do not modify `data/docs_raw` or corpus-derived evidence as part of this identity migration.
- Preserve `chatbot` terminology only for the explicit chatbot dispatch API and consumer-scope contract.
- Replace repository slug, package names, default DB examples, virtualenv examples, Docker cache/service labels, and local persistence keys that still use `rag_platform`/`rag_platform`.
- Do not hide security issues found during identity search; redact secrets in reports and remove hardcoded credentials when touched.
- Use Graphify locally; if semantic extraction needs unavailable external LLM credentials, use `--code-only` and document the limit.

---

### Task 1: Repo Identity Contract

**Files:**
- Create: `app/back/tests/rag_platform/test_repo_identity_contract.py`
- Modify: `package.json`
- Modify: `pyproject.toml`
- Modify: `app/front/package.json`
- Modify: `app/front/package-lock.json`

**Interfaces:**
- Consumes: root package metadata and Python project metadata.
- Produces: canonical package identity `rag_platform`.

- [ ] **Step 1: Write the failing test**

```python
import json
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


def test_repo_package_identity_is_rag_platform() -> None:
    package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    front_package = json.loads((ROOT / "app/front/package.json").read_text(encoding="utf-8"))

    assert package["name"] == "rag_platform"
    assert package["description"] == "RAG Platform multiproyecto con ingesta, versionado, indexacion y retrieval trazable."
    assert pyproject["project"]["name"] == "rag-platform"
    assert front_package["name"] == "rag-platform-operator-ui"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `C:\venvs\rag_platform\Scripts\python.exe -m pytest app/back/tests/rag_platform/test_repo_identity_contract.py -q`

Expected: FAIL because metadata still says `rag_platform`.

- [ ] **Step 3: Write minimal implementation**

Set root npm name to `rag_platform`, Python distribution to `rag-platform`, frontend package to `rag-platform-operator-ui`, and update the matching lockfile package names.

- [ ] **Step 4: Run test to verify it passes**

Run: `C:\venvs\rag_platform\Scripts\python.exe -m pytest app/back/tests/rag_platform/test_repo_identity_contract.py -q`

Expected: PASS.

### Task 2: Runtime and Operator Persistence Names

**Files:**
- Modify: `package.json`
- Modify: `docker-compose.yml`
- Modify: `app/back/Dockerfile`
- Modify: `app/back/docker/worker-entrypoint.sh`
- Modify: `app/back/tests/chatbot/test_chatbot_runtime_docker_config.py`
- Modify: `app/front/src/features/platform/platformPersistence.ts`
- Modify: `app/front/src/features/platform/platformPersistence.test.mjs`
- Modify: `app/front/src/features/dashboard/dashboardPersistence.ts`
- Modify: `app/front/src/dashboardPersistence.test.mjs`
- Modify: `app/front/src/features/chunking/chunkingPersistence.ts`
- Modify: `app/front/src/features/chunking/chunkingPersistence.test.mjs`
- Modify: `app/front/src/features/platform/platformContractGuards.test.tsx`
- Modify: `app/front/src/features/operator/components/OperatorAuthWorkspace.tsx`

**Interfaces:**
- Consumes: runtime env vars and frontend localStorage keys.
- Produces: `RAG_PLATFORM_*` runtime/cache naming and `rag-platform.*` browser persistence keys.

- [ ] **Step 1: Update tests first**

Change tests to expect `rag-platform-hf-cache`, `/var/lib/rag_platform/hf-cache`, `RAG_PLATFORM_RUNTIME_*`, and `rag-platform.*` storage keys while keeping `/api/chatbot` route tests unchanged.

- [ ] **Step 2: Run focused tests to verify failure**

Run: `C:\venvs\rag_platform\Scripts\python.exe -m pytest app/back/tests/chatbot/test_chatbot_runtime_docker_config.py -q`

Run: `npm --prefix app/front run test -- platformPersistence dashboardPersistence chunkingPersistence platformContractGuards`

Expected: FAIL on legacy names.

- [ ] **Step 3: Implement runtime/key rename**

Rename Docker service/cache labels and env vars that encode platform runtime identity. Preserve backwards-compatible reads for existing `CHATBOT_RUNTIME_*` env vars only if tests cover fallback.

- [ ] **Step 4: Run focused tests to verify pass**

Run the same backend and frontend tests.

### Task 3: Documentation Identity Refresh

**Files:**
- Modify: `README.md`
- Modify: `AGENTS.md`
- Modify: `CLAUDE.md`
- Modify: `docs/README.md`
- Modify: `docs/rag-platform/README.md`
- Modify: `docs/ingestion/README.md`
- Modify: `docs/runbooks/gui-operator-session.md`
- Modify: `docs/runbooks/pre-phase7-readiness.md`
- Modify: `docs/observability/current-contracts.md`
- Modify: docs that reference the old GitHub slug, old venv path, or old DB example outside historical evidence.

**Interfaces:**
- Consumes: documentation navigation and operational bootstrap instructions.
- Produces: canonical repo identity and local path `C:\Users\jvrincon\Documents\rag_platform`.

- [ ] **Step 1: Scan documentation**

Run: `rg -n "rag_platform|rag_platform|C:\\\\venvs\\\\rag_platform|github.com/jvrincon-syc/rag_platform" docs README.md AGENTS.md CLAUDE.md README_REGLAS.md`

- [ ] **Step 2: Update current docs**

Replace non-historical repo identity with `rag_platform`, `rag-platform`, `RAG Platform`, `C:\venvs\rag_platform`, `rag_platform` DB examples, and `github.com/jvrincon-syc/rag_platform`.

- [ ] **Step 3: Preserve historical boundaries**

Keep old names only where the document explicitly describes historical migration evidence, legacy compatibility, or chatbot dispatch as a consumer capability.

### Task 4: Security Cleanup During Identity Sweep

**Files:**
- Modify: `scripts/discover_release_ids.py`
- Create or modify a focused test if the script remains.

**Interfaces:**
- Consumes: ad hoc script that currently contains absolute local path and a hardcoded database password.
- Produces: no hardcoded secret; script either uses environment variables or is removed if unused.

- [ ] **Step 1: Decide keep/remove**

Search references to `discover_release_ids.py`. If no caller exists, delete it as dead ad hoc code. If it must remain, rewrite it to use `SST_POSTGRES_DSN`/`DATABASE_URL` and no absolute repo path.

- [ ] **Step 2: Verify secret removal**

Run: `rg -n "Fitomega|password=|C:/Users/jvrincon/Documents/rag_platform" scripts app docs`

Expected: no hardcoded password or old absolute repo root.

### Task 5: Graphify Dead-Code Audit

**Files:**
- Generate ignored output under `graphify-out/`.
- Modify or create a short audit report under `docs/revision/` only if findings need to be versioned.

**Interfaces:**
- Consumes: local source graph.
- Produces: audit summary of hubs, isolated candidates, and dead-code suspects.

- [ ] **Step 1: Extract graph**

Run: `graphify extract . --code-only --no-cluster --out .`

- [ ] **Step 2: Query graph**

Run: `graphify god-nodes --top 20 --graph graphify-out/graph.json --json`

Run targeted `graphify query`, `graphify explain`, or `graphify affected` commands for modules surfaced by identity/dead-code search.

- [ ] **Step 3: Cross-check candidates**

For each candidate, use `rg` and tests before removing or recommending deletion.

### Task 6: Local Folder and Git Remote Rename

**Files:**
- Modify: `.git/config` via `git remote set-url`.
- Filesystem move outside the current workspace.

**Interfaces:**
- Consumes: current local path `C:\Users\jvrincon\Documents\rag_platform\rag_platform`.
- Produces: target local path `C:\Users\jvrincon\Documents\rag_platform`.

- [ ] **Step 1: Update remote URL**

Run: `git remote set-url origin https://github.com/jvrincon-syc/rag_platform.git`

- [ ] **Step 2: Move repo folder after file verification**

From `C:\Users\jvrincon\Documents`, move `rag_platform\rag_platform` to `rag_platform` only if target does not exist and source resolves to the current repo.

- [ ] **Step 3: Report final path**

Final repo path should be `C:\Users\jvrincon\Documents\rag_platform`.

