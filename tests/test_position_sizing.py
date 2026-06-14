from ecd.position_sizing import compute_position, risk_score


def test_base_low_risk_trend():
    r = compute_position(edge_pct=0.30, tail_risk_level="LOW", model_validity_score=80, holding_period="TREND")
    assert r["position_size_pct_nav"] == 0.08
    assert r["audit"]["cap_applied"] is False


def test_swing_halves_position():
    r = compute_position(edge_pct=0.30, tail_risk_level="MEDIUM", model_validity_score=80, holding_period="SWING")
    assert r["position_size_pct_nav"] == 0.02


def test_hard_cap_at_ten_percent():
    r = compute_position(edge_pct=0.45, tail_risk_level="LOW", model_validity_score=80, holding_period="PERMANENT")
    assert r["position_size_pct_nav"] == 0.10
    assert r["audit"]["cap_applied"] is True


def test_low_conviction_reduces_size():
    r = compute_position(edge_pct=0.30, tail_risk_level="LOW", model_validity_score=50, holding_period="TREND")
    assert r["position_size_pct_nav"] == round(0.08 * 1.0 * 0.6, 4)


def test_risk_score_mapping():
    assert risk_score("LOW") == 1
    assert risk_score("MEDIUM") == 2
    assert risk_score("HIGH") == 3
