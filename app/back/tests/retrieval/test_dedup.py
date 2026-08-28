from __future__ import annotations

from retrieval.domain.dedup import select_unique_slots


def test_select_unique_slots_without_texts_keeps_count_cap_only() -> None:
    """Backward-compat: no texts given -> old behavior, count cap alone decides."""

    slots, dropped, _merged = select_unique_slots(
        fingerprints=["a", "b", "c"],
        parent_ids=["p1", "p1", "p1"],
        source_ranks=[0, 0, 0],
        max_per_parent=2,
    )

    assert [index for _slot, index in slots] == [0, 1]
    assert dropped == 1


def test_select_unique_slots_drops_near_duplicate_sibling_even_under_the_cap() -> None:
    """q16/q56-style repetition: same parent, two children that are basically
    the same content restated -- the cap alone (2) would let both through.
    """

    slots, dropped, _merged = select_unique_slots(
        fingerprints=["a", "b"],
        parent_ids=["p1", "p1"],
        source_ranks=[0, 0],
        max_per_parent=2,
        texts=[
            "El Comite recibira y dara tramite a la queja en un plazo de cinco dias.",
            "El Comite recibira y dara tramite a la queja en un plazo maximo de cinco dias calendario.",
        ],
    )

    assert [index for _slot, index in slots] == [0]
    assert dropped == 1


def test_select_unique_slots_keeps_genuinely_complementary_sibling() -> None:
    slots, dropped, _merged = select_unique_slots(
        fingerprints=["a", "b"],
        parent_ids=["p1", "p1"],
        source_ranks=[0, 0],
        max_per_parent=2,
        texts=[
            "El Comite recibira y dara tramite a la queja en un plazo de cinco dias.",
            "El periodo del Comite sera de dos anos, contados desde su conformacion.",
        ],
    )

    assert [index for _slot, index in slots] == [0, 1]
    assert dropped == 0
