# Evidence Pack Schema

The evidence pack is the handoff between scripts and agent judgment. It should be generated daily or on event triggers.

## Minimal JSON Shape

```json
{
  "analysis_as_of": "YYYY-MM-DD",
  "source_report": "examples/SPCX_prior_thesis_skeleton.md",
  "market_session": {
    "last_close_date": "YYYY-MM-DD",
    "is_trading_day": true
  },
  "calendar": {
    "fomc_freeze_active": false,
    "greenshoe_active": true,
    "msci_inclusion_pending": true,
    "ndx_inclusion_pending": true,
    "rklb_ndx_freeze_active": true,
    "asts_launch_freeze_active": true,
    "phase_hint": "phase_0"
  },
  "market_data": {
    "SPCX": {
      "last_price": null,
      "close": null,
      "rsi_14": null,
      "volume": null,
      "vwap": null,
      "data_timestamp": null
    },
    "QQQ": {},
    "RKLB": {},
    "ASTS": {},
    "LUNR": {},
    "PL": {},
    "RDW": {},
    "TSLA": {
      "last_price": null,
      "close": null,
      "rsi_14": null,
      "volume": null,
      "vwap": null,
      "data_timestamp": null
    }
  },
  "macro": {
    "us10y": null,
    "brent": null,
    "vix": null,
    "fomc_tone": null,
    "data_timestamp": null
  },
  "instruments": {
    "spcx_options_available": false,
    "spcx_options_data_quality": "missing",
    "spcx_borrow_available": false,
    "spcx_borrow_fee_pct": null,
    "data_timestamp": null
  },
  "narrative": {
    "wordfreq_window_days": 3,
    "group_a_record_ipo": null,
    "group_b_ipo_drain_lockup": null,
    "group_c_tech_concentration_bubble": null,
    "group_d_vertical_ai": null,
    "bc_gt_a_consecutive_days": null,
    "high_quality_carriers": [],
    "polymarket_signals": {
      "spcx_end_of_month_closing_market_cap_above_current": null,
      "spcx_first_month_close_up": null,
      "spcx_day2_open_up": null,
      "spcx_day2_close_up": null,
      "spcx_ndx_inclusion_2026": null,
      "spcx_sp500_inclusion_2026": null,
      "spcx_volatility_halt_first_month": null,
      "spcx_vs_openai_higher_ipo_marketcap": null,
      "openai_or_anthropic_s1_filed": null,
      "google_x_spacex_space_data_center": null,
      "tsla_spacex_merger_2026": null,
      "tldr": null,
      "source": "polymarket.com",
      "data_timestamp": null
    }
  },
  "hard_data": {
    "openai_or_anthropic_s1_filed": false,
    "spacex_chip_fab_substantive_announcement": false,
    "xai_quarterly_loss_usd_bn": null,
    "starlink_monthly_net_adds_mn": null,
    "sats_lockup_terms_known": false,
    "sats_tax_leakage_known": false,
    "sats_transaction_path_known": false,
    "tsla_spacex_merger_agreement_signed": false,
    "tsla_spacex_exchange_ratio_known": false,
    "tsla_special_committee_formed": false,
    "tsla_shareholder_litigation_active": false
  },
  "prior_positions": {
    "SPCX": 0.0,
    "RKLB": 0.0,
    "SATS": 0.0
  },
  "computed": {
    "freshness_errors": [],
    "freshness_warnings": [],
    "candidate_triggers": [],
    "rr_checks": []
  }
}
```

## Required Freshness

Realtime/action-critical fields must be same day or latest completed trading session:
- SPCX current/close price
- RSI and technical signals
- options chain
- borrow availability and fee
- US10Y, VIX, Brent

These fields are stale if older than **1 trading day** (business-day aware, so Friday data checked Monday is still fresh). `spcx_decision_pack.py validate` writes any stale action-critical field to `computed.freshness_errors` and FAILS validation (exit 1). Action-critical staleness is therefore a hard block, not a warning. The validator tolerates both `YYYY-MM-DD` and ISO datetime timestamp formats.

