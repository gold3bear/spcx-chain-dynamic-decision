#!/usr/bin/env python3
"""Fetch a YES probability from Polymarket's public Gamma API.

Pure parsing (`parse_probability`) is separated from the network wrapper
(`fetch_probability`, which takes an injectable `opener` so tests never touch
the network). All failures degrade to None so callers can keep prior values.
"""

from __future__ import annotations

import json
import urllib.request
from typing import Callable, Optional

GAMMA_URL = "https://gamma-api.polymarket.com/markets?slug={slug}"


def _coerce_list(value):
    if isinstance(value, str):
        try:
            return json.loads(value)
        except (ValueError, TypeError):
            return None
    return value


def parse_probability(market: dict) -> Optional[float]:
    """Return the YES outcome price (0..1) from a Gamma market object, or None."""
    outcomes = _coerce_list(market.get("outcomes"))
    prices = _coerce_list(market.get("outcomePrices"))
    if not outcomes or not prices or len(outcomes) != len(prices):
        return None
    for name, price in zip(outcomes, prices):
        if str(name).strip().lower() == "yes":
            try:
                return float(price)
            except (ValueError, TypeError):
                return None
    return None


def _default_opener(url: str, timeout: float = 8.0):
    return urllib.request.urlopen(url, timeout=timeout)


def fetch_probability(slug: str, opener: Optional[Callable] = None) -> Optional[float]:
    """Fetch the YES probability for a market slug. Returns None on any failure."""
    opener = opener or _default_opener
    url = GAMMA_URL.format(slug=slug)
    try:
        with opener(url, timeout=8.0) as resp:
            payload = json.loads(resp.read())
    except Exception:
        return None
    if isinstance(payload, list):
        if not payload:
            return None
        payload = payload[0]
    if not isinstance(payload, dict):
        return None
    return parse_probability(payload)
