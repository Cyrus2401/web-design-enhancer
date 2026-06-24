"""Tests for aesthetic_harden.py - reliability harness around the vision judge (#3)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import aesthetic_harden as ah


def test_variance_agreeing_runs():
    r = ah.variance_report([81, 83, 82])
    assert r["uncertain"] is False
    assert r["median"] == 82


def test_variance_disagreeing_runs_flag_uncertain():
    r = ah.variance_report([60, 85, 72])
    assert r["uncertain"] is True
    assert "human review" in r["reason"]


def test_variance_uses_median_not_mean():
    # one rogue run should not swing the verdict
    r = ah.variance_report([80, 81, 79, 79, 81])
    assert r["median"] == 80


def test_variance_empty():
    r = ah.variance_report([])
    assert r["uncertain"] is True and r["median"] is None


def test_calibrate_via_comparisons_band():
    comps = [
        {"anchor_score": 60, "candidate_better": True},
        {"anchor_score": 75, "candidate_better": True},
        {"anchor_score": 90, "candidate_better": False},
    ]
    c = ah.calibrate_via_comparisons(comps)
    assert c["low"] == 75 and c["high"] == 90
    assert c["score"] == 83 or c["score"] == 82
    assert c["consistent"] is True


def test_calibrate_detects_inconsistency():
    comps = [
        {"anchor_score": 90, "candidate_better": True},   # beats the best
        {"anchor_score": 60, "candidate_better": False},  # but loses to a worse one
    ]
    c = ah.calibrate_via_comparisons(comps)
    assert c["consistent"] is False


def test_validate_evidence_flags_bare_numbers():
    verdict = {"dimensions": {
        "hierarchy": {"score": 8, "evidence": "H1 at 110px against 16px body = 7:1 jump"},
        "color": {"score": 7, "evidence": ""},
        "restraint": {"score": 6},
    }}
    missing = ah.validate_evidence(verdict)
    assert "color" in missing and "restraint" in missing
    assert "hierarchy" not in missing


def test_aggregate_runs_combines_everything():
    runs = [
        {"overall": 81, "dimensions": {"a": {"score": 8, "evidence": "clear focal hero region"}}},
        {"overall": 83, "dimensions": {"a": {"score": 8, "evidence": "clear focal hero region"}}},
    ]
    rep = ah.aggregate_runs(runs)
    assert rep["median"] == 82
    assert rep["evidence_complete"] is True


# --- #5 calibration corpus wiring ---
import json as _json
_CORPUS_PATH = Path(__file__).parent.parent / "references" / "calibration_corpus.json"


def test_corpus_file_exists_and_schema():
    data = _json.loads(_CORPUS_PATH.read_text(encoding="utf-8"))
    anchors = data["anchors"]
    assert len(anchors) >= 5
    for a in anchors:
        assert set(["id", "archetype", "score", "source"]).issubset(a)
        assert 0 <= a["score"] <= 100


def test_load_corpus_returns_id_map():
    corpus = ah.load_corpus(str(_CORPUS_PATH))
    assert "stripe-press-2023" in corpus
    assert corpus["stripe-press-2023"]["score"] == 92


def test_comparisons_from_corpus_builds_dicts():
    corpus = ah.load_corpus(str(_CORPUS_PATH))
    comps = ah.comparisons_from_corpus(corpus,
        beats=["saas-generic-template"], loses=["stripe-press-2023"])
    assert {"anchor_score", "candidate_better"}.issubset(comps[0])
    assert any(c["candidate_better"] for c in comps)
    assert any(not c["candidate_better"] for c in comps)


def test_calibrate_against_corpus_band():
    res = ah.calibrate_against_corpus(str(_CORPUS_PATH),
        beats=["saas-generic-template", "brutalist-balenciaga"],
        loses=["stripe-press-2023", "linear-landing-2024"])
    assert res["low"] == 78 and res["high"] == 90
    assert res["consistent"] is True


def test_comparisons_ignore_unknown_ids():
    comps = ah.comparisons_from_corpus(str(_CORPUS_PATH), beats=["does-not-exist"], loses=[])
    assert comps == []
