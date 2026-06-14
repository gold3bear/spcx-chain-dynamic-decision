"""Generic evidence-pack envelope: template + validation.

This is the domain-agnostic core. A concrete chain (see examples/spcx-chain)
adds its own domain fields and its own validator, reusing ecd.freshness for
the action-critical staleness gate. Keep this file free of any domain field.
"""

from __future__ import annotations

from datetime import date

from ecd.freshness import check_block_freshness, parse_date

REQUIRED_TOP_LEVEL = ["analysis_as_of", "market_session", "market_data", "macro", "computed"]

# Default action-critical keys per block. Override per chain as needed.
MARKET_DATA_ACTION_KEYS = ["last_price", "close", "rsi_14"]
MACRO_ACTION_KEYS = ["us10y", "vix"]


def generic_template(today: str) -> dict:
    """Return a minimal, valid generic envelope. ``today`` is YYYY-MM-DD."""
    return {
        "analysis_as_of": today,
        "source_report": None,
        "market_session": {"last_close_date": None, "is_trading_day": None},
        "calendar": {"phase_hint": None},
        "market_data": {},
        "macro": {"us10y": None, "vix": None, "data_timestamp": None},
        "computed": {"freshness_errors": [], "freshness_warnings": []},
    }


def validate_envelope(data: dict, today: "date | None" = None) -> dict:
    """Validate the generic envelope: required keys, analysis_as_of parseable,
    action-critical freshness (blocking), and any pre-existing computed
    freshness_errors (blocking)."""
    if today is None:
        today = date.today()

    errors: list[str] = []
    warnings: list[str] = []
    freshness_errors: list[str] = []
    freshness_warnings: list[str] = []

    for key in REQUIRED_TOP_LEVEL:
        if key not in data:
            errors.append(f"missing top-level key: {key}")

    if "analysis_as_of" in data and parse_date(data.get("analysis_as_of")) is None:
        errors.append("analysis_as_of is missing or not a parseable date")

    market_data = data.get("market_data")
    if isinstance(market_data, dict):
        for ticker, block in market_data.items():
            be, bw = check_block_freshness(
                block, MARKET_DATA_ACTION_KEYS, f"market_data.{ticker}", today=today
            )
            freshness_errors.extend(be)
            freshness_warnings.extend(bw)
    elif "market_data" in data:
        errors.append("market_data must be an object")

    macro = data.get("macro")
    if isinstance(macro, dict):
        be, bw = check_block_freshness(macro, MACRO_ACTION_KEYS, "macro", today=today)
        freshness_errors.extend(be)
        freshness_warnings.extend(bw)

    computed = data.get("computed", {})
    if isinstance(computed, dict):
        freshness_errors.extend(computed.get("freshness_errors") or [])
        freshness_warnings.extend(computed.get("freshness_warnings") or [])
    elif "computed" in data:
        errors.append("computed must be an object")

    errors.extend(freshness_errors)
    warnings.extend(freshness_warnings)

    return {
        "valid": not errors,
        "errors": errors,
        "warnings": warnings,
        "freshness_errors": freshness_errors,
        "freshness_warnings": freshness_warnings,
    }
