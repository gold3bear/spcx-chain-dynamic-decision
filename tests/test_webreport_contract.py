import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "webreport" / "sample" / "decision_sample.json"


def _load():
    return json.loads(SAMPLE.read_text(encoding="utf-8"))


def test_narrative_tree_present_with_days_and_now():
    t = _load()["narrative_tree"]
    assert len(t["days"]) >= 2
    assert t["now"] == t["days"][-1]["date"]
    for d in t["days"]:
        assert set(d["wordfreq"]) >= {"a", "b", "c", "d"}


def test_tree_tense_partition_and_single_present():
    nodes = _load()["narrative_tree"]["nodes"]
    tenses = [n["tense"] for n in nodes]
    assert tenses.count("present") == 1
    assert tenses.count("past") >= 1
    assert tenses.count("future") >= 2


def test_future_nodes_have_decision_fields():
    nodes = _load()["narrative_tree"]["nodes"]
    for n in nodes:
        if n["tense"] == "future":
            for k in ("prob", "trigger", "invalidation", "expected_return", "risk"):
                assert k in n, f"future node {n['id']} missing {k}"
            assert 0.0 <= float(n["prob"]) <= 1.0


def test_tree_edges_reference_existing_nodes():
    t = _load()["narrative_tree"]
    ids = {n["id"] for n in t["nodes"]}
    for e in t["edges"]:
        assert e["from"] in ids and e["to"] in ids
        assert e["tense"] in {"past", "present", "future"}
