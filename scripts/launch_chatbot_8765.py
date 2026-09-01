"""Launch the full SST chatbot API on :8765 (the port chatbot-aplicado dispatches to).

Loads secrets.env into the process env (feature flags, webhook callback URL + bearer,
Postgres), builds the postgres-backed pipeline, and serves via uvicorn. Startup warms
BGE-M3 (~110s) so the first real question pays no cold load.
"""
import os

# Force cache-only model loading BEFORE transformers/huggingface_hub are first imported
# (they read these flags at their own import time; setting later is too late). This box is
# offline; every model — bge-m3, the light reranker, embedders — is already in the HF cache.
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app" / "back" / "src"))
sys.path.insert(0, str(ROOT / "scripts" / "indexing"))

from prepare_postgres_indexing import build_dsn_from_env, load_env_file

env = dict(load_env_file(ROOT / "secrets.env"))
for key, value in env.items():
    os.environ[key] = value
os.environ["SST_POSTGRES_DSN"] = build_dsn_from_env(env)
os.environ["SST_PERSISTENCE_MODE"] = "postgres"

# --- Retrieval speed (Fase 0/1, free) ---------------------------------------
# Rerank BGE-M3 on CPU costs ~2s/candidate; pool 30 (default) took ~85s, pool 10 ~13s
# with negligible change to the final top-4. This is the single biggest retrieval win.
os.environ.setdefault("RETRIEVAL_RERANK_POOL_SIZE", "10")
# fp16 BGE-M3 weights: ~0.5GB less RAM, dense cosine 1.0000 vs fp32, no CPU slowdown. On an
# 8GB box the real bottleneck is memory swap, so trimming the model footprint helps latency.
os.environ.setdefault("BGE_USE_FP16", "true")
# Use every core for the BGE torch runtime (embed + rerank). Marginal on this box
# (BGE-M3 is RAM-bandwidth bound, measured ~noise), but free; set before torch imports.
_cores = str(os.cpu_count() or 10)
os.environ.setdefault("OMP_NUM_THREADS", _cores)
os.environ.setdefault("MKL_NUM_THREADS", _cores)
try:
    import torch

    torch.set_num_threads(int(_cores))
except Exception:
    pass

from api.app import create_app
from api.dependencies import build_pipeline_services_from_env

services = build_pipeline_services_from_env(
    chunks_root=ROOT / "data" / "projects" / "sst-general" / "chunks",
    embeddings_root=ROOT / "data" / "projects" / "sst-general" / "embeddings",
)
app = create_app(services=services)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8765)
