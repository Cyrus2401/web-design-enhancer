#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
aesthetic_harden.py - deterministic reliability harness around the vision judge (#3).

aesthetic_review.py is the real arbiter of beauty, but a single absolute 0-100
score from one model run is noisy and prompt-fragile. This module hardens it
WITHOUT pretending the judgment is deterministic:

  - variance_report      : judge N times, report median + spread, flag 'uncertain'
                           when runs disagree (-> route to human review).
  - calibrate_via_comparisons : models are far better at A-vs-B than at absolute
                           scoring. Given reference screenshots with KNOWN scores,
                           turn pairwise verdicts into a calibrated score band.
  - validate_evidence    : reject verdicts that are bare numbers; every dimension
                           must cite a concrete visual reason (auditable).

All functions are pure and unit-tested; the CLI aggregates verdict JSON files.
"""
import argparse
import json
import statistics
import sys
from pathlib import Path

UNCERTAIN_SPREAD = 10  # points; if N runs differ by more than this -> uncertain


def variance_report(scores, uncertain_spread=UNCERTAIN_SPREAD):
    """N independent judge scores -> median (robust), spread and an uncertainty flag.
    Median is reported (not mean) so one rogue run does not swing the verdict."""
    vals = [float(s) for s in scores if s is not None]
    if not vals:
        return {"n": 0, "median": None, "spread": None, "uncertain": True,
                "reason": "no scores"}
    spread = max(vals) - min(vals)
    return {
        "n": len(vals),
        "median": round(statistics.median(vals), 1),
        "mean": round(statistics.mean(vals), 1),
        "min": min(vals), "max": max(vals),
        "spread": round(spread, 1),
        "stdev": round(statistics.pstdev(vals), 2) if len(vals) > 1 else 0.0,
        "uncertain": spread > uncertain_spread,
        "reason": ("judges disagree - human review" if spread > uncertain_spread
                   else "judges agree"),
    }


def calibrate_via_comparisons(comparisons):
    """Turn pairwise A-vs-B verdicts into an absolute score band.

    comparisons: [{"anchor_score": int, "candidate_better": bool}, ...]
    The candidate sits above every anchor it beats and below every anchor it loses
    to. Returns the band and a midpoint score, plus a consistency flag (it is
    incoherent to beat a high anchor yet lose to a lower one)."""
    beaten = sorted(c["anchor_score"] for c in comparisons if c["candidate_better"])
    lost = sorted(c["anchor_score"] for c in comparisons if not c["candidate_better"])
    low = max(beaten) if beaten else 0
    high = min(lost) if lost else 100
    consistent = (not beaten or not lost) or (max(beaten) <= min(lost))
    if low > high:  # inconsistent ordering; fall back to the overlap midpoint
        low, high = min(low, high), max(low, high)
    return {"low": low, "high": high, "score": round((low + high) / 2),
            "consistent": consistent,
            "anchors_beaten": beaten, "anchors_lost": lost}


def validate_evidence(verdict, min_len=12):
    """Every scored dimension must cite a concrete visual reason. Returns the list
    of dimensions whose evidence is missing or too thin (bare-number scoring)."""
    dims = verdict.get("dimensions", {})
    missing = []
    for name, d in dims.items():
        ev = (d.get("evidence") or "").strip() if isinstance(d, dict) else ""
        if len(ev) < min_len:
            missing.append(name)
    return missing


def aggregate_runs(run_verdicts, anchors=None):
    """Combine N judge runs into one hardened verdict."""
    scores = [v.get("overall") if isinstance(v, dict) else v for v in run_verdicts]
    rep = variance_report(scores)
    evidence_gaps = []
    for v in run_verdicts:
        if isinstance(v, dict):
            evidence_gaps.extend(validate_evidence(v))
    rep["evidence_complete"] = len(evidence_gaps) == 0
    rep["evidence_gaps"] = sorted(set(evidence_gaps))
    if anchors:
        comps = anchors  # already comparison dicts
        rep["calibration"] = calibrate_via_comparisons(comps)
    return rep


def load_corpus(path):
    """Load the labeled calibration corpus (#5). Returns a dict id -> anchor."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    anchors = data.get("anchors", data if isinstance(data, list) else [])
    return {a["id"]: a for a in anchors}


def comparisons_from_corpus(corpus, beats=None, loses=None):
    """Turn "candidate beats anchors X,Y / loses to Z" into calibrated comparison
    dicts the calibrator consumes. Unknown ids are ignored. corpus may be the
    id->anchor dict from load_corpus() or a path to the corpus JSON."""
    if isinstance(corpus, (str, Path)):
        corpus = load_corpus(corpus)
    comps = []
    for cid in (beats or []):
        if cid in corpus:
            comps.append({"anchor_id": cid, "anchor_score": corpus[cid]["score"],
                          "candidate_better": True})
    for cid in (loses or []):
        if cid in corpus:
            comps.append({"anchor_id": cid, "anchor_score": corpus[cid]["score"],
                          "candidate_better": False})
    return comps


def calibrate_against_corpus(corpus, beats=None, loses=None):
    """Convenience: corpus + win/loss ids -> calibrated score band."""
    return calibrate_via_comparisons(comparisons_from_corpus(corpus, beats, loses))


def _load_json_dir(path):
    out = []
    p = Path(path)
    files = sorted(p.glob("*.json")) if p.is_dir() else [p]
    for fp in files:
        try:
            out.append(json.loads(fp.read_text(encoding="utf-8")))
        except Exception:
            pass
    return out


def main():
    ap = argparse.ArgumentParser(prog="aesthetic_harden",
                                 description="Reliability harness for the vision judge (#3)")
    ap.add_argument("--verdicts", required=True, help="dir or file of judge verdict JSONs")
    ap.add_argument("--anchors", default=None, help="JSON file of pairwise comparisons")
    ap.add_argument("--json", action="store_true", dest="as_json")
    args = ap.parse_args()
    runs = _load_json_dir(args.verdicts)
    anchors = None
    if args.anchors and Path(args.anchors).exists():
        anchors = json.loads(Path(args.anchors).read_text(encoding="utf-8"))
    rep = aggregate_runs(runs, anchors)
    if args.as_json:
        print(json.dumps(rep, indent=2, ensure_ascii=False))
    else:
        print("=" * 60)
        print(f"AESTHETIC (hardened)  median {rep['median']}  spread {rep['spread']}  "
              f"n={rep['n']}")
        print(f"  {'UNCERTAIN - human review' if rep['uncertain'] else 'judges agree'}")
        if not rep["evidence_complete"]:
            print(f"  evidence missing for: {', '.join(rep['evidence_gaps'])}")
        if "calibration" in rep:
            c = rep["calibration"]
            print(f"  anchored score {c['score']} (band {c['low']}-{c['high']}, "
                  f"{'consistent' if c['consistent'] else 'INCONSISTENT'})")
        print("=" * 60)
    sys.exit(0 if not rep["uncertain"] else 1)


if __name__ == "__main__":
    main()
