#!/usr/bin/env python3
"""
Spacing Audit Script - Checks that all spacings are multiples of 8px

Analyzes CSS/TSX/JSX files to detect:
- Non-8px-multiple padding/margin
- Non-4px-multiple radius sizes
- Inconsistent spacings

Usage:
    python3 audit_spacing.py --path ./client/src --output report.json
    python3 audit_spacing.py --file client/src/index.css
"""

import sys
import re
import json
from pathlib import Path
from typing import List, Dict, Tuple
from collections import defaultdict


class SpacingAuditor:
    """Spacing audit for the codebase."""

    def __init__(self, path: str = None, file: str = None):
        self.path = Path(path) if path else None
        self.file = Path(file) if file else None
        self.issues: List[Dict] = []
        self.stats = defaultdict(int)

    def run(self) -> bool:
        """Run the audit."""
        if self.file:
            self._audit_file(self.file)
        elif self.path:
            self._audit_directory(self.path)
        else:
            print("[ERROR] Specify --path or --file")
            return False

        self._print_report()
        return len(self.issues) == 0

    def _audit_directory(self, directory: Path):
        """Audit all CSS/TSX/JSX files in the directory."""
        extensions = {".css", ".tsx", ".jsx", ".ts", ".js"}

        for file_path in directory.rglob("*"):
            if file_path.suffix in extensions:
                self._audit_file(file_path)

    def _audit_file(self, file_path: Path):
        """Audit a specific file."""
        if not file_path.exists():
            print(f"[ERROR] File not found: {file_path}")
            return

        content = file_path.read_text(encoding="utf-8", errors="ignore")

        # Layout properties subject to the 8px grid
        # Note: box-shadow, transform, border-width, outline are EXCLUDED —
        # these decoration/effect properties don't belong to the layout grid.
        LAYOUT_PROPS = {
            "padding": r"padding(?:-(?:top|right|bottom|left|block|inline))?:\s*([^;}\n]+)",
            "margin":  r"margin(?:-(?:top|right|bottom|left|block|inline))?:\s*([^;}\n]+)",
            "gap":     r"(?:gap|row-gap|column-gap):\s*([^;}\n]+)",
            "top|right|bottom|left": r"(?<!box-shadow:\s)(?:^|\s)(?:top|right|bottom|left):\s*([^;}\n]+)",
        }

        # Radius properties — 4px grid
        RADIUS_PROPS = {
            "border-radius": r"border-radius(?:-(?:top|bottom)-(?:left|right))?:\s*([^;}\n]+)",
        }

        # Properties NOT subject to the grid (effects, decorations):
        # box-shadow, transform (translateY, scale...), border-width, outline,
        # width/height (can be free: 1px hairline, 2px cursor, etc.)

        all_prop_patterns = {**LAYOUT_PROPS, **RADIUS_PROPS}

        for prop, pattern in all_prop_patterns.items():
            matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                value = match.group(1).strip()

                # Skip CSS variables (--var) and calc()
                if "--" in value or "calc(" in value or "var(" in value:
                    continue

                line_num = content[:match.start()].count("\n") + 1
                px_values = re.findall(r"(\d+)px", value)

                for px_val in px_values:
                    num = int(px_val)

                    if prop == "border-radius":
                        # 4px grid for radii; 0 and 9999 always allowed
                        if num != 0 and num != 9999 and num % 4 != 0:
                            self.issues.append({
                                "file": str(file_path),
                                "line": line_num,
                                "property": prop,
                                "value": value,
                                "issue": f"Radius {num}px not a multiple of 4px",
                                "severity": "warning"
                            })
                            self.stats["invalid_radius"] += 1
                    else:
                        # 8px grid for layout, 4px tolerated (micro-spacing)
                        # 2px tolerated for margin-left/right (typographic cursors, micro-details)
                        is_micro_margin = (prop == "margin" and
                                          re.search(r"margin-(?:left|right)", match.group(0).split(":")[0], re.IGNORECASE)
                                          and num == 2)
                        if num != 0 and num % 8 != 0 and num != 4 and not is_micro_margin:
                            self.issues.append({
                                "file": str(file_path),
                                "line": line_num,
                                "property": prop,
                                "value": value,
                                "issue": f"Spacing {num}px not a multiple of 8px",
                                "severity": "warning"
                            })
                            self.stats["invalid_spacing"] += 1

    def _print_report(self):
        """Print the audit report."""
        print("\n" + "=" * 70)
        print("SPACING AUDIT REPORT")
        print("=" * 70)

        if not self.issues:
            print("\n[OK] AUDIT PASSED - All spacings are valid!")
        else:
            print(f"\n[ERROR] {len(self.issues)} spacing issues detected:\n")

            # Group by file
            by_file = defaultdict(list)
            for issue in self.issues:
                by_file[issue["file"]].append(issue)

            for file_path in sorted(by_file.keys()):
                print(f"\n  {file_path}")
                for issue in by_file[file_path]:
                    print(f"  Line {issue['line']}: {issue['property']}")
                    print(f"    Value: {issue['value']}")
                    print(f"    [WARN] {issue['issue']}")

        # Statistics
        print("\n" + "-" * 70)
        print("STATISTICS:")
        print(f"  Invalid spacings: {self.stats['invalid_spacing']}")
        print(f"  Invalid radii: {self.stats['invalid_radius']}")
        print("=" * 70 + "\n")

        return len(self.issues) == 0


def main():
    import argparse

    parser = argparse.ArgumentParser(description="CSS spacing audit")
    parser.add_argument("--path", help="Directory to audit")
    parser.add_argument("--file", help="Specific file to audit")
    parser.add_argument("--output", help="JSON output file")

    args = parser.parse_args()

    auditor = SpacingAuditor(path=args.path, file=args.file)
    success = auditor.run()

    if args.output:
        with open(args.output, "w") as f:
            json.dump(auditor.issues, f, indent=2)
        print(f"Report saved: {args.output}")

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
