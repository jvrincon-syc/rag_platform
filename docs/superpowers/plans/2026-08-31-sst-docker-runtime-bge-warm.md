# SST Docker Runtime + BGE Warm Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a dedicated Dockerized `app/back` runtime foundation with a real ASGI RAG API entrypoint, a persistent BGE-M3 warm worker, and explicit health/readiness wiring that keeps the model warm before traffic.

**Architecture:** Introduce a new `chatbot_runtime` package that is independent from the legacy `ingestion.gui.server` bridge and owns runtime settings, BGE warmup, and dedicated FastAPI/Uvicorn composition for RAG traffic. Package that runtime in Docker with separate `api` and `worker` services sharing a Hugging Face cache volume so BGE warmup survives ordinary restarts and does not cold-load on the first real request.

**Tech Stack:** Python 3.12, FastAPI, Uvicorn, Docker, Docker Compose, FlagEmbedding/BGE-M3, Hugging Face cache volume, pytest.

**Spec:** `C:\Users\jvrincon\.codex\attachments\1f2eb9ae-41bb-4a4a-9923-e3fe976805d1\pasted-text.txt` (goal, scope, sections 4, 5, 8, 19, 30, 32, 33, 38)

## Global Constraints

- SST RAG traffic must run through a real ASGI server, not `ThreadingHTTPServer + AsgiBridge`.
- BGE cold load in the user request path must be `0`.
- The worker must keep one persistent BGE-M3 runtime warm before readiness becomes healthy.
- Query embedding and reranking must reuse one BGE runtime.
- Bearer authentication on the API must remain enabled.
- Release isolation and fail-closed behavior must remain intact.
- The work in this plan is limited to `app/back` foundation work and must not implement the full Redis/webhook architecture yet.
- Dockerization is mandatory for the SST BGE runtime in this phase.
- Containers must avoid baking secrets or raw corpus content into images.
- Tests must prove readiness is false before warmup and true after warmup.

---

### Task 1: Runtime Settings and Warmup State

**Files:**
- Create: `app/back/src/chatbot_runtime/settings.py`
- Create: `app/back/src/chatbot_runtime/warmup.py`
- Create: `app/back/src/chatbot_runtime/__init__.py`
- Test: `app/back/tests/chatbot/test_chatbot_warmup.py`

**Interfaces:**
- Consumes: `indexing.infrastructure.embeddings.bge.BgeModelCache`, `retrieval.infrastructure.bge_reranker.BgeReranker`, `embedding.application.engine_registry.DefaultEmbeddingEngineRegistry` patterns already used by the composition root.
- Produces: `RuntimeSettings.from_env(environ: Mapping[str, str]) -> RuntimeSettings`
- Produces: `WarmupStatusSnapshot`
- Produces: `BgeWarmupService.warm() -> WarmupStatusSnapshot`
- Produces: `BgeWarmupService.status() -> WarmupStatusSnapshot`
- Produces: `BgeWarmupService.ready() -> bool`

- [ ] **Step 1: Write the failing test**

```python
def test_readiness_false_antes_del_warmup() -> None:
    service = BgeWarmupService(
        embed_probe=lambda: None,
        rerank_probe=lambda: None,
    )

    status = service.status()

    assert status.ready is False
    assert status.warmed_embedding is False
    assert status.warmed_reranker is False


def test_readiness_true_despues_de_warmup_exitoso() -> None:
    called: list[str] = []
    service = BgeWarmupService(
        embed_probe=lambda: called.append("embed"),
        rerank_probe=lambda: called.append("rerank"),
    )

    status = service.warm()

    assert called == ["embed", "rerank"]
    assert status.ready is True
    assert status.warmed_embedding is True
    assert status.warmed_reranker is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.\.venv_windows_trabajo\Scripts\python.exe -m pytest app/back/tests/chatbot/test_chatbot_warmup.py -q`
Expected: FAIL because `chatbot_runtime.warmup` and/or `BgeWarmupService` do not exist yet.

- [ ] **Step 3: Write minimal implementation**

