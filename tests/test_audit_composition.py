"""Tests for audit_composition.py - geometry composition metrics (#2)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import audit_composition as ac

GOOD = {
    "viewport": {"width": 1440, "height": 2700},
    "sections": [
        {"tag": "header", "x": 0, "y": 0, "w": 1440, "h": 72},
        {"tag": "section", "role": "hero", "x": 0, "y": 72, "w": 1440, "h": 820},
        {"tag": "section", "x": 120, "y": 1212, "w": 1200, "h": 300},
        {"tag": "section", "x": 120, "y": 1608, "w": 1200, "h": 300},
        {"tag": "section", "x": 120, "y": 2004, "w": 1200, "h": 300},
        {"tag": "footer", "x": 0, "y": 2400, "w": 1440, "h": 140},
    ],
}
CHAOTIC = {
    "viewport": {"width": 1440, "height": 1700},
    "sections": [
        {"x": 0, "y": 0, "w": 700, "h": 300},
        {"x": 133, "y": 310, "w": 680, "h": 295},
        {"x": 47, "y": 655, "w": 690, "h": 305},
        {"x": 210, "y": 1001, "w": 705, "h": 298},
        {"x": 88, "y": 1400, "w": 695, "h": 302},
    ],
}


def test_good_layout_scores_well():
    r = ac.analyze_layout(GOOD)
    assert r["composition_score"] >= 70, r


def test_chaotic_layout_scores_poorly():
    r = ac.analyze_layout(CHAOTIC)
    assert r["composition_score"] < 40, r


def test_good_beats_chaotic_by_margin():
    good = ac.analyze_layout(GOOD)["composition_score"]
    bad = ac.analyze_layout(CHAOTIC)["composition_score"]
    assert good - bad >= 20


def test_metrics_keys_present():
    r = ac.analyze_layout(GOOD)
    for k in ("focal", "whitespace", "rhythm", "alignment"):
        assert k in r["metrics"]
        assert 0 <= r["metrics"][k]["points"] <= r["metrics"][k]["max"]


def test_focal_dominance_detects_single_hero():
    pts, _ = ac.score_focal(GOOD["sections"])
    flat_pts, _ = ac.score_focal(CHAOTIC["sections"])
    assert pts > flat_pts


def test_alignment_rewards_shared_edges():
    pts, _ = ac.score_alignment(GOOD["sections"])
    chaos, _ = ac.score_alignment(CHAOTIC["sections"])
    assert pts > chaos


def test_static_fallback_runs_without_layout():
    css = "body{font-size:16px} h1{font-size:120px} .s{padding:96px} .t{gap:24px}"
    r = ac.analyze_static(css)
    assert r["mode"] == "static-fallback"
    assert r["metrics"]["focal"]["points"] > 0
    assert "confidence" in r
