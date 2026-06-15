#!/usr/bin/env python3
"""Create or validate SPCX chain decision evidence packs.

Domain-specific reference implementation built on a generic event-chain decision framework (the ecd package).
Date/freshness logic is delegated to ecd.freshness; this file owns only the
SPCX-specific schema and field checks. It makes no investment decisions.
"""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path
from typing import Any

from ecd.freshness import check_block_freshness, parse_date, trading_days_old

REQUIRED_TOP_LEVEL = [
    "analysis_as_of", "source_report", "market_session", "calendar", "market_data",
    "macro", "instruments", "narrative", "hard_data", "prior_positions", "computed",
]


def template() -> dict[str, Any]:
    today = date.today().isoformat()
    return {
        "analysis_as_of": today,
        "source_report": "examples/SPCX_prior_thesis_skeleton.md",
        "market_session": {"last_close_date": None, "is_trading_day": None},
        "calendar": {
            "fomc_freeze_active": None, "greenshoe_active": None,
            "msci_inclusion_pending": None, "ndx_inclusion_pending": None,
            "rklb_ndx_freeze_active": None, "asts_launch_freeze_active": None,
            "phase_hint": None,
        },
        "market_data": {
            ticker: {
                "last_price": None, "close": None, "rsi_14": None,
                "volume": None, "vwap": None, "data_timestamp": None,
            }
            for ticker in ["SPCX", "QQQ", "RKLB", "ASTS", "LUNR", "PL", "RDW", "TSLA"]
        },
        "macro": {"us10y": None, "brent": None, "vix": None, "fomc_tone": None, "data_timestamp": None},
        "instruments": {
            "spcx_options_available": False, "spcx_options_data_quality": "missing",
            "spcx_borrow_available": False, "spcx_borrow_fee_pct": None, "data_timestamp": None,
        },
        "narrative": {
            "wordfreq_window_days": 3,
            "group_a_record_ipo": None, "group_b_ipo_drain_lockup": None,
            "group_c_tech_concentration_bubble": None, "group_d_vertical_ai": None,
            "bc_gt_a_consecutive_days": None, "high_quality_carriers": [],
            "polymarket_signals": {
                "spcx_end_of_month_closing_market_cap_above_current": None,
                "spcx_first_month_close_up": None, "spcx_day2_open_up": None,
                "spcx_day2_close_up": None, "spcx_ndx_inclusion_2026": None,
                "spcx_sp500_inclusion_2026": None, "spcx_volatility_halt_first_month": None,
                "spcx_vs_openai_higher_ipo_marketcap": None, "openai_or_anthropic_s1_filed": None,
                "google_x_spacex_space_data_center": None, "tsla_spacex_merger_2026": None,
                "tldr": None, "source": "polymarket.com", "data_timestamp": None,
            },
        },
        "hard_data": {
            "openai_or_anthropic_s1_filed": False, "spacex_chip_fab_substantive_announcement": False,
            "xai_quarterly_loss_usd_bn": None, "starlink_monthly_net_adds_mn": None,
            "sats_lockup_terms_known": False, "sats_tax_leakage_known": False,
            "sats_transaction_path_known": False,
            "tsla_spacex_merger_agreement_signed": False, "tsla_spacex_exchange_ratio_known": False,
            "tsla_special_committee_formed": False, "tsla_shareholder_litigation_active": False,
        },
        "prior_positions": {"SPCX": 0.0, "RKLB": 0.0, "SATS": 0.0},
        "computed": {"freshness_errors": [], "freshness_warnings": [], "candidate_triggers": [], "rr_checks": []},
    }


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("Evidence pack must be a JSON object.")
    return data


