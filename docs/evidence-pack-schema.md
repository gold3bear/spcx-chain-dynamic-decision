# Evidence Pack Schema (generic envelope)

The evidence pack is the handoff between collectors (scripts) and agent
judgment. The generic envelope is domain-agnostic; a concrete chain extends it.

## Required top-level keys
`analysis_as_of`, `market_session`, `market_data`, `macro`, `computed`.

## Freshness rules
- Action-critical realtime fields (price, RSI, rates, options/borrow) are stale
  if older than **1 trading day** (business-day aware). Stale -> `computed.freshness_errors`
  -> `validate` returns invalid (exit 1). This is a hard block.
- Timestamps may be `YYYY-MM-DD` or ISO-8601 datetime; both are tolerated.
- Lower-tier auxiliary signals (e.g. prediction-market probabilities) use a
  looser window and produce `freshness_warnings`, never blocking errors.

## Extending with your own chain
1. Start from `ecd.evidence_pack.generic_template`.
2. Add your domain blocks (instruments, narrative signals, hard-data gates).
3. Write a chain validator that calls `ecd.freshness.check_block_freshness` for
   each action-critical block and merges results, exactly as
   `scripts/spcx_decision_pack.py` does.
4. Keep domain fields out of `ecd.evidence_pack` — that file stays generic.
