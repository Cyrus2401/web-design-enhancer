#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
audit_composition.py - the geometry layer (#2).

Regex sees TOKENS; vision sees a VIBE. Neither can measure how the page is
actually laid out. This sits in between: given the rendered geometry of the major
sections (a layout.json emitted by visual_audit.py via getBoundingClientRect), it
computes objective composition metrics that line-level regex fundamentally cannot:

  - focal dominance   : is there ONE clear hero, or does everything compete?
  - whitespace breath : does some region deliberately breathe far more than baseline?
  - rhythm regularity : do the vertical gaps follow a systematic spacing scale?
  - alignment grid    : do elements share a small set of left edges (a real grid)?

When no layout.json is available it falls back to a STATIC estimate from the CSS
(type-scale jump + spacing scale), clearly flagged as lower-confidence.

Exit codes: 0 = pass, 1 = below floor, 2 = usage/error.
"""
import argparse
import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import wde_measure as wm

WEIGHTS = {"focal": 30, "whitespace": 25, "rhythm": 25, "alignment": 20}


def _round_bucket(v, step=8):
    return round(v / step) * step


def _vertical_gaps(sections):
    """Gaps between the bottom of one section and the top of the next, in DOM order."""
    ordered = sorted(sections, key=lambda s: s.get("y", 0))
    gaps = []
    for a, b in zip(ordered, ordered[1:]):
        gap = b.get("y", 0) - (a.get("y", 0) + a.get("h", 0))
        if gap >= 0:
            gaps.append(gap)
    return gaps


def score_focal(sections):
    """One dominant region scores high; a flat field of equals scores low."""
    areas = sorted((s.get("w", 0) * s.get("h", 0) for s in sections), reverse=True)
    areas = [a for a in areas if a > 0]
    if len(areas) < 2:
        return WEIGHTS["focal"], "single region - trivially focal"
    ratio = areas[0] / max(areas[1], 1)
    pts = wm.graded(ratio, 1.15, 2.2, WEIGHTS["focal"])
    return pts, f"hero/second area ratio {ratio:.2f}x"


def score_whitespace(sections):
    gaps = _vertical_gaps(sections)
    ratio = wm.whitespace_ratio(gaps)
    pts = wm.graded(ratio, 1.4, 4.0, WEIGHTS["whitespace"])
    return pts, f"max/median vertical gap {ratio:.2f}x"


def score_rhythm(sections):
    """Systematic rhythm = gaps cluster onto a few buckets of a spacing scale.
    Many distinct gap sizes = noisy, ad-hoc spacing."""
    gaps = [g for g in _vertical_gaps(sections) if g > 0]
    if len(gaps) < 3:
        return WEIGHTS["rhythm"], "too few gaps to judge rhythm - assumed clean"
    buckets = {_round_bucket(g) for g in gaps}
    distinct_ratio = len(buckets) / len(gaps)  # 1.0 = every gap different (bad)
    # fewer distinct buckets -> higher score. Invert: 1.0 -> 0, <=0.34 -> full.
    pts = wm.graded(1.0 - distinct_ratio, 0.0, 0.66, WEIGHTS["rhythm"])
    return pts, f"{len(buckets)} distinct gap buckets across {len(gaps)} gaps"


def score_alignment(sections):
    """A real grid means elements share a small set of left edges."""
    lefts = [_round_bucket(s.get("x", 0), 4) for s in sections if s.get("w", 0) > 0]
    if not lefts:
        return 0, "no elements with width"
    distinct = len(set(lefts))
    ratio = distinct / len(lefts)  # 1.0 = every element its own edge (chaos)
    pts = wm.graded(1.0 - ratio, 0.0, 0.6, WEIGHTS["alignment"])
    return pts, f"{distinct} distinct left edges across {len(lefts)} elements"


def analyze_layout(layout):
    sections = layout.get("sections", [])
    if not sections:
        return {"mode": "layout", "error": "no sections in layout.json",
                "composition_score": 0, "metrics": {}}
    metrics = {}
    total = 0
    for name, fn in (("focal", score_focal), ("whitespace", score_whitespace),
                     ("rhythm", score_rhythm), ("alignment", score_alignment)):
        pts, note = fn(sections)
        metrics[name] = {"points": pts, "max": WEIGHTS[name], "note": note}
        total += pts
    return {"mode": "layout", "composition_score": total,
            "section_count": len(sections), "metrics": metrics}


def analyze_static(code_text):
    """No rendered geometry: estimate hierarchy + breath from CSS alone."""
    jump = wm.scale_jump_ratio(code_text)
    spaces = wm.extract_spacing_px(code_text)
    ws = wm.whitespace_ratio(spaces)
    buckets = {_round_bucket(s) for s in spaces} if spaces else set()
    distinct_ratio = (len(buckets) / len(spaces)) if spaces else 1.0
    focal = wm.graded(jump, 2.0, 6.0, WEIGHTS["focal"])
    whitespace = wm.graded(ws, 1.5, 5.0, WEIGHTS["whitespace"])
    rhythm = wm.graded(1.0 - distinct_ratio, 0.0, 0.66, WEIGHTS["rhythm"])
    # alignment cannot be estimated statically; award a neutral half.
    alignment = WEIGHTS["alignment"] // 2
    total = focal + whitespace + rhythm + alignment
    return {"mode": "static-fallback", "composition_score": total,
            "confidence": "low (no rendered geometry - run visual_audit --emit-layout)",
            "metrics": {
                "focal": {"points": focal, "max": WEIGHTS["focal"], "note": f"type-scale jump {jump:.1f}x"},
                "whitespace": {"points": whitespace, "max": WEIGHTS["whitespace"], "note": f"spacing ratio {ws:.1f}x"},
                "rhythm": {"points": rhythm, "max": WEIGHTS["rhythm"], "note": f"{len(buckets)} spacing buckets"},
                "alignment": {"points": alignment, "max": WEIGHTS["alignment"], "note": "not measurable statically"},
            }}


def _collect_code(path):
    p = Path(path)
    if p.is_file():
        return p.read_text(encoding="utf-8", errors="ignore")
    parts = []
    for ext in ("*.css", "*.scss", "*.html", "*.jsx", "*.tsx", "*.js", "*.ts", "*.vue"):
        for fp in p.rglob(ext):
            if any(s in fp.parts for s in ("node_modules", ".git", "dist", "build")):
                continue
            try:
                parts.append(fp.read_text(encoding="utf-8", errors="ignore"))
            except Exception:
                pass
    return "\n".join(parts)


def run(layout_path=None, code_path=".", floor=50, passing=70, as_json=False):
    if layout_path and Path(layout_path).exists():
        result = analyze_layout(json.loads(Path(layout_path).read_text(encoding="utf-8")))
    else:
        result = analyze_static(_collect_code(code_path))
    score = result["composition_score"]
    result["floor"] = floor
    result["passing"] = passing
    result["status"] = "pass" if score >= passing else ("weak" if score >= floor else "blocked")
    if as_json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print("=" * 60)
        print(f"COMPOSITION  [{result['mode']}]  score {score}/100  -> {result['status'].upper()}")
        for name, m in result.get("metrics", {}).items():
            print(f"  {name:<11} {m['points']:>2}/{m['max']:<2}  {m['note']}")
        if "confidence" in result:
            print(f"  confidence: {result['confidence']}")
        print("=" * 60)
    return 0 if score >= floor else 1


def main():
    ap = argparse.ArgumentParser(prog="audit_composition",
                                 description="Geometry-based composition metrics (#2)")
    ap.add_argument("--layout", default=None, help="layout.json from visual_audit --emit-layout")
    ap.add_argument("--code", default=".", help="code dir for static fallback")
    ap.add_argument("--threshold", nargs=2, type=int, metavar=("FLOOR", "PASS"), default=[50, 70])
    ap.add_argument("--json", action="store_true", dest="as_json")
    args = ap.parse_args()
    sys.exit(run(args.layout, args.code, args.threshold[0], args.threshold[1], args.as_json))


if __name__ == "__main__":
    main()
