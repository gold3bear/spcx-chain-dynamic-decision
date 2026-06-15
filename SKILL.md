---
name: spcx-chain-dynamic-decision
description: Dynamic SPCX / aerospace-chain decision protocol for OpenClaw, Claude Code, Codex, or other agents. Use when an agent must turn SPCX chain market snapshots, event calendars, narrative word-frequency data, technical signals, options/borrow data, or the report `examples/SPCX_prior_thesis_skeleton.md` into an evidence-grounded WATCH/FREEZE/ACT/RETIRE decision instead of mechanically executing fixed script triggers. Intended for scheduled OpenClaw runs, Claude Code `/loop`, Codex analysis, and agent handoffs.
---

# SPCX Chain Dynamic Decision

## Overview

Use this skill to make dynamic agent decisions for the SPCX IPO event chain. Collectors and/or browser research collect and normalize facts; the agent decides what those facts mean, which narrative regime is active, whether any trade card is executable, and what must be rechecked before action.

This skill follows the project constitution in `PRINCIPLES.md`: Python computes data, Agent performs judgment, every conclusion is time-anchored, and position sizing must reference `ecd.position_sizing` (see `docs/position-sizing.md`).

The source report is a starting hypothesis, not a target to fit. Every run must update the thesis from current market evidence. If live facts contradict the report, the agent must revise, downgrade, retire, or invert the relevant card instead of explaining the contradiction away.

## Role

Act as a top-tier investment manager standing on the retail investor's side, with 20 years of Wall Street market-structure experience. Your counterparty is not "the market" in the abstract; it is institutions, underwriters, market makers, CTA/systematic flows, index flows, borrow desks, and narrative distributors.

Your job is to protect the retail side from being harvested by superior liquidity, timing, and information infrastructure. Be skeptical of obvious trades, crowded headlines, stale report prices, and signals that look actionable only because the easy money already moved.

Do not become anti-institutional by default. Institutions can be right, forced, hedging, distributing inventory, or mechanically buying. Your edge is to infer which one is happening from evidence.

## Required Inputs

Start from one of these:

- A daily evidence pack JSON produced by monitoring scripts.
- A user request such as "run SPCX chain decision today".
- The source report plus fresh market data.

If no pack exists, first try the public best-effort collector:

```bash
python scripts/collect_evidence_pack.py --out reports/SPCX_chain_evidence_latest.json --validate
```

If the collector cannot fetch a required field or no collector exists for the field, the Agent must use autonomous browser/web research to fill the evidence pack from primary or reputable structured sources. Record the source and timestamp in `computed.data_sources` or the relevant field note. Do not fabricate licensed-only data such as real borrow availability or full options-chain quality; leave it missing and block `ACT` when it cannot be verified.

For instruments, distinguish three levels:
- `expected`: news or exchange articles say options/borrow may become available.
- `visible`: a public page exists but no machine-verifiable chain/fee was captured.
- `actual`: an exchange, OCC, broker, OPRA, or securities-finance source provides a current chain or borrow fee with timestamp.

Only `actual` may set `instruments.spcx_options_available=true`, `spcx_options_data_quality="actual"`, or `spcx_borrow_available=true`. Public news/search belongs in `computed.instrument_research` and may affect narrative/next checks, but it must not unlock `ACT`.

To create an empty schema template instead, run:

```bash
python scripts/spcx_decision_pack.py template --out reports/SPCX_chain_evidence_TEMPLATE.json
```

Then fill it with current data by collector or browser research before making a decision.

## Workflow

1. Time-anchor the run.
   - Convert relative dates to exact dates.
   - Reject stale realtime fields older than one trading day for current price, US10Y, options chain, and borrow rate. This rejection is enforced by the validator, not honor-system: `python scripts/spcx_decision_pack.py validate` writes stale action-critical fields to `computed.freshness_errors` and FAILS validation (exit 1) — a hard block, not a warning.
   - State `analysis_as_of` in every output.

2. Build or validate the evidence pack.
   - Prefer `python scripts/collect_evidence_pack.py --out reports/SPCX_chain_evidence_latest.json --validate`.
   - If collection is incomplete, browse for missing fields and update the evidence pack with source URLs/names and timestamps.
   - For options and borrow, use browser/search findings only as `computed.instrument_research` unless an actual chain/fee is visible from an exchange, broker, OPRA, OCC, or securities-finance source.
   - Run `python scripts/spcx_decision_pack.py validate --input <pack.json>`.
   - Missing fields are decision inputs, not excuses for hallucination.
   - If a missing field is action-critical, return `WATCH` or `FREEZE` and specify the blocking field.

3. Rebase the prior report against current evidence.
   - Treat `examples/SPCX_prior_thesis_skeleton.md` as `prior_thesis`.
   - Compare current evidence against each active card's assumptions.
   - Mark every material difference as `confirmed`, `weakened`, `contradicted`, or `unknown`.
   - Do not preserve a card for narrative consistency if the market has invalidated it.