Quarterly/event fields can be stale if no new event exists, but must include the known date.

## Polymarket Signals (L3 narrative cross-validation)

`narrative.polymarket_signals` is a **required** sub-object as of skill v3.1. It captures
prediction-market probabilities that surface expectations the source report and word-frequency
data cannot reach — specifically retail-counterparty consensus and forward-curve framing.

### Field Reference

| Field | Type | Meaning |
|------|------|--------|
| `spcx_end_of_month_closing_market_cap_above_current` | float 0-1 | Probability that SPCX month-end market cap is above the price at evidence pack time. **<0.4 = bearish consensus**, >0.6 = bullish consensus. |
| `spcx_first_month_close_up` | float 0-1 | First-month close direction. <0.5 = bearish tilt. |
| `spcx_day2_open_up` | float 0-1 | Day 2 open vs Day 1 close. |
| `spcx_day2_close_up` | float 0-1 | Day 2 close vs Day 1 close. |
| `spcx_ndx_inclusion_2026` | float 0-1 | NDX inclusion probability (mechanical-bid confirmation). |
| `spcx_sp500_inclusion_2026` | float 0-1 | S&P 500 inclusion probability (GAAP-constraint dependent). |
| `spcx_volatility_halt_first_month` | float 0-1 | Probability of trading halt in first month. >0.10 = elevated concern. |
| `spcx_vs_openai_higher_ipo_marketcap` | float 0-1 | Comparative market cap race. |
| `openai_or_anthropic_s1_filed` | float 0-1 | IPO drain node ④ carrier probability. |
| `google_x_spacex_space_data_center` | float 0-1 | Vertical AI migration node ⑤ carrier probability. |
| `tldr` | string | One-sentence summary of consensus direction (written by collector). |
| `source` | string | Always `"polymarket.com"` (L3 evidence). |
| `data_timestamp` | string | YYYY-MM-DD of fetch. |

### Freshness Rule

- `data_timestamp` is stale if older than **2 calendar days** → mark as `freshness_warning` (non-blocking, L3 auxiliary), agent downgrades confidence
- Polymarket contracts expire/resolve; stale probabilities = wrong signal
- A Polymarket `freshness_warning` never blocks ACT — the strict same-day/previous-trading-day rule applies to realtime hard data, not L3 signals

### Evidence Tier

Polymarket data is **L3 evidence** (LLM-driven prediction market summary). It is **auxiliary**:
- ✅ Validates narrative shifts (空头机构报告 + Polymarket 偏空同向 = high confidence)
- ❌ Does NOT replace L1/L2 hard data (10-K, options chain, borrow fee)
- ❌ Polymarket probabilities are NOT executable prices — they reflect crowd expectation, not institutional positioning

### Cardinality

Markets are identified by question slug. Collector must enumerate markets that match:
- `SpaceX` / `SPCX` / `Starlink` / `Starship` / `xAI`
- Related chain: `OpenAI IPO`, `Anthropic IPO`, `Google SpaceX data center`
- Mechanical: `Nasdaq-100 inclusion`, `S&P 500 inclusion`

Minimum fields that should be populated on a weekday pack; a null value yields a `freshness_warning`, never a hard error — Polymarket is L3 auxiliary and must never block ACT:
- `spcx_end_of_month_closing_market_cap_above_current`
- `spcx_ndx_inclusion_2026`
- `spcx_first_month_close_up`
- `data_timestamp`

Other fields nullable when no contract exists.

## News and Front-Page Attention

Collectors may include narrative attention blocks:

```json
{
  "news_attention": {
    "status": "loaded",
    "source": "Google News RSS search",
    "query": "SpaceX SPCX IPO",
    "group_scores": {"group_a_record_ipo": 100},
    "carrier_titles": ["..."]
  },
  "frontpage_attention": {
    "status": "loaded",
    "source": "Yahoo Finance front page",
    "group_scores": {"macro_market": 41, "group_d_vertical_ai": 100},
    "carrier_titles": ["..."]
  }
}
```

