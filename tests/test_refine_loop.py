"""Tests for refine_loop.py - the iterative enhancement loop's decision engine."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import refine_loop as rl


def _entry(scores):
    return {"scores": scores, "aggregate": rl.aggregate(scores)}


def test_gate_passes_higher_is_better():
    assert rl.gate_passes("beauty", 75) is True
    assert rl.gate_passes("beauty", 60) is False


def test_gate_passes_lower_is_better_uniqueness():
    assert rl.gate_passes("uniqueness", 50) is True     # below 65 floor = good
    assert rl.gate_passes("uniqueness", 80) is False    # too template-like


def test_absent_metric_does_not_block():
    assert rl.gate_passes("beauty", None) is True
    assert rl.all_pass({"composition": 90}) is True


def test_all_pass():
    assert rl.all_pass({"beauty": 80, "composition": 75, "uniqueness": 40}) is True
    assert rl.all_pass({"beauty": 80, "composition": 50}) is False


def test_aggregate_inverts_uniqueness():
    # high uniqueness score (template-like) should drag the aggregate down
    good = rl.aggregate({"uniqueness": 20})
    bad = rl.aggregate({"uniqueness": 90})
    assert good > bad


def test_decide_converged():
    hist = [_entry({"beauty": 82, "composition": 78, "uniqueness": 30, "wow": 75})]
    v = rl.decide(hist)
    assert v["action"] == "stop" and "converged" in v["reason"]


def test_decide_continue_when_failing():
    hist = [_entry({"beauty": 55, "composition": 60})]
    v = rl.decide(hist)
    assert v["action"] == "continue"


def test_decide_max_iterations():
    hist = [_entry({"beauty": 40 + i}) for i in range(6)]
    v = rl.decide(hist, max_iter=6)
    assert v["action"] == "stop" and "max-iter" in v["reason"]


def test_decide_plateau():
    hist = [_entry({"beauty": 60}), _entry({"beauty": 60.5}), _entry({"beauty": 61})]
    v = rl.decide(hist, plateau_k=2, epsilon=1.5)
    assert v["action"] == "stop" and "plateau" in v["reason"]


def test_decide_flags_regression():
    hist = [_entry({"beauty": 68}), _entry({"beauty": 55})]
    v = rl.decide(hist)
    assert any("regression" in f for f in v.get("flags", []))


def test_prioritize_orders_by_leverage():
    scores = {"beauty": 50, "composition": 68, "uniqueness": 90}
    fixes = rl.prioritize(scores, {"beauty": ["fix typography"], "uniqueness": ["differentiate"]})
    gates = [f["gate"] for f in fixes]
    # all three fail; beauty (weight25, big gap) and uniqueness (weight20, big gap)
    # should outrank composition (weight20, small gap)
    assert "composition" in gates
    assert gates.index("composition") == len(gates) - 1
    assert fixes[0]["leverage"] >= fixes[-1]["leverage"]


def test_prioritize_skips_passing_gates():
    fixes = rl.prioritize({"beauty": 90, "composition": 50})
    assert [f["gate"] for f in fixes] == ["composition"]
