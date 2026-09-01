"""BGE-M3 embed + rerank server (and a Qwen llama-server supervisor) for a Lightning studio.

Runs BOTH models the chatbot needs from one command on the studio:
  - BGE-M3 embed + rerank over FastAPI (:8002), backed by ONE shared BGEM3FlagModel — same model and
    weights as local, so vectors and colbert+sparse+dense rerank scores are compatible with the
    corpus already indexed in Postgres (zero quality change).
  - Qwen3-1.7B (Q5_K_M) via a supervised llama-server (:8000, OpenAI-compatible) that auto-restarts
    on crash. Set START_QWEN=0 to run it separately.

Both are tuned for the 32-core CPU studio (all threads, fp32 for BGE, CPU llama-server). Attach a
GPU and set QWEN_NGL=99 (llama offload) — BGE picks up CUDA automatically — for the real speedup.

Run on the Lightning studio (ATTACH A GPU first, else it runs on CPU with no speedup):
    pip install "FlagEmbedding==1.3.4" "transformers==4.48.3" fastapi uvicorn
    python lightning_bge_server.py
The version pins mirror the combination proven to load BGE-M3 (FlagEmbedding 1.4 passes a `dtype`
kwarg that newer transformers rejects; 1.3.4 + transformers 4.48.3 is the known-good pair).
Then expose port 8002 — Lightning gives a public URL like https://8002-<id>.cloudspaces.litng.ai
(its proxy applies the same bearer auth as the llama.cpp studio). Use that URL as REMOTE_BGE_URL
and the studio's key as REMOTE_BGE_KEY on the SST side.

Endpoints (match what the SST remote client calls):
    POST /embed   {"texts": ["..."]}            -> {"vectors": [[float, ...], ...]}   (dense, L2-normalized)
    POST /rerank  {"query": "...", "passages": ["..."]} -> {"scores": [float, ...]}
    GET  /health                                 -> {"status": "ok"}
"""
from __future__ import annotations

import os

# Use every core of the 32-core studio: BGE-M3 embed + rerank are BLAS-bound, so more threads =
# faster on CPU. These env vars must be set BEFORE torch/transformers import (read at import time).
_cores = str(os.cpu_count() or 16)
os.environ.setdefault("OMP_NUM_THREADS", _cores)
os.environ.setdefault("MKL_NUM_THREADS", _cores)
os.environ.setdefault("HF_HUB_OFFLINE", "0")  # studio has internet; let it fetch BAAI/bge-m3 once

import shutil
import subprocess
import threading
import time

from fastapi import FastAPI
from pydantic import BaseModel
from FlagEmbedding import BGEM3FlagModel

import torch


def _qwen_supervisor() -> None:
    """Keep a CPU-optimized Qwen3-1.7B llama-server (Q5_K_M) alive on :8000, restarting on crash.

    Uses every core, thinking off, deterministic, KV-prefix reuse. `-ngl 0` = CPU; bump to 99 once a
    GPU is attached. Robust: if llama-server dies (crash/OOM) it relaunches after a short backoff, so
    the endpoint never stays dead. Skipped if llama-server is not on PATH or START_QWEN=0.
    """

    # Resolve the llama.cpp binary: explicit LLAMA_SERVER_BIN wins, else search PATH. The modern CLI
    # is `llama serve ...`; the older build is `llama-server ...`. If none is found, skip Qwen (keep
    # serving BGE) rather than crash.
    binary = (
        os.environ.get("LLAMA_SERVER_BIN")
        or shutil.which("llama")
        or shutil.which("llama-server")
        or shutil.which("llama-cpp-server")
    )
    if not binary:
        print(
            "[qwen] llama binary not found. Set LLAMA_SERVER_BIN=/path/to/llama (or llama-server), "
            "or run Qwen separately and start this with START_QWEN=0.",
            flush=True,
        )
        return

    # `llama` needs the `serve` subcommand; `llama-server` does not.
    subcommand = ["serve"] if os.path.basename(binary).split(".")[0] == "llama" else []
    command = [
        binary, *subcommand,
        "-hf", os.environ.get("QWEN_HF", "bartowski/Qwen_Qwen3-1.7B-GGUF:Q5_K_M"),
        "--host", "0.0.0.0", "--port", "8000",
        "--reasoning", "off",
        "-t", _cores, "-tb", _cores,
        "-c", "4096", "-n", "200",
        "-b", "1024", "-ub", "512", "-np", "1",
        "-ngl", os.environ.get("QWEN_NGL", "0"),  # 0 = CPU studio; set QWEN_NGL=99 with a GPU
        "--cache-prompt", "--cache-reuse", "256", "--cache-ram", "1024",
        "--load-mode", "mmap+mlock",
    ]
    while True:
        try:
            print(f"[qwen] starting {binary} on :8000 ({_cores} threads, ngl={os.environ.get('QWEN_NGL', '0')}) ...", flush=True)
            return_code = subprocess.call(command)
            print(f"[qwen] llama-server exited rc={return_code}; restarting in 3s", flush=True)
        except Exception as error:  # noqa: BLE001 - supervisor must never die on a transient error
            print(f"[qwen] supervisor error: {error}; restarting in 3s", flush=True)
        time.sleep(3)


