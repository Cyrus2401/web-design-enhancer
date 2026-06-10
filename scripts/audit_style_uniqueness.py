#!/usr/bin/env python3
"""
audit_style_uniqueness.py
─────────────────────────
Detects when an AI-generated project is a clone of the 'Generic AI Template'.
Scores 12 template signals and reports a Template Score (0-100).

Exit codes:
  0 — score ≤ threshold_warn  (unique / acceptable)
  1 — score between warn and block  (high template risk)
  2 — score > threshold_block (delivery blocked — too generic)
"""

import argparse
import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

# Windows terminals may default to cp1252 — force UTF-8 for emoji output
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from typing import Any

# ──────────────────────────────────────────────────────────────────────────────
# ANSI colour helpers
# ──────────────────────────────────────────────────────────────────────────────

def _ansi(code: str) -> str:
    """Return ANSI escape if stdout is a TTY, else empty string."""
    return f"\033[{code}m" if sys.stdout.isatty() else ""

RESET  = _ansi("0")
BOLD   = _ansi("1")
RED    = _ansi("31")
YELLOW = _ansi("33")
GREEN  = _ansi("32")
CYAN   = _ansi("36")
DIM    = _ansi("2")


# ──────────────────────────────────────────────────────────────────────────────
# Core auditor
# ──────────────────────────────────────────────────────────────────────────────

