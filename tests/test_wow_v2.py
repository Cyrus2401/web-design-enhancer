"""Tests for audit_wow.py V2: graded W1 (scale-jump) and the two-axis decomposition."""
import json
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).parent.parent / "scripts" / "audit_wow.py"

BRIEF_TYPO_EXTREME = """# CREATIVE-BRIEF.md
## Hero Dimension
- [x] Typography
## Design Dials
- VARIANCE: **9**
- MOTION: **2**
- DENSITY: **6**
"""

CSS_HUGE = "h1{font-size:clamp(48px,11vw,132px);font-family:'Playfair Display'}"
CSS_MODERATE = "body{font-size:16px} h1{font-size:48px;font-family:'Playfair Display'}"


def run(tmp_path, css, brief, *args):
    (tmp_path / "styles.css").write_text(css, encoding="utf-8")
    (tmp_path / "CREATIVE-BRIEF.md").write_text(brief, encoding="utf-8")
    dpath = tmp_path / "DESIGN.md"
    dpath.write_text("", encoding="utf-8")
    cmd = [sys.executable, str(SCRIPT), "--code", str(tmp_path),
           "--brief", str(tmp_path / "CREATIVE-BRIEF.md"), "--design", str(dpath),
           "--archetype", "02 Editorial", "--json", *args]
    return subprocess.run(cmd, capture_output=True, text=True)


def _w1(data):
    return next(l for l in data["levers"] if l["id"] == "W1")


def test_w1_graded_partial_for_moderate_jump(tmp_path):
    """A 48px-on-16px jump (ratio 3x) is below the legacy binary trigger but should
    now earn PARTIAL W1 credit instead of a flat zero."""
    r = run(tmp_path, CSS_MODERATE, BRIEF_TYPO_EXTREME)
    data = json.loads(r.stdout)
    w1 = _w1(data)
    assert 0 < w1["points"] < w1["max"], w1


def test_w1_full_for_violent_jump(tmp_path):
    r = run(tmp_path, CSS_HUGE, BRIEF_TYPO_EXTREME)
    data = json.loads(r.stdout)
    assert _w1(data)["points"] == _w1(data)["max"]


def test_axes_present_in_json(tmp_path):
    r = run(tmp_path, CSS_HUGE, BRIEF_TYPO_EXTREME)
    data = json.loads(r.stdout)
    assert "axes" in data
    for k in ("ambition", "execution", "diagnosis", "balanced"):
        assert k in data["axes"]


def test_axes_ambitious_but_botched(tmp_path):
    """Huge type + extreme dial = high ambition; no gestures/signature = low execution."""
    r = run(tmp_path, CSS_HUGE, BRIEF_TYPO_EXTREME)
    data = json.loads(r.stdout)
    ax = data["axes"]
    assert ax["ambition"] >= 60
    assert ax["execution"] < 60
    assert "botched" in ax["diagnosis"]
