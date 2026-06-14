# Design Principles

These principles govern every decision the framework produces. They are the
non-negotiable core; tooling and schemas may change, these do not.

## 1. Data / Judgment Separation
Python computes "what the world looks like" (numbers, JSON, freshness, ratios).
The agent decides "what it means" (regime, causality, whether a trigger is
trustworthy). Scripts MUST NOT hardcode domain judgment (keyword lists, ticker
whitelists, sector branches). The agent MUST NOT recompute numeric transforms in
prose.

## 2. Time Anchoring
Every datum and parameter carries an effective date. Every output states
`analysis_as_of`. Action-critical realtime fields (price, rates, options chain,
borrow) older than one trading day BLOCK action — enforced by the validator, not
by honor system. Relative dates ("last quarter", "recently") must be converted to
absolute dates before use.

## 3. Graceful Degradation
No step blocks more than ~2 minutes on an external dependency. Data-source order:
structured local data, then live fetch, then LLM-driven summary (lower tier,
labeled), then knowledge base (lowest confidence). Missing data is a decision
input (downgrade to WATCH/FREEZE and name the blocking field), never an excuse to
hallucinate.

## 4. Anti-Hardcoding
No concrete values, company names, or assumption constants buried in code.
Thresholds live in config/params and are referenced, not inlined. Schema-level
literals (enum membership, structural field names) are the only allowed
exception.

## 5. Single Source of Truth
Shared logic lives in one place (the `ecd` package and these docs). Consumers
reference, never re-define. Duplicated definitions are latent bugs.

## 6. Evidence Tiering and Falsifiability
Every datum is tier-labeled (executable hard data > structured source >
LLM/crowd summary). Lower-tier signals never override higher-tier hard data.
Every actionable thesis carries an explicit invalidation trigger; an
unfalsifiable view does not enter the decision.
