#!/usr/bin/env python3
"""
aesthetic_review.py — aesthetic judgment of rendered screenshots.

The Beauty Score (audit_beauty.py) measures craft markers from source code.
But "is this magnificent at a glance?" is a question only an eye can answer.
This script turns the rendered screenshots (from visual_audit.py) into a
scored, structured verdict — the closest thing to a human designer looking
at the page.

It is the Phase 4 counterpart to visual_audit.py: that one catches mechanical
slop in the DOM; this one judges whether the result actually looks designed
by a human.

Two modes:
  agent (DEFAULT) — the model executing this skill IS vision-capable, so it
      judges with its OWN vision. No API key. The script emits the screenshots
      + rubric + verdict schema; the agent looks, writes a verdict JSON, then
      re-runs with --verdict to score it and get the gate exit code.
  api — call an external vision model (OpenAI-compatible or Anthropic) for
      fully-unsupervised pipelines. Reads OPENAI_API_KEY / ANTHROPIC_API_KEY
      from the environment on the machine running the skill.

Usage:
    # after visual_audit.py has produced ./audit-results/*.png
    python3 scripts/aesthetic_review.py --screenshots ./audit-results --archetype "§3 Luxury"
    #   -> prints screenshots + rubric; the agent looks, writes verdict.json, then:
    python3 scripts/aesthetic_review.py --verdict verdict.json
    # unsupervised, external model:
    python3 scripts/aesthetic_review.py --screenshots ./audit-results --mode api --provider anthropic

Exit codes:
  0 — overall_score ≥ pass threshold (looks designed) / agent manifest emitted
  1 — floor ≤ score < pass (acceptable, polish)
  2 — score < floor (BLOCKED — does not look human-designed)
"""

import argparse
import base64
import json
import os
import sys
from pathlib import Path
from typing import Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


# ── ANSI helpers ─────────────────────────────────────────────────────────────

def _ansi(code: str) -> str:
    return f"\033[{code}m" if sys.stdout.isatty() else ""

RESET, BOLD = _ansi("0"), _ansi("1")
RED, YELLOW, GREEN, CYAN, DIM = _ansi("31"), _ansi("33"), _ansi("32"), _ansi("36"), _ansi("2")


# ── The rubric ───────────────────────────────────────────────────────────────
# Seven dimensions a human designer judges in the first seconds. Each maps loosely
# to the code-level Beauty Score (D1-D5) but adds what only the eye catches.

RUBRIC_DIMENSIONS = [
    ("first_impression", "Magnificence at a glance — does it look professionally designed?"),
    ("visual_hierarchy", "Does the eye land where it should? Clear focal point and flow."),
    ("whitespace_balance", "Composition, breathing room, optical alignment, balance."),
    ("typography_craft", "Scale contrast, pairing, rhythm — as rendered."),
    ("colour_harmony", "Palette cohesion and one intentional, owned accent."),
    ("finish_consistency", "Alignment, spacing regularity, no wonky geometry or orphans."),
    ("human_vs_ai", "Does it read as hand-designed, or as generic AI template output?"),
]

_RUBRIC_TEXT = "\n".join(f"  - {k}: {desc}" for k, desc in RUBRIC_DIMENSIONS)


# ── Reviewer provenance ──────────────────────────────────────────────────────
# The deepest validity problem: the model that GENERATED the design is usually
# the same one scoring its screenshots. It unconsciously fills in the visual
# gaps it intended, so a self-review is systematically inflated. We cannot force
# independence from inside one process, but we can (a) make provenance explicit
# and (b) structurally discount a self-review so the cheapest path to a high
# score is to have someone/something else judge.

REVIEWER_SELF = {"self", "agent"}          # the generating model judged itself
REVIEWER_CLONE = {"independent-clone", "clone"}  # SAME model, but a fresh-context judge
REVIEWER_INDEPENDENT = {"independent", "api"}  # a DIFFERENT model judged
REVIEWER_HUMAN = {"human"}                 # a person signed the verdict

# Discount applied to an explicitly self-judged verdict. Tuned to pull a
# self-flattered "shippable" 75-80 below the pass mark unless the work is
# genuinely strong, without nuking an honest mid-score into the floor.
SELF_JUDGE_DISCOUNT = 8

# A context-isolated clone (same model, but a subagent spawned with a BLANK
# context that sees ONLY the screenshots + rubric — never the brief, DESIGN.md,
# or generation reasoning) removes the *intent* inflation that poisons self-review:
# it cannot credit the page for craft it merely intended, because it never saw the
# intent. It does NOT remove the model's own aesthetic blind spots (same weights),
# so a small residual discount remains — far below the self-judge penalty.
# This tier is ONLY legitimate if context hygiene was actually respected.
CLONE_JUDGE_DISCOUNT = 3

