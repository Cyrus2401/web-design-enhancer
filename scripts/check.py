#!/usr/bin/env python3
"""
check.py — web-design-enhancer validation orchestrator
Turns SKILL.md phases into mechanical gates.
Compatible with any AI model — no platform dependency.

Usage:
  python3 scripts/check.py --gate 0          # Phase 0 executed?
  python3 scripts/check.py --gate 1          # DESIGN.md valid? (blocks before code)
  python3 scripts/check.py --final           # Full validation before delivery
  python3 scripts/check.py --final --code ./src

Exit codes:
  0 = OK, continue
  1 = BLOCKED, fix before continuing
"""

import sys
import os
import re
import json
import hashlib
import argparse
import subprocess
from pathlib import Path
from datetime import datetime

# --- Terminal colors -------------------------------------------------------
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

def ok(msg):  print(f"  {GREEN}[OK] {msg}{RESET}")
def fail(msg): print(f"  {RED}[ERROR] {msg}{RESET}")
def warn(msg): print(f"  {YELLOW}[WARN] {msg}{RESET}")
def info(msg): print(f"  {CYAN}->  {msg}{RESET}")

SCRIPTS_DIR = Path(__file__).parent
LOG_FILE    = Path(".phase-log.json")
DESIGN_FILE = Path("DESIGN.md")

# Gates whose validity depends on the content of DESIGN.md
# (if DESIGN.md changes after pass, the gate is auto-invalidated)
DESIGN_DEPENDENT_GATES = {"gate0", "gate1"}


# --- Phase log -------------------------------------------------------------

def _design_hash():
    """SHA-256 of the current DESIGN.md, or None if absent."""
    if not DESIGN_FILE.exists():
        return None
    return hashlib.sha256(DESIGN_FILE.read_bytes()).hexdigest()

def load_log():
    if LOG_FILE.exists():
        try:
            return json.loads(LOG_FILE.read_text())
        except Exception:
            pass
    return {}

def save_log(log):
    LOG_FILE.write_text(json.dumps(log, indent=2))

def mark_passed(gate):
    log = load_log()
    entry = {"passed": True, "at": datetime.now().isoformat()}
    # For gates that depend on DESIGN.md, persist the current hash.
    # Any later modification of the file invalidates the pass.
    if gate in DESIGN_DEPENDENT_GATES:
        h = _design_hash()
        if h is not None:
            entry["design_hash"] = h
    log[gate] = entry
    save_log(log)

def gate_passed(gate):
    """Returns True if the gate was validated AND DESIGN.md hasn't changed since."""
    entry = load_log().get(gate, {})
    if not entry.get("passed", False):
        return False
    # Auto-invalidate if DESIGN.md changed since the pass
    if gate in DESIGN_DEPENDENT_GATES:
        stored_hash = entry.get("design_hash")
        current_hash = _design_hash()
        if stored_hash and current_hash and stored_hash != current_hash:
            warn(f"{gate} invalidated: DESIGN.md was modified since validation.")
            info(f"Re-run: python3 scripts/check.py --gate {gate[-1]}")
            return False
        # If the gate depends on DESIGN.md but no hash was stored
        # (old log in pre-hash format), invalidate as a precaution
        if stored_hash is None and current_hash is not None:
            warn(f"{gate}: stale log (no hash) — re-run the gate.")
            return False
    return True


# --- Gate 0 — Phase 0 execution proof --------------------------------------

def check_gate0():
    print(f"\n{BOLD}{'='*60}{RESET}")
    print(f"{BOLD}  GATE 0 — Phase 0 executed?{RESET}")
    print(f"{BOLD}{'='*60}{RESET}")

    errors = []

    # 1. design-system-output.md present (produced by search.py --save)
    ds_files = list(Path(".").glob("design-system-output*.md"))
    if ds_files:
        ok(f"design-system-output.md found ({ds_files[0].name})")
    else:
        fail("design-system-output.md missing")
        info("Run: python3 scripts/search.py \"<description>\" --design-system -p \"<Project>\" --save")
        errors.append("search.py not executed")

    # 2. A getdesign reference DESIGN.md file present
    getdesign_files = list(Path(".").glob("getdesign-*.md")) + list(Path(".").glob("brand-*.md"))
    if getdesign_files:
        ok(f"getdesign.md reference found ({getdesign_files[0].name})")
    else:
        fail("No getdesign.md reference file found")
        info("Run: npx getdesign@latest add <brand>")
        info("Brand examples: vercel / stripe / linear / notion / supabase")
        errors.append("getdesign.md not executed")

    # 3. Project DESIGN.md present
    if Path("DESIGN.md").exists():
        ok("DESIGN.md present")
    else:
        fail("DESIGN.md missing — create from templates/design-md-template.md")
        errors.append("DESIGN.md missing")

    # 4. Sources Phase 0 section in DESIGN.md
    if Path("DESIGN.md").exists():
        content = Path("DESIGN.md").read_text(encoding="utf-8")
        if "## 0. Sources Phase 0" in content:
            ok("Section '## 0. Sources Phase 0' present in DESIGN.md")
            # Check that placeholders were replaced
            if "[Ex:" in content or "<brand>" in content or "<description>" in content:
                fail("DESIGN.md still contains unfilled placeholders")
                info("Replace all [Ex: ...] and <placeholder> with real values")
                errors.append("Unfilled placeholders in DESIGN.md")
        else:
            fail("Section '## 0. Sources Phase 0' missing from DESIGN.md")
            info("Use templates/design-md-template.md as a base")
            errors.append("Sources section missing from DESIGN.md")

    # Result
    _print_result(errors, "GATE 0")
    if not errors:
        mark_passed("gate0")
    return len(errors) == 0