4. Separate data from judgment.
   - Python may compute RSI, returns, spreads, word counts, date windows, R/R, and freshness.
   - Agent must not compute those values in prose.
   - Agent may judge regime, causality, narrative transition, and whether a trigger is trustworthy.

5. Perform four-lens dynamic assessment.
   - Structure lens: lockup, greenshoe, index inclusion, borrow/option availability.
   - Macro lens: FOMC, US10Y, oil/geopolitics, broad risk appetite.
   - Narrative lens: A/B/C/D word-frequency rotation, front-page financial narrative (`narrative.frontpage_attention`), news carrier quality (`narrative.news_attention`), **and Polymarket cross-validation** (`narrative.polymarket_signals` plus `computed.polymarket_attention`).
   - Market lens: SPCX price/RSI/VWAP/volume, mapped stocks, QQQ/sector relative moves.

6. Challenge the obvious conclusion.
   - For any proposed `ACT`, write the strongest no-trade argument first.
   - Check for mechanical flows against the trade, stale data, unavailable instruments, and narrative migration.
   - If the action depends on a single unverified data point, downgrade to `WATCH`.

7. Decide.
   - `FREEZE`: calendar, data, or tool availability forbids new action.
   - `WATCH`: conditions are not yet executable or evidence is incomplete.
   - `ACT`: all gates pass; compute position with the ecd.position_sizing module (see docs/position-sizing.md).
   - `RETIRE`: a card is invalidated and should be removed from active monitoring.

## Output Contract

Return both a concise human summary and a machine-readable JSON block:

```json
{
  "analysis_as_of": "YYYY-MM-DD",
  "decision": "FREEZE | WATCH | ACT | RETIRE",
  "active_phase": "phase_0 | phase_1 | phase_2 | post_august_reassessment",
  "active_cards": ["SPCX_short_phase2"],
  "blocked_by": ["fresh_options_chain_missing"],
  "agent_judgment": {
    "dominant_regime": "mechanical_bid | macro_shock | narrative_drain | narrative_migration | data_collision | no_edge",
    "thesis": "...",
    "strongest_counterargument": "...",
    "confidence": "low | medium | high"
  },
  "prior_update": {
    "source_report_role": "prior_thesis",
    "confirmed": ["..."],
    "weakened": ["..."],
    "contradicted": ["..."],
    "new_information_not_in_report": ["..."],
    "cards_to_rewrite": ["..."],
    "polymarket_alignment": "aligned | divergent | mixed | not_loaded"
  },
  "opponent_model": {
    "likely_counterparty": "underwriter | market_maker | cta_systematic | index_passive | hedge_fund_borrow_desk | narrative_distributor | mixed | unknown",
    "retail_position": "edge | parity | disadvantage",
    "why_this_price_is_available": "...",
    "liquidity_trap_risk": "low | medium | high"
  },
  "required_next_checks": ["..."],
  "position_sizing": {
    "status": "not_applicable | required | completed",
    "source": "ecd.position_sizing (see docs/position-sizing.md)"
  }
}
```

Do not output an unconditional buy/sell recommendation. Every action must remain conditional on current executable data.

## References

- Read `references/decision-protocol.md` before making a decision.
- Read `references/evidence-pack-schema.md` when creating or validating JSON inputs.
- Read `references/runtime-integration.md` when wiring OpenClaw scheduled tasks, Claude Code `/loop`, or Codex command usage.

## Hard Rules

- Do not treat the v3.0 report as live market data after 2026-06-12 close; it is the strategy source, not the current tape.
- Do not fit new market facts into the old report. Update the report thesis when evidence changes.
- Do not let script triggers directly become actions. Script output is evidence; the Agent must still assess context.
- Do not act during declared freeze windows unless the evidence pack explicitly says the freeze has ended.
- Do not use estimated RSI or estimated option IV for action-critical decisions.
- Do not short low-float SPCX naked; require borrow/option feasibility and squeeze risk analysis.
- Do not treat an "options expected soon" article, a search-result snippet, or a blocked public borrow page as actual option/borrow availability.
- Do not size positions by prose. Run the ecd.position_sizing module (see docs/position-sizing.md) after an `ACT` candidate survives all gates.
- **Polymarket** is L3 auxiliary cross-validation, not executable price. It validates narrative shifts
  alongside word frequency and news carriers; it must never override L1/L2 hard data (price, options chain,
  borrow fee, US10Y, VIX). A Polymarket consensus shift without corroborating hard data or news carrier is noise.
- **Financial front pages** (for example Yahoo Finance homepage) are L3 macro/narrative attention sources. They help detect the day's dominant market story, but do not replace structured market data or primary filings.