# ── Panel of judges (opt-in --panel) ──────────────────────────────────────────
# Instead of one generalist verdict, a context-isolated PANEL: three narrow
# specialists critique their own domain (and can HARD-FAIL it), then an
# art-director CHAIR synthesises their verdicts + the screenshots into the final
# call. This mirrors a real design review: specialists gather evidence, the AD
# decides. A domain hard-fail is BLOCKING regardless of the chair's overall score,
# so a good average can never bury a broken fundamental.
PANEL_ROLES = {
    "typographer": {
        "title": "Typographer",
        "lens": (
            "You judge ONLY type & reading: scale contrast, font pairing, rhythm, "
            "measure (line length), leading, hierarchy legibility, and whether the eye "
            "lands where it should. Ignore brand strategy and colour mood."
        ),
        "hard_fail": (
            "HARD-FAIL if hierarchy is illegible, body measure is unreadable (>~85ch or "
            "cramped), there is no real type-scale contrast (everything one size), or the "
            "pairing fights itself."
        ),
        "dims": ["typography_craft", "visual_hierarchy"],
    },
    "ux_minimalist": {
        "title": "UX Minimalist",
        "lens": (
            "You judge ONLY composition & restraint: whitespace, optical alignment, spacing "
            "regularity, and whether EVERY element earns its place. Decoration without "
            "function is a defect. Ignore type pairing and brand voice."
        ),
        "hard_fail": (
            "HARD-FAIL if there is nonfunctional decoration (unrequested badges, glow, "
            "particles), wonky geometry / broken alignment / orphans, or the layout reads "
            "as cluttered or arbitrarily spaced."
        ),
        "dims": ["whitespace_balance", "finish_consistency"],
    },
    "brand_strategist": {
        "title": "Brand Strategist",
        "lens": (
            "You judge ONLY point of view: first impression, colour intent, and whether the "
            "page has ONE nameable, owned idea that makes it un-generic. Ignore px-level "
            "type and spacing nits."
        ),
        "hard_fail": (
            "HARD-FAIL if it reads as generic AI/template output, has no memorable owned "
            "idea you can name in one sentence, or the colour has no intentional accent."
        ),
        "dims": ["first_impression", "colour_harmony", "human_vs_ai"],
    },
}


def build_prompt(archetype: str | None, breakpoints: list[str]) -> str:
    """Assemble the instruction sent alongside the screenshots."""
    arch = (
        f"The design committed to archetype: {archetype}. Judge it against that intent "
        f"(e.g. a Luxury archetype SHOULD be restrained — do not penalise it for being quiet).\n"
        if archetype else
        "No archetype was declared. Judge it as a general professional web design.\n"
    )
    bp = ", ".join(breakpoints)
    return (
        "You are a senior product designer doing a brutally honest design review.\n"
        "You are shown the SAME page rendered at these breakpoints: " + bp + ".\n\n"
        + arch +
        "\nGoal of the project: the page must look magnificent and indistinguishable from "
        "the work of a skilled human designer — not generic AI output.\n\n"
        "THE ART-DIRECTOR TEST (apply it before scoring):\n"
        "  Would an art director at a top studio (Pentagram, Koto, Instrument) save a "
        "screenshot of this to their inspiration folder? If your honest answer is 'no, but "
        "it's clean and professional', that is NOT a pass — that is the FLOOR. 'Clean' and "
        "'professional' earn ~65, no more. Points above 70 must be EARNED by a specific, "
        "memorable, owned idea you can name in one sentence (a signature type treatment, a "
        "deliberate compositional tension, one fearless colour move). If you cannot name that "
        "one thing, the design is competent wallpaper — cap the overall_score at 65.\n\n"
        "Score each dimension 0-100 (0 = amateur/AI-slop, 100 = award-worthy):\n"
        + _RUBRIC_TEXT +
        "\n\nCalibration anchors — score like a skeptical senior reviewer, not a cheerleader:\n"
        "  90-100  award-worthy, would headline a design gallery — RARE.\n"
        "  80-89   strong, polished, clearly human-crafted, only minor nits.\n"
        "  70-79   good and shippable, but with visible weaknesses.\n"
        "  60-69   acceptable but generic in places; needs real work.\n"
        "  below 60  reads as AI-slop or amateur.\n"
        "Most competent first attempts land 72-85. Reserve 90+ for genuinely exceptional work and justify why.\n"
        "Uniform near-perfect scores (everything > 95) are treated as un-calibrated and automatically penalised.\n\n"
        "Then give an overall_score (0-100) as your honest holistic judgment (NOT a mean), "
        "a one-line verdict, whether it reads_as \"human\" or \"ai\", and the concrete, high-leverage "
        "fixes ranked by impact. You MUST list AT LEAST 2 specific fixes — even excellent designs have them; "
        "reference exactly what you see.\n\n"
        "Respond with ONLY a JSON object, no prose, in exactly this shape:\n"
        "{\n"
        '  "overall_score": <int>,\n'
        '  "verdict": "<one line>",\n'
        '  "reads_as": "human" | "ai",\n'
        '  "memorable_idea": "<the one nameable owned idea, or null if none>",\n'
        '  "dimensions": { "first_impression": {"score": <int>, "note": "<str>"}, ... all 7 ... },\n'
        '  "top_fixes": ["<fix>", ...]\n'
        "}"
    )


