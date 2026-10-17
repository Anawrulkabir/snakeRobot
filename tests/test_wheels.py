"""Wheel contact physics (G3) via scripts/drag_test.py and scripts/yaw_test.py.

Each check is paired with a planted fault it must catch (CLAUDE.md 9).
"""

import copy
import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import drag_test  # noqa: E402
import yaw_test  # noqa: E402
import snake.model_builder as mb  # noqa: E402
from snake import config as cfgmod  # noqa: E402

TOL = drag_test.RATIO_TOL


@pytest.fixture
def cfg():
    return cfgmod.load()


def ratio(cfg, kind, speed=0.05):
    f, _ = drag_test.drag_force(cfg, "forward", kind, speed)
    s, _ = drag_test.drag_force(cfg, "sideways", kind, speed)
    return s / f


@pytest.mark.parametrize("kind", ["head", "body"])
def test_sideways_resistance_is_coulomb(cfg, kind):
    # Sliding sideways, the tyre resists with mu * N, N = segment weight.
    f, _ = drag_test.drag_force(cfg, "sideways", kind, 0.01)
    assert f == pytest.approx(cfg["ground"]["friction_sliding"] * drag_test.segment_weight(cfg, kind), rel=0.01)


@pytest.mark.parametrize("kind", ["head", "body"])
@pytest.mark.parametrize("speed", [0.01, 0.05])
def test_ratio_matches_target_for_each_segment(cfg, kind, speed):
    # G3 follow-up, item 1: each segment gets the target ratio within TOL,
    # at both speeds (so the law is rate-independent, i.e. Coulomb-like).
    assert ratio(cfg, kind, speed) == pytest.approx(cfg["ground"]["anisotropy_ratio"], rel=TOL)


def test_ratio_law_holds_at_other_targets(cfg):
    # The formula mu_roll = mu r / sqrt(R^2 - 1) is a law, not a fit to 1.6.
    for R in (1.2, 3.0):
        c = copy.deepcopy(cfg)
        c["ground"]["anisotropy_ratio"] = R
        assert ratio(c, "body") == pytest.approx(R, rel=TOL)


def test_ratio_check_catches_naive_rolling_formula(cfg, monkeypatch):
    # Planted fault: mu_roll = mu r / R, which ignores the elliptic-cone
    # coupling. It gives about 1.89:1, which the check must reject.
    real = mb.build_mjcf
    g = cfg["ground"]
    good = g["friction_sliding"] * g["wheel_radius"] / math.sqrt(g["anisotropy_ratio"] ** 2 - 1)
    naive = g["friction_sliding"] * g["wheel_radius"] / g["anisotropy_ratio"]

    def naive_build(c=None, drag_rig=False):
        return real(c, drag_rig).replace(f'{good:.9g}"', f'{naive:.9g}"')

    monkeypatch.setattr(mb, "build_mjcf", naive_build)
    assert ratio(cfg, "body") != pytest.approx(g["anisotropy_ratio"], rel=TOL)


def test_anisotropy_check_catches_wheel_turned_90deg(cfg, monkeypatch):
    # Planted fault: axle along the body instead of across it. The wheel then
    # rolls sideways, so the ratio falls below 1.
    real = mb.build_mjcf

    def turned(c=None, drag_rig=False):
        return (
            real(c, drag_rig)
            .replace('type="hinge" axis="0 1 0"', 'type="hinge" axis="1 0 0"')
            .replace('zaxis="0 1 0"', 'zaxis="1 0 0"')
        )

    monkeypatch.setattr(mb, "build_mjcf", turned)
    assert ratio(cfg, "body") < 1


def test_axle_friction_is_torque_over_radius(cfg):
    # With rolling friction made negligible (huge ratio), extra axle friction
    # tau is felt at the ground as tau / r. Valid from 0.02 m/s; at 0.01 m/s
    # the constraint softening still shows (force about 12% low). Axle friction
    # is 0 in main runs and only used as an E4 knob (robot.yaml note).
    c = copy.deepcopy(cfg)
    c["ground"]["anisotropy_ratio"] = 1e6
    c["ground"]["axle_friction"] = 1e-3
    for v in (0.02, 0.05):
        f, _ = drag_test.drag_force(c, "forward", "body", v)
        assert f == pytest.approx(1e-3 / c["ground"]["wheel_radius"], rel=0.02)


def test_axle_check_catches_viscous_friction(cfg):
    # Planted fault: MuJoCo's default friction time constant (0.02 s) makes the
    # 'dry' axle friction act viscous, far below tau / r at 0.01 m/s.
    c = copy.deepcopy(cfg)
    c["ground"]["anisotropy_ratio"] = 1e6
    c["ground"]["axle_friction"] = 1e-3
    c["ground"]["axle_friction_timeconst"] = 0.02
    f, _ = drag_test.drag_force(c, "forward", "body", 0.01)
    assert f < 0.5 * 1e-3 / c["ground"]["wheel_radius"]


def test_torsional_friction_not_meaningful(cfg):
    # G3 follow-up, item 2.
    assert not yaw_test.run(cfg)["meaningful"]


def test_torsion_check_catches_mujoco_default(cfg):
    # Planted fault: MuJoCo's default torsional coefficient (0.005 m).
    c = copy.deepcopy(cfg)
    c["ground"]["torsional_friction"] = 0.005
    assert yaw_test.run(c)["meaningful"]
