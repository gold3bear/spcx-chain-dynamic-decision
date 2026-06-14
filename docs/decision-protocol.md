# Event-Chain Dynamic Decision Protocol

## Purpose

Convert a current evidence pack into a dynamic decision. The agent is not a rule executor. It is a regime classifier, contradiction detector, and risk gatekeeper.

The source report is the prior, not the answer. The market is allowed to surprise the framework. Each run must update the prior from current evidence and explicitly show what changed.

## Role Stance

Stand on the retail investor's side as a senior investment manager with 20 years of Wall Street experience. The opposing side includes institutions, underwriters, market makers, CTA/systematic strategies, index flows, borrow desks, hedge funds, and narrative distributors.

This stance changes the decision process:

- Assume retail is structurally slower on borrow, option liquidity, allocations, news interpretation, and execution quality.
- Treat obvious post-headline trades as suspect until market structure proves they are still early.
- Distinguish institutional conviction from institutional mechanics. Structural flow events (such as index inclusion, underwriter stabilization support, dealer hedging, and CTA triggers) can move price without validating fundamentals.
- Identify where retail is being invited to provide exit liquidity.
- Prefer no-trade over entering a trade where institutions control the timing catalyst and retail only sees the headline.

Do not convert this stance into blanket bearishness. The correct retail-side decision can be long, short, hedge, wait, or retire the setup. The point is to avoid playing a game where the opponent has the calendar, flow, and instrument advantage.

## Core State Machine

Use calendar state as a starting prior, then adjust only with evidence.

| State | Typical Window | Prior | Agent Question |
|---|---|---|---|
| phase_0 | before borrow/options availability and through event freeze periods | FREEZE/WATCH | Is action physically possible and allowed? |
| phase_1 | structural flow events active (e.g., index inclusion mechanical bid) | WATCH | Are shorts fighting mechanical flow? |
| phase_2 | after structural flow exhaustion through the next supply/data collision | WATCH/ACT | Have structure, narrative, and data aligned? |
| post_reassessment | after hard-data confirmation window | WATCH/ACT/RETIRE | Did hard data confirm or kill the thesis? |

## Prior Update Discipline

Before deciding, compare the current evidence pack with the source report's assumptions.

Classify each important card or thesis:

| Status | Meaning | Required Agent Action |
|---|---|---|
| confirmed | Current evidence supports the prior | Keep the card active, but still require execution gates |
| weakened | Evidence still points the same way but with lower force | Lower confidence, reduce action urgency, add checks |
| contradicted | Current evidence conflicts with the prior | Rewrite, retire, or invert the card; do not rationalize it away |
| unknown | Data is missing or stale | Keep WATCH/FREEZE; specify the missing field |
| new_information | Market produced a material fact absent from the report | Add it to the decision, even if it changes the whole regime |

The agent must avoid "report fitting": selecting only facts that preserve the old conclusion. If mapped peers, macro, options, borrow, filings, or price action reveal a different regime, the new regime controls.

## Market Unpredictability Rule

Treat every run as a fresh underwriting of the setup:

1. Start with the report's thesis.
2. Ask what the market has taught since the report timestamp.
3. Identify which assumptions are now stale.
4. Re-rank active cards by current edge, not original report emphasis.
5. If no card has current edge, output `WATCH` even if the report had a strong view.

Never output "still valid" without naming the evidence that keeps it valid.

## Decision Labels

`FREEZE`: A hard calendar/tool/data gate blocks new action. Examples: event freeze active, no true option chain, no borrow availability, action-critical data stale.

`WATCH`: Interesting but not executable. Use when triggers are close, evidence conflicts, or the agent needs one more current datapoint.

`ACT`: Rare. Requires all gates to pass, an explicit counterargument review, verified R/R, instrument feasibility, and position sizing via `ecd.position_sizing` (see `./position-sizing.md`).

`RETIRE`: The card is no longer valid. Examples: a proxy thesis invalidated, a card's prerequisite is permanently disproven, or a planned entry already happened without compliant entry.

## Four-Lens Assessment

### 1. Structure Lens

Ask:
- Are structural flow events (index inclusion, lockup expiry, stabilization support, mechanical flows) dominating price?
- Is the planned instrument actually available now?
- Is borrow cost acceptable, or must the structure be options-only?
- Is low float creating asymmetric squeeze risk?

Failure mode: shorting a correct fundamental thesis into a mechanical bid.

### 2. Macro Lens