# ── Image handling ───────────────────────────────────────────────────────────

def collect_screenshots(screenshots_dir: Path) -> list[tuple[str, Path]]:
    """Return [(breakpoint_name, path)] for PNGs in the directory, stable order."""
    if not screenshots_dir.is_dir():
        raise FileNotFoundError(f"screenshots dir not found: {screenshots_dir}")
    pngs = sorted(screenshots_dir.glob("*.png"))
    if not pngs:
        raise FileNotFoundError(f"no .png screenshots in {screenshots_dir}")
    return [(p.stem, p) for p in pngs]


def encode_image(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("ascii")


# ── Request assembly (provider-specific, no network here — testable) ──────────

def build_openai_payload(model: str, prompt: str, shots: list[tuple[str, Path]]) -> dict[str, Any]:
    content: list[dict[str, Any]] = [{"type": "text", "text": prompt}]
    for name, path in shots:
        content.append({"type": "text", "text": f"[breakpoint: {name}]"})
        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/png;base64,{encode_image(path)}"},
        })
    return {
        "model": model,
        "messages": [{"role": "user", "content": content}],
        "max_tokens": 1500,
        "temperature": 0.2,
    }


def build_anthropic_payload(model: str, prompt: str, shots: list[tuple[str, Path]]) -> dict[str, Any]:
    content: list[dict[str, Any]] = [{"type": "text", "text": prompt}]
    for name, path in shots:
        content.append({"type": "text", "text": f"[breakpoint: {name}]"})
        content.append({
            "type": "image",
            "source": {"type": "base64", "media_type": "image/png", "data": encode_image(path)},
        })
    return {
        "model": model,
        "max_tokens": 1500,
        "temperature": 0.2,
        "messages": [{"role": "user", "content": content}],
    }


# ── Response parsing ─────────────────────────────────────────────────────────

def extract_text_openai(resp: dict[str, Any]) -> str:
    return resp["choices"][0]["message"]["content"]


def extract_text_anthropic(resp: dict[str, Any]) -> str:
    parts = resp.get("content", [])
    return "".join(p.get("text", "") for p in parts if p.get("type") == "text")


def parse_verdict(text: str) -> dict[str, Any]:
    """Pull the JSON object out of a model reply, tolerating code fences / prose."""
    t = text.strip()
    if t.startswith("```"):
        t = t.split("```", 2)[1]
        if t.lstrip().lower().startswith("json"):
            t = t.lstrip()[4:]
    start, end = t.find("{"), t.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("no JSON object found in model response")
    data = json.loads(t[start:end + 1])
    if "overall_score" not in data:
        raise ValueError("model response missing 'overall_score'")
    data["overall_score"] = int(data["overall_score"])
    return data


# ── Network call (only place that touches the API) ────────────────────────────

def call_model(provider: str, base_url: str, model: str, payload: dict[str, Any]) -> dict[str, Any]:
    import urllib.request
    import urllib.error

    if provider == "anthropic":
        url = base_url.rstrip("/") + "/v1/messages"
        key = os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            raise RuntimeError("ANTHROPIC_API_KEY not set in environment")
        headers = {
            "x-api-key": key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
    else:  # openai-compatible
        url = base_url.rstrip("/") + "/v1/chat/completions"
        key = os.environ.get("OPENAI_API_KEY")
        if not key:
            raise RuntimeError("OPENAI_API_KEY not set in environment")
        headers = {"Authorization": f"Bearer {key}", "content-type": "application/json"}

    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"API error {e.code}: {e.read().decode('utf-8', 'replace')[:500]}")


# ── Reporting ────────────────────────────────────────────────────────────────

def score_colour(score: int, floor: int, passing: int) -> str:
    if score >= passing:
        return GREEN
    if score >= floor:
        return YELLOW
    return RED