`news_attention` tracks topic-specific SpaceX/SPCX news. `frontpage_attention` tracks broader daily
financial-market narratives and can surface macro themes such as Fed, oil, market-wide risk appetite, or
AI/data-center framing. Both are L3 attention signals and must not override executable hard data.

## TSLA Dual Role & Merger Card

`market_data.TSLA` is tracked, but it is **not a structural aerospace-chain peer** like RKLB/ASTS/PL/RDW.
TSLA plays two distinct roles, both judged in the Narrative lens (never the Market lens "mapped stock leads/warns" logic):

1. **Musk-complex sentiment / liquidity proxy** — shared Elon ownership means SPCX attention and TSLA
   sentiment co-move; SPCX IPO can drain retail "Musk exposure" out of TSLA (corroborates `ipo_drain_lockup`).
   A TSLA move driven by its own autos/FSD/China macro is **noise for the chain** — do not read it as chain weakness.
2. **Merger-concept target** — see the merger hard-data block below.

### Merger Hard-Data (gates the `TSLA_SPCX_merger` card)

These `hard_data` booleans flip the merger card from `WATCH` to an evaluable event. Until
`tsla_spacex_merger_agreement_signed=true` AND `tsla_spacex_exchange_ratio_known=true`, the card is `WATCH`
(no announced terms → no computable spread → cannot ACT):

| Field | Meaning | Effect when true |
|------|------|------|
| `tsla_spacex_merger_agreement_signed` | A definitive merger agreement is signed/announced (8-K / S-4) | WATCH → evaluable; classic merger-arb logic now applies |
| `tsla_spacex_exchange_ratio_known` | Stock-for-stock exchange ratio is public | Enables R/R and implied-deal-value computation |
| `tsla_special_committee_formed` | Tesla independent special committee formed | Conflict-of-interest process underway (Musk both-sides) |
| `tsla_shareholder_litigation_active` | Shareholder suit filed to block/challenge | Deal-break risk elevated; size down or RETIRE |

`narrative.polymarket_signals.tsla_spacex_merger_2026` (float 0-1) is the **L3 crowd-probability** cross-check
for this card. Per Polymarket hard rules it is auxiliary only — a high merger probability does NOT justify a
position without signed terms + executable instrument feasibility. As of 2026-06, the live state is:
no signed agreement; only SpaceX S-1 equity-issuance language, SpaceX-president verbal hints, and a Tesla
SpaceX-equity stake — all `signed=false`. Treat any "80% in a year" sell-side figure as L3 opinion, not official.

## Candidate Trigger Format

Scripts may emit candidate triggers, but not final decisions:

```json
{
  "card": "SPCX_short_phase2",
  "trigger": "greenshoe_expired_and_close_below_150",
  "status": "candidate",
  "evidence": ["calendar.greenshoe_active=false", "market_data.SPCX.close=147.2"],
  "requires_agent_judgment": [
    "Is the move idiosyncratic or macro-led?",
    "Are options/borrow executable?",
    "Is narrative drain active or only price weakness?"
  ]
}
```

## Instrument Research

Collectors may include public web/search findings under `computed.instrument_research`.
This is useful for tracking whether options or borrow availability may be approaching,
but it is not execution-grade by itself:

```json
{
  "options_expected_from_public_news": true,
  "options_status": "Public news/search indicates SPCX options may list or are expected, but collector did not verify an actual option chain.",
  "options_carriers": ["..."],
  "borrow_public_page_found": true,
  "borrow_status": "Public search found borrow/short-interest references, but collector did not verify executable borrow availability or fee.",
  "borrow_carriers": ["..."],
  "actionability": "research_only_not_ACT_grade"
}
```

Only an exchange/OCC/broker/OPRA chain or broker/securities-finance borrow source may flip
`instruments.spcx_options_available`, `spcx_options_data_quality="actual"`, or
`instruments.spcx_borrow_available`.

## Agent Must Not

- Fill missing numeric fields from memory.
- Infer RSI from a 52-week range.
- Treat `candidate_triggers` as executable orders.
- Use report reference price for R/R if current executable price differs.
