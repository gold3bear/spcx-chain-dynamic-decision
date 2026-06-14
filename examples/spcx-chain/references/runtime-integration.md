# Runtime Integration

This skill is runtime-agnostic. OpenClaw, Claude Code, Codex, or another agent can all use the same evidence pack and decision protocol.

## OpenClaw Scheduled Task

Run collectors first, then call the agent with this skill and the evidence pack.

Suggested schedule in Asia/Shanghai time:
- 06:30 daily after US close: full daily evidence pack.
- Event days: add one-off runs after FOMC, option listing, index inclusion, greenshoe expiry, earnings, and lockup windows.

Example Windows task for evidence pack validation:

```powershell
schtasks /Create /SC DAILY /TN "SPCX Evidence Pack Validate" /ST 06:30 /TR "powershell -NoProfile -ExecutionPolicy Bypass -Command cd D:\projects\event-chain-decision; python examples\spcx-chain\scripts\spcx_decision_pack.py validate --input reports\SPCX_chain_evidence_latest.json"
```

OpenClaw should then prompt the agent:

```text
Use examples/spcx-chain/SKILL.md.
Read reports/SPCX_chain_evidence_latest.json.
Return the decision JSON and concise human brief.
```

## Claude Code `/loop`

Use `/loop` for market watch iterations:

```text
/loop every weekday after US close:
1. Refresh SPCX evidence pack.
2. Use skill spcx-chain-dynamic-decision.
3. If decision is ACT, stop loop and ask for human confirmation before execution.
4. Otherwise write reports/SPCX_chain_decision_YYYYMMDD.md.
```

Do not allow `/loop` to place orders. It may only produce a decision brief and required next checks.

## Codex

Codex should read the skill body and relevant references, then run:

```bash
python examples/spcx-chain/scripts/spcx_decision_pack.py validate --input reports/SPCX_chain_evidence_latest.json
```

If validation passes, Codex performs the agent judgment steps. If validation fails, Codex reports which missing fields block action.

## Other Agents

Any agent can use this skill if it respects three boundaries:

1. Evidence pack is the only numeric input authority for the run.
2. Scripts compute; agent judges.
3. Final action is gated by `FREEZE/WATCH/ACT/RETIRE` plus explicit evidence and counterargument.