def print_report(verdict: dict[str, Any], floor: int, passing: int, effective: int | None = None, flags: list | None = None, blocked_reason: str | None = None) -> None:
    raw = verdict["overall_score"]
    s = effective if effective is not None else raw
    colour = score_colour(s, floor, passing)
    reads = verdict.get("reads_as", "?")
    sep = "=" * 52
    print(f"\n{BOLD}{sep}{RESET}")
    print("  AESTHETIC REVIEW — vision judgment")
    print(f"{BOLD}{sep}{RESET}\n")
    print(f"  Overall: {colour}{BOLD}{s}/100{RESET}   reads as: "
          f"{(GREEN if reads=='human' else RED)}{reads.upper()}{RESET}")
    kind = reviewer_kind(verdict)
    _rev_colour = {"independent": GREEN, "human": GREEN, "clone": CYAN,
                   "self": YELLOW, "unknown": YELLOW}.get(kind, YELLOW)
    _rev_label = {"independent": "INDEPENDENT (different model)", "human": "HUMAN",
                  "clone": "INDEPENDENT-CLONE (fresh-context, same model)",
                  "self": "SELF (generating model judged itself)",
                  "unknown": "UNDECLARED"}.get(kind, "UNDECLARED")
    print(f"  reviewer: {_rev_colour}{_rev_label}{RESET}")
    print(f"  {DIM}{verdict.get('verdict','')}{RESET}\n")
    if effective is not None and effective != raw:
        print(f"  {DIM}(raw self-score {raw} -> calibrated {s}){RESET}")
    for _fl in (flags or []):
        print(f"  {YELLOW}⚠ {_fl}{RESET}")
    if flags:
        print()

    dims = verdict.get("dimensions", {})
    for key, desc in RUBRIC_DIMENSIONS:
        d = dims.get(key, {})
        sc = d.get("score", "?")
        mark = score_colour(sc, floor, passing) if isinstance(sc, int) else DIM
        print(f"  {BOLD}{key:<20}{RESET} {mark}{str(sc):>3}{RESET}  {DIM}{d.get('note','')[:70]}{RESET}")
    print()

    fixes = verdict.get("top_fixes", [])
    if fixes:
        print(f"  {YELLOW}Top fixes (ranked by impact):{RESET}")
        for i, f in enumerate(fixes, 1):
            print(f"   {i}. {f}")
        print()

    print(f"{BOLD}{sep}{RESET}")
    if blocked_reason:
        print(f"  {RED}{BOLD}❌ BLOCKED{RESET} — {blocked_reason} "
              f"(chair would otherwise be {s}/100).")
    elif s < floor:
        print(f"  {RED}{BOLD}❌ BLOCKED{RESET} — {s}/100 below floor {floor}. "
              f"Does not yet read as human-designed.")
    elif s < passing:
        print(f"  {YELLOW}{BOLD}⚠️  POLISH{RESET} — {s}/100 below pass {passing}. "
              f"Apply the fixes above.")
    else:
        print(f"  {GREEN}{BOLD}✅ PASSED{RESET} — {s}/100. Reads as deliberate, human design.")
    print(f"{BOLD}{sep}{RESET}\n")


def exit_code_for(score: int, floor: int, passing: int) -> int:
    if score < floor:
        return 2
    if score < passing:
        return 1
    return 0


def reviewer_kind(verdict: dict[str, Any]) -> str:
    """Classify who produced the verdict: 'self' | 'independent' | 'human' | 'unknown'.

    'unknown' = no reviewer field (legacy verdicts) — treated as self for warning
    purposes but NOT discounted, to stay backward compatible.
    """
    raw = str(verdict.get("reviewer", "")).strip().lower()
    if not raw:
        return "unknown"
    if raw in REVIEWER_HUMAN:
        return "human"
    if raw in REVIEWER_CLONE:
        return "clone"
    if raw in REVIEWER_INDEPENDENT:
        return "independent"
    if raw in REVIEWER_SELF:
        return "self"
    return "unknown"


