# Position Sizing

Sizing is deterministic and auditable, computed by `ecd.position_sizing`, never
by prose. Iron rules:

- **Single position <= 10% NAV** (hard cap).
- **EV <= 0 -> no trade.** EV > 0 -> size is a function of edge, tail risk,
  conviction, and holding period.
- **Holding-period role split:** for SWING (1-8 weeks) with options/leverage,
  R/R < 1:1 is forbidden. For TREND/VALUE/PERMANENT, R/R is a sizing input, not
  a gate.
- Risk decides size, not whether to trade.

Formula: `size = base(tail_risk) x holding_period_adj x edge_factor x conviction`,
clamped to 10%.

| Input | Effect |
|------|------|
| tail_risk HIGH / MEDIUM / LOW | base 1.5% / 4% / 8% |
| holding SWING / TREND / VALUE / PERMANENT | x0.5 / x1 / x1.5 / x1.8 |
| edge_pct | edge_factor = clamp(edge/0.30, 0.5, 1.5) |
| model_validity_score | >=80 -> 1.0; 60-79 -> 0.8; <60 -> 0.6 |

Usage:
```bash
python -m ecd.position_sizing --edge 0.29 --tail-risk HIGH --model-score 60 --holding-period SWING --json
```
