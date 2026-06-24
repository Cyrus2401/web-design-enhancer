"""Tests for audit_beauty.py #4 dial-coherence (anti-gaming). No brief => no-op."""
import tempfile, textwrap
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from audit_beauty import BeautyAuditor

BRIEF_MOTION_HIGH = "## Design Dials\nVARIANCE: 5\nMOTION: **8**\nDENSITY: 6\n"

# Craft markers present but ZERO motion -> contradicts declared MOTION 8
CSS_NO_MOTION = """
    :root{--color-accent:#e63946;--ink:#1a1a1a;--paper:#faf7f0}
    body{font-size:1rem;color:var(--ink);background:var(--paper)}
    h1{font-size:clamp(40px,9vw,120px);letter-spacing:-0.03em;font-weight:800}
    h2{font-size:2.5rem} h3{font-size:1.5rem} small{font-size:.8rem}
    .section{padding:96px 24px}
    .card{padding:32px;gap:24px;box-shadow:0 1px 2px rgba(0,0,0,.1),0 8px 24px rgba(0,0,0,.12)}
"""

def _make(css):
    tmp = Path(tempfile.mkdtemp())
    (tmp / "styles.css").write_text(textwrap.dedent(css), encoding="utf-8")
    return tmp

def _audit(css, brief=""):
    a = BeautyAuditor(root_path=_make(css), brief_text=brief)
    a.scan()
    return a

def test_no_brief_is_noop():
    a = _audit(CSS_NO_MOTION)
    assert a.coherence == []
    assert a.coherence_penalty == 0

def test_declared_motion_not_realized_flagged():
    a = _audit(CSS_NO_MOTION, BRIEF_MOTION_HIGH)
    signals = [c["signal"] for c in a.coherence]
    assert "MOTION" in signals
    assert a.coherence_penalty > 0

def test_coherence_penalty_capped():
    a = _audit(CSS_NO_MOTION, BRIEF_MOTION_HIGH)
    assert a.coherence_penalty <= 12

def test_coherence_lowers_score_vs_no_brief():
    base = _audit(CSS_NO_MOTION).score
    penalised = _audit(CSS_NO_MOTION, BRIEF_MOTION_HIGH).score
    assert penalised <= base

def test_to_dict_exposes_coherence():
    d = _audit(CSS_NO_MOTION, BRIEF_MOTION_HIGH).to_dict()
    assert "coherence" in d and "coherence_penalty" in d
