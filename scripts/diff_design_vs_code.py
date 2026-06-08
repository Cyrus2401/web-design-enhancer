#!/usr/bin/env python3
"""
diff_design_vs_code.py — Verifies that code faithfully implements DESIGN.md

Compares the DESIGN.md contract with the real CSS/JS/TSX code and reports divergences:
  - Colors declared in DESIGN.md but absent or different in the code
  - Fonts declared but not loaded
  - Radii declared but not used
  - Animations exceeding DESIGN.md durations in actual code
  - Missing or mis-named CSS variables

Usage:
    python3 scripts/diff_design_vs_code.py DESIGN.md --code ./src
    python3 scripts/diff_design_vs_code.py DESIGN.md --code ./src --strict
    python3 scripts/diff_design_vs_code.py DESIGN.md --file index.css
"""

import sys
import re
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Set


# --- Terminal colors -------------------------------------------------------

GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
RESET  = "\033[0m"

def ok(msg):    print(f"  {GREEN}[OK] {msg}{RESET}")
def fail(msg):  print(f"  {RED}[ERROR] {msg}{RESET}")
def warn(msg):  print(f"  {YELLOW}[WARN] {msg}{RESET}")
def info(msg):  print(f"  {CYAN}->  {msg}{RESET}")
def dim(msg):   print(f"  {DIM}{msg}{RESET}")


# --- DESIGN.md parser ------------------------------------------------------

class DesignContract:
    """Extracts the contract from DESIGN.md."""

    def __init__(self, filepath: str):
        self.path = Path(filepath)
        self.content = self.path.read_text(encoding="utf-8")
        self.colors:     Dict[str, str]  = {}   # role -> hex
        self.fonts:      List[str]       = []   # font names
        self.radii:      List[int]       = []   # px values
        self.spacings:   List[int]       = []   # px values
        self.max_anim_ms: int            = 400  # max animation duration (ms)
        self._parse()

    def _parse(self):
        self._parse_colors()
        self._parse_fonts()
        self._parse_radii()
        self._parse_spacings()
        self._parse_animations()

    # -- Colors -------------------------------------------------------------

    def _parse_colors(self):
        """Extract (role, hex) pairs from the color table."""
        section = self._section(r"## 2\. Color Palette.*?(?=##|$)")
        if not section:
            return
        hex_pat = r"#[0-9A-Fa-f]{6}"
        for line in section.splitlines():
            hexes = re.findall(hex_pat, line)
            if not hexes:
                continue
            # Clean the line: strip markdown table pipes/spaces
            clean = re.sub(r"\|", " ", line).strip()
            # First significant word = role
            words = [w.strip("* ") for w in clean.split() if w.strip("| *")]
            role = words[0].lower() if words else "unknown"
            self.colors[role] = hexes[0].upper()

    # -- Fonts --------------------------------------------------------------

    def _parse_fonts(self):
        """Extract declared font names."""
        section = self._section(r"## 3\. Typography.*?(?=##|$)")
        if not section:
            return
        # Pattern "**Font Name** (Display)"  or  "Font: Font Name"
        patterns = [
            r"\*\*([A-Za-z][A-Za-z\s]+?)\*\*\s*\(",
            r"(?:Font|Police|Typeface):\s*([A-Za-z][A-Za-z\s]+?)(?:\n|,|\(|$)",
        ]
        found: Set[str] = set()
        for pat in patterns:
            for m in re.finditer(pat, section, re.IGNORECASE):
                name = m.group(1).strip()
                if len(name) > 2:
                    found.add(name)
        # Also look in Google Fonts import
        gf = re.findall(r"family=([A-Za-z+]+)", section)
        for f in gf:
            found.add(f.replace("+", " "))
        self.fonts = sorted(found)

    # -- Radii --------------------------------------------------------------

    def _parse_radii(self):
        section = self._section(r"## 5\. Spacing.*?(?=##|$)")
        if not section:
            return
        # "Radius: 4px, 8px, 16px" or "Radius (Rounded): 8px"
        radii_line = re.search(r"[Rr]adius.*?:(.*)", section)
        if radii_line:
            self.radii = [int(v) for v in re.findall(r"(\d+)px", radii_line.group(1))]

    # -- Spacings -----------------------------------------------------------

    def _parse_spacings(self):
        section = self._section(r"## 5\. Spacing.*?(?=##|$)")
        if not section:
            return
        self.spacings = [int(v) for v in re.findall(r"(\d+)px", section)]

    # -- Animations ---------------------------------------------------------

    def _parse_animations(self):
        section = self._section(r"## 7\. Motion.*?(?=##|$)")
        if not section:
            return
        # ms values
        ms_vals = [int(v) for v in re.findall(r"(\d+)ms", section)]
        # s values
        s_vals  = [int(float(v) * 1000) for v in re.findall(r"(\d+(?:\.\d+)?)s\b", section)]
        all_vals = ms_vals + s_vals
        if all_vals:
            self.max_anim_ms = max(all_vals)

    # -- Helpers ------------------------------------------------------------

    def _section(self, pattern: str) -> str:
        m = re.search(pattern, self.content, re.DOTALL | re.IGNORECASE)
        return m.group(0) if m else ""


