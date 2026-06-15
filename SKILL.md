---
name: spcx-chain-dynamic-decision
description: Dynamic SPCX / aerospace-chain decision protocol for OpenClaw, Claude Code, Codex, or other agents. Use when an agent must turn SPCX chain market snapshots, event calendars, narrative word-frequency data, technical signals, options/borrow data, or the report `examples/SPCX_prior_thesis_skeleton.md` into an evidence-grounded WATCH/FREEZE/ACT/RETIRE decision instead of mechanically executing fixed script triggers. Intended for scheduled OpenClaw runs, Claude Code `/loop`, Codex analysis, and agent handoffs.
---

# SPCX Chain Dynamic Decision

## Overview

Use this skill to make dynamic agent decisions for the SPCX IPO event chain. Scripts collect and normalize facts; the agent decides what those facts mean, which narrative regime is active, whether any trade card is executable, and what must be rechecked before action.

This skill follows the project constitution in `PRINCIPLES.md`: Python computes data, Agent performs judgment, every conclusion is time-anchored, and position sizing must reference `position-sizing-rules`.

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

If no pack exists, run:

```bash
python scripts/spcx_decision_pack.py template --out reports/SPCX_chain_evidence_TEMPLATE.json
```

Then fill it with current data or wire a collector to the same schema.

## Workflow

1. Time-anchor the run.
   - Convert relative dates to exact dates.
   - Reject stale realtime fields older than one trading day for current price, US10Y, options chain, and borrow rate. This rejection is enforced by the validator, not honor-system: `spcx_decision_pack.py validate` writes stale action-critical fields to `computed.freshness_errors` and FAILS validation (exit 1) — a hard block, not a warning.
   - State `analysis_as_of` in every output.

2. Build or validate the evidence pack.
   - Run `spcx_decision_pack.py validate --input <pack.json>`.
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
   - Narrative lens: A/B/C/D word-frequency rotation, news carrier quality, **and Polymarket cross-validation** (`narrative.polymarket_signals`).
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
- Do not size positions by prose. Run the ecd.position_sizing module (see docs/position-sizing.md) after an `ACT` candidate survives all gates.
- **Polymarket** is L3 auxiliary cross-validation, not executable price. It validates narrative shifts
  alongside word frequency and news carriers; it must never override L1/L2 hard data (price, options chain,
  borrow fee, US10Y, VIX). A Polymarket consensus shift without corroborating hard data or news carrier is noise.
