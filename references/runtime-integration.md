# Runtime Integration

This skill is runtime-agnostic. OpenClaw, Claude Code, Codex, or another agent can all use the same evidence pack and decision protocol.

## OpenClaw Scheduled Task

Run collectors first, then call the agent with this skill and the evidence pack. If a collector cannot obtain a field, the agent should use browser/web research to fill it from primary or reputable structured sources, with provenance recorded in the pack.

Suggested schedule in Asia/Shanghai time:
- 06:30 daily after US close: full daily evidence pack.
- Event days: add one-off runs after FOMC, option listing, index inclusion, greenshoe expiry, earnings, and lockup windows.

Example Windows task for evidence pack validation:

```powershell
schtasks /Create /SC DAILY /TN "SPCX Evidence Pack Collect" /ST 06:30 /TR "powershell -NoProfile -ExecutionPolicy Bypass -Command cd D:\projects\spcx-chain-dynamic-decision; python scripts\collect_evidence_pack.py --out reports\SPCX_chain_evidence_latest.json --validate"
```

OpenClaw should then prompt the agent:

```text
Use SKILL.md.
Read reports/SPCX_chain_evidence_latest.json.
Return the decision JSON and concise human brief.
```

## Claude Code `/loop`

Use `/loop` for market watch iterations:

```text
/loop every weekday after US close:
1. Refresh SPCX evidence pack.
2. If collector fields are missing, browse primary/reputable sources and patch the pack with provenance.
3. Use skill spcx-chain-dynamic-decision.
4. If decision is ACT, stop loop and ask for human confirmation before execution.
5. Otherwise write reports/SPCX_chain_decision_YYYYMMDD.md.
```

Do not allow `/loop` to place orders. It may only produce a decision brief and required next checks.

## Codex

Codex should read the skill body and relevant references, then run:

```bash
python scripts/collect_evidence_pack.py --out reports/SPCX_chain_evidence_latest.json --validate
```

If validation passes, Codex performs the agent judgment steps. If validation fails or returns warnings, Codex should browse for missing fields where public sources exist, update the pack with provenance, and re-run validation. If a field is not publicly verifiable, Codex reports which missing fields block action. For options and borrow, record public search results in `computed.instrument_research` unless an actual chain/fee is available from an exchange, broker, OPRA/OCC, or securities-finance source.

## Other Agents

Any agent can use this skill if it respects three boundaries:

1. Evidence pack is the only numeric input authority for the run.
2. Scripts compute; agent judges.
3. Final action is gated by `FREEZE/WATCH/ACT/RETIRE` plus explicit evidence and counterargument.