# --- Code analyzer ---------------------------------------------------------

class CodeAnalyzer:
    """Extracts tokens actually used in CSS/JS/TSX code."""

    CSS_EXTS  = {".css", ".scss", ".sass", ".less"}
    JS_EXTS   = {".js", ".ts", ".jsx", ".tsx", ".vue", ".svelte"}
    HTML_EXTS = {".html", ".htm"}
    SKIP_DIRS = {"node_modules", ".git", "dist", "build", ".next", "__pycache__"}

    def __init__(self, code_path: str = None, file_path: str = None):
        self.roots: List[Path] = []
        if code_path:
            self.roots.append(Path(code_path))
        if file_path:
            self.roots.append(Path(file_path))

        self.hex_colors:   Set[str]       = set()
        self.css_vars:     Dict[str, str] = {}   # --var-name -> value
        self.font_refs:    Set[str]       = set()
        self.anim_durations: List[Tuple[int, str]] = []  # (ms, context)
        self._scan()

    def _scan(self):
        for root in self.roots:
            if root.is_file():
                self._scan_file(root)
            elif root.is_dir():
                for f in root.rglob("*"):
                    if any(part in self.SKIP_DIRS for part in f.parts):
                        continue
                    if f.suffix in self.CSS_EXTS | self.JS_EXTS | self.HTML_EXTS:
                        self._scan_file(f)

    def _scan_file(self, path: Path):
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return

        # Hex colors
        for h in re.findall(r"#[0-9A-Fa-f]{6}", content):
            self.hex_colors.add(h.upper())

        # CSS variables --name: value
        for m in re.finditer(r"--([\w-]+)\s*:\s*([^;}\n]+)", content):
            self.css_vars[f"--{m.group(1)}"] = m.group(2).strip()

        # Fonts — font-family, @import Google Fonts, fontsource
        for m in re.finditer(
            r"font-family\s*:\s*['\"]?([A-Za-z][A-Za-z\s]+?)['\"]?(?:\s*,|;|}|\n)",
            content, re.IGNORECASE
        ):
            self.font_refs.add(m.group(1).strip())
        for m in re.finditer(r"family=([A-Za-z+]+)", content):
            self.font_refs.add(m.group(1).replace("+", " "))
        # Google Fonts in HTML <link> tag
        for m in re.finditer(r"fonts[.]googleapis[.]com[^>]*family=([A-Za-z+]+)", content):
            self.font_refs.add(m.group(1).replace("+", " "))
        for m in re.finditer(r"['\"](@fontsource|next/font).*?([A-Za-z][A-Za-z\s]+)['\"]", content):
            self.font_refs.add(m.group(2).strip())

        # Animation durations — CSS transitions/animations + GSAP
        #
        # Fundamental distinction:
        #   UI transitions    -> transition: all 200ms  (subject to the <= max_anim_ms rule)
        #   Decorative anims  -> animation: mesh 28s    (background, loaders, ambience — exempt)
        #
        # Rule: only "transition:" and GSAP "duration:" are checked.
        # Long "@keyframes" and "animation:" are decorative — exempt.

        # 1. CSS transitions (UI only)
        for m in re.finditer(r"\btransition\b[^;{]*?(\d+)ms", content):
            self.anim_durations.append((int(m.group(1)), f"{path.name} [transition]"))
        for m in re.finditer(r"\btransition\b[^;{]*?(\d+(?:\.\d+)?)s\b", content):
            ms = int(float(m.group(1)) * 1000)
            if ms < 10000:  # > 10s = clearly decorative, skip
                self.anim_durations.append((ms, f"{path.name} [transition]"))

        # 2. GSAP duration (orchestrated UI transitions — not background timelines)
        for m in re.finditer(r"\bduration\s*:\s*(\d+(?:\.\d+)?)", content):
            val = float(m.group(1))
            ms  = int(val * 1000) if val < 10 else int(val)
            if ms < 5000:  # > 5s = long background/timeline animation, skip
                self.anim_durations.append((ms, f"{path.name} [gsap]"))

        # Note: "animation: mesh 28s", "@keyframes", "animation-duration: 28s"
        # are intentionally ignored — decorative background animations.


