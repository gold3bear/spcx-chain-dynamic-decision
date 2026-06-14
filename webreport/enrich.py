#!/usr/bin/env python3
"""Bake Polymarket probabilities into a decision JSON (offline-safe, opt-in).

For each future node with `prob_source` == "polymarket:<slug>", replace `prob`
with the fetched YES probability. Any failure leaves the existing `prob` intact.
"""

from __future__ import annotations

from typing import Callable, Optional

import polymarket

PREFIX = "polymarket:"


def enrich_probabilities(data: dict, fetch: Optional[Callable] = None) -> int:
    """Mutate data in place; return how many node probs were updated."""
    fetch = fetch or polymarket.fetch_probability
    tree = data.get("narrative_tree") or {}
    updated = 0
    for node in tree.get("nodes", []):
        src = node.get("prob_source")
        if not (isinstance(src, str) and src.startswith(PREFIX)):
            continue
        slug = src[len(PREFIX):]
        value = fetch(slug)
        if value is not None:
            node["prob"] = round(float(value), 4)
            updated += 1
    return updated
