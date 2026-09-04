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
import os
import re
import unicodedata
from collections import OrderedDict
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
    source_url: str | None = None


def normalize(text: str) -> str:
    """Frontmatter normalization: lowercase, trim, strip diacritics + punctuation, collapse spaces."""

    text = text.lower().strip()
    text = "".join(
        c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn"
    )
    text = re.sub(r"[^\w\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


_BLOCK = re.compile(r"##\s*(FAQ-\d+)\s*\n```yaml\n(.*?)\n```", re.DOTALL)


def _build_source_url_from_ref(reference: dict[str, Any] | None, base_url: str) -> str | None:
    """Build a document source URL from a FAQ reference dict."""
    if not base_url or not reference:
        return None
    normalized_path = reference.get("normalized_path")
    if not normalized_path:
        return None
    return f"{base_url}/api/documents/raw/{normalized_path}"


@dataclass
class FaqResolver:
    """Fuzzy/lexical FAQ lookup over the curated question set."""

    entries: list[tuple[str, str, str, str, dict | None, str, str | None]]
    threshold: float = 0.72

    @classmethod
    def from_file(cls, path: str | Path, threshold: float = 0.72) -> "FaqResolver":
        import os

        import yaml

        base_url = os.environ.get("SST_DOCUMENTS_BASE_URL", "").strip().rstrip("/")
        raw = Path(path).read_text(encoding="utf-8")
        entries: list[tuple[str, str, str, str, dict | None, str, str | None]] = []
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
            source_url = str(data.get("source_url", "")).strip() or _build_source_url_from_ref(reference, base_url)
            entries.append((faq_id, question, answer, status, reference, normalize(question), source_url))
        return cls(entries=entries, threshold=threshold)

    def match(self, question: str) -> FaqMatch | None:
        """Return the best FAQ hit at/above the threshold, else ``None`` (fall back to embedding)."""

        query_norm = normalize(question)
        if not query_norm:
            return None

        best = self._best_score(query_norm)  # (score_0_1, entry_index) or None
        if best is not None and best[0] >= self.threshold:
            faq_id, q_text, answer, status, reference, _, source_url = self.entries[best[1]]
            return FaqMatch(
                faq_id=faq_id, question=q_text, answer=answer,
                status=status, score=best[0], reference=reference,
                source_url=source_url,
            )
        return None

    def _best_score(self, query_norm: str) -> tuple[float, int] | None:
        choices = [entry[5] for entry in self.entries]  # normalized FAQ questions (index 5)
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


_PROJECT_ID_PREFIX = "proj_"


def _project_slug(project_id: str) -> str:
    """``proj_<slug>`` -> ``<slug>`` (matches ``ProjectStorageResolver``'s convention)."""

    return project_id[len(_PROJECT_ID_PREFIX) :] if project_id.startswith(_PROJECT_ID_PREFIX) else project_id


def _project_faq_path(data_root: Path, project_id: str) -> Path:
    """Return the project-scoped FAQ path — no glob, no ``matches[0]`` (PR-3 3.1).

    Before, ``sorted(data_root.glob("projects/*/faq/sst-faq-80.md"))[0]`` picked
    the alphabetically-first project's FAQ file for *every* project's question —
    a multi-project process could answer project A from project B's curated Q&A.
    This resolves the exact path for ``project_id`` and nothing else.
    """

    return data_root / "projects" / _project_slug(project_id) / "faq" / "sst-faq-80.md"


class FaqResolverRegistry:
    """One ``FaqResolver`` per project; lazily loaded, LRU-bounded (PR-3 3.2).

    Replaces the single global resolver that a multi-project process shared
    across every project (the cross-project leak 3.1 fixes at the path level).
    A missing/invalid FAQ file for a project just disables the shortcut for that
    project — it never blocks another project's shortcut nor raises.

    ``FAQ_PATH`` (explicit operator override) is intentionally global: if an
    operator points every project at one curated file, every project shares it
    on purpose — that is a deliberate, explicit configuration, not the silent
    ``glob()[0]`` collision this class exists to remove.
    """

    def __init__(
        self,
        *,
        data_root: Path,
        threshold: float = 0.85,
        max_projects: int = 64,
    ) -> None:
        self._data_root = Path(data_root)
        self._threshold = threshold
        self._max_projects = max_projects
        self._cache: "OrderedDict[str, FaqResolver | None]" = OrderedDict()
        explicit = os.environ.get("FAQ_PATH", "").strip()
        self._explicit_override = Path(explicit) if explicit else None

    def resolver_for(self, project_id: str) -> FaqResolver | None:
        """Return the cached (or freshly loaded) resolver for ``project_id``."""

        if project_id in self._cache:
            self._cache.move_to_end(project_id)
            return self._cache[project_id]
        resolver = self._load(project_id)
        self._cache[project_id] = resolver
        self._cache.move_to_end(project_id)
        if len(self._cache) > self._max_projects:
            self._cache.popitem(last=False)
        return resolver

    def _load(self, project_id: str) -> FaqResolver | None:
        path = (
            self._explicit_override
            if self._explicit_override is not None
            else _project_faq_path(self._data_root, project_id)
        )
        if not path.exists():
            return None
        try:
            return FaqResolver.from_file(path, threshold=self._threshold)
        except Exception:  # noqa: BLE001 - the FAQ shortcut is a best-effort optimization
            return None


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
            if m.source_url:
                print(f"       -> {m.source_url}")
    print("OK")