def calibrate_verdict(verdict: dict[str, Any], floor: int, passing: int) -> tuple[int, list]:
    """Anti-inflation calibration for a vision verdict.

    Two independent axes of inflation are corrected:

    1. SCORE inflation — a self-flattered near-perfect verdict is discounted and
       a verdict without concrete critiques is treated as un-calibrated.
    2. PROVENANCE inflation (#5B) — when the SAME model that generated the design
       also judged it ('reviewer': 'self'/'agent'), the score is structurally
       discounted, because self-review fills in intended-but-absent craft. An
       'independent' (different model) or 'human' verdict is trusted as-is.

    Returns (effective_score, flags).
    """
    raw = int(verdict.get("overall_score", 0))
    dims = verdict.get("dimensions", {}) or {}
    dim_scores = [d.get("score") for d in dims.values()
                  if isinstance(d, dict) and isinstance(d.get("score"), int)]
    fixes = [f for f in (verdict.get("top_fixes") or [])
             if isinstance(f, str) and len(f.strip()) >= 8]
    flags: list = []
    effective = raw

    uniform_perfect = raw >= 95 or (len(dim_scores) >= 5 and min(dim_scores) >= 95)
    if uniform_perfect:
        penalty = 18 if len(fixes) < 3 else 10
        effective = max(0, raw - penalty)
        flags.append(
            f"INFLATION GUARD - near-perfect scores (overall {raw}, {len(fixes)} concrete "
            f"fix(es)) match the self-flattery pattern. Applied -{penalty} calibration "
            f"penalty -> effective {effective}/100."
        )

    kind = reviewer_kind(verdict)
    if kind == "self":
        before = effective
        effective = max(0, effective - SELF_JUDGE_DISCOUNT)
        flags.append(
            f"SELF-JUDGED - the generating model also scored its own work "
            f"(reviewer=self). Self-review is structurally inflated; applied "
            f"-{SELF_JUDGE_DISCOUNT} provenance discount -> {effective}/100. For a "
            f"trustworthy verdict, have a DIFFERENT model judge "
            f"(--mode api --provider <other>), a fresh-context clone (--reviewer "
            f"independent-clone), or a human sign off (--reviewer human)."
        )
        _ = before
    elif kind == "clone":
        effective = max(0, effective - CLONE_JUDGE_DISCOUNT)
        flags.append(
            f"CLONE-JUDGED - a fresh-context judge (same model, blank context: saw only "
            f"the screenshots, never the intent) scored this. Intent inflation is removed, "
            f"so only a small -{CLONE_JUDGE_DISCOUNT} residual discount applies for shared "
            f"model taste -> {effective}/100. NOTE: this tier is only valid if context "
            f"hygiene was respected (no brief/DESIGN.md leaked to the judge)."
        )
    elif kind == "unknown":
        flags.append(
            "PROVENANCE UNKNOWN - verdict has no 'reviewer' field. Declare who "
            "judged: 'self' (generating model), 'independent' (different model), "
            "or 'human'. Independent review is strongly recommended."
        )

    if len(fixes) < 2:
        flags.append(
            "UNCALIBRATED - fewer than 2 concrete critiques. No shippable design is flawless: "
            "re-review honestly and list at least 2 specific, high-leverage fixes."
        )

    return effective, flags


# ── CLI ──────────────────────────────────────────────────────────────────────

def build_juror_prompt(role_key: str, archetype: str | None, breakpoints: list[str]) -> str:
    """A narrow specialist prompt. The juror judges ONLY its domain and may hard-fail it."""
    role = PANEL_ROLES[role_key]
    arch = (f"The design committed to archetype: {archetype}. Judge against that intent.\n"
            if archetype else "No archetype declared. Judge as general professional web design.\n")
    bp = ", ".join(breakpoints)
    return (
        f"You are a {role['title']} on a blind design review panel. You have NEVER seen this "
        f"project before and you do not know what it was meant to be — judge ONLY the rendered "
        f"screenshots shown at these breakpoints: {bp}.\n\n"
        + arch +
        "\nYOUR LENS (judge nothing outside it): " + role["lens"] + "\n\n"
        + role["hard_fail"] + "\n\n"
        "Score your domain 0-100 like a skeptical senior reviewer (90+ is rare and must be earned "
        "by a specific, nameable move; 'clean and professional' caps at ~65). List at least 2 "
        "concrete, high-leverage fixes in your domain — reference exactly what you see.\n\n"
        "Respond with ONLY this JSON, no prose:\n"
        "{\n"
        f'  "role": "{role_key}",\n'
        '  "domain_score": <int 0-100>,\n'
        '  "hard_fail": <true|false>,\n'
        '  "hard_fail_reason": "<one line, or null>",\n'
        '  "notes": "<one line on the strongest and weakest thing in your domain>",\n'
        '  "fixes": ["<fix>", "<fix>", ...]\n'
        "}"
    )


def build_chair_prompt(archetype: str | None, breakpoints: list[str], jurors_present: bool = True) -> str:
    """The art-director chair: synthesises the juror verdicts + screenshots into the final call.

    The chair does NOT re-do the specialists' work — it arbitrates and renders the holistic
    overall_score and go/no-go. It still sees ONLY the screenshots (and the juror JSON), never
    the brief or generation reasoning, so it stays a context-isolated (clone) reviewer.
    """
    base = build_prompt(archetype, breakpoints)
    chair_note = (
        "\n\n--- YOU ARE THE CHAIR (Art Director) ---\n"
        "You are also given three specialist juror verdicts (typographer, UX minimalist, brand "
        "strategist) as JSON. Weigh them, but the holistic overall_score is YOURS — it is NOT a "
        "mean of their domain scores. Your job is judgment and arbitration. If a juror raised a "
        "hard_fail, treat that fundamental as decisive in your verdict even if everything else is "
        "strong. Keep your verdict in the SAME 7-dimension schema already specified above, and set "
        '"reviewer": "independent-clone".\n'
        if jurors_present else ""
    )
    return base + chair_note


