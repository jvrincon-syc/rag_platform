from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RetrievedCandidate:
    node_id: str
    text: str
    score: float
    source: str
    metadata: dict[str, Any]


def reciprocal_rank_fusion(
    ranked_lists: list[list[RetrievedCandidate]],
    *,
    k: int = 60,
) -> list[RetrievedCandidate]:
    scores: dict[str, float] = {}
    candidates: dict[str, RetrievedCandidate] = {}
    sources: dict[str, list[str]] = {}
    for ranked in ranked_lists:
        for rank, candidate in enumerate(ranked, start=1):
            scores[candidate.node_id] = scores.get(candidate.node_id, 0.0) + 1.0 / (k + rank)
            candidates.setdefault(candidate.node_id, candidate)
            source_list = sources.setdefault(candidate.node_id, [])
            if candidate.source not in source_list:
                source_list.append(candidate.source)

    fused: list[RetrievedCandidate] = []
    for node_id, candidate in candidates.items():
        metadata = {
            **candidate.metadata,
            "retrieval_sources": sources[node_id],
        }
        fused.append(
            RetrievedCandidate(
                node_id=node_id,
                text=candidate.text,
                score=scores[node_id],
                source="fusion",
                metadata=metadata,
            )
        )
    return sorted(fused, key=lambda item: item.score, reverse=True)


def vector_primary_hybrid_fusion(
    vector_candidates: list[RetrievedCandidate],
    lexical_candidates: list[RetrievedCandidate],
    *,
    k: int = 60,
    lexical_boost: float = 0.15,
    rescue_boost: float = 0.10,
) -> list[RetrievedCandidate]:
    """Vector-primary fusion: dense remains the authority, lexical refines.

    Rules:
    1. Dense candidates keep their RRF-based rank (base authority).
    2. Dense + lexical: moderate boost via ``lexical_boost`` additive.
    3. Lexical-only: rescue candidates with ``rescue_boost``, ranked below
       all vector-backed results.
    4. Lexical-only cannot jump above any vector-backed candidate.
    """
    if not vector_candidates and not lexical_candidates:
        return []

    lexical_ids = {c.node_id for c in lexical_candidates}
    vector_ids = {c.node_id for c in vector_candidates}
    all_ids = vector_ids | lexical_ids

    # Lexical-only candidates ranked by their lexical score (descending).
    rescue_by_score: dict[str, float] = {
        c.node_id: c.score for c in lexical_candidates if c.node_id not in vector_ids
    }
    sorted_rescue_ids = sorted(rescue_by_score, key=rescue_by_score.get, reverse=True)  # type: ignore[arg-type]

    # All candidates keyed by node_id, preferring vector text/metadata when available.
    by_id: dict[str, RetrievedCandidate] = {}
    for c in vector_candidates:
        by_id[c.node_id] = c
    for c in lexical_candidates:
        if c.node_id not in by_id:
            by_id[c.node_id] = c

    # Base score: RRF over all candidates (same formula as reciprocal_rank_fusion).
    rrf_scores: dict[str, float] = {}
    sources_map: dict[str, list[str]] = {}
    for rank, c in enumerate(vector_candidates, start=1):
        rrf_scores[c.node_id] = rrf_scores.get(c.node_id, 0.0) + 1.0 / (k + rank)
        src = sources_map.setdefault(c.node_id, [])
        if c.source not in src:
            src.append(c.source)
    for rank, c in enumerate(lexical_candidates, start=1):
        rrf_scores[c.node_id] = rrf_scores.get(c.node_id, 0.0) + 1.0 / (k + rank)
        src = sources_map.setdefault(c.node_id, [])
        if c.source not in src:
            src.append(c.source)

    # Apply boosts: lexical-only gets rescue_boost; vector+lexical gets lexical_boost.
    boosted_scores: dict[str, float] = {}
    for nid in all_ids:
        base = rrf_scores.get(nid, 0.0)
        in_vector = nid in vector_ids
        in_lexical = nid in lexical_ids
        if in_vector and in_lexical:
            boosted_scores[nid] = base + lexical_boost
        elif in_lexical:
            boosted_scores[nid] = rescue_boost
        else:
            boosted_scores[nid] = base

    # Compute minimum vector-backed score as a floor for rescue candidates.
    vector_backed = [nid for nid in all_ids if nid in vector_ids]
    min_vector_score = min((boosted_scores[nid] for nid in vector_backed), default=0.0)
    rescue_floor = min_vector_score * 0.9 if vector_backed else rescue_boost

    # Build result: vector-backed sorted by boosted score, then rescue candidates.
    result: list[RetrievedCandidate] = []
    for nid in sorted(
        [nid for nid in all_ids if nid in vector_ids],
        key=lambda x: boosted_scores[x],
        reverse=True,
    ):
        c = by_id[nid]
        metadata = {
            **c.metadata,
            "retrieval_sources": sources_map.get(nid, [c.source]),
        }
        result.append(
            RetrievedCandidate(
                node_id=nid,
                text=c.text,
                score=boosted_scores[nid],
                source="fusion",
                metadata=metadata,
            )
        )

    for nid in sorted_rescue_ids:
        c = by_id[nid]
        metadata = {
            **c.metadata,
            "retrieval_sources": [c.source],
        }
        result.append(
            RetrievedCandidate(
                node_id=nid,
                text=c.text,
                score=rescue_floor,
                source="fusion",
                metadata=metadata,
            )
        )

    return result
