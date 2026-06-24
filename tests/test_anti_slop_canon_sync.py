"""
tests/test_anti_slop_canon_sync.py

Guard-rail for integration #2: the AI-default "Tailwind indigo" palette lives in
TWO places — the vendored human canon (references/craft/anti-ai-slop.md) and the
mirror constant CANON_DEFAULT_INDIGO in scripts/detect_ai_slop.py. They MUST NOT
drift. If someone edits one without the other, this test fails loudly.

Canon origin: nexu-io/open-design @ 009ff65 (Apache-2.0).
"""
import re
from pathlib import Path

import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import detect_ai_slop  # noqa: E402

CANON = ROOT / "references" / "craft" / "anti-ai-slop.md"


def _canon_text() -> str:
    assert CANON.exists(), f"vendored canon missing: {CANON}"
    return CANON.read_text(encoding="utf-8")


def test_canon_file_is_vendored_and_attributed():
    txt = _canon_text()
    # Apache provenance must be traceable from the canon itself.
    assert re.search(r"open-design", txt, re.I), "canon must cite its open-design origin"


def test_constant_hexes_all_present_in_canon():
    """Every hex in the mirror constant must appear verbatim in the canon."""
    txt = _canon_text().lower()
    missing = [h for h in detect_ai_slop.CANON_DEFAULT_INDIGO if h.lower() not in txt]
    assert not missing, (
        f"CANON_DEFAULT_INDIGO drifted from the canon — these hexes are in the "
        f"constant but NOT in references/craft/anti-ai-slop.md: {missing}. "
        f"Re-sync the two or update both together."
    )


def test_canon_indigo_hexes_all_present_in_constant():
    """Every AI-default indigo hex documented in the canon must be enforced."""
    txt = _canon_text()
    # The canon lists the indigo palette as inline-code hexes (e.g. `#6366f1`).
    canon_hexes = {h.lower() for h in re.findall(r"#[0-9a-fA-F]{6}", txt)}
    const_hexes = {h.lower() for h in detect_ai_slop.CANON_DEFAULT_INDIGO}
    # Only assert over the known indigo set (canon may list other example hexes).
    indigo = {"#6366f1", "#4f46e5", "#4338ca", "#3730a3", "#8b5cf6", "#7c3aed", "#a855f7"}
    documented = indigo & canon_hexes
    not_enforced = documented - const_hexes
    assert not not_enforced, (
        f"Canon documents indigo hexes the constant does not enforce: {not_enforced}"
    )


def test_constant_is_nonempty_tuple():
    assert isinstance(detect_ai_slop.CANON_DEFAULT_INDIGO, tuple)
    assert len(detect_ai_slop.CANON_DEFAULT_INDIGO) >= 5
