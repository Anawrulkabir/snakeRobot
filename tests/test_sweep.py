"""Tests for the sweep runner's variant overrides."""

import copy
import importlib.util
from pathlib import Path

import pytest

from snake import config as cfgmod

spec = importlib.util.spec_from_file_location(
    "run_sweep", Path(__file__).resolve().parent.parent / "experiments" / "run_sweep.py"
)
rs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rs)


def configs():
    return (
        copy.deepcopy(cfgmod.load()),
        copy.deepcopy(cfgmod.load("arena.yaml")),
        copy.deepcopy(cfgmod.load("metrics.yaml")),
    )


def test_overrides_reach_each_config():
    cfg, arena, mc = configs()
    s = rs.apply_overrides(
        {
            "robot.servo.stall_torque": 1.0,
            "arena.lattice.post_friction": 0.1,
            "metrics.overload.min_duration_s": 3.0,
            "gait.amplitude_scale": 0.85,
        },
        cfg,
        arena,
        mc,
    )
    assert (cfg["servo"]["stall_torque"], arena["lattice"]["post_friction"], mc["overload"]["min_duration_s"], s) == (
        1.0,
        0.1,
        3.0,
        0.85,
    )


def test_override_typo_is_an_error():
    # Planted fault: a misspelt key must not silently add a new, unused entry.
    cfg, arena, mc = configs()
    with pytest.raises(KeyError):
        rs.apply_overrides({"robot.servo.stall_torqe": 1.0}, cfg, arena, mc)


@pytest.mark.parametrize("name, n_cond", [("calib_step1.yaml", 3), ("calib_step2.yaml", 7)])
def test_calibration_file_overrides_are_valid(name, n_cond):
    ex = cfgmod.values(cfgmod.yaml.safe_load(open(cfgmod.CONFIG_DIR / "experiments" / name)))["run"]
    for ov in ex["variants"].values():
        rs.apply_overrides(ov, *configs())
    assert len(rs.jobs_for(ex)) == len(ex["variants"]) * n_cond * 5


spec2 = importlib.util.spec_from_file_location(
    "analyze_calibration", Path(__file__).resolve().parent.parent / "experiments" / "analyze_calibration.py"
)
ac = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(ac)


def cell(succ, rate):
    return {"successes": succ, "rate_mean": rate}


def test_selection_skips_implausible_levels():
    # The 1.0 N m bound wins on the data but is not eligible.
    v, _ = ac.select(
        "servo_torque", {"baseline": cell(0, 0.005), "servo_paper_eq": cell(1, 0.01), "servo_bound_1.0": cell(5, 0.05)}
    )
    assert v == "servo_paper_eq"


def test_selection_uses_rate_when_no_success_and_keeps_baseline_on_tie():
    v, _ = ac.select("amplitude", {"baseline": cell(0, 0.004), "amp_0.85": cell(0, 0.006)})
    assert v == "amp_0.85"
    v, _ = ac.select("amplitude", {"baseline": cell(0, 0.006), "amp_0.85": cell(0, 0.006)})
    assert v == "baseline"


def test_selection_success_beats_rate():
    v, _ = ac.select(
        "post_friction", {"baseline": cell(0, 0.02), "friction_0.2": cell(1, 0.01), "friction_0.1": cell(0, 0.03)}
    )
    assert v == "friction_0.2"


def test_override_string_number_is_an_error():
    # Planted fault (calib_step1 crash, 2026-10-17): YAML read 1.0e9 as the string '1.0e9'.
    cfg, arena, mc = configs()
    bad = cfgmod.yaml.safe_load("v: 1.0e9")["v"]
    with pytest.raises(TypeError):
        rs.apply_overrides({"metrics.overload.min_duration_s": bad}, cfg, arena, mc)


spec3 = importlib.util.spec_from_file_location(
    "analyze_calib_step2", Path(__file__).resolve().parent.parent / "experiments" / "analyze_calib_step2.py"
)
a2 = importlib.util.module_from_spec(spec3)
spec3.loader.exec_module(a2)


def S(g0, g75, g1, g15):
    return {0.0: g0, 0.75: g75, 1.0: g1, 1.5: g15}


@pytest.mark.parametrize(
    "s, expected",
    [
        (S(0, 3, 1, 1), "mid-G wins"),  # 3 >= 0+2 and 3 >= 1+2
        (S(1, 1, 3, 0), "mid-G wins"),  # the better mid setting counts
        (S(1, 2, 2, 1), "inconclusive"),  # margin 1 is not enough
        (S(4, 1, 0, 0), "reversed"),  # the friction-0.1 step-1 pattern
        (S(0, 1, 1, 3), "reversed"),  # loose end wins
        (S(2, 4, 0, 3), "inconclusive"),  # beats G = 0 by 2 but G = 1.5 by only 1
        (S(0, 0, 0, 0), "inconclusive"),  # floor effect
    ],
)
def test_step2_outcome_rule(s, expected):
    assert a2.outcome(s) == expected


def test_step2_rule_check_catches_margin_one(monkeypatch):
    # Planted fault: a margin of 1 would call (1, 2, 2, 1) a mid-G win.
    monkeypatch.setattr(a2, "MARGIN", 1)
    assert a2.outcome(S(1, 2, 2, 1)) != "inconclusive"