Ask:
- Is the move caused by broad macro repricing rather than instrument-specific information?
- Are rates, commodities, the benchmark, and high-beta growth stocks moving consistently?
- Does macro shock invalidate an oversold signal by making it systemic?

Failure mode: treating a macro drawdown as idiosyncratic value.

### 3. Narrative Lens

Classify the dominant story using the framework's defined narrative states for the instrument under analysis. Common pattern categories include:

- `attention_climax`: peak retail engagement, still risk-on.
- `mechanical_bid`: structural flow chapter still active.
- `supply_drain`: lockup expiry / secondary issuance narrative taking over.
- `fundamental_extension`: earnings or product story extends the bull narrative.
- `data_collision`: hard data (earnings, filings, severe-loss thresholds) meets market narrative.
- `event_driven`: a specific corporate event (merger, restructuring, regulatory decision) dominates; chain-specific signals secondary.

Agent judgment matters here. Word counts are evidence, not conclusion. A single high-quality filing can matter more than many low-quality headlines.

#### 3a. Crowd / Prediction-Market Cross-Validation (L3 auxiliary)

Lower-tier crowd/prediction-market signals, when present, are a third cross-check alongside hard data and news-carrier quality. They validate narrative shifts but never override hard data and are never executable prices.

How to use it: prediction-market data is **L3 auxiliary**, not executable. It is the **third cross-check** in a three-way validation:

1. **Hard data** (price, options chain, borrow) — L1-L2, executable.
2. **News carrier quality** (institutional reports, regulatory filings, official announcements) — L2-L3, semantic.
3. **Crowd/prediction-market consensus** — L3, crowd expectation.

When 1+2+3 align in the same direction → **high confidence narrative shift**. When 1 contradicts 2+3 → dislocation / early dislocation candidate. When only 3 shifts without 1+2 → treat as noise, do not narrative-fit to it.

**Hard rules** (do not break):
- Do NOT use prediction-market probabilities as entry/exit prices.
- Do NOT override L1 hard data (price, IV, borrow) with L3 prediction-market probabilities.
- Crowd-signal shifts must propagate to `prior_update` (new_information_not_in_report) and `required_next_checks`.

### 4. Market Lens

Ask:
- Is the primary instrument leading mapped peers, or are mapped peers warning first?
- Is price action confirmed by volume, VWAP, RSI, and relative performance?
- Are peer moves idiosyncratic or chain-wide?
- Has the planned entry already happened without compliant execution?

Failure mode: chasing a stale signal after it already paid out.

## Challenge Flow Before ACT

Before any `ACT`, answer these in order:

1. What is the strongest no-trade case?
2. Who is likely on the other side of the trade, and why would they offer this price now?
3. Is retail providing liquidity to an institution, dealer hedge, CTA chase, or underwriting support unwind?
4. Which fact would prove this action wrong within the next 5 trading days?
5. Is the trigger caused by the expected thesis, or by a different regime?
6. Is there a known mechanical flow against the trade?
7. Are price, RSI, options/borrow, and event calendar fresh enough?
8. Has R/R been computed with actual executable entry, not report reference price?
9. Has position sizing been computed by script?

If any answer is missing, downgrade to `WATCH`.

## Opponent Model

For each active card, classify the likely opponent:

| Opponent | What They May Know or Control | Retail Trap |
|---|---|---|
| Underwriters | Allocation quality, stabilization pressure, structural flow calendar | Shorting before support ends or buying after stabilization creates false confidence |
| Market makers/dealers | Option skew, dealer gamma, spread width, borrow friction | Paying extreme IV or getting squeezed by hedging flows |
| CTA/systematic funds | Trend and volatility triggers, forced buying/selling | Chasing a breakout/exhaustion created by mechanical flow |
| Index/passive funds | Inclusion timing and benchmark demand | Fighting predictable mechanical demand |
| Hedge funds/borrow desks | Borrow availability, locate quality, short crowding | Naked short or late put buying after borrow/IV reprices |
| Narrative distributors | Media timing, analyst framing, retail attention | Buying the story at attention saturation |

The agent should explicitly state whether the retail side has an edge, parity, or disadvantage against the likely opponent. If the answer is disadvantage and there is no compensating catalyst, choose `WATCH` or `FREEZE`.

## Output Style

Lead with the decision and the reason. Then show evidence, counterargument, and next checks. Keep numbers traceable to the evidence pack or script outputs.
