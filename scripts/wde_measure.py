#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
wde_measure.py - shared measurement primitives for graded, ratio-based scoring.

Philosophy: WOW and beauty are RELATIONAL, not absolute. A 132px headline is not
"wow" because it is large - it is wow because of the JUMP from the 16px body
around it. These helpers turn "is X present" booleans into "how far did it go"
ratios so scoring is continuous, faithful to the design idea, and hard to game
with a single magic number.

Pure functions, no third-party dependencies. Fully unit-testable.
"""
import re
import statistics
from typing import List, Dict, Optional

PX_PER_REM = 16.0

# Tailwind text-* scale -> approx px
TW_TEXT_SCALE = {
    "xs": 12, "sm": 14, "base": 16, "lg": 18, "xl": 20, "2xl": 24, "3xl": 30,
    "4xl": 36, "5xl": 48, "6xl": 60, "7xl": 72, "8xl": 96, "9xl": 128,
}
# Tailwind spacing step = 4px (p-4 => 16px). Used for p-/m-/gap-/py-/px- etc.
TW_SPACE_STEP = 4.0

_NUM = r"([0-9]*\.?[0-9]+)"


def _vals_px_from_token(token: str) -> List[float]:
    """Return all px-equivalent literal lengths found in a single CSS value token.
    Handles raw px, rem, and clamp()/min()/max() (every literal inside counts)."""
    out: List[float] = []
    for m in re.finditer(_NUM + r"\s*px", token, re.I):
        out.append(float(m.group(1)))
    for m in re.finditer(_NUM + r"\s*rem", token, re.I):
        out.append(float(m.group(1)) * PX_PER_REM)
    return out


def extract_font_sizes_px(text: str) -> List[float]:
    """Collect every font-size we can read, in px. Covers CSS font-size,
    Tailwind text-[..px], and Tailwind text-<scale> utilities."""
    sizes: List[float] = []
    if not text:
        return sizes
    for m in re.finditer(r"font-size\s*:\s*([^;}\n]+)", text, re.I):
        sizes.extend(_vals_px_from_token(m.group(1)))
    for m in re.finditer(r"text-\[\s*([^\]]+)\]", text, re.I):
        sizes.extend(_vals_px_from_token(m.group(1)))
    for m in re.finditer(r"\btext-([0-9]?xl|xs|sm|base|lg)\b", text, re.I):
        key = m.group(1).lower()
        if key in TW_TEXT_SCALE:
            sizes.append(float(TW_TEXT_SCALE[key]))
    return sizes


def scale_jump_ratio(text: str) -> float:
    """The headline jump: largest display size / representative body size.
    Body = median of sizes <= 24px, else min size, else assume 16px.
    This is the metric the project's own philosophy calls 'the jump IS the design'."""
    sizes = extract_font_sizes_px(text)
    if not sizes:
        return 0.0
    display = max(sizes)
    body_candidates = [s for s in sizes if s <= 24.0]
    if body_candidates:
        body = statistics.median(body_candidates)
    else:
        body = min(sizes)
    if body <= 0:
        body = PX_PER_REM
    return display / body


def extract_spacing_px(text: str) -> List[float]:
    """Collect margin/padding/gap lengths (px/rem) + Tailwind spacing utilities."""
    out: List[float] = []
    if not text:
        return out
    for m in re.finditer(r"(?:margin|padding|gap|row-gap|column-gap)[^:;{}]*:\s*([^;}\n]+)", text, re.I):
        out.extend(_vals_px_from_token(m.group(1)))
    for m in re.finditer(r"\b(?:p|m|gap|py|px|pt|pb|pl|pr|my|mx|mt|mb|ml|mr)-([0-9]{1,2})\b", text):
        out.append(float(m.group(1)) * TW_SPACE_STEP)
    return [v for v in out if v > 0]


def whitespace_ratio(spacings: List[float]) -> float:
    """Ratio of the largest breathing gap to the median gap. High ratio = one
    region deliberately breathes far more than the rhythm baseline."""
    vals = [v for v in spacings if v > 0]
    if len(vals) < 2:
        return 0.0
    med = statistics.median(vals)
    if med <= 0:
        return 0.0
    return max(vals) / med


def graded(value: float, lo: float, hi: float, max_points: float) -> int:
    """Linear ramp: value<=lo -> 0, value>=hi -> max_points, linear between.
    Returns a rounded int so callers can compare against integer maxima."""
    if hi <= lo:
        return int(round(max_points)) if value >= hi else 0
    frac = (value - lo) / (hi - lo)
    frac = max(0.0, min(1.0, frac))
    return int(round(frac * max_points))


def parse_dials(text: str) -> Dict[str, Optional[int]]:
    """Read the Design Dials (VARIANCE / MOTION / DENSITY, 1-10) from a brief or
    DESIGN.md. Mirrors audit_brief's dial regex so the value is consistent."""
    dials: Dict[str, Optional[int]] = {"variance": None, "motion": None, "density": None}
    if not text:
        return dials
    for name in ("variance", "motion", "density"):
        m = re.search(name + r"\s*[:=]\s*\*{0,2}\s*([0-9]{1,2})", text, re.I)
        if m:
            v = int(m.group(1))
            if 1 <= v <= 10:
                dials[name] = v
    return dials


def color_dominance_hint(text: str) -> bool:
    """Heuristic: is a saturated accent committed to a full-bleed region rather
    than sprinkled on buttons? Relational signal for the 'colour' hero dim."""
    if not text:
        return False
    patterns = [
        r"(?:section|header|main|\.hero)[^{]*\{[^}]*background[^}]*var\(--color",
        r"100vh[^}]*background:\s*var\(--color-accent",
        r"\bbg-(?:accent|primary)\b[^\"']*\bmin-h-screen\b",
        r"background:\s*#[0-9a-f]{3,6}[^;]*;[^}]*min-height:\s*100",
    ]
    return any(re.search(p, text, re.I) for p in patterns)