class StyleUniquenessAuditor:
    """
    Scans a directory for files that match 'Generic AI Template' signatures.
    Each signal is scored and the sum produces a Template Score (0-100).
    """

    TEMPLATE_SIGNALS: list[dict[str, Any]] = [
        {
            "id": "T1",
            "name": "Blue→purple hero gradient",
            "weight": 15,
            "file_types": [".css", ".html", ".jsx", ".tsx", ".scss", ".sass"],
            # Matches linear-gradient with blue-500+purple-500 OR Tailwind from-blue-*/to-purple-* classes.
            "pattern": (
                r"(?:"
                r"linear-gradient\s*\([^)]*(?:#3[Bb]82[Ff]6|blue-500|from-blue)[^)]*(?:#8[Bb]5[Cc][Ff]6|purple-500|violet|to-purple|to-violet)[^)]*\)"
                r"|from-blue-\d+[^>\n]*to-(?:purple|violet|indigo)-\d+"
                r")"
            ),
            "suggestion": (
                "Replace with a project-specific palette from DESIGN.md §2.\n"
                "       → Try: Swiss (§1) or Technical (§6) or Luxury (§3)"
            ),
        },
        {
            "id": "T2",
            "name": "Default AI font combo (Inter + Poppins)",
            "weight": 10,
            "file_types": [".css", ".html", ".jsx", ".tsx", ".scss", ".sass"],
            # Detected at project level: BOTH fonts present anywhere in the tree.
            "pattern": r"font-family\s*:[^;\"']*['\"]?(?:Inter|Poppins)['\"]?",
            "suggestion": (
                "Choose a single purposeful typeface that fits the brand.\n"
                "       → Reference design-archetypes.md §typography per archetype"
            ),
        },
        {
            "id": "T3",
            "name": "Testimonial / review card class",
            "weight": 8,
            "file_types": [".css", ".html", ".jsx", ".tsx", ".scss", ".sass"],
            # Matches class="testimonial-card" in HTML/JSX OR .testimonial-card selector in CSS.
            "pattern": (
                r"(?:"
                r"(?:class|className)\s*=\s*[\"'][^\"']*(?:testimonial|review)-card[^\"']*[\"']"
                r"|\.(?:testimonial|review)-card\b"
                r")"
            ),
            "suggestion": (
                "Remove testimonial section unless explicitly requested in brief.\n"
                "       → Section bloat is Generic AI Template §structure signal (see T5)"
            ),
        },
        {
            "id": "T4",
            "name": "Glassmorphism overuse (backdrop-filter blur on 3+ elements)",
            "weight": 10,
            "file_types": [".css", ".html", ".jsx", ".tsx", ".scss", ".sass"],
            # Each match is one element; the auditor counts occurrences per project.
            "pattern": r"backdrop-filter\s*:\s*blur\s*\(",
            "suggestion": (
                "Limit backdrop-filter to ≤1 intentional accent element.\n"
                "       → Prefer flat surfaces (Swiss §1) or sharp edges (Technical §6)"
            ),
        },
        {
            "id": "T5",
            "name": "Hero+Features+Testimonials+CTA all present",
            "weight": 12,
            "file_types": [".html", ".jsx", ".tsx"],
            # Each section matched separately; auditor checks co-occurrence.
            "pattern": (
                r"(?:id|class|section)\s*=?\s*[\"']?\s*"
                r"(?:hero|features|testimonials?|cta|call.to.action)"
                r"\s*[\"']?"
            ),
            "suggestion": (
                "Remove at least 2 unrequested sections.\n"
                "       → Keep only what the brief specifies (§0b D1)"
            ),
        },
        {
            "id": "T6",
            "name": "Hero badge / pill with decorative text",
            "weight": 6,
            "file_types": [".html", ".jsx", ".tsx"],
            "pattern": (
                r"(?:badge|pill|chip)[^>\"']*[\"'][^\"']*"
                r"(?:New|Beta|🚀|✨|🎉|Launch|Alpha|v\d|Now\s+Available)"
            ),
            "suggestion": (
                "Remove decorative launch badges unless specified in brief.\n"
                "       → Earned social proof > decorative claims (§0b D2)"
            ),
        },
        {
            "id": "T7",
            "name": "Sole grid: repeat(3, 1fr)",
            "weight": 7,
            "file_types": [".css", ".html", ".jsx", ".tsx", ".scss", ".sass"],
            # Matches CSS property OR Tailwind grid-cols-3 utility class.
            "pattern": (
                r"(?:"
                r"grid-template-columns\s*:\s*repeat\s*\(\s*3\s*,\s*1fr\s*\)"
                r"|\bgrid-cols-3\b"
                r")"
            ),
            "suggestion": (
                "Break the 3-column tyranny — use asymmetric or editorial layouts.\n"
                "       → Reference design-archetypes.md §grid per archetype"
            ),
        },
        {
            "id": "T8",
            "name": "Dramatic card shadow (0 25px / 0 20px)",
            "weight": 6,
            "file_types": [".css", ".html", ".jsx", ".tsx", ".scss", ".sass"],
            "pattern": r"box-shadow\s*:[^;]*0\s+(?:25|20|50|40)px",
            "suggestion": (
                "Replace theatrical shadows with intentional depth hierarchy.\n"
                "       → Flat: Swiss §1 — Layered: Playful §4"
            ),
        },
        {
            "id": "T9",
            "name": "Unsolicited float/pulse keyframes",
            "weight": 8,
            "file_types": [".css", ".html", ".jsx", ".tsx", ".scss", ".sass"],
            "pattern": r"@keyframes\s+(?:float|pulse|bounce|wiggle|spin-slow)",
            "suggestion": (
                "Remove decorative animations not tied to UX purpose.\n"
                "       → Motion must serve meaning (see design-archetypes.md §motion)"
            ),
        },
        {
            "id": "T10",
            "name": "Lucide icon dump (5+ icons imported)",
            "weight": 6,
            "file_types": [".jsx", ".tsx", ".js", ".ts"],
            # Each named import from lucide-react counts; auditor checks total.
            "pattern": r"from\s+['\"]lucide-react['\"]",
            "suggestion": (
                "Limit to ≤3 purposeful icons; avoid icon decoration.\n"
                "       → Iconless layouts often read as more confident (Swiss §1)"
            ),
        },
        {
            "id": "T11",
            "name": "Generic section IDs (hero + features + pricing)",
            "weight": 8,
            "file_types": [".html", ".jsx", ".tsx"],
            "pattern": r'id\s*=\s*["\'](?:hero|features|pricing|testimonials)["\']',
            "suggestion": (
                "Use semantic, project-specific IDs rather than template defaults.\n"
                "       → Generic IDs signal copy-paste template structure"
            ),
        },
        {
            "id": "T12",
            "name": "Hardcoded Tailwind blue-500 (#3B82F6) as primary",
            "weight": 5,
            "file_types": [".css", ".html", ".jsx", ".tsx", ".scss", ".sass"],
            "pattern": r"#3[Bb]82[Ff]6",
            "suggestion": (
                "Define a custom primary colour in DESIGN.md §2 token system.\n"
                "       → #3B82F6 is the most common AI-generated primary colour"
            ),
        },
    ]

    ARCHETYPE_RECOMMENDATIONS = {
        range(0, 21): "No specific archetype required — design is sufficiently unique.",
        range(21, 41): "Review flagged items; no archetype change required yet.",
        range(41, 66): "Technical/Monochrome (§6) or Swiss/Minimalist (§1)",
        range(66, 101): "Immediate redesign — pick any archetype except the default gradient template.",
    }

    def __init__(
        self,
        root_path: Path,
        threshold_warn: int = 40,
        threshold_block: int = 65,
    ) -> None:
        self.root_path = root_path
        self.threshold_warn = threshold_warn
        self.threshold_block = threshold_block

        # Collected data
        self.violations: list[dict[str, Any]] = []
        self.raw_score: int = 0
        self.capped_score: int = 0

        # Per-signal hit tracking (for multi-occurrence signals)
        self._signal_hits: dict[str, list[dict]] = defaultdict(list)

    # ── file collection ────────────────────────────────────────────────────────

    def _collect_files(self) -> list[Path]:
        """Recursively collect all scannable source files."""
        all_exts = {".css", ".scss", ".sass", ".html", ".jsx", ".tsx", ".js", ".ts"}
        skip_dirs = {"node_modules", ".git", "dist", "build", ".next", "__pycache__", "vendor"}
        files: list[Path] = []
        for dirpath, dirnames, filenames in os.walk(self.root_path):
            # Prune unwanted directories in-place
            dirnames[:] = [d for d in dirnames if d not in skip_dirs]
            for filename in filenames:
                p = Path(dirpath) / filename
                if p.suffix in all_exts:
                    files.append(p)
        return files

    # ── scanning ───────────────────────────────────────────────────────────────

    def scan(self) -> None:
        """Run the full scan and populate self.violations / self.raw_score."""
        files = self._collect_files()
        if not files:
            return

        for signal in self.TEMPLATE_SIGNALS:
            sig_id = signal["id"]
            target_exts = set(signal["file_types"])
            compiled = re.compile(signal["pattern"], re.IGNORECASE | re.DOTALL)

            for file_path in files:
                if file_path.suffix not in target_exts:
                    continue
                try:
                    text = file_path.read_text(encoding="utf-8", errors="replace")
                except OSError:
                    continue

                for m in compiled.finditer(text):
                    line_no = text[: m.start()].count("\n") + 1
                    rel = str(file_path.relative_to(self.root_path))
                    self._signal_hits[sig_id].append(
                        {"file": rel, "line": line_no, "match": m.group(0)[:80]}
                    )

        # ── Post-processing: multi-occurrence signals ──────────────────────────
        self._evaluate_signals()

    def _evaluate_signals(self) -> None:
        """
        For each signal, decide whether it is triggered and record a violation.
        Some signals require special co-occurrence logic.
        """
        for signal in self.TEMPLATE_SIGNALS:
            sid = signal["id"]
            hits = self._signal_hits.get(sid, [])

            triggered = False
            representative_hits: list[dict] = []

            if sid == "T2":
                # Both Inter AND Poppins must appear in the project
                has_inter = any(
                    "inter" in h["match"].lower() for h in hits
                )
                has_poppins = any(
                    "poppins" in h["match"].lower() for h in hits
                )
                triggered = has_inter and has_poppins
                if triggered:
                    representative_hits = hits[:3]

            elif sid == "T4":
                # Need 3+ occurrences of backdrop-filter: blur
                triggered = len(hits) >= 3
                if triggered:
                    representative_hits = hits[:3]

            elif sid == "T5":
                # Need hero + features + testimonials + cta all present
                sections_found = set()
                for h in hits:
                    text_lower = h["match"].lower()
                    if "hero" in text_lower:
                        sections_found.add("hero")
                    if "feature" in text_lower:
                        sections_found.add("features")
                    if "testimonial" in text_lower:
                        sections_found.add("testimonials")
                    if "cta" in text_lower or "call" in text_lower:
                        sections_found.add("cta")
                triggered = sections_found >= {"hero", "features", "testimonials", "cta"}
                if triggered:
                    representative_hits = hits[:4]

            elif sid == "T10":
                # Collect all lucide imports and count distinct icon names
                # by reading the full import lines
                icon_count = 0
                files_with_lucide: list[dict] = []
                for h in hits:
                    # Re-read the file to count imports on that import line
                    try:
                        fp = self.root_path / h["file"]
                        text = fp.read_text(encoding="utf-8", errors="replace")
                        lines = text.splitlines()
                        for i, line in enumerate(lines):
                            if "lucide-react" in line and "from" in line:
                                # Count identifiers in the import braces
                                brace_match = re.search(r"\{([^}]+)\}", line)
                                if brace_match:
                                    icons = [
                                        x.strip()
                                        for x in brace_match.group(1).split(",")
                                        if x.strip()
                                    ]
                                    icon_count += len(icons)
                                    files_with_lucide.append(
                                        {"file": h["file"], "line": i + 1,
                                         "match": line.strip()[:80]}
                                    )
                    except OSError:
                        pass
                triggered = icon_count >= 5
                if triggered:
                    representative_hits = files_with_lucide[:2]

            elif sid == "T11":
                # Need at least 3 of the 4 generic IDs
                ids_found = set()
                for h in hits:
                    text_lower = h["match"].lower()
                    for gid in ("hero", "features", "pricing", "testimonials"):
                        if gid in text_lower:
                            ids_found.add(gid)
                triggered = len(ids_found) >= 3
                if triggered:
                    representative_hits = hits[:3]

            else:
                # Default: any hit triggers the signal
                triggered = len(hits) >= 1
                representative_hits = hits[:2]

            if triggered:
                self.violations.append(
                    {
                        "id": sid,
                        "name": signal["name"],
                        "weight": signal["weight"],
                        "suggestion": signal["suggestion"],
                        "hits": representative_hits,
                    }
                )
                self.raw_score += signal["weight"]

        self.capped_score = min(self.raw_score, 100)

    # ── reporting ──────────────────────────────────────────────────────────────

    def _score_label(self) -> tuple[str, str]:
        """Return (emoji + label, ANSI colour) based on capped score."""
        s = self.capped_score
        w = self.threshold_warn
        b = self.threshold_block
        if s <= 20:
            return ("✅ UNIQUE", GREEN)
        elif s <= w:
            return ("⚠️  SOME AI PATTERNS", YELLOW)
        elif s <= b:
            return ("⚠️  HIGH TEMPLATE RISK", YELLOW)
        else:
            return ("❌ BLOCKED", RED)

    def _score_bar(self, width: int = 24) -> str:
        """Return a filled/empty bar string representing the score."""
        filled = round(self.capped_score / 100 * width)
        empty = width - filled
        return f"[{'█' * filled}{'░' * empty}]"

    def _recommended_archetype(self) -> str:
        for r, text in self.ARCHETYPE_RECOMMENDATIONS.items():
            if self.capped_score in r:
                return text
        return "—"

    def print_report(self) -> None:
        """Print a formatted terminal report."""
        label, colour = self._score_label()
        bar = self._score_bar()
        score = self.capped_score
        w = self.threshold_warn
        b = self.threshold_block

        sep = "=" * 52
        print(f"\n{BOLD}{sep}{RESET}")
        print(f"  STYLE UNIQUENESS AUDIT")
        print(f"{BOLD}{sep}{RESET}\n")

        print(f"  Template Score: {colour}{BOLD}{score}/100  {label}{RESET}")
        print(f"  {colour}{bar} {score}%{RESET}\n")

        if self.violations:
            print(f"  Detected template signals:\n")
            for v in self.violations:
                vid = v["id"]
                vname = v["name"]
                vweight = v["weight"]
                vsugg = v["suggestion"]
                vhits = v["hits"]

                print(f"  {BOLD}{CYAN}[{vid}]{RESET} {vname} ({vweight}pts)")
                for h in vhits[:2]:
                    print(f"       {DIM}File: {h['file']}:{h['line']}{RESET}")
                print(f"       {YELLOW}Fix:{RESET} {vsugg}")
                print()
        else:
            print(f"  {GREEN}No template signals detected.{RESET}\n")

        archetype = self._recommended_archetype()
        print(f"  RECOMMENDED ARCHETYPE: {BOLD}{archetype}{RESET}")
        print()

        print(f"{BOLD}{sep}{RESET}")
        if score > b:
            print(
                f"  {RED}{BOLD}❌ DELIVERY BLOCKED{RESET} — Score {score}/100 exceeds "
                f"threshold {b}\n"
                f"  Differentiate the design before re-running check.py --final"
            )
        elif score > w:
            print(
                f"  {YELLOW}{BOLD}⚠️  HIGH TEMPLATE RISK{RESET} — Score {score}/100 "
                f"exceeds warning threshold {w}\n"
                f"  Review flagged items and differentiate before delivery."
            )
        else:
            print(
                f"  {GREEN}{BOLD}✅ PASSED{RESET} — Score {score}/100 is within "
                f"acceptable range."
            )
        print(f"{BOLD}{sep}{RESET}\n")

    def to_dict(self) -> dict[str, Any]:
        """Return machine-readable result dict."""
        label, _ = self._score_label()
        return {
            "template_score": self.capped_score,
            "raw_score": self.raw_score,
            "label": label.strip(),
            "threshold_warn": self.threshold_warn,
            "threshold_block": self.threshold_block,
            "exit_code": self._exit_code(),
            "violations": self.violations,
            "recommended_archetype": self._recommended_archetype(),
        }

    # ── exit code ─────────────────────────────────────────────────────────────

    def _exit_code(self) -> int:
        if self.capped_score > self.threshold_block:
            return 2
        if self.capped_score > self.threshold_warn:
            return 1
        return 0