```python
@dataclass(frozen=True)
class WarmupStatusSnapshot:
    ready: bool
    warmed_embedding: bool
    warmed_reranker: bool
    last_error: str | None


class BgeWarmupService:
    def __init__(self, *, embed_probe, rerank_probe) -> None:
        ...

    def warm(self) -> WarmupStatusSnapshot:
        ...

    def status(self) -> WarmupStatusSnapshot:
        ...

    def ready(self) -> bool:
        ...
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.\.venv_windows_trabajo\Scripts\python.exe -m pytest app/back/tests/chatbot/test_chatbot_warmup.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/back/src/chatbot_runtime/__init__.py app/back/src/chatbot_runtime/settings.py app/back/src/chatbot_runtime/warmup.py app/back/tests/chatbot/test_chatbot_warmup.py
git commit -m "feat: add chatbot runtime warmup foundation"
```

### Task 2: Dedicated ASGI RAG Runtime

**Files:**
- Create: `app/back/src/chatbot_runtime/app.py`
- Create: `app/back/src/chatbot_runtime/dependencies.py`
- Create: `app/back/src/chatbot_runtime/main.py`
- Modify: `app/back/src/api/dependencies.py`
- Test: `app/back/tests/chatbot/test_chatbot_runtime_worker.py`

**Interfaces:**
- Consumes: `build_pipeline_services_from_env(...) -> PipelineServices`
- Consumes: `create_app(services: PipelineServices) -> FastAPI`
- Consumes: `RuntimeSettings`
- Consumes: `BgeWarmupService`
- Produces: `create_chatbot_runtime_app(...) -> FastAPI`
- Produces: `build_chatbot_runtime(...) -> ChatbotRuntime`
- Produces: `python -m chatbot_runtime.main` as the dedicated ASGI entrypoint

- [ ] **Step 1: Write the failing test**

```python
def test_runtime_expone_health_y_readiness_separados(tmp_path: Path) -> None:
    runtime = build_chatbot_runtime(
        chunks_root=tmp_path / "chunks",
        embeddings_root=tmp_path / "embeddings",
        environ=_runtime_env(),
        warmup_service=_stub_warmup(ready=False),
    )
    client = TestClient(runtime.app)

    assert client.get("/healthz").status_code == 200
    readiness = client.get("/readyz")
    assert readiness.status_code == 503
    assert readiness.json()["ready"] is False


def test_runtime_reporta_ready_cuando_bge_ya_esta_warm(tmp_path: Path) -> None:
    runtime = build_chatbot_runtime(
        chunks_root=tmp_path / "chunks",
        embeddings_root=tmp_path / "embeddings",
        environ=_runtime_env(),
        warmup_service=_stub_warmup(ready=True),
    )
    client = TestClient(runtime.app)

    readiness = client.get("/readyz")
    assert readiness.status_code == 200
    assert readiness.json()["ready"] is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.\.venv_windows_trabajo\Scripts\python.exe -m pytest app/back/tests/chatbot/test_chatbot_runtime_worker.py -q`
Expected: FAIL because `chatbot_runtime.app`/`build_chatbot_runtime` do not exist yet.

- [ ] **Step 3: Write minimal implementation**

```python
@dataclass
class ChatbotRuntime:
    app: FastAPI
    services: PipelineServices
    warmup: BgeWarmupService


def build_chatbot_runtime(..., warmup_service: BgeWarmupService | None = None) -> ChatbotRuntime:
    ...


def create_chatbot_runtime_app(...) -> FastAPI:
    app = FastAPI(...)
    app.mount("/", pipeline_app)
    @app.get("/healthz")
    def healthz() -> dict[str, object]: ...
    @app.get("/readyz")
    def readyz(response: Response) -> dict[str, object]: ...
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.\.venv_windows_trabajo\Scripts\python.exe -m pytest app/back/tests/chatbot/test_chatbot_runtime_worker.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/back/src/chatbot_runtime/app.py app/back/src/chatbot_runtime/dependencies.py app/back/src/chatbot_runtime/main.py app/back/src/api/dependencies.py app/back/tests/chatbot/test_chatbot_runtime_worker.py
git commit -m "feat: add dedicated chatbot asgi runtime"
```

### Task 3: Docker Packaging and Warm Worker Commands

**Files:**
- Create: `app/back/Dockerfile`
- Create: `docker-compose.yml`
- Create: `.dockerignore`
- Create: `app/back/docker/api-entrypoint.sh`
- Create: `app/back/docker/worker-entrypoint.sh`
- Test: `app/back/tests/chatbot/test_chatbot_runtime_docker_config.py`

