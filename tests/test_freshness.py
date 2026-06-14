from datetime import date
from ecd.freshness import parse_date, trading_days_old, check_block_freshness


def test_parse_bare_date():
    assert parse_date("2026-06-14") == date(2026, 6, 14)


def test_parse_iso_datetime_with_z():
    assert parse_date("2026-06-14T06:30:00Z") == date(2026, 6, 14)


def test_parse_iso_datetime_with_offset():
    assert parse_date("2026-06-14T06:30:00+08:00") == date(2026, 6, 14)


def test_parse_garbage_returns_none():
    assert parse_date("not-a-date") is None
    assert parse_date(None) is None
    assert parse_date("") is None


def test_trading_days_friday_checked_monday_is_zero():
    # Fri 2026-06-12 checked on Mon 2026-06-15 -> only Sat/Sun between -> 0
    assert trading_days_old(date(2026, 6, 12), today=date(2026, 6, 15)) == 0


def test_trading_days_future_is_zero():
    assert trading_days_old(date(2026, 6, 20), today=date(2026, 6, 15)) == 0


def test_trading_days_ten_days_is_stale():
    assert trading_days_old(date(2026, 6, 1), today=date(2026, 6, 15)) == 9


def test_block_fresh_when_no_action_values():
    block = {"last_price": None, "close": None, "rsi_14": None, "data_timestamp": None}
    errors, warnings = check_block_freshness(block, ["last_price", "close", "rsi_14"], "market_data.SPCX")
    assert errors == [] and warnings == []


def test_block_stale_action_value_blocks():
    block = {"close": 147.2, "data_timestamp": "2026-06-01"}
    errors, warnings = check_block_freshness(
        block, ["last_price", "close", "rsi_14"], "market_data.SPCX", today=date(2026, 6, 15)
    )
    assert len(errors) == 1 and "stale" in errors[0]


def test_block_missing_timestamp_warns_not_errors():
    block = {"close": 147.2, "data_timestamp": None}
    errors, warnings = check_block_freshness(
        block, ["last_price", "close", "rsi_14"], "market_data.SPCX", today=date(2026, 6, 15)
    )
    assert errors == [] and len(warnings) == 1


def test_block_has_action_override_for_booleans():
    # instruments-style: action presence is computed by caller, not auto-detected
    block = {"spcx_options_available": False, "data_timestamp": "2026-06-01"}
    errors, _ = check_block_freshness(
        block, [], "instruments", today=date(2026, 6, 15), has_action=True
    )
    assert len(errors) == 1


def test_block_unparseable_timestamp_errors():
    block = {"close": 147.2, "data_timestamp": "garbage"}
    errors, warnings = check_block_freshness(
        block, ["last_price", "close", "rsi_14"], "market_data.SPCX", today=date(2026, 6, 15)
    )
    assert len(errors) == 1 and "unparseable" in errors[0]
