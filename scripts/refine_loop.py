#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
refine_loop.py - turn the validator into an ENHANCER (the loop).

The rest of the pipeline is a one-shot gate: pass or fail. Real design is
iterative - measure, fix the highest-leverage problem, measure again, converge.
This module is that loop's brain. It does NOT edit code (that is the model's job
between iterations); it MEASURES, DECIDES whether to keep going, PRIORITISES what
to fix next, and HISTORISES every pass to .refine-log.json so progress (and
regressions) are visible.

Separation of concerns:
  - measure()        : run the audits, normalise their scores  (impure, subprocess)
  - decide()         : convergence / plateau / regression / max-iter  (PURE)
  - prioritize()     : rank failing gates by leverage = weight x gap  (PURE)

Exit code: 0 when converged (stop), 1 when more work is advised (keep looping).
"""
import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent

# name -> (higher_is_better, floor, weight). uniqueness is "lower is better"
# (it measures resemblance to the Generic AI Template; block above the floor).
GATES = {
    "beauty":      (True,  70, 25),
    "composition": (True,  70, 20),
    "aesthetic":   (True,  80, 20),
    "wow":         (True,  70, 15),
    "uniqueness":  (False, 65, 20),
}


# ---------------------------------------------------------------------------
# PURE decision engine (unit-tested without a project)
# ---------------------------------------------------------------------------
def gate_passes(name, value):
    if value is None or name not in GATES:
        return True  # absent metric does not block
    higher_is_better, floor, _ = GATES[name]
    return value >= floor if higher_is_better else value <= floor


def gate_gap(name, value):
    """How far a metric is from passing, normalised 0..1 (0 = passes)."""
    if value is None or name not in GATES or gate_passes(name, value):
        return 0.0
    higher_is_better, floor, _ = GATES[name]
    if higher_is_better:
        return max(0.0, (floor - value) / max(floor, 1))
    return max(0.0, (value - floor) / max(100 - floor, 1))


def all_pass(scores):
    return all(gate_passes(n, scores.get(n)) for n in GATES if scores.get(n) is not None)


def aggregate(scores):
    """Single 0..100 health number, weighted across present gates."""
    num = den = 0.0
    for name, (higher_is_better, _floor, weight) in GATES.items():
        v = scores.get(name)
        if v is None:
            continue
        norm = v if higher_is_better else max(0.0, 100 - v)
        num += weight * norm
        den += weight
    return round(num / den, 1) if den else 0.0


def prioritize(scores, issues=None):
    """Failing gates ranked by leverage = weight x gap, each with its fix hints."""
    issues = issues or {}
    ranked = []
    for name, (_hib, _floor, weight) in GATES.items():
        v = scores.get(name)
        if v is None or gate_passes(name, v):
            continue
        ranked.append({
            "gate": name,
            "value": v,
            "floor": GATES[name][1],
            "leverage": round(weight * gate_gap(name, v), 2),
            "fixes": issues.get(name, [])[:3],
        })
    ranked.sort(key=lambda r: r["leverage"], reverse=True)
    return ranked


def decide(history, max_iter=6, plateau_k=2, epsilon=1.5):
    """Given the iteration history, decide whether to stop and why."""
    if not history:
        return {"action": "continue", "reason": "no measurements yet"}
    latest = history[-1]
    scores = latest.get("scores", {})
    agg = latest.get("aggregate", aggregate(scores))

    if all_pass(scores):
        return {"action": "stop", "reason": "converged - all gates pass", "aggregate": agg}
    if len(history) >= max_iter:
        return {"action": "stop", "reason": f"max-iterations ({max_iter}) reached", "aggregate": agg}

    flags = []
    if len(history) >= 2:
        prev = history[-2].get("aggregate", 0)
        if agg < prev - epsilon:
            flags.append(f"regression: aggregate {prev} -> {agg}")
    if len(history) >= plateau_k + 1:
        window = [h.get("aggregate", 0) for h in history[-(plateau_k + 1):]]
        if max(window) - min(window) <= epsilon:
            return {"action": "stop",
                    "reason": f"plateau - no gain >{epsilon} over {plateau_k} iters",
                    "aggregate": agg, "flags": flags}
    return {"action": "continue", "reason": "gates still failing", "aggregate": agg, "flags": flags}


# ---------------------------------------------------------------------------
# Measurement (impure - runs the audits)
# ---------------------------------------------------------------------------
def _run_json(script, args):
    try:
        r = subprocess.run([sys.executable, str(SCRIPTS_DIR / script), *args],
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=120)
        out = (r.stdout or "").strip()
        start = out.find("{")
        return json.loads(out[start:]) if start >= 0 else None
    except Exception:
        return None


def measure(code=".", design="DESIGN.md", brief="CREATIVE-BRIEF.md",
            layout=None, archetype=None):
    scores, issues = {}, {}

    b = _run_json("audit_beauty.py", ["--path", code, "--json"] +
                  (["--brief", brief] if Path(brief).exists() else []))
    if b:
        scores["beauty"] = b.get("beauty_score")
        issues["beauty"] = [w.get("fix", w.get("message", "")) for w in b.get("weaknesses", [])]
        issues["beauty"] += [c.get("fix", "") for c in b.get("coherence", [])]

    comp = _run_json("audit_composition.py",
                     (["--layout", layout] if layout else ["--code", code]) + ["--json"])
    if comp:
        scores["composition"] = comp.get("composition_score")
        issues["composition"] = [f"{k}: {m['note']}" for k, m in comp.get("metrics", {}).items()
                                 if m["points"] < m["max"]]

    wargs = ["--code", code, "--design", design, "--json"]
    if Path(brief).exists():
        wargs += ["--brief", brief]
    if archetype:
        wargs += ["--archetype", archetype]
    wow = _run_json("audit_wow.py", wargs)
    if wow:
        scores["wow"] = wow.get("score")
        issues["wow"] = [l.get("note", "") for l in wow.get("levers", []) if l.get("points", 0) < l.get("max", 0)]

    uniq = _run_json("audit_style_uniqueness.py", ["--path", code, "--json"])
    if uniq:
        scores["uniqueness"] = uniq.get("score")

    return scores, issues


# ---------------------------------------------------------------------------
# Log + CLI
# ---------------------------------------------------------------------------
def _code_hash(code):
    h = hashlib.sha256()
    p = Path(code)
    files = sorted(p.rglob("*")) if p.is_dir() else [p]
    for fp in files:
        if fp.is_file() and not any(s in fp.parts for s in ("node_modules", ".git")):
            try:
                h.update(fp.read_bytes())
            except Exception:
                pass
    return h.hexdigest()[:12]


def load_log(path):
    p = Path(path)
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []


def main():
    ap = argparse.ArgumentParser(prog="refine_loop",
                                 description="Iterative design-enhancement loop brain")
    ap.add_argument("--code", default=".")
    ap.add_argument("--design", default="DESIGN.md")
    ap.add_argument("--brief", default="CREATIVE-BRIEF.md")
    ap.add_argument("--layout", default=None)
    ap.add_argument("--archetype", default=None)
    ap.add_argument("--log", default=".refine-log.json")
    ap.add_argument("--max-iter", type=int, default=6)
    ap.add_argument("--json", action="store_true", dest="as_json")
    ap.add_argument("--status", action="store_true", help="read the log and decide, no new measurement")
    args = ap.parse_args()

    history = load_log(args.log)
    if not args.status:
        scores, issues = measure(args.code, args.design, args.brief, args.layout, args.archetype)
        entry = {"iteration": len(history) + 1, "ts": int(time.time()),
                 "code_hash": _code_hash(args.code), "scores": scores,
                 "aggregate": aggregate(scores)}
        history.append(entry)
        Path(args.log).write_text(json.dumps(history, indent=2), encoding="utf-8")
    else:
        issues = {}

    verdict = decide(history, max_iter=args.max_iter)
    latest = history[-1] if history else {"scores": {}, "aggregate": 0}
    next_fixes = prioritize(latest.get("scores", {}), issues)
    report = {"verdict": verdict, "iteration": latest.get("iteration"),
              "aggregate": latest.get("aggregate"), "scores": latest.get("scores", {}),
              "next_fixes": next_fixes}

    if args.as_json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print("=" * 64)
        print(f"REFINE LOOP - iteration {report['iteration']}  aggregate {report['aggregate']}/100")
        for n in GATES:
            v = report["scores"].get(n)
            if v is not None:
                mark = "OK " if gate_passes(n, v) else "XX "
                print(f"  [{mark}] {n:<12} {v}")
        print(f"  -> {verdict['action'].upper()}: {verdict['reason']}")
        for fx in next_fixes:
            print(f"\n  FIX {fx['gate']} (leverage {fx['leverage']}):")
            for f in fx["fixes"]:
                if f:
                    print(f"     - {f}")
        print("=" * 64)

    sys.exit(0 if verdict["action"] == "stop" and "converged" in verdict["reason"] else 1)


if __name__ == "__main__":
    main()
