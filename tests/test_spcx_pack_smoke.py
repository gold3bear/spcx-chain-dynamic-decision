import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "spcx_decision_pack.py"


def _run(args):
    return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True)


def test_template_then_validate_is_valid(tmp_path):
    out = tmp_path / "pack.json"
    r = _run(["template", "--out", str(out)])
    assert r.returncode == 0
    r2 = _run(["validate", "--input", str(out)])
    result = json.loads(r2.stdout)
    assert result["valid"] is True
    assert r2.returncode == 0


def test_stale_realtime_blocks(tmp_path):
    out = tmp_path / "pack.json"
    _run(["template", "--out", str(out)])
    data = json.loads(out.read_text(encoding="utf-8"))
    data["market_data"]["SPCX"]["close"] = 147.2
    data["market_data"]["SPCX"]["data_timestamp"] = "2026-06-01"
    out.write_text(json.dumps(data), encoding="utf-8")
    r = _run(["validate", "--input", str(out)])
    result = json.loads(r.stdout)
    assert result["valid"] is False
    assert r.returncode == 1


def test_sanitized_example_has_no_real_positions(tmp_path):
    out = tmp_path / "pack.json"
    _run(["template", "--out", str(out)])
    data = json.loads(out.read_text(encoding="utf-8"))
    assert all(v == 0.0 for v in data["prior_positions"].values())
