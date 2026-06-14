#!/usr/bin/env python3
"""Render a decision JSON into a 9:16 portrait PDF report (static export).

Injects the JSON plus window.REPORT_STATIC=true so the web app freezes the
narrative tree at "now" with all branches expanded and no controls, then
screenshots each .page (1080x1920, 2x) with Playwright and assembles the PNGs
into one PDF with Pillow. Heavy imports live inside render() so
expected_page_count imports without Playwright/Pillow installed.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEMPLATE = HERE / "template" / "index.html"


def expected_page_count(data: dict) -> int:
    """pages = 15 fixed sections + one per card."""
    return 15 + len(data.get("cards", []))


def render(input_path: str, out_dir: str, enrich: bool = False) -> dict:
    from playwright.sync_api import sync_playwright
    from PIL import Image

    # Force registration of Pillow's format plugins (notably JPEG/DCTDecode used
    # by the PDF encoder). On some installs Image.SAVE is lazily populated and
    # stays empty until init(), which makes the PDF save raise KeyError('JPEG').
    Image.init()

    data = json.loads(Path(input_path).read_text(encoding="utf-8"))
    if enrich:
        import enrich as enrich_mod
        enrich_mod.enrich_probabilities(data)

    out = Path(out_dir)
    pages_dir = out / "pages"
    pages_dir.mkdir(parents=True, exist_ok=True)

    png_paths = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1080, "height": 1920}, device_scale_factor=2)
        page.add_init_script(
            "window.REPORT_STATIC = true; window.REPORT_DATA = "
            + json.dumps(data, ensure_ascii=False) + ";"
        )
        page.goto(TEMPLATE.as_uri())
        page.wait_for_function("window.__RENDER_DONE === true", timeout=20000)
        html = page.content()
        elements = page.query_selector_all(".page")
        for i, el in enumerate(elements, 1):
            f = pages_dir / f"{i:02d}.png"
            el.screenshot(path=str(f))
            png_paths.append(f)
        browser.close()

    imgs = [Image.open(f).convert("RGB") for f in png_paths]
    pdf_path = out / f"report_{data.get('analysis_as_of', 'latest')}.pdf"
    if imgs:
        imgs[0].save(pdf_path, save_all=True, append_images=imgs[1:])

    return {"pdf": str(pdf_path), "page_count": len(png_paths), "html": html, "pages_dir": str(pages_dir)}


def main() -> int:
    parser = argparse.ArgumentParser(description="Render decision JSON to a 9:16 PDF report")
    parser.add_argument("--input", default=str(HERE / "sample" / "decision_sample.json"))
    parser.add_argument("--out", default=str(HERE / "out"))
    parser.add_argument("--enrich", action="store_true", help="overwrite branch probs from Polymarket (network)")
    args = parser.parse_args()
    result = render(args.input, args.out, enrich=args.enrich)
    print(json.dumps({k: result[k] for k in ("pdf", "page_count", "pages_dir")}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
