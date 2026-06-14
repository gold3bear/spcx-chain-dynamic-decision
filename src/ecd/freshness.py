"""Date parsing and trading-day freshness helpers (domain-agnostic).

Used to gate action-critical realtime data: data older than N trading days
must block an ACT decision. Trading-day counting is business-day aware so
Friday data checked on Monday is not falsely flagged stale.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta


def parse_date(value) -> "date | None":
    """Parse a YYYY-MM-DD string or an ISO-8601 datetime into a date.

    Tolerates a trailing 'Z' and timezone offsets. Returns None on any failure
    (non-string, empty, or unparseable).
    """
    if not isinstance(value, str):
        return None
    text = value.strip()
    if not text:
        return None
    try:
        return date.fromisoformat(text)
    except ValueError:
        pass
    try:
        cleaned = text.replace("Z", "+00:00").replace("z", "+00:00")
        return datetime.fromisoformat(cleaned).date()
    except ValueError:
        return None


def trading_days_old(d: date, today: "date | None" = None) -> int:
    """Count weekdays (Mon-Fri) strictly between ``d`` and ``today``.

    Friday checked on Monday -> 0 (only Sat/Sun lie strictly between).
    A future-or-equal date -> 0.
    """
    if today is None:
        today = date.today()
    if d >= today:
        return 0
    delta_days = (today - d).days
    if delta_days > 366:
        # Far stale: exact trading-day count is irrelevant for any realistic
        # threshold, and this bounds the loop. Return a large, clearly-stale value.
        return delta_days
    count = 0
    cur = d + timedelta(days=1)
    while cur < today:
        if cur.weekday() < 5:
            count += 1
        cur += timedelta(days=1)
    return count


def check_block_freshness(
    block,
    action_keys,
    block_name: str,
    timestamp_key: str = "data_timestamp",
    max_trading_days: int = 1,
    today: "date | None" = None,
    has_action: "bool | None" = None,
) -> "tuple[list[str], list[str]]":
    """Return (errors, warnings) for one action-critical block.

    Only evaluated when the block actually carries action-critical data:
      - by default, when any ``action_keys`` value is non-null;
      - or when the caller passes ``has_action=True`` (e.g. boolean flags
        where ``is not None`` is the wrong test).

    Stale (older than ``max_trading_days`` trading days) -> blocking error.
    Missing timestamp -> warning. Unparseable timestamp -> error.
    """
    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(block, dict):
        return errors, warnings

    active = has_action if has_action is not None else any(
        block.get(k) is not None for k in action_keys
    )
    if not active:
        return errors, warnings

    ts = block.get(timestamp_key)
    if ts is None:
        warnings.append(
            f"{block_name}.{timestamp_key} missing; cannot verify freshness of action-critical data"
        )
        return errors, warnings

    d = parse_date(ts)
    if d is None:
        errors.append(f"{block_name}.{timestamp_key}={ts} is unparseable")
        return errors, warnings

    if trading_days_old(d, today=today) > max_trading_days:
        errors.append(
            f"{block_name}.{timestamp_key}={ts} is older than {max_trading_days} "
            f"trading day(s); action-critical data is stale"
        )
    return errors, warnings
