from datetime import date
from ecd.evidence_pack import generic_template, validate_envelope


def test_template_is_valid():
    pack = generic_template(today="2026-06-15")
    result = validate_envelope(pack, today=date(2026, 6, 15))
    assert result["valid"] is True
    assert result["errors"] == []


def test_missing_required_key_fails():
    pack = generic_template(today="2026-06-15")
    del pack["market_data"]
    result = validate_envelope(pack, today=date(2026, 6, 15))
    assert result["valid"] is False
    assert any("market_data" in e for e in result["errors"])


def test_stale_market_data_blocks():
    pack = generic_template(today="2026-06-15")
    pack["market_data"]["PRIMARY"] = {"close": 147.2, "data_timestamp": "2026-06-01"}
    result = validate_envelope(pack, today=date(2026, 6, 15))
    assert result["valid"] is False
    assert any("stale" in e for e in result["freshness_errors"])


def test_preexisting_computed_freshness_errors_block():
    pack = generic_template(today="2026-06-15")
    pack["computed"]["freshness_errors"] = ["collector said price feed down"]
    result = validate_envelope(pack, today=date(2026, 6, 15))
    assert result["valid"] is False
