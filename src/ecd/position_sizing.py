#!/usr/bin/env python3
"""Deterministic position-sizing engine (domain-agnostic iron rules).

Replaces subjective sizing with a fixed, auditable formula:
    size = base(by tail risk) * holding_period_adj * edge_factor * conviction
capped at 10% NAV.
"""

import argparse
import json


def compute_position(
    edge_pct: float,
    tail_risk_level: str,
    model_validity_score: int = 50,
    holding_period: str = "TREND",
) -> dict:
    """Compute position size as a fraction of NAV with a full audit trail.

    Args:
        edge_pct:             E[V] vs current price as a decimal (0.292 = +29.2%).
        tail_risk_level:      "HIGH" / "MEDIUM" / "LOW".
        model_validity_score: 0-100, drives the conviction multiplier.
        holding_period:       "SWING" / "TREND" / "VALUE" / "PERMANENT".
    """
    if tail_risk_level == "HIGH":
        base = 0.015
        risk_label = "HIGH (>=1 fatal risk with prob > 20%)"
    elif tail_risk_level == "MEDIUM":
        base = 0.04
        risk_label = "MEDIUM (fatal risks at 10-20%, none > 20%)"
    else:
        base = 0.08
        risk_label = "LOW (all fatal risks < 10%)"

    if holding_period == "SWING":
        base *= 0.5
        period_label = "SWING (1-8 weeks): high uncertainty, position halved"
    elif holding_period == "VALUE":
        base *= 1.5
        period_label = "VALUE (6 months-3 years): safety-margin priority, can increase"
    elif holding_period == "PERMANENT":
        base *= 1.8
        period_label = "PERMANENT (3+ years): extremely high confidence"
    else:
        period_label = "TREND (1-6 months): base case"

    edge_factor = min(max(edge_pct / 0.30, 0.5), 1.5)
    edge_label = f"edge_pct={edge_pct:.3f} -> edge_factor={edge_factor:.3f} (clamped to [0.5, 1.5])"

    if model_validity_score >= 80:
        conviction = 1.0
        conviction_label = f"model_validity_score={model_validity_score} >= 80 -> conviction=1.0"
    elif model_validity_score >= 60:
        conviction = 0.8
        conviction_label = f"model_validity_score={model_validity_score} in [60,79] -> conviction=0.8"
    else:
        conviction = 0.6
        conviction_label = f"model_validity_score={model_validity_score} < 60 -> conviction=0.6"

    size = base * edge_factor * conviction
    capped = min(size, 0.10)  # Hard cap: single position <= 10% NAV

    return {
        "position_size_pct_nav": round(capped, 4),
        "formula": "base x edge_factor x conviction",
        "formula_breakdown": {
            "base_by_risk": {"value": base, "tail_risk": tail_risk_level, "description": risk_label},
            "holding_period": {
                "value": holding_period,
                "adjustment": "x0.5/x1.5/x1.8" if holding_period != "TREND" else "none",
                "description": period_label,
            },
            "edge_factor": {"value": round(edge_factor, 4), "description": edge_label},
            "conviction_multiplier": {"value": conviction, "description": conviction_label},
        },
        "audit": {
            "raw_size_before_cap": round(size, 4),
            "cap_applied": size > 0.10,
            "final_capped": round(capped, 4),
        },
    }


def risk_score(level: str) -> int:
    """Map a tail-risk level to a numeric score for portfolio aggregation."""
    return {"LOW": 1, "MEDIUM": 2, "HIGH": 3}[level]


def main() -> None:
    parser = argparse.ArgumentParser(description="Deterministic position sizing engine")
    parser.add_argument("--edge", type=float, required=True, help="E[V] vs price as decimal (0.292 = +29.2%)")
    parser.add_argument("--tail-risk", dest="tail_risk", choices=["HIGH", "MEDIUM", "LOW"], required=True)
    parser.add_argument("--model-score", dest="model_score", type=int, default=50)
    parser.add_argument(
        "--holding-period", dest="holding_period",
        choices=["SWING", "TREND", "VALUE", "PERMANENT"], default="TREND",
    )
    parser.add_argument("--json", action="store_true", help="Output JSON")
    args = parser.parse_args()

    result = compute_position(args.edge, args.tail_risk, args.model_score, args.holding_period)
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"Position Size: {result['position_size_pct_nav']:.2%} NAV")
        print(f"Formula: {result['formula']}")
        if result["audit"]["cap_applied"]:
            print(f"  CAP APPLIED: raw={result['audit']['raw_size_before_cap']:.2%} -> capped at 10%")


if __name__ == "__main__":
    main()