def build_panel_manifest(archetype: str | None, shots: list, floor: int, passing: int) -> dict[str, Any]:
    """Emit everything the orchestrating agent needs to spawn a context-isolated panel.

    The script cannot spawn subagents itself; it hands the agent the exact prompts, the
    screenshots to transfer, the file each judge must write, and the strict context-hygiene
    rule. The agent runs the jurors in parallel, then the chair, then aggregates with
    `--panel --verdicts <dir>`.
    """
    breakpoints = [name for name, _ in shots]
    screenshot_paths = [str(p.resolve()) for _, p in shots]
    jurors = []
    for key in PANEL_ROLES:
        jurors.append({
            "role": key,
            "title": PANEL_ROLES[key]["title"],
            "spawn_as": "context-isolated subagent (blank context)",
            "transfer_only": screenshot_paths,
            "prompt": build_juror_prompt(key, archetype, breakpoints),
            "write_verdict_to": f"juror-{key}.json",
        })
    return {
        "status": "awaiting_panel_vision",
        "context_hygiene_rule": (
            "EACH judge must be a subagent with a BLANK context that receives ONLY the "
            "screenshots + its prompt. Do NOT pass the brief, DESIGN.md, the creative reasoning, "
            "or this conversation — leaking intent re-introduces the self-review bias and the "
            "'independent-clone' tag becomes a lie."
        ),
        "orchestration": [
            "1. Spawn the 3 jurors in parallel (e.g. invoke_agent), each transferring ONLY the "
            "screenshots, each writing its JSON to the named file in the verdicts dir.",
            "2. Then spawn the CHAIR subagent: transfer the screenshots + the 3 juror JSON files, "
            "give it the chair prompt, write chair.json.",
            "3. Aggregate + score: python3 scripts/aesthetic_review.py --panel --verdicts <dir> "
            f"--threshold {floor} {passing}",
        ],
        "screenshots": screenshot_paths,
        "jurors": jurors,
        "chair": {
            "spawn_as": "context-isolated subagent (blank context)",
            "transfer_only": screenshot_paths + ["the 3 juror-*.json files"],
            "prompt": build_chair_prompt(archetype, breakpoints, jurors_present=True),
            "write_verdict_to": "chair.json",
            "reviewer_field": "independent-clone",
        },
        "thresholds": {"floor": floor, "pass": passing},
    }


