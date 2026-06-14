# Report Data Contract

`render.py` consumes one JSON object (`decision.json`). v1 uses
`sample/decision_sample.json`; v2 will have the skill/agent emit this shape.

## Top-level fields
- `analysis_as_of` (YYYY-MM-DD), `report_title`, `overall_stance`, `disclaimer`, `skill_attribution`
- `active_phase` ∈ {phase_0, phase_1, phase_2, post_august_reassessment}, `phase_note`
- `regime`, `narrative_cycle` ∈ {seeding, acceleration, saturation, falsification}
- `narrative_wordfreq`: { a, b, c, d (0-100), bc_gt_a_consecutive_days }
- `opponent_model`: { likely_counterparty, retail_position ∈ {edge,parity,disadvantage}, liquidity_trap_risk ∈ {low,medium,high}, why_this_price }
- `timeline`: [ { date, event, status ∈ {upcoming, today, done} } ]

## `cards[]` (one report page each)
`{ id, label, status ∈ {FREEZE,WATCH,ACT,RETIRE}, direction ∈ {long,short,none},
   gates: { data, time, structure, narrative, rr } each ∈ {pass,fail,na},
   blocking_field, distance_to_trigger, invalidation, changed_today }`

## `dashboards` (one page each; rows are free-form key/value + `state`)
Keys rendered in order: `spcx, macro, mapped_stocks, fundamental, sats_gs_supply, merger`
(generic tables), then `daily_review` ([{q, answer}]).
Row `state` ∈ {ok, warn, stale, watch, na}; `stale`/`na`/missing → grey "待补".

## `narrative_tree` (drives the hero decision-tree page + playback)
- `days`: [ { date, wordfreq:{a,b,c,d} } ] — per-day narrative word frequency for playback. Last day == top-level `narrative_wordfreq` (single source).
- `now`: date string; equals `days[-1].date`.
- `nodes`: [ {
    id, label, phase, `tense` ∈ {past, present, future}, date, intensity (0-100),
    tickers (card ids this narrative implicates),
    detail,
    // future-only: prob (0..1), prob_source ("polymarket:<slug>" or null),
    //              trigger, invalidation, expected_return, risk
  } ] — exactly one `present` node; ≥1 `past`; ≥2 `future`.
- `edges`: [ { from, to, `tense` ∈ {past, present, future}, prob? (0..1) } ].

Layout is precomputed (vertical time axis, top=past → bottom=future); no force layout, no third-party lib.
Branch `prob` may be overwritten from Polymarket by `enrich.py`; the browser never fetches.

## Page count
`pages = 15 + len(cards)` (cover + phase-map + narrative-cycle + narrative-tree + opponent + timeline + board = 7; + N cards; + 6 dashboards + daily_review = 7; + closing = 1).
