"""Unit tests for scripts/wde_measure.py - shared ratio/measurement primitives."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import wde_measure as m


def test_font_sizes_px_handles_px_rem_clamp_tailwind():
    css = "body{font-size:16px} h1{font-size:clamp(48px,11vw,132px)} .x{font-size:2rem}"
    sizes = m.extract_font_sizes_px(css)
    assert 132 in sizes and 16 in sizes and 48 in sizes
    assert 32.0 in sizes  # 2rem -> 32px


def test_tailwind_text_scale():
    sizes = m.extract_font_sizes_px("<h1 class='text-9xl'>hi</h1> <p class='text-base'>x</p>")
    assert 128 in sizes and 16 in sizes


def test_scale_jump_ratio_big_vs_small():
    big = m.scale_jump_ratio("body{font-size:16px} h1{font-size:132px}")
    small = m.scale_jump_ratio(".h{font-size:24px}")
    assert big > 6.0
    assert small < 2.0


def test_whitespace_ratio():
    assert m.whitespace_ratio([8, 8, 8, 96]) > 5.0
    assert m.whitespace_ratio([16, 16, 16]) == 1.0
    assert m.whitespace_ratio([]) == 0.0


def test_graded_ramp_endpoints_and_middle():
    assert m.graded(1.0, 2.5, 6.0, 40) == 0
    assert m.graded(6.0, 2.5, 6.0, 40) == 40
    assert m.graded(10.0, 2.5, 6.0, 40) == 40  # clamped
    mid = m.graded(4.25, 2.5, 6.0, 40)
    assert 0 < mid < 40


def test_parse_dials():
    d = m.parse_dials("VARIANCE: **9**\nMOTION = 2\ndensity: 5")
    assert d == {"variance": 9, "motion": 2, "density": 5}
    assert m.parse_dials("nothing here") == {"variance": None, "motion": None, "density": None}


def test_parse_dials_rejects_out_of_range():
    assert m.parse_dials("VARIANCE: 42")["variance"] is None
