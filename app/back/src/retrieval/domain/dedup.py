"""Dedup determinista de candidatos de recuperación.

El corpus contiene gemelos de contenido entre archivos distintos (transcripción
``.md`` vs PDF escaneado oficial): no son pares por nombre, así que el dedup es
por huella del TEXTO del chunk, nunca por filename. Funciones puras, sin I/O,
reutilizables por la ruta de producción y por el reporte del E2E.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from hashlib import sha256

_WHITESPACE = re.compile(r"\s+")


def content_fingerprint(text: str) -> str:
    """Huella estable del contenido: minúsculas y espacios colapsados."""

    normalized = _WHITESPACE.sub(" ", text.strip().lower())
    return sha256(normalized.encode("utf-8")).hexdigest()


def format_source_rank(source_relpath: str | None) -> int:
    """Rango de calidad de fuente: menor es mejor.

    El `.md` nativo gana sobre el PDF escaneado a igualdad de contenido (el OCR
    introduce ruido). Formato desconocido empata con nativo para que la
    preferencia solo aplique cuando el formato es realmente conocido.
    """

    if not source_relpath:
        return 0
    lowered = source_relpath.lower()
    if lowered.endswith(".pdf"):
        return 1
    return 0


def select_unique_slots(
    *,
    fingerprints: Sequence[str],
    parent_ids: Sequence[str | None],
    source_ranks: Sequence[int],
    max_per_parent: int = 2,
) -> tuple[list[tuple[int, int]], int, dict[int, list[int]]]:
    """Selecciona qué posiciones (en orden de ranking) sobreviven al dedup.

    - Primera aparición de una huella gana su slot; si un duplicado posterior
      tiene MEJOR fuente (rank menor), reemplaza el contenido del slot sin
      alterar la posición en el ranking.
    - Máximo ``max_per_parent`` slots por ``parent_node_id``: evita que un
      párrafo largo ocupe medio top-k.
    - Los slots sin padre se agrupan por posición propia (nunca comparten cupo).

    Devuelve ``(slots, dropped_count, slot_to_merged_indices)`` donde
    ``slots`` mapea posición del ranking -> índice del elemento elegido para
    esa posición, y ``slot_to_merged_indices`` mapea cada slot a TODOS los
    índices originales que se fusionaron en él (ganador + duplicados).
    """

    if not (len(fingerprints) == len(parent_ids) == len(source_ranks)):
        raise ValueError("fingerprints, parent_ids y source_ranks deben tener igual largo")

    fingerprint_to_slot: dict[str, int] = {}
    slot_to_chosen: dict[int, int] = {}
    slot_to_merged: dict[int, list[int]] = {}
    per_parent: dict[str, int] = {}
    dropped = 0

    for index in range(len(fingerprints)):
        fingerprint = fingerprints[index]
        parent_key = parent_ids[index] or f"__no_parent_{index}"
        source_rank = source_ranks[index]

        existing_slot = fingerprint_to_slot.get(fingerprint)
        if existing_slot is not None:
            chosen_index = slot_to_chosen[existing_slot]
            if source_rank < source_ranks[chosen_index]:
                slot_to_chosen[existing_slot] = index
            slot_to_merged[existing_slot].append(index)
            dropped += 1
            continue

        used = per_parent.get(parent_key, 0)
        if used >= max_per_parent:
            dropped += 1
            continue

        fingerprint_to_slot[fingerprint] = index
        slot_to_chosen[index] = index
        slot_to_merged[index] = [index]
        per_parent[parent_key] = used + 1

    return sorted(slot_to_chosen.items()), dropped, slot_to_merged