# ──────────────────────────────────────────────────────────────────────────────
# CLI entry point
# ──────────────────────────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="audit_style_uniqueness",
        description=(
            "Detects 'Generic AI Template' clones in web projects.\n"
            "Scores 12 template signals and reports a Template Score (0-100)."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--path",
        type=Path,
        default=Path("."),
        help="Root directory to scan (default: current directory)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Output machine-readable JSON instead of formatted terminal report",
    )
    parser.add_argument(
        "--threshold",
        nargs=2,
        type=int,
        metavar=("WARN", "BLOCK"),
        default=[40, 65],
        help="Custom warning and block thresholds (default: 40 65)",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    root = args.path.resolve()
    if not root.exists():
        print(f"Error: path '{root}' does not exist.", file=sys.stderr)
        return 2
    if not root.is_dir():
        print(f"Error: path '{root}' is not a directory.", file=sys.stderr)
        return 2

    warn, block = args.threshold
    if warn < 0 or block < 0 or warn >= block or block > 100:
        print(
            "Error: thresholds must satisfy 0 ≤ WARN < BLOCK ≤ 100.",
            file=sys.stderr,
        )
        return 2

    auditor = StyleUniquenessAuditor(
        root_path=root,
        threshold_warn=warn,
        threshold_block=block,
    )

    try:
        auditor.scan()
    except Exception as exc:  # noqa: BLE001
        print(f"Error during scan: {exc}", file=sys.stderr)
        return 2

    if args.json_output:
        print(json.dumps(auditor.to_dict(), indent=2, ensure_ascii=False))
    else:
        auditor.print_report()

    return auditor._exit_code()


if __name__ == "__main__":
    sys.exit(main())