# Start Qwen first so it downloads/loads in parallel with the BGE model below (both share the CPU,
# but the wall-clock overlap beats loading them one after the other).
if os.environ.get("START_QWEN", "1") != "0":
    threading.Thread(target=_qwen_supervisor, daemon=True).start()

torch.set_num_threads(int(_cores))
_use_gpu = torch.cuda.is_available()
# fp16 is a GPU win but a CPU pessimization: CPUs have no native fp16 matmul, so they upcast per op
# and run SLOWER than fp32. On this CPU studio (plenty of RAM) fp32 lets the 32-core BLAS run flat
# out; only switch to fp16 when a real GPU is attached.
_use_fp16 = _use_gpu
_device = "cuda" if _use_gpu else f"cpu x{_cores} threads (fp32)"
print(f"[bge-m3-remote] loading BAAI/bge-m3 on {_device}, fp16={_use_fp16} ...", flush=True)
MODEL = BGEM3FlagModel("BAAI/bge-m3", use_fp16=_use_fp16)
print(f"[bge-m3-remote] model loaded on {_device}; serving /embed /rerank /health on :8002", flush=True)
# BGE-M3's own combined-score weighting (must match the local BgeReranker: dense/sparse/colbert).
RERANK_WEIGHTS = [0.4, 0.2, 0.4]

app = FastAPI(title="bge-m3-remote")


class EmbedRequest(BaseModel):
    texts: list[str]


class RerankRequest(BaseModel):
    query: str
    passages: list[str]


@app.get("/health")
def health() -> dict:
    print("[health] ok", flush=True)
    return {"status": "ok"}


@app.post("/embed")
def embed(request: EmbedRequest) -> dict:
    start = time.time()
    print(f"[embed] IN  {len(request.texts)} text(s), first={request.texts[0][:60]!r} ...", flush=True)
    try:
        dense = MODEL.encode(request.texts, max_length=512)["dense_vecs"]
        print(f"[embed] OUT {len(dense)} vec(s) dim={len(dense[0]) if len(dense) else 0} in {time.time() - start:.2f}s", flush=True)
        return {"vectors": [list(map(float, v)) for v in dense]}
    except Exception as error:  # noqa: BLE001 - log then re-raise so the client sees a 500, not a hang
        print(f"[embed] ERROR after {time.time() - start:.2f}s: {error!r}", flush=True)
        raise


@app.post("/rerank")
def rerank(request: RerankRequest) -> dict:
    start = time.time()
    print(f"[rerank] IN  query={request.query[:60]!r} x{len(request.passages)} passage(s) ...", flush=True)
    if not request.passages:
        print("[rerank] OUT 0 (no passages)", flush=True)
        return {"scores": []}
    try:
        pairs = [[request.query, passage] for passage in request.passages]
        raw = MODEL.compute_score(pairs, weights_for_different_modes=RERANK_WEIGHTS)
        scores = raw["colbert+sparse+dense"] if isinstance(raw, dict) else raw
        if not isinstance(scores, list):
            scores = [scores]
        print(f"[rerank] OUT x{len(scores)} in {time.time() - start:.2f}s", flush=True)
        return {"scores": [float(s) for s in scores]}
    except Exception as error:  # noqa: BLE001 - log then re-raise
        print(f"[rerank] ERROR after {time.time() - start:.2f}s: {error!r}", flush=True)
        raise


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8002)
