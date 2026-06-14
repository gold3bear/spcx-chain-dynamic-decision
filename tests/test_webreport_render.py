import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "webreport"))
import render  # noqa: E402

SAMPLE = ROOT / "webreport" / "sample" / "decision_sample.json"


def _playwright_available():
    try:
        from playwright.sync_api import sync_playwright  # noqa: F401
        from PIL import Image  # noqa: F401
    except Exception:
        return False
    return True


@pytest.mark.skipif(not _playwright_available(), reason="playwright/Pillow not installed")
def test_render_sample_produces_expected_pages(tmp_path):
    try:
        result = render.render(str(SAMPLE), str(tmp_path))
    except Exception as e:
        if "executable" in str(e).lower() or "chromium" in str(e).lower():
            pytest.skip("chromium not installed (run: playwright install chromium)")
        raise

    data = json.loads(SAMPLE.read_text(encoding="utf-8"))
    expected = render.expected_page_count(data)

    # 1. page count matches the 15 + len(cards) invariant
    assert result["page_count"] == expected == 22

    # 2. PDF exists and is non-empty
    pdf = Path(result["pdf"])
    assert pdf.exists() and pdf.stat().st_size > 0

    # 3. exactly `expected` page PNGs were produced
    pngs = sorted(Path(result["pages_dir"]).glob("*.png"))
    assert len(pngs) == expected

    # 4. the decision-tree page rendered: future branches + a present pulse exist
    html = result["html"]
    assert html.count("tn-future") >= 3       # >= 3 future branches
    assert "tn-present" in html               # present node present
    assert "叙事决策树" in html                # tree page heading

    # 5. static mode: no interactive controls/overlay leaked into the PDF DOM
    for forbidden in ("tctl", 'id="tdetail"'):
        assert forbidden not in html, f"static render leaked interactive element '{forbidden}'"

    # 6. no unfilled template variables / undefined leaked into the DOM
    for bad in ("{{", "undefined", "NaN"):
        assert bad not in html, f"rendered HTML contains '{bad}'"
