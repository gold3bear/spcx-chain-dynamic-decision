# webreport — narrative decision-tree web app (+ 9:16 PDF export)

A vanilla (no-Node) web app that shows narrative migration as a **decision tree** on a vertical time
axis: past (solid spine) → present (pulsing "you are here") → future (dashed, probabilistic branches).
In a browser it animates and is interactive; the 9:16 portrait PDF is a static export.

## Setup
```bash
pip install -e ".[report]"
python -m playwright install chromium
```

## View interactively
Open `webreport/template/index.html` in a browser (it fetches `sample/decision_sample.json`).
- ▶ plays the multi-day migration (the A/B/C/D mini-bars shift day by day).
- Click a future branch → detail panel (probability, expected return, risk, trigger, invalidation, impacted tickers).
- Append `?static` to the URL to preview exactly what the PDF captures (no controls, all branches shown).

## Export the PDF
```bash
python webreport/render.py --input webreport/sample/decision_sample.json --out webreport/out
# -> webreport/out/report_2026-06-14.pdf  (+ out/pages/NN.png)
# add --enrich to overwrite branch probabilities from Polymarket (requires network)
```

## How it works
1. `template/render.js` builds one `.page` (1080×1920) per report section from `window.REPORT_DATA`;
   `template/tree.js` renders the hero decision-tree page.
2. `render.py` injects the JSON + `window.REPORT_STATIC=true`, screenshots each page at 2×, and Pillow
   assembles the PDF. The browser never makes network calls.
3. Branch probabilities are baked in by `polymarket.py` / `enrich.py` (offline-safe; opt-in via `--enrich`).

Fixed template, data-driven: a new card in `cards[]` adds a page automatically; missing data renders as a
grey "待补" cell. Page count = `15 + len(cards)`. Contract: `REPORT_SCHEMA.md`.

## Data contract highlights
- `narrative_tree.days[]` drives playback; `nodes[]` carry `tense ∈ {past,present,future}`; future nodes
  carry `prob`, `prob_source`, `trigger`, `invalidation`, `expected_return`, `risk`, `tickers`.

## Not in v1
True per-day historical tree snapshots (v1 reveals a single canonical tree along the cursor), A4 profile,
day-over-day diff, any backend, live in-browser Polymarket fetch.
