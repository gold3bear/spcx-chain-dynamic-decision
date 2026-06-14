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

## Page count
`pages = 14 + len(cards)` (cover + 3 maps + timeline + board = 6; + N cards; + 6 dashboards + daily_review = 7; + closing = 1).