def validate(data: dict[str, Any], today: "date | None" = None) -> dict[str, Any]:
    if today is None:
        today = date.today()
    errors: list[str] = []
    warnings: list[str] = []
    freshness_errors: list[str] = []
    freshness_warnings: list[str] = []

    for key in REQUIRED_TOP_LEVEL:
        if key not in data:
            errors.append(f"missing top-level key: {key}")

    calendar = data.get("calendar", {})
    if isinstance(calendar, dict):
        phase = calendar.get("phase_hint")
        if phase not in {None, "phase_0", "phase_1", "phase_2", "post_august_reassessment"}:
            errors.append("calendar.phase_hint must be phase_0/phase_1/phase_2/post_august_reassessment or null")
    else:
        errors.append("calendar must be an object")

    instruments = data.get("instruments", {})
    if isinstance(instruments, dict):
        quality = instruments.get("spcx_options_data_quality")
        if quality not in {None, "missing", "estimated", "actual"}:
            errors.append("instruments.spcx_options_data_quality must be missing/estimated/actual or null")
        inst_active = (
            instruments.get("spcx_options_available") is True
            or instruments.get("spcx_borrow_available") is True
            or instruments.get("spcx_borrow_fee_pct") is not None
        )
        be, bw = check_block_freshness(instruments, [], "instruments", today=today, has_action=inst_active)
        freshness_errors.extend(be)
        freshness_warnings.extend(bw)
    else:
        errors.append("instruments must be an object")

    market_data = data.get("market_data")
    if isinstance(market_data, dict):
        spcx = market_data.get("SPCX")
        if not isinstance(spcx, dict):
            errors.append("market_data.SPCX must be an object")
        else:
            if spcx.get("rsi_14") is None:
                warnings.append("SPCX RSI is missing; RSI-dependent cards cannot ACT")
            if spcx.get("close") is None and spcx.get("last_price") is None:
                warnings.append("SPCX price is missing; all price-dependent cards are WATCH/FREEZE")
        for ticker, block in market_data.items():
            be, bw = check_block_freshness(
                block, ["last_price", "close", "rsi_14"], f"market_data.{ticker}", today=today
            )
            freshness_errors.extend(be)
            freshness_warnings.extend(bw)
    else:
        errors.append("market_data must be an object")

    macro = data.get("macro", {})
    if isinstance(macro, dict):
        be, bw = check_block_freshness(macro, ["us10y", "vix"], "macro", today=today)
        freshness_errors.extend(be)
        freshness_warnings.extend(bw)

    narrative = data.get("narrative", {})
    if isinstance(narrative, dict):
        pm = narrative.get("polymarket_signals")
        if pm is None:
            freshness_warnings.append("narrative.polymarket_signals missing; L3 cross-validation unavailable")
        elif isinstance(pm, dict):
            ts = pm.get("data_timestamp")
            if ts is not None:
                d = parse_date(ts)
                if d is not None and (today - d).days > 2:
                    freshness_warnings.append(
                        f"narrative.polymarket_signals.data_timestamp={ts} is >2 calendar days old; L3 may be stale"
                    )
            if data.get("market_session", {}).get("is_trading_day") is True:
                for f in ("spcx_end_of_month_closing_market_cap_above_current",
                          "spcx_ndx_inclusion_2026", "spcx_first_month_close_up", "data_timestamp"):
                    if pm.get(f) is None:
                        freshness_warnings.append(f"narrative.polymarket_signals.{f} is null on a weekday pack (L3 auxiliary, non-blocking)")

    computed = data.get("computed", {})
    if isinstance(computed, dict):
        freshness_errors.extend(computed.get("freshness_errors") or [])
        freshness_warnings.extend(computed.get("freshness_warnings") or [])
    else:
        errors.append("computed must be an object")

    errors.extend(freshness_errors)
    warnings.extend(freshness_warnings)

    return {
        "valid": not errors, "errors": errors, "warnings": warnings,
        "freshness_errors": freshness_errors, "freshness_warnings": freshness_warnings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="SPCX chain evidence pack helper")
    sub = parser.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("template", help="write an evidence pack template")
    t.add_argument("--out", required=True)
    v = sub.add_parser("validate", help="validate an evidence pack")
    v.add_argument("--input", required=True)
    args = parser.parse_args()

    if args.cmd == "template":
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(template(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"written": str(out)}, ensure_ascii=False))
        return 0

    data = load_json(Path(args.input))
    result = validate(data)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
