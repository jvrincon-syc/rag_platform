"""Direct-FAQ resolver: a fast lexical/fuzzy shortcut checked BEFORE the BGE embedding path.

Loads ``sst-faq-80.md`` (80 curated Q&A), normalizes per the file's frontmatter rules, and matches
an incoming question with stdlib ``difflib`` ratio + token Jaccard — no heavy dependency, no
embedding, sub-10ms over 80 entries. Because the match is milliseconds and the embed is seconds,
the retrieval port checks the FAQ first: on a confident hit it answers directly and the embed never
runs; on a miss it returns ``None`` and the normal release-scoped retrieval proceeds. That delivers
"si está en FAQ se para el embedding, si no continúa" without spending embed compute on hits.

rapidfuzz would be a drop-in upgrade for the scorer, but difflib keeps this dependency-free and
offline.
"""

from __future__ import annotations

import difflib
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class FaqMatch:
    """A resolved FAQ hit: the curated answer plus audit metadata."""

    faq_id: str
    question: str
    answer: str
    status: str
    score: float
    reference: dict[str, Any] | None


def normalize(text: str) -> str:
    """Frontmatter normalization: lowercase, trim, strip diacritics + punctuation, collapse spaces."""

    text = text.lower().strip()
    text = "".join(
        c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn"
    )
    text = re.sub(r"[^\w\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


_BLOCK = re.compile(r"##\s*(FAQ-\d+)\s*\n```yaml\n(.*?)\n```", re.DOTALL)


@dataclass
class FaqResolver:
    """Fuzzy/lexical FAQ lookup over the curated question set."""

    entries: list[tuple[str, str, str, str, dict | None, str]]
    threshold: float = 0.72

    @classmethod
    def from_file(cls, path: str | Path, threshold: float = 0.72) -> "FaqResolver":
        import yaml

        raw = Path(path).read_text(encoding="utf-8")
        entries: list[tuple[str, str, str, str, dict | None, str]] = []
        for block in _BLOCK.finditer(raw):
            faq_id = block.group(1)
            data = yaml.safe_load(block.group(2)) or {}
            question = str(data.get("question", "")).strip()
            answer = str(data.get("answer", "")).strip()
            if not question or not answer:
                continue
            references = data.get("references") or []
            reference = references[0] if references else None
            status = str(data.get("status", "supported"))
            entries.append((faq_id, question, answer, status, reference, normalize(question)))
        return cls(entries=entries, threshold=threshold)

    def match(self, question: str) -> FaqMatch | None:
        """Return the best FAQ hit at/above the threshold, else ``None`` (fall back to embedding)."""

        query_norm = normalize(question)
        if not query_norm:
            return None

        best = self._best_score(query_norm)  # (score_0_1, entry_index) or None
        if best is not None and best[0] >= self.threshold:
            faq_id, q_text, answer, status, reference, _ = self.entries[best[1]]
            return FaqMatch(
                faq_id=faq_id, question=q_text, answer=answer,
                status=status, score=best[0], reference=reference,
            )
        return None

    def _best_score(self, query_norm: str) -> tuple[float, int] | None:
        choices = [entry[5] for entry in self.entries]  # normalized FAQ questions
        try:
            from rapidfuzz import fuzz, process
        except ImportError:
            return self._best_score_difflib(query_norm, choices)
        # token_sort_ratio aligns tokens and scores by real word overlap, so unrelated questions
        # (no shared content words) score low — measured: real paraphrases 78-90, junk <=45, a clean
        # gap. WRatio/token_set_ratio inflate on common short words ("de","la") and blur that gap.
        hit = process.extractOne(query_norm, choices, scorer=fuzz.token_sort_ratio)
        if hit is None:
            return None
        _, score, index = hit
        return (score / 100.0, index)

    @staticmethod
    def _best_score_difflib(query_norm: str, choices: list[str]) -> tuple[float, int] | None:
        query_tokens = set(query_norm.split())
        best: tuple[float, int] | None = None
        for index, faq_norm in enumerate(choices):
            faq_tokens = set(faq_norm.split())
            union = query_tokens | faq_tokens
            jaccard = len(query_tokens & faq_tokens) / len(union) if union else 0.0
            ratio = difflib.SequenceMatcher(None, query_norm, faq_norm).ratio()
            score = 0.5 * jaccard + 0.5 * ratio
            if best is None or score > best[0]:
                best = (score, index)
        return best


if __name__ == "__main__":
    import sys

    faq_path = (
        Path(__file__).resolve().parents[5]
        / "data" / "projects" / "sst-general" / "faq" / "sst-faq-80.md"
    )
    resolver = FaqResolver.from_file(faq_path)
    print(f"loaded {len(resolver.entries)} FAQ entries, threshold={resolver.threshold}")

    # Every canonical question must match its own entry (exact -> score 1.0).
    exact_ok = sum(1 for e in resolver.entries if (m := resolver.match(e[1])) and m.faq_id == e[0])
    print(f"exact self-match: {exact_ok}/{len(resolver.entries)}")
    assert exact_ok == len(resolver.entries), "some canonical questions did not self-match"

    # Paraphrases / typos should still hit; unrelated should miss.
    probes = [
        "que establece la politica de seguridad y salud en el trabajo",       # exact-ish
        "cuales son los objetivos del sgsst",                                  # typo/spacing
        "a que correo se mandan las quejas de convivencia",                    # paraphrase
        "cual es la receta de la bandeja paisa",                               # unrelated -> miss
    ]
    for p in probes:
        m = resolver.match(p)
        print(f"  {'HIT ' if m else 'miss'} score={m.score:.2f} {m.faq_id}" if m else f"  miss        {p!r}")
        if m:
            print(f"       -> {m.answer[:70]}...")
    print("OK")