# --- Gate 1 — DESIGN.md validation -----------------------------------------

def check_gate1():
    print(f"\n{BOLD}{'='*60}{RESET}")
    print(f"{BOLD}  GATE 1 — DESIGN.md valid? (before any code){RESET}")
    print(f"{BOLD}{'='*60}{RESET}")

    # Gate 0 must have passed
    if not gate_passed("gate0"):
        fail("Gate 0 not validated — run first: python3 scripts/check.py --gate 0")
        _print_result(["Gate 0 not passed"], "GATE 1")
        return False

    if not Path("DESIGN.md").exists():
        fail("DESIGN.md missing")
        _print_result(["DESIGN.md missing"], "GATE 1")
        return False

    ok("Gate 0 validated")

    # Run validate_design.py
    result = subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / "validate_design.py"), "DESIGN.md"],
        capture_output=True, text=True
    )
    print(result.stdout)
    if result.returncode == 0:
        mark_passed("gate1")
        return True
    return False


# --- Final Gate — Full validation before delivery --------------------------

def check_final(code_path=None):
    print(f"\n{BOLD}{'='*60}{RESET}")
    print(f"{BOLD}  FINAL GATE — Validation before delivery{RESET}")
    print(f"{BOLD}{'='*60}{RESET}")

    # Gate 1 must have passed
    if not gate_passed("gate1"):
        fail("Gate 1 not validated — run first: python3 scripts/check.py --gate 1")
        _print_result(["Gate 1 not passed"], "FINAL GATE")
        return False

    ok("Gate 1 validated")
    errors = []

    # 1. detect_ai_slop.py
    print(f"\n{CYAN}[1/3] Detecting AI antipatterns...{RESET}")
    slop_args = [sys.executable, str(SCRIPTS_DIR / "detect_ai_slop.py"), "--design", "DESIGN.md"]
    if code_path:
        slop_args += ["--code", code_path]
    r = subprocess.run(slop_args, capture_output=True, text=True)
    print(r.stdout)
    if r.returncode != 0:
        errors.append("detect_ai_slop.py — antipatterns detected")

    # 2. audit_spacing.py
    print(f"\n{CYAN}[2/3] 8px grid audit...{RESET}")
    spacing_path = code_path or "."
    r = subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / "audit_spacing.py"), "--path", spacing_path],
        capture_output=True, text=True
    )
    print(r.stdout)
    if r.returncode != 0:
        errors.append("audit_spacing.py — 8px grid violations")

    # 3. validate_design.py (final pass)
    print(f"\n{CYAN}[3/4] Final DESIGN.md validation...{RESET}")
    r = subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / "validate_design.py"), "DESIGN.md"],
        capture_output=True, text=True
    )
    print(r.stdout)
    if r.returncode != 0:
        errors.append("validate_design.py — DESIGN.md contract not respected")

    # 4. diff_design_vs_code.py
    print(f"\n{CYAN}[4/4] DESIGN.md <-> code diff...{RESET}")
    if code_path:
        r = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "diff_design_vs_code.py"), "DESIGN.md", "--code", code_path],
            capture_output=True, text=True
        )
        print(r.stdout)
        if r.returncode != 0:
            errors.append("diff_design_vs_code.py — code diverges from DESIGN.md")
    else:
        warn("diff_design_vs_code.py skipped (no --code provided)")

    _print_result(errors, "FINAL GATE")
    if not errors:
        mark_passed("final")
        _print_delivery_ok()
    return len(errors) == 0


# --- Helpers ---------------------------------------------------------------

def _print_result(errors, gate_name):
    print(f"\n{BOLD}{'-'*60}{RESET}")
    if errors:
        print(f"{RED}{BOLD}  [ERROR] {gate_name}: BLOCKED — {len(errors)} issue(s){RESET}")
        for e in errors:
            print(f"     - {e}")
        print(f"\n{YELLOW}  -> Fix the errors and re-run this command.{RESET}")
        print(f"{YELLOW}  -> Do not move to the next step until this gate is green.{RESET}")
    else:
        print(f"{GREEN}{BOLD}  [OK] {gate_name}: VALIDATED — continue{RESET}")
    print(f"{BOLD}{'-'*60}{RESET}\n")

def _print_delivery_ok():
    print(f"""
{GREEN}{BOLD}+----------------------------------------------+
|  [OK]  DELIVERY AUTHORIZED                    |
|  All 3 gates green. Zero AI slop detected.    |
+----------------------------------------------+{RESET}
""")


# --- Entry point -----------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="web-design-enhancer — validation orchestrator")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--gate", type=int, choices=[0, 1], help="Check a specific gate (0 or 1)")
    group.add_argument("--final", action="store_true", help="Full validation before delivery")
    parser.add_argument("--code", type=str, default=None, help="Source code path (for --final)")
    args = parser.parse_args()

    if args.gate == 0:
        success = check_gate0()
    elif args.gate == 1:
        success = check_gate1()
    elif args.final:
        success = check_final(args.code)

    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
