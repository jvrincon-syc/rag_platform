"""BGE-M3 + instrumented Qwen llama-server for a 4-vCPU / 13-GB Lightning studio.

Public endpoints:
  :8002  POST /embed
         POST /rerank
         GET  /health
         GET  /metrics

  :8000  OpenAI-compatible proxy for Qwen
         /v1/* -> internal llama-server on 127.0.0.1:8001
         GET /health
         GET /metrics

Why the proxy?
The original script exposed llama-server directly on :8000, so Python could not reliably log
"LLM request arrived -> upstream accepted -> first streamed token -> response completed". This
version keeps the external contract on :8000 but moves the real llama-server to :8001 and places a
very small FastAPI/httpx proxy in front of it.

Tracing headers (recommended from the SST backend):
  X-Request-ID:      one UUID preserved for the whole chatbot request
  X-Trace-Start-Ms:  Unix epoch milliseconds when the chatbot backend first received the question

With those two headers, BGE and LLM logs show exactly how many milliseconds had elapsed before the
request reached each service.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import threading
import time
import uuid
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, AsyncIterator

# ---------------------------------------------------------------------------
# CPU tuning MUST happen before torch / transformers / FlagEmbedding imports.
# ---------------------------------------------------------------------------
HOST_CPUS = os.cpu_count() or 4
CPU_BUDGET = max(1, min(int(os.environ.get("CPU_BUDGET", "4")), HOST_CPUS))
BGE_THREADS = max(1, min(int(os.environ.get("BGE_THREADS", str(CPU_BUDGET))), CPU_BUDGET))
QWEN_THREADS = max(1, min(int(os.environ.get("QWEN_THREADS", "3")), CPU_BUDGET))
QWEN_BATCH_THREADS = max(1, min(int(os.environ.get("QWEN_BATCH_THREADS", str(CPU_BUDGET))), CPU_BUDGET))

# Do not inherit an accidental 32-thread BLAS configuration on a 4-vCPU machine.
os.environ["OMP_NUM_THREADS"] = str(BGE_THREADS)
os.environ["MKL_NUM_THREADS"] = str(BGE_THREADS)
os.environ["OPENBLAS_NUM_THREADS"] = str(BGE_THREADS)
os.environ["NUMEXPR_NUM_THREADS"] = str(BGE_THREADS)
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("HF_HUB_OFFLINE", "0")

import httpx  # noqa: E402
import torch  # noqa: E402
import uvicorn  # noqa: E402
from fastapi import FastAPI, HTTPException, Request, Response  # noqa: E402
from fastapi.responses import JSONResponse, StreamingResponse  # noqa: E402
from FlagEmbedding import BGEM3FlagModel  # noqa: E402
from pydantic import BaseModel  # noqa: E402

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
BGE_PORT = int(os.environ.get("BGE_PORT", "8002"))
QWEN_PUBLIC_PORT = int(os.environ.get("QWEN_PORT", "8000"))
QWEN_INTERNAL_PORT = int(os.environ.get("QWEN_INTERNAL_PORT", "8001"))

EMBED_MAX_LENGTH = int(os.environ.get("EMBED_MAX_LENGTH", "512"))
EMBED_BATCH_SIZE = int(os.environ.get("EMBED_BATCH_SIZE", "4"))
RERANK_QUERY_MAX_LENGTH = int(os.environ.get("RERANK_QUERY_MAX_LENGTH", "512"))
RERANK_PASSAGE_MAX_LENGTH = int(os.environ.get("RERANK_PASSAGE_MAX_LENGTH", "512"))
RERANK_BATCH_SIZE = int(os.environ.get("RERANK_BATCH_SIZE", "4"))
RERANK_WEIGHTS = [0.4, 0.2, 0.4]

METRIC_WINDOW = int(os.environ.get("METRIC_WINDOW", "500"))
MODEL_LOCK = threading.Lock()


def _now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="milliseconds")


def _trace_elapsed_ms(request: Request) -> float | None:
    raw = request.headers.get("x-trace-start-ms")
    if not raw:
        return None
    try:
        return max(0.0, time.time() * 1000.0 - float(raw))
    except ValueError:
        return None


def _request_id(request: Request) -> str:
    rid = getattr(request.state, "request_id", None) or request.headers.get("x-request-id")
    if not rid:
        rid = uuid.uuid4().hex[:12]
    return rid


def log_event(component: str, event: str, *, request_id: str = "-", **fields: Any) -> None:
    parts = [f"ts={_now_iso()}", f"component={component}", f"event={event}", f"rid={request_id}"]
    for key, value in fields.items():
        if value is None:
            continue
        if isinstance(value, float):
            parts.append(f"{key}={value:.2f}")
        else:
            text = str(value).replace("\n", "\\n")
            parts.append(f"{key}={text}")
    print(" | ".join(parts), flush=True)


class MetricStore:
    def __init__(self, window: int) -> None:
        self._values: dict[str, deque[float]] = defaultdict(lambda: deque(maxlen=window))
        self._lock = threading.Lock()

    def record(self, name: str, value_ms: float) -> None:
        with self._lock:
            self._values[name].append(float(value_ms))

    @staticmethod
    def _percentile(values: list[float], p: float) -> float:
        if not values:
            return 0.0
        values = sorted(values)
        idx = int(round((len(values) - 1) * p))
        return values[idx]

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            copied = {name: list(values) for name, values in self._values.items()}
        out: dict[str, Any] = {}
        for name, values in copied.items():
            if not values:
                continue
            out[name] = {
                "count_in_window": len(values),
                "avg_ms": round(sum(values) / len(values), 2),
                "p50_ms": round(self._percentile(values, 0.50), 2),
                "p95_ms": round(self._percentile(values, 0.95), 2),
                "max_ms": round(max(values), 2),
            }
        return out


METRICS = MetricStore(METRIC_WINDOW)


# ---------------------------------------------------------------------------
# Qwen llama-server supervisor (:8001 internal)
# ---------------------------------------------------------------------------
def _qwen_command(binary: str) -> list[str]:
    subcommand = ["serve"] if os.path.basename(binary).split(".")[0] == "llama" else []
    command = [
        binary,
        *subcommand,
        "-hf",
        os.environ.get("QWEN_HF", "bartowski/Qwen_Qwen3-1.7B-GGUF:Q5_K_M"),
        "--host",
        "127.0.0.1",
        "--port",
        str(QWEN_INTERNAL_PORT),
        "--reasoning",
        "off",
        "-t",
        str(QWEN_THREADS),
        "-tb",
        str(QWEN_BATCH_THREADS),
        "-c",
        os.environ.get("QWEN_CTX", "2048"),
        "-n",
        os.environ.get("QWEN_MAX_TOKENS", "120"),
        "-b",
        os.environ.get("QWEN_BATCH", "512"),
        "-ub",
        os.environ.get("QWEN_UBATCH", "256"),
        "-np",
        "1",
        "-ngl",
        os.environ.get("QWEN_NGL", "0"),
        "-ctk",
        os.environ.get("QWEN_CTK", "q4_0"),
        "-ctv",
        os.environ.get("QWEN_CTV", "q4_0"),
        "--cache-prompt",
        "--cache-reuse",
        os.environ.get("QWEN_CACHE_REUSE", "64"),
        "--cache-ram",
        os.environ.get("QWEN_CACHE_RAM", "64"),
        "--poll",
        os.environ.get("QWEN_POLL", "0"),
        "--prio",
        os.environ.get("QWEN_PRIO", "-1"),
    ]
    return command


def _qwen_supervisor() -> None:
    binary = (
        os.environ.get("LLAMA_SERVER_BIN")
        or shutil.which("llama")
        or shutil.which("llama-server")
        or shutil.which("llama-cpp-server")
    )
    if not binary:
        log_event(
            "qwen-supervisor",
            "binary_not_found",
            detail="Set LLAMA_SERVER_BIN or START_QWEN=0",
        )
        return

    command = _qwen_command(binary)
    raw_logs = os.environ.get("QWEN_RAW_LOGS", "1") != "0"

    while True:
        started = time.perf_counter()
        try:
            log_event(
                "qwen-supervisor",
                "starting",
                binary=binary,
                internal_port=QWEN_INTERNAL_PORT,
                threads=QWEN_THREADS,
                batch_threads=QWEN_BATCH_THREADS,
                ctx=os.environ.get("QWEN_CTX", "2048"),
                ngl=os.environ.get("QWEN_NGL", "0"),
            )
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
            assert process.stdout is not None
            for raw_line in process.stdout:
                line = raw_line.rstrip()
                if not line:
                    continue
                if raw_logs:
                    # llama.cpp itself prints prompt-eval/eval timings. Prefixing them with a wall-clock
                    # timestamp makes those timings correlate with the proxy's request-id timeline.
                    log_event("llama", "native", line=line)
            return_code = process.wait()
            log_event(
                "qwen-supervisor",
                "exited",
                rc=return_code,
                uptime_s=time.perf_counter() - started,
                restart_in_s=3,
            )
        except Exception as error:  # supervisor must survive transient process errors
            log_event("qwen-supervisor", "error", error=repr(error), restart_in_s=3)
        time.sleep(3)


# ---------------------------------------------------------------------------
# Instrumented OpenAI-compatible proxy (:8000 public -> :8001 internal)
# ---------------------------------------------------------------------------
@asynccontextmanager
async def _llm_proxy_lifespan(app: FastAPI) -> AsyncIterator[None]:
    timeout = httpx.Timeout(connect=10.0, read=None, write=30.0, pool=30.0)
    limits = httpx.Limits(max_connections=8, max_keepalive_connections=4)
    app.state.client = httpx.AsyncClient(timeout=timeout, limits=limits)
    try:
        yield
    finally:
        await app.state.client.aclose()


LLM_PROXY_APP = FastAPI(title="qwen-traced-proxy", lifespan=_llm_proxy_lifespan)


def _check_optional_proxy_auth(request: Request) -> None:
    expected = os.environ.get("LLAMA_API_KEY")
    if not expected:
        return
    actual = request.headers.get("authorization", "")
    if actual != f"Bearer {expected}":
        raise HTTPException(status_code=401, detail="Invalid API Key")


def _forward_headers(request: Request, rid: str) -> dict[str, str]:
    headers: dict[str, str] = {
        "x-request-id": rid,
        "content-type": request.headers.get("content-type", "application/json"),
    }
    trace_start = request.headers.get("x-trace-start-ms")
    if trace_start:
        headers["x-trace-start-ms"] = trace_start
    return headers


def _inspect_llm_payload(body: bytes) -> dict[str, Any]:
    try:
        payload = json.loads(body or b"{}")
    except json.JSONDecodeError:
        return {"stream": False}
    messages = payload.get("messages") or []
    prompt_chars = 0
    for message in messages:
        content = message.get("content", "") if isinstance(message, dict) else ""
        if isinstance(content, str):
            prompt_chars += len(content)
    return {
        "stream": bool(payload.get("stream", False)),
        "model": payload.get("model"),
        "messages": len(messages),
        "prompt_chars": prompt_chars,
        "max_tokens": payload.get("max_tokens"),
    }


@LLM_PROXY_APP.get("/health")
async def llm_proxy_health(request: Request) -> Response:
    _check_optional_proxy_auth(request)
    started = time.perf_counter()
    try:
        response = await request.app.state.client.get(f"http://127.0.0.1:{QWEN_INTERNAL_PORT}/health")
        return JSONResponse(
            status_code=response.status_code,
            content={
                "status": "ok" if response.is_success else "upstream_error",
                "upstream_status": response.status_code,
                "latency_ms": round((time.perf_counter() - started) * 1000.0, 2),
            },
        )
    except httpx.HTTPError as error:
        return JSONResponse(status_code=503, content={"status": "unavailable", "error": str(error)})


@LLM_PROXY_APP.get("/metrics")
async def llm_proxy_metrics(request: Request) -> dict[str, Any]:
    _check_optional_proxy_auth(request)
    return {"metrics": METRICS.snapshot()}


@LLM_PROXY_APP.api_route("/v1/{path:path}", methods=["GET", "POST"])
async def proxy_openai(path: str, request: Request) -> Response:
    _check_optional_proxy_auth(request)
    rid = request.headers.get("x-request-id") or uuid.uuid4().hex[:12]
    start = time.perf_counter()
    body = await request.body()
    info = _inspect_llm_payload(body)
    since_trace = _trace_elapsed_ms(request)

    log_event(
        "llm-proxy",
        "IN",
        request_id=rid,
        endpoint=f"/v1/{path}",
        since_trace_start_ms=since_trace,
        stream=info.get("stream"),
        model=info.get("model"),
        messages=info.get("messages"),
        prompt_chars=info.get("prompt_chars"),
        max_tokens=info.get("max_tokens"),
    )

    upstream_url = f"http://127.0.0.1:{QWEN_INTERNAL_PORT}/v1/{path}"
    method = request.method.upper()
    headers = _forward_headers(request, rid)
    client: httpx.AsyncClient = request.app.state.client

    if info.get("stream"):
        try:
            built = client.build_request(method, upstream_url, content=body, headers=headers)
            upstream = await client.send(built, stream=True)
        except httpx.HTTPError as error:
            elapsed = (time.perf_counter() - start) * 1000.0
            METRICS.record("llm.error_ms", elapsed)
            log_event("llm-proxy", "ERROR_CONNECT", request_id=rid, total_ms=elapsed, error=repr(error))
            raise HTTPException(status_code=503, detail="Qwen upstream unavailable") from error

        headers_ms = (time.perf_counter() - start) * 1000.0
        METRICS.record("llm.headers_ms", headers_ms)
        log_event(
            "llm-proxy",
            "UPSTREAM_HEADERS",
            request_id=rid,
            status=upstream.status_code,
            headers_ms=headers_ms,
        )

        # If llama-server rejects immediately, preserve its actual HTTP status/body.
        if upstream.status_code >= 400:
            raw = await upstream.aread()
            await upstream.aclose()
            total_ms = (time.perf_counter() - start) * 1000.0
            METRICS.record("llm.total_ms", total_ms)
            log_event("llm-proxy", "OUT_ERROR", request_id=rid, status=upstream.status_code, total_ms=total_ms)
            return Response(
                content=raw,
                status_code=upstream.status_code,
                media_type=upstream.headers.get("content-type", "application/json"),
                headers={"x-request-id": rid},
            )

        async def stream_body() -> AsyncIterator[bytes]:
            first_chunk_logged = False
            first_token_logged = False
            chunks = 0
            bytes_out = 0
            sse_buffer = ""
            try:
                async for chunk in upstream.aiter_raw():
                    if not chunk:
                        continue
                    chunks += 1
                    bytes_out += len(chunk)
                    if not first_chunk_logged:
                        first_chunk_ms = (time.perf_counter() - start) * 1000.0
                        METRICS.record("llm.first_chunk_ms", first_chunk_ms)
                        log_event("llm-proxy", "FIRST_CHUNK", request_id=rid, elapsed_ms=first_chunk_ms)
                        first_chunk_logged = True

                    if not first_token_logged:
                        # Inspect SSE without changing what is forwarded to the client.
                        sse_buffer += chunk.decode("utf-8", errors="ignore")
                        while "\n\n" in sse_buffer:
                            event, sse_buffer = sse_buffer.split("\n\n", 1)
                            for line in event.splitlines():
                                if not line.startswith("data:"):
                                    continue
                                data = line[5:].strip()
                                if not data or data == "[DONE]":
                                    continue
                                try:
                                    payload = json.loads(data)
                                    choices = payload.get("choices") or []
                                    delta = choices[0].get("delta", {}) if choices else {}
                                    content = delta.get("content")
                                    if content:
                                        first_token_ms = (time.perf_counter() - start) * 1000.0
                                        METRICS.record("llm.first_token_ms", first_token_ms)
                                        log_event(
                                            "llm-proxy",
                                            "FIRST_TOKEN",
                                            request_id=rid,
                                            elapsed_ms=first_token_ms,
                                        )
                                        first_token_logged = True
                                        break
                                except (json.JSONDecodeError, AttributeError, IndexError):
                                    pass
                            if first_token_logged:
                                break
                    yield chunk
            except Exception as error:
                elapsed = (time.perf_counter() - start) * 1000.0
                METRICS.record("llm.stream_error_ms", elapsed)
                log_event("llm-proxy", "STREAM_ERROR", request_id=rid, elapsed_ms=elapsed, error=repr(error))
                raise
            finally:
                await upstream.aclose()
                total_ms = (time.perf_counter() - start) * 1000.0
                METRICS.record("llm.total_ms", total_ms)
                log_event(
                    "llm-proxy",
                    "OUT",
                    request_id=rid,
                    status=upstream.status_code,
                    total_ms=total_ms,
                    chunks=chunks,
                    bytes=bytes_out,
                )

        return StreamingResponse(
            stream_body(),
            status_code=upstream.status_code,
            media_type=upstream.headers.get("content-type", "text/event-stream"),
            headers={"x-request-id": rid, "cache-control": "no-cache"},
        )

    # Non-streaming path.
    try:
        upstream = await client.request(method, upstream_url, content=body, headers=headers)
    except httpx.HTTPError as error:
        elapsed = (time.perf_counter() - start) * 1000.0
        METRICS.record("llm.error_ms", elapsed)
        log_event("llm-proxy", "ERROR_CONNECT", request_id=rid, total_ms=elapsed, error=repr(error))
        raise HTTPException(status_code=503, detail="Qwen upstream unavailable") from error

    total_ms = (time.perf_counter() - start) * 1000.0
    METRICS.record("llm.total_ms", total_ms)
    usage: dict[str, Any] = {}
    try:
        parsed = upstream.json()
        usage = parsed.get("usage") or {} if isinstance(parsed, dict) else {}
    except Exception:
        pass
    log_event(
        "llm-proxy",
        "OUT",
        request_id=rid,
        status=upstream.status_code,
        total_ms=total_ms,
        prompt_tokens=usage.get("prompt_tokens"),
        completion_tokens=usage.get("completion_tokens"),
        total_tokens=usage.get("total_tokens"),
        bytes=len(upstream.content),
    )
    media_type = upstream.headers.get("content-type", "application/json").split(";", 1)[0]
    return Response(
        content=upstream.content,
        status_code=upstream.status_code,
        media_type=media_type,
        headers={"x-request-id": rid},
    )


def _run_llm_proxy() -> None:
    log_event("llm-proxy", "starting", public_port=QWEN_PUBLIC_PORT, upstream_port=QWEN_INTERNAL_PORT)
    config = uvicorn.Config(
        LLM_PROXY_APP,
        host="0.0.0.0",
        port=QWEN_PUBLIC_PORT,
        workers=1,
        log_level="warning",
        access_log=False,
    )
    uvicorn.Server(config).run()


# ---------------------------------------------------------------------------
# Start Qwen + proxy before BGE load so Qwen model download/load overlaps BGE.
# ---------------------------------------------------------------------------
if os.environ.get("START_QWEN", "1") != "0":
    threading.Thread(target=_qwen_supervisor, daemon=True, name="qwen-supervisor").start()

if os.environ.get("START_LLM_PROXY", "1") != "0":
    threading.Thread(target=_run_llm_proxy, daemon=True, name="llm-proxy").start()

# ---------------------------------------------------------------------------
# BGE-M3 model
# ---------------------------------------------------------------------------
torch.set_num_threads(BGE_THREADS)
try:
    torch.set_num_interop_threads(1)
except RuntimeError:
    pass

USE_GPU = torch.cuda.is_available()
USE_FP16 = USE_GPU
DEVICE_LABEL = "cuda(fp16)" if USE_GPU else f"cpu({BGE_THREADS} threads, fp32)"

load_started = time.perf_counter()
log_event(
    "bge",
    "MODEL_LOAD_START",
    device=DEVICE_LABEL,
    host_cpus=HOST_CPUS,
    cpu_budget=CPU_BUDGET,
    embed_batch=EMBED_BATCH_SIZE,
    rerank_batch=RERANK_BATCH_SIZE,
)
MODEL = BGEM3FlagModel("BAAI/bge-m3", use_fp16=USE_FP16)
load_s = time.perf_counter() - load_started
log_event("bge", "MODEL_LOAD_DONE", device=DEVICE_LABEL, load_s=load_s)


# ---------------------------------------------------------------------------
# BGE FastAPI (:8002)
# ---------------------------------------------------------------------------
app = FastAPI(title="bge-m3-remote-traced")


class EmbedRequest(BaseModel):
    texts: list[str]


class RerankRequest(BaseModel):
    query: str
    passages: list[str]


@app.middleware("http")
async def trace_http(request: Request, call_next):
    rid = request.headers.get("x-request-id") or uuid.uuid4().hex[:12]
    request.state.request_id = rid
    started = time.perf_counter()
    log_event(
        "bge-http",
        "IN",
        request_id=rid,
        method=request.method,
        path=request.url.path,
        since_trace_start_ms=_trace_elapsed_ms(request),
    )
    try:
        response = await call_next(request)
    except Exception as error:
        total_ms = (time.perf_counter() - started) * 1000.0
        log_event("bge-http", "ERROR", request_id=rid, path=request.url.path, total_ms=total_ms, error=repr(error))
        raise
    total_ms = (time.perf_counter() - started) * 1000.0
    response.headers["x-request-id"] = rid
    response.headers["x-server-total-ms"] = f"{total_ms:.2f}"
    log_event(
        "bge-http",
        "OUT",
        request_id=rid,
        path=request.url.path,
        status=response.status_code,
        total_ms=total_ms,
    )
    return response


@app.get("/health")
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "device": DEVICE_LABEL,
        "host_cpus": HOST_CPUS,
        "cpu_budget": CPU_BUDGET,
        "bge_threads": BGE_THREADS,
        "qwen_threads": QWEN_THREADS,
        "qwen_batch_threads": QWEN_BATCH_THREADS,
        "embed_batch_size": EMBED_BATCH_SIZE,
        "embed_max_length": EMBED_MAX_LENGTH,
        "rerank_batch_size": RERANK_BATCH_SIZE,
        "rerank_query_max_length": RERANK_QUERY_MAX_LENGTH,
        "rerank_passage_max_length": RERANK_PASSAGE_MAX_LENGTH,
    }


@app.get("/metrics")
def metrics() -> dict[str, Any]:
    return {
        "window": METRIC_WINDOW,
        "metrics": METRICS.snapshot(),
    }


@app.post("/embed")
def embed(payload: EmbedRequest, request: Request) -> dict[str, Any]:
    rid = _request_id(request)
    total_start = time.perf_counter()
    if not payload.texts:
        log_event("bge-embed", "EMPTY", request_id=rid)
        return {"vectors": []}

    total_chars = sum(len(text) for text in payload.texts)
    log_event(
        "bge-embed",
        "ARRIVED",
        request_id=rid,
        texts=len(payload.texts),
        chars=total_chars,
        first=repr(payload.texts[0][:80]),
        since_trace_start_ms=_trace_elapsed_ms(request),
    )

    queue_start = time.perf_counter()
    with MODEL_LOCK:
        queue_ms = (time.perf_counter() - queue_start) * 1000.0
        METRICS.record("embed.queue_ms", queue_ms)
        log_event("bge-embed", "MODEL_BEGIN", request_id=rid, queue_ms=queue_ms)

        model_start = time.perf_counter()
        dense = MODEL.encode(
            payload.texts,
            batch_size=EMBED_BATCH_SIZE,
            max_length=EMBED_MAX_LENGTH,
            return_dense=True,
            return_sparse=False,
            return_colbert_vecs=False,
        )["dense_vecs"]
        model_ms = (time.perf_counter() - model_start) * 1000.0
        METRICS.record("embed.model_ms", model_ms)
        log_event(
            "bge-embed",
            "MODEL_DONE",
            request_id=rid,
            model_ms=model_ms,
            vectors=len(dense),
            dim=len(dense[0]) if len(dense) else 0,
        )

    serialize_start = time.perf_counter()
    vectors = [list(map(float, vector)) for vector in dense]
    serialize_ms = (time.perf_counter() - serialize_start) * 1000.0
    total_ms = (time.perf_counter() - total_start) * 1000.0
    METRICS.record("embed.serialize_ms", serialize_ms)
    METRICS.record("embed.total_ms", total_ms)
    log_event(
        "bge-embed",
        "DONE",
        request_id=rid,
        queue_ms=queue_ms,
        model_ms=model_ms,
        serialize_ms=serialize_ms,
        total_ms=total_ms,
    )
    return {"vectors": vectors}


@app.post("/rerank")
def rerank(payload: RerankRequest, request: Request) -> dict[str, Any]:
    rid = _request_id(request)
    total_start = time.perf_counter()
    if not payload.passages:
        log_event("bge-rerank", "EMPTY", request_id=rid)
        return {"scores": []}

    total_chars = len(payload.query) + sum(len(p) for p in payload.passages)
    log_event(
        "bge-rerank",
        "ARRIVED",
        request_id=rid,
        passages=len(payload.passages),
        chars=total_chars,
        query=repr(payload.query[:80]),
        since_trace_start_ms=_trace_elapsed_ms(request),
    )

    pairs = [[payload.query, passage] for passage in payload.passages]
    pair_build_ms = (time.perf_counter() - total_start) * 1000.0
    METRICS.record("rerank.pair_build_ms", pair_build_ms)

    queue_start = time.perf_counter()
    with MODEL_LOCK:
        queue_ms = (time.perf_counter() - queue_start) * 1000.0
        METRICS.record("rerank.queue_ms", queue_ms)
        log_event("bge-rerank", "MODEL_BEGIN", request_id=rid, queue_ms=queue_ms)

        model_start = time.perf_counter()
        raw = MODEL.compute_score(
            pairs,
            batch_size=RERANK_BATCH_SIZE,
            max_query_length=RERANK_QUERY_MAX_LENGTH,
            max_passage_length=RERANK_PASSAGE_MAX_LENGTH,
            weights_for_different_modes=RERANK_WEIGHTS,
        )
        model_ms = (time.perf_counter() - model_start) * 1000.0
        METRICS.record("rerank.model_ms", model_ms)

    scores = raw["colbert+sparse+dense"] if isinstance(raw, dict) else raw
    if not isinstance(scores, list):
        scores = [scores]
    convert_start = time.perf_counter()
    out_scores = [float(score) for score in scores]
    convert_ms = (time.perf_counter() - convert_start) * 1000.0
    total_ms = (time.perf_counter() - total_start) * 1000.0
    METRICS.record("rerank.convert_ms", convert_ms)
    METRICS.record("rerank.total_ms", total_ms)
    log_event(
        "bge-rerank",
        "DONE",
        request_id=rid,
        queue_ms=queue_ms,
        model_ms=model_ms,
        convert_ms=convert_ms,
        total_ms=total_ms,
        scores=len(out_scores),
    )
    return {"scores": out_scores}


if __name__ == "__main__":
    log_event(
        "server",
        "READY_TO_SERVE",
        bge_port=BGE_PORT,
        qwen_public_port=QWEN_PUBLIC_PORT,
        qwen_internal_port=QWEN_INTERNAL_PORT,
        cpu_budget=CPU_BUDGET,
        bge_threads=BGE_THREADS,
        qwen_threads=QWEN_THREADS,
    )
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=BGE_PORT,
        workers=1,
        log_level="warning",
        access_log=False,
    )
