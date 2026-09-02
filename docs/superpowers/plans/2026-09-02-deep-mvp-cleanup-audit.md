# Deep MVP Cleanup Audit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove only repository artifacts and code proven unused while preserving every existing MVP path.

**Architecture:** Use the existing Graphify dependency graph as one input, then validate each candidate through repository references, executable entrypoints, configuration, and focused regression tests. Treat graph roots, dynamic imports, CLIs, and deployment scripts as potentially reachable until independently disproven.

**Tech Stack:** Python/FastAPI, React/Vite, pytest, Vitest, Graphify, Git.

**Spec:** `AGENTS.md`

## Global Constraints

- Do not add functionality or change product behavior.
- Preserve user-authored working-tree changes and immutable source documents.
- Delete only artifacts or code with evidence that no supported path consumes them.
- Keep Graphify output outside tracked source directories and prevent generated outputs from returning.
- Run focused tests for every source area changed; report pre-existing failures separately.

---

### Task 1: Recover and inspect dependency evidence

**Files:**
- Read: Git-tracked `graphify-out/graph.html`, `graphify-out/graph.json`, and `graphify-out/GRAPH_REPORT.md`
- Read: `package.json`, `pyproject.toml`, `README.md`, service entrypoints, deployment files

**Interfaces:**
- Consumes: Graphify node/edge data and declared runtime commands.
- Produces: Candidate inventory labeled `reachable`, `externally reachable`, `generated artifact`, or `needs manual decision`.

- [x] **Step 1: Inspect Graphify node roots and isolated components**

Run: `git show HEAD:graphify-out/GRAPH_REPORT.md`

Expected: A summary of isolated files and dependency clusters without restoring generated output.

- [x] **Step 2: Cross-check each isolated candidate**

Run: `rg -n --fixed-strings "candidate_name" --glob '!node_modules/**' .`

Expected: References, test coverage, configuration references, or no reachable consumer.

### Task 2: Audit source code by executable boundary

**Files:**
- Read: `app/back/src/**`, `app/front/src/**`, `scripts/**`, `docker-compose.yml`, CI and package manifests

**Interfaces:**
- Consumes: Candidate inventory from Task 1.
- Produces: Small, independently justified cleanup changes.

- [x] **Step 1: Review backend routes, dependency wiring, CLI entrypoints, and experiment boundaries**

Run: `rg -n "FastAPI\(|include_router|uvicorn|if __name__ == .__main__." app/back/src scripts`

Expected: Every backend module is classified as runtime, test-only, developer tooling, or dead candidate.

- [x] **Step 2: Review frontend route and component reachability**

Run: `rg -n "createBrowserRouter|Routes|Route|lazy\(|import\(" app/front/src`

Expected: Every apparent leaf component is checked against routing and imports.

### Task 3: Apply only proven-safe cleanup

**Files:**
- Modify: `.gitignore` only if a generated artifact lacks an existing ignore rule
- Delete: exact paths proven generated or unconsumed in Tasks 1-2

**Interfaces:**
- Consumes: Evidence that a target is not an entrypoint, dynamically loaded module, fixture, or documented command.
- Produces: A smaller worktree with no behavior changes.

- [x] **Step 1: Verify targets and delete exact paths**

Run: `git ls-files -- path/to/candidate` and `rg -n --fixed-strings "candidate_name" .`

Expected: The target is generated or unreferenced outside its own path before deletion.

- [x] **Step 2: Inspect the resulting diff for accidental scope expansion**

Run: `git diff --check` and `git diff --stat`

Expected: No whitespace errors and only cleanup-related changes plus pre-existing user changes.

### Task 4: Verify MVP behavior

**Files:**
- Test: affected backend pytest modules
- Test: `app/front` Vitest suite when frontend files are changed

**Interfaces:**
- Consumes: cleanup diff.
- Produces: Evidence that supported code paths remain intact.

- [x] **Step 1: Run focused regression tests for changed source areas**

Run: `python -m pytest <affected tests> -q`

Expected: PASS, or a documented unrelated baseline failure.

- [x] **Step 2: Run frontend tests when frontend reachability changes**

Run: `npm.cmd --prefix app/front run test`

Expected: PASS for all discovered test files.

- [x] **Step 3: Report retained risks and protected files**

Expected: A concise list of ambiguous candidates deliberately retained because static analysis cannot prove they are unused.