**Interfaces:**
- Consumes: `python -m chatbot_runtime.main`
- Consumes: `python -m chatbot_runtime.warmup`
- Consumes: `RuntimeSettings`
- Produces: Docker service `sst-rag-api`
- Produces: Docker service `sst-rag-worker`
- Produces: shared volume for `HF_HUB_CACHE`

- [ ] **Step 1: Write the failing test**

```python
def test_runtime_settings_default_to_dedicated_api_and_worker_commands() -> None:
    settings = RuntimeSettings.from_env({})

    assert settings.api_bind_host == "0.0.0.0"
    assert settings.api_port == 8780
    assert settings.worker_mode == "warm"


def test_dockerfile_declares_api_and_worker_entrypoints() -> None:
    dockerfile = Path("app/back/Dockerfile").read_text(encoding="utf-8")

    assert "api-entrypoint.sh" in dockerfile
    assert "worker-entrypoint.sh" in dockerfile
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.\.venv_windows_trabajo\Scripts\python.exe -m pytest app/back/tests/chatbot/test_chatbot_runtime_docker_config.py -q`
Expected: FAIL because the Docker assets and/or settings defaults do not exist yet.

- [ ] **Step 3: Write minimal implementation**

```dockerfile
FROM python:3.12-slim
...
COPY app/back/docker/api-entrypoint.sh /app/app/back/docker/api-entrypoint.sh
COPY app/back/docker/worker-entrypoint.sh /app/app/back/docker/worker-entrypoint.sh
```

```yaml
services:
  sst-rag-api:
    build:
      context: .
      dockerfile: app/back/Dockerfile
    command: ["/app/app/back/docker/api-entrypoint.sh"]
  sst-rag-worker:
    build:
      context: .
      dockerfile: app/back/Dockerfile
    command: ["/app/app/back/docker/worker-entrypoint.sh"]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.\.venv_windows_trabajo\Scripts\python.exe -m pytest app/back/tests/chatbot/test_chatbot_runtime_docker_config.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/back/Dockerfile app/back/docker/api-entrypoint.sh app/back/docker/worker-entrypoint.sh docker-compose.yml .dockerignore app/back/tests/chatbot/test_chatbot_runtime_docker_config.py
git commit -m "build: add dockerized chatbot runtime services"
```

### Task 4: Worker Warmup CLI and Runtime Verification

**Files:**
- Modify: `app/back/src/chatbot_runtime/warmup.py`
- Modify: `app/back/src/chatbot_runtime/main.py`
- Modify: `README.md`
- Test: `app/back/tests/chatbot/test_chatbot_runtime_cli.py`

**Interfaces:**
- Consumes: `BgeWarmupService.warm() -> WarmupStatusSnapshot`
- Consumes: `build_chatbot_runtime(...) -> ChatbotRuntime`
- Produces: `python -m chatbot_runtime.warmup`
- Produces: `python -m chatbot_runtime.main`

- [ ] **Step 1: Write the failing test**

```python
def test_warmup_cli_returns_zero_when_warmup_succeeds(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("chatbot_runtime.warmup.run_runtime_warmup", lambda: True)

    assert main([]) == 0


def test_warmup_cli_returns_non_zero_when_warmup_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("chatbot_runtime.warmup.run_runtime_warmup", lambda: False)

    assert main([]) == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.\.venv_windows_trabajo\Scripts\python.exe -m pytest app/back/tests/chatbot/test_chatbot_runtime_cli.py -q`
Expected: FAIL because the CLI entrypoint does not exist yet.

- [ ] **Step 3: Write minimal implementation**

```python
def run_runtime_warmup(...) -> bool:
    ...


def main(argv: Sequence[str] | None = None) -> int:
    return 0 if run_runtime_warmup(...) else 1
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.\.venv_windows_trabajo\Scripts\python.exe -m pytest app/back/tests/chatbot/test_chatbot_runtime_cli.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/back/src/chatbot_runtime/warmup.py app/back/src/chatbot_runtime/main.py README.md app/back/tests/chatbot/test_chatbot_runtime_cli.py
git commit -m "feat: add chatbot runtime warmup cli"
```