def aggregate_panel(verdicts_dir: Path, floor: int, passing: int,
                    reviewer_override: str | None = None) -> dict[str, Any]:
    """Combine juror verdicts + the chair verdict into one final result with domain veto.

    File convention (written by the agent after spawning the judges):
      <dir>/juror-typographer.json, juror-ux_minimalist.json, juror-brand_strategist.json
      <dir>/chair.json   (full 7-dimension verdict)
    """
    vdir = Path(verdicts_dir)
    chair_path = vdir / "chair.json"
    if not chair_path.exists():
        raise FileNotFoundError(f"chair verdict missing: {chair_path}")
    chair = parse_verdict(chair_path.read_text(encoding="utf-8"))
    chair["reviewer"] = reviewer_override or chair.get("reviewer") or "independent-clone"

    jurors: list[dict[str, Any]] = []
    vetoes: list[str] = []
    for key in PANEL_ROLES:
        jp = vdir / f"juror-{key}.json"
        if not jp.exists():
            continue
        try:
            jv = json.loads(jp.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        jurors.append(jv)
        if jv.get("hard_fail"):
            reason = jv.get("hard_fail_reason") or "unspecified"
            vetoes.append(f"{PANEL_ROLES[key]['title']} VETO: {reason}")

    merged_fixes = list(chair.get("top_fixes") or [])
    seen = {f.strip().lower() for f in merged_fixes if isinstance(f, str)}
    for jv in jurors:
        for f in (jv.get("fixes") or []):
            if isinstance(f, str) and f.strip().lower() not in seen:
                merged_fixes.append(f)
                seen.add(f.strip().lower())
    chair["top_fixes"] = merged_fixes

    effective, flags = calibrate_verdict(chair, floor, passing)
    uncalibrated = any(f.startswith("UNCALIBRATED") for f in flags)

    if vetoes:
        code = 2
        flags.append(
            "DOMAIN VETO - a specialist hard-failed their domain; this is BLOCKING even though "
            "the chair's overall would otherwise pass. Fix the vetoed fundamental(s) first."
        )
    else:
        code = 2 if uncalibrated else exit_code_for(effective, floor, passing)

    return {
        "final": chair,
        "effective_score": effective,
        "flags": flags,
        "vetoes": vetoes,
        "juror_scores": {jv.get("role", f"juror{i}"): jv.get("domain_score")
                         for i, jv in enumerate(jurors)},
        "exit_code": code,
    }


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="aesthetic_review",
        description="Aesthetic judgment of rendered screenshots — by the agent's own vision (default) or an external vision API.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--screenshots", type=Path, default=Path("./audit-results"),
                   help="Directory of PNG screenshots (from visual_audit.py)")
    p.add_argument("--archetype", type=str, default=None,
                   help="Declared archetype, so the review judges against intent")
    p.add_argument("--mode", choices=["agent", "api"], default="agent",
                   help="agent (default): the model executing the skill judges with its own vision, no API key. "
                        "api: call an external vision model.")
    p.add_argument("--verdict", type=Path, default=None,
                   help="Path to a verdict JSON the agent produced; scores it and returns the gate exit code.")
    p.add_argument("--panel", action="store_true",
                   help="Panel mode: emit prompts for 3 context-isolated specialist jurors + an "
                        "art-director chair (with --screenshots), or aggregate them with domain "
                        "veto (with --verdicts).")
    p.add_argument("--verdicts", type=Path, default=None,
                   help="(panel mode) Directory holding juror-*.json + chair.json to aggregate.")
    p.add_argument("--reviewer", choices=["self", "agent", "independent-clone", "clone",
                                          "independent", "human"], default=None,
                   help="Override/declare who judged: self (generating model — discounted -8), "
                        "independent-clone (fresh-context subagent, same model — discounted -3), "
                        "independent (different model — no discount), or human. Overrides the "
                        "verdict's own 'reviewer' field in --verdict / --panel aggregation.")
    p.add_argument("--threshold", nargs=2, type=int, metavar=("FLOOR", "PASS"), default=[60, 75])
    p.add_argument("--json", action="store_true", dest="json_output")
    # --- api mode only ---
    p.add_argument("--provider", choices=["openai", "anthropic"], default="openai",
                   help="(api mode) vision provider")
    p.add_argument("--model", type=str, default=None,
                   help="(api mode) vision model (default: gpt-4o / claude-3-5-sonnet-latest)")
    p.add_argument("--base-url", type=str, default="https://api.openai.com",
                   help="(api mode) API base URL (any OpenAI-compatible endpoint)")
    p.add_argument("--dry-run", action="store_true",
                   help="(api mode) assemble the request and print a summary; do NOT call the API")
    return p


def default_model(provider: str) -> str:
    return "claude-3-5-sonnet-latest" if provider == "anthropic" else "gpt-4o"


