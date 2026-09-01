"""ONNX query-embedding engine for BGE-M3 dense vectors.

The BGE-M3 dense query vector is the L2-normalized CLS token of the model's last hidden
state. Running that forward pass through onnxruntime (from bge-m3's cached ``onnx/model.onnx``)
is ~170x faster on CPU than FlagEmbedding's PyTorch path (~0.1s vs ~12s per query) and, crucially,
produces the **same** vector — validated cosine 1.0000 against ``BGEM3FlagModel.encode(...)['dense_vecs']``.
Same embedding space, so no corpus re-embed is needed; only the query path changes.

Query-only by design: document embedding (rebuild) keeps the full FlagEmbedding runtime, since
docs also need sparse/colbert heads. This engine implements the same ``EmbeddingEngine`` surface
as ``ProviderEngineAdapter`` so ``QueryEmbeddingService`` and the compatibility gate see no change.
"""

from __future__ import annotations

import glob
import os
from collections.abc import Sequence

from embedding.domain.models import Normalization


def _local_snapshot(model_name: str) -> str:
    repo = "models--" + model_name.replace("/", "--")
    hits = glob.glob(os.path.expanduser(f"~/.cache/huggingface/hub/{repo}/snapshots/*/"))
    if not hits:
        raise FileNotFoundError(f"no local HF snapshot for {model_name}; ONNX query embed needs it cached")
    return hits[0]


class OnnxBgeQueryEngine:
    """Embeds queries with BGE-M3's ONNX dense pass; matches the durable bge profile."""

    def __init__(self, *, model_name: str, dimension: int, max_length: int = 512) -> None:
        self._model_name = model_name
        self._dimension = dimension
        self._max_length = max_length
        self._session = None
        self._tokenizer = None
        self._input_names: set[str] = set()

    @property
    def provider_name(self) -> str:
        return "bge"

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def dimension(self) -> int:
        return self._dimension

    @property
    def normalization(self) -> Normalization:
        return "l2"

    @property
    def supports_queries(self) -> bool:
        return True

    def observe_revision(self) -> str:
        # The snapshot dir is named after the resolved HF commit; good enough as a runtime observation.
        return os.path.basename(os.path.normpath(_local_snapshot(self._model_name)))

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        raise NotImplementedError("OnnxBgeQueryEngine is query-only; document embedding uses FlagEmbedding")

    def embed_queries(self, texts: Sequence[str]) -> list[list[float]]:
        import numpy as np

        session, tokenizer, input_names = self._ensure_loaded()
        enc = tokenizer(
            list(texts), padding=True, truncation=True,
            max_length=self._max_length, return_tensors="np",
        )
        feed = {k: v for k, v in enc.items() if k in input_names}
        last_hidden = session.run(None, feed)[0]  # [batch, seq, hidden]
        cls = last_hidden[:, 0, :]
        normalized = cls / np.linalg.norm(cls, axis=1, keepdims=True)
        return normalized.astype(float).tolist()

    def warm(self) -> None:
        """Load the ONNX session + tokenizer now (cheap: ~1s) so the first query pays nothing."""

        self._ensure_loaded()

    def _ensure_loaded(self):
        if self._session is None:
            os.environ.setdefault("HF_HUB_OFFLINE", "1")
            os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
            import onnxruntime as ort
            from transformers import AutoTokenizer

            snapshot = _local_snapshot(self._model_name)
            self._tokenizer = AutoTokenizer.from_pretrained(snapshot)
            self._session = ort.InferenceSession(
                os.path.join(snapshot, "onnx", "model.onnx"),
                providers=["CPUExecutionProvider"],
            )
            self._input_names = {i.name for i in self._session.get_inputs()}
        return self._session, self._tokenizer, self._input_names
