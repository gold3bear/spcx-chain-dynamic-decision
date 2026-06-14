import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "webreport"))
import polymarket  # noqa: E402


def test_parse_probability_from_outcome_prices():
    # Polymarket Gamma markets return outcomePrices as a JSON-encoded string list.
    market = {"outcomes": '["Yes", "No"]', "outcomePrices": '["0.37", "0.63"]'}
    assert polymarket.parse_probability(market) == 0.37


def test_parse_probability_handles_list_form():
    market = {"outcomes": ["Yes", "No"], "outcomePrices": [0.42, 0.58]}
    assert polymarket.parse_probability(market) == 0.42


def test_parse_probability_returns_none_when_no_yes():
    market = {"outcomes": '["Up", "Down"]', "outcomePrices": '["0.5", "0.5"]'}
    assert polymarket.parse_probability(market) is None


def test_fetch_probability_uses_injected_opener_and_parses():
    payload = b'[{"outcomes": "[\\"Yes\\", \\"No\\"]", "outcomePrices": "[\\"0.6\\", \\"0.4\\"]"}]'

    class FakeResp:
        def read(self):
            return payload

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    def fake_opener(url, timeout=0):
        assert "slug=demo-market" in url
        return FakeResp()

    assert polymarket.fetch_probability("demo-market", opener=fake_opener) == 0.6


def test_fetch_probability_returns_none_on_error():
    def boom(url, timeout=0):
        raise OSError("network down")

    assert polymarket.fetch_probability("x", opener=boom) is None


import enrich  # noqa: E402


def test_enrich_updates_only_polymarket_nodes_and_falls_back():
    data = {
        "narrative_tree": {
            "nodes": [
                {"id": "p", "tense": "past"},
                {"id": "a", "tense": "future", "prob": 0.30, "prob_source": "polymarket:up"},
                {"id": "b", "tense": "future", "prob": 0.35, "prob_source": "polymarket:down"},
                {"id": "c", "tense": "future", "prob": 0.35, "prob_source": None},
            ]
        }
    }

    def fake_fetch(slug):
        return 0.5 if slug == "up" else None  # "down" fails -> keep 0.35

    updated = enrich.enrich_probabilities(data, fetch=fake_fetch)
    nodes = {n["id"]: n for n in data["narrative_tree"]["nodes"]}
    assert updated == 1
    assert nodes["a"]["prob"] == 0.5
    assert nodes["b"]["prob"] == 0.35
    assert nodes["c"]["prob"] == 0.35