def main() -> int:
    args = build_parser().parse_args()
    floor, passing = args.threshold
    if not (0 <= floor < passing <= 100):
        print("Error: thresholds must satisfy 0 ≤ FLOOR < PASS ≤ 100.", file=sys.stderr)
        return 2

    # ── Panel mode ────────────────────────────────────────────────────────────
    if args.panel:
        # Aggregate an already-judged panel (juror-*.json + chair.json).
        if args.verdicts is not None:
            try:
                result = aggregate_panel(args.verdicts, floor, passing, reviewer_override=args.reviewer)
            except (OSError, ValueError, FileNotFoundError) as e:
                print(f"Error aggregating panel: {e}", file=sys.stderr)
                return 2
            if args.json_output:
                out = dict(result["final"])
                out["raw_score"] = out.get("overall_score")
                out["effective_score"] = result["effective_score"]
                out["juror_scores"] = result["juror_scores"]
                out["vetoes"] = result["vetoes"]
                out["calibration_flags"] = result["flags"]
                out["exit_code"] = result["exit_code"]
                print(json.dumps(out, indent=2, ensure_ascii=False))
            else:
                print("\nPANEL — juror domain scores:")
                for role, sc in result["juror_scores"].items():
                    print(f"  · {role}: {sc}")
                if result["vetoes"]:
                    print("\n  DOMAIN VETO(ES) — BLOCKING:")
                    for v in result["vetoes"]:
                        print(f"    ✗ {v}")
                _blocked = ("domain veto — " + "; ".join(result["vetoes"])) if result["vetoes"] else None
                print_report(result["final"], floor, passing,
                             effective=result["effective_score"], flags=result["flags"],
                             blocked_reason=_blocked)
            return result["exit_code"]

        # Emit the panel manifest (prompts for the agent to spawn the judges).
        try:
            shots = collect_screenshots(args.screenshots)
        except FileNotFoundError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 2
        print(json.dumps(build_panel_manifest(args.archetype, shots, floor, passing),
                         indent=2, ensure_ascii=False))
        return 0

    # Loop-closer: score a verdict the agent already produced with its own vision.
    if args.verdict is not None:
        try:
            verdict = parse_verdict(args.verdict.read_text(encoding="utf-8"))
        except (OSError, ValueError) as e:
            print(f"Error reading verdict: {e}", file=sys.stderr)
            return 2
        if args.reviewer:
            verdict["reviewer"] = args.reviewer
        effective, flags = calibrate_verdict(verdict, floor, passing)
        uncalibrated = any(f.startswith("UNCALIBRATED") for f in flags)
        code = 2 if uncalibrated else exit_code_for(effective, floor, passing)
        if args.json_output:
            verdict["raw_score"] = verdict["overall_score"]
            verdict["effective_score"] = effective
            verdict["calibration_flags"] = flags
            verdict["exit_code"] = code
            print(json.dumps(verdict, indent=2, ensure_ascii=False))
        else:
            print_report(verdict, floor, passing, effective=effective, flags=flags)
        return code

    try:
        shots = collect_screenshots(args.screenshots)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2
    breakpoints = [name for name, _ in shots]
    prompt = build_prompt(args.archetype, breakpoints)

    # Default: the model executing the skill judges with its OWN native vision — no API key.
    if args.mode == "agent":
        declared_reviewer = args.reviewer or "self"
        manifest = {
            "status": "awaiting_agent_vision",
            "instructions": (
                "You (the model executing this skill) are vision-capable. Open each screenshot "
                "listed below with your own vision, apply the rubric, and write the verdict JSON "
                "to a file. Then run: python3 scripts/aesthetic_review.py --verdict <file.json> "
                f"--threshold {floor} {passing}  to score it and get the gate exit code.\n"
                "NOTE: if you generated this design, your verdict is 'self' and will be "
                "discounted — self-review is structurally inflated. For a trustworthy score, "
                "have a DIFFERENT model judge (--mode api --provider <other>) or a human sign "
                "off (--reviewer human)."
            ),
            "screenshots": [str(p.resolve()) for _, p in shots],
            "rubric": prompt,
            "verdict_schema": {
                "overall_score": "int 0-100",
                "verdict": "one line",
                "reads_as": "human | ai",
                "reviewer": "self | independent | human  (be honest: 'self' if you made this design)",
                "memorable_idea": "the one nameable owned idea, or null",
                "dimensions": {k: {"score": "int", "note": "str"} for k, _ in RUBRIC_DIMENSIONS},
                "top_fixes": ["str", "..."],
            },
            "declared_reviewer": declared_reviewer,
            "thresholds": {"floor": floor, "pass": passing},
        }
        print(json.dumps(manifest, indent=2, ensure_ascii=False))
        return 0

    # api mode: call an external vision model (for unsupervised pipelines).
    model = args.model or default_model(args.provider)
    payload = (build_anthropic_payload if args.provider == "anthropic" else build_openai_payload)(model, prompt, shots)
    if args.dry_run:
        print(json.dumps({
            "provider": args.provider, "model": model, "base_url": args.base_url,
            "breakpoints": breakpoints, "n_images": len(shots),
            "prompt_chars": len(prompt), "thresholds": {"floor": floor, "pass": passing},
        }, indent=2))
        return 0
    try:
        raw = call_model(args.provider, args.base_url, model, payload)
        text = extract_text_anthropic(raw) if args.provider == "anthropic" else extract_text_openai(raw)
        verdict = parse_verdict(text)
    except Exception as e:  # noqa: BLE001
        print(f"Error: {e}", file=sys.stderr)
        return 2
    # An external provider genuinely judged — provenance is independent unless overridden.
    verdict["reviewer"] = args.reviewer or "independent"
    effective, flags = calibrate_verdict(verdict, floor, passing)
    uncalibrated = any(f.startswith("UNCALIBRATED") for f in flags)
    code = 2 if uncalibrated else exit_code_for(effective, floor, passing)
    if args.json_output:
        verdict["raw_score"] = verdict["overall_score"]
        verdict["effective_score"] = effective
        verdict["calibration_flags"] = flags
        verdict["exit_code"] = code
        print(json.dumps(verdict, indent=2, ensure_ascii=False))
    else:
        print_report(verdict, floor, passing, effective=effective, flags=flags)
    return code


if __name__ == "__main__":
    sys.exit(main())