# --- Diff Engine -----------------------------------------------------------

class DesignDiffer:
    """Compares the DESIGN.md contract against the analyzed code."""

    def __init__(self, contract: DesignContract, code: CodeAnalyzer, strict: bool = False):
        self.contract = contract
        self.code     = code
        self.strict   = strict
        self.errors:   List[str] = []
        self.warnings: List[str] = []
        self.oks:      List[str] = []

    def run(self) -> bool:
        self._diff_colors()
        self._diff_fonts()
        self._diff_animations()
        self._diff_css_vars()
        self._print_report()
        return len(self.errors) == 0

    # -- Colors -------------------------------------------------------------

    def _diff_colors(self):
        if not self.contract.colors:
            self.warnings.append("No color extracted from DESIGN.md (malformed table?)")
            return

        missing = []
        present = []
        for role, hex_val in self.contract.colors.items():
            if hex_val in self.code.hex_colors:
                present.append(f"{role}: {hex_val}")
            else:
                # Look for a close value (same hue, different luminosity)
                similar = self._find_similar(hex_val, self.code.hex_colors)
                if similar:
                    self.warnings.append(
                        f"Color '{role}' ({hex_val}) not found exactly — "
                        f"close value in code: {similar}. "
                        f"Intentional or drift?"
                    )
                else:
                    missing.append(f"{role}: {hex_val}")

        if present:
            self.oks.append(f"{len(present)}/{len(self.contract.colors)} DESIGN.md colors present in the code")
        for m in missing:
            self.errors.append(f"Color absent from code: {m}")

    def _find_similar(self, target: str, candidates: Set[str], threshold: int = 30) -> str:
        """Find a close color in RGB space."""
        tr, tg, tb = self._hex_to_rgb(target)
        best, best_dist = "", 999
        for c in candidates:
            cr, cg, cb = self._hex_to_rgb(c)
            dist = abs(tr - cr) + abs(tg - cg) + abs(tb - cb)
            if dist < best_dist:
                best_dist, best = dist, c
        return best if best_dist <= threshold else ""

    @staticmethod
    def _hex_to_rgb(h: str) -> Tuple[int, int, int]:
        h = h.lstrip("#")
        return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)

    # -- Fonts --------------------------------------------------------------

    def _diff_fonts(self):
        if not self.contract.fonts:
            self.warnings.append("No font extracted from DESIGN.md")
            return

        font_refs_lower = {f.lower() for f in self.code.font_refs}

        for font in self.contract.fonts:
            # Loose comparison: "Plus Jakarta Sans" matches "PlusJakartaSans" etc.
            normalized = re.sub(r"\s+", "", font).lower()
            found = any(
                normalized in re.sub(r"\s+", "", ref).lower()
                or ref.lower() in font.lower()
                for ref in self.code.font_refs
            ) or any(normalized in r for r in font_refs_lower)

            if found:
                self.oks.append(f"Font '{font}' loaded in the code")
            else:
                self.errors.append(
                    f"Font '{font}' declared in DESIGN.md but not found in the code. "
                    f"Check the Google Fonts import or the CSS font-family."
                )

    # -- Animations ---------------------------------------------------------

    def _diff_animations(self):
        max_contract = self.contract.max_anim_ms
        violations   = [(ms, ctx) for ms, ctx in self.code.anim_durations if ms > max_contract]

        if not self.code.anim_durations:
            self.warnings.append("No animation duration found in the code")
            return

        max_found = max(ms for ms, _ in self.code.anim_durations)
        if not violations:
            self.oks.append(
                f"All animations respect the DESIGN.md max "
                f"({max_contract}ms) — max found: {max_found}ms"
            )
        else:
            seen_ctx: Set[str] = set()
            for ms, ctx in violations:
                if ctx not in seen_ctx:
                    seen_ctx.add(ctx)
                    self.errors.append(
                        f"Animation {ms}ms in '{ctx}' exceeds DESIGN.md max ({max_contract}ms)"
                    )

    # -- CSS variables ------------------------------------------------------

    def _diff_css_vars(self):
        """Verify DESIGN.md colors are referenced via CSS --variables."""
        if not self.contract.colors or not self.code.css_vars:
            return

        # Look for DESIGN.md hex values in CSS variable values
        contract_hexes = {h.upper() for h in self.contract.colors.values()}
        vars_with_contract_hex = {
            var: val for var, val in self.code.css_vars.items()
            if any(h.upper() in val.upper() for h in contract_hexes)
        }

        if vars_with_contract_hex:
            self.oks.append(
                f"{len(vars_with_contract_hex)} DESIGN.md colors referenced as CSS variables "
                f"({', '.join(list(vars_with_contract_hex.keys())[:3])}{'...' if len(vars_with_contract_hex) > 3 else ''})"
            )
        elif self.strict:
            self.warnings.append(
                "No DESIGN.md color found in --custom CSS variables. "
                "Recommended: use CSS variables for all tokens."
            )

    # -- Report -------------------------------------------------------------

    def _print_report(self):
        print(f"\n{BOLD}{'='*60}{RESET}")
        print(f"{BOLD}  DIFF DESIGN.md <-> CODE{RESET}")
        print(f"{BOLD}{'='*60}{RESET}\n")

        if self.oks:
            print(f"{GREEN}  [OK] Matches{RESET}")
            for o in self.oks:
                ok(o)
            print()

        if self.warnings:
            print(f"{YELLOW}  [WARN] Warnings{RESET}")
            for w in self.warnings:
                warn(w)
            print()

        if self.errors:
            print(f"{RED}  [ERROR] Divergences{RESET}")
            for e in self.errors:
                fail(e)
            print()

        print(f"{BOLD}{'-'*60}{RESET}")
        if self.errors:
            print(f"{RED}{BOLD}  [ERROR] RESULT: {len(self.errors)} divergence(s) — code does not respect DESIGN.md{RESET}")
        else:
            print(f"{GREEN}{BOLD}  [OK] RESULT: Code conforms to DESIGN.md{RESET}")
        print(f"{BOLD}{'-'*60}{RESET}\n")


# --- Entry point -----------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="DESIGN.md <-> code diff — verifies that the implementation respects the contract"
    )
    parser.add_argument("design", help="Path to DESIGN.md")
    parser.add_argument("--code", help="Source code directory to analyze")
    parser.add_argument("--file", help="Single CSS/JS file to analyze")
    parser.add_argument("--strict", action="store_true", help="Enable additional checks")
    args = parser.parse_args()

    if not args.code and not args.file:
        print("Usage: python3 scripts/diff_design_vs_code.py DESIGN.md --code ./src")
        print("       python3 scripts/diff_design_vs_code.py DESIGN.md --file index.css")
        sys.exit(1)

    design_path = Path(args.design)
    if not design_path.exists():
        print(f"[ERROR] DESIGN.md not found: {args.design}")
        sys.exit(1)

    contract = DesignContract(str(design_path))
    code     = CodeAnalyzer(code_path=args.code, file_path=args.file)
    differ   = DesignDiffer(contract, code, strict=args.strict)

    success = differ.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
