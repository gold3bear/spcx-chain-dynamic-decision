import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "webreport"))
import render  # noqa: E402


def test_expected_page_count_formula():
    assert render.expected_page_count({"cards": [1, 2, 3]}) == 18  # 15 + 3


def test_expected_page_count_sample():
    data = json.loads((ROOT / "webreport" / "sample" / "decision_sample.json").read_text(encoding="utf-8"))
    assert render.expected_page_count(data) == 15 + len(data["cards"]) == 22
