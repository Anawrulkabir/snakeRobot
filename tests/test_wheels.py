"""Wheel contact physics (G3) via scripts/drag_test.py, each check with a planted fault."""
import copy
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import drag_test  # noqa: E402
import snake.model_builder as mb  # noqa: E402
from snake import config as cfgmod  # noqa: E402

G = 9.81


@pytest.fixture
def cfg():
    return cfgmod.load()


def head_weight(cfg):
    m = cfg["mass"]
    return (m["shell"] + m["hardware"] + m["head_electronics"]) * G


def test_sideways_resistance_is_coulomb(cfg):
    # Sliding sideways, the tyre should resist with mu * N, N = segment weight.
    f_side, _ = drag_test.drag_force(cfg, "sideways")
    assert f_side == pytest.approx(cfg["ground"]["friction_sliding"] * head_weight(cfg), rel=0.02)


def test_forward_resistance_is_axle_torque_over_radius(cfg):
    # Rolling forward at constant speed, the only resistance is the axle's dry
    # friction torque tau, felt at the ground as tau / r.
    c = copy.deepcopy(cfg)
    c["ground"]["axle_friction"] = 1e-3
    f_fwd, _ = drag_test.drag_force(c, "forward")
    assert f_fwd == pytest.approx(1e-3 / c["ground"]["wheel_radius"], rel=0.02)


def test_axle_check_catches_viscous_friction(cfg):
    # Planted fault: MuJoCo's default friction time constant (0.02 s). At the
    # drag speed the 'dry' axle friction then acts viscous (force ~ speed)
    # and falls well short of tau / r.
    c = copy.deepcopy(cfg)
    c["ground"]["axle_friction"] = 1e-3
    c["ground"]["axle_friction_timeconst"] = 0.02
    f_fwd, _ = drag_test.drag_force(c, "forward")
    assert f_fwd < 0.9 * 1e-3 / c["ground"]["wheel_radius"]


def test_wheels_make_sideways_harder(cfg):
    c = copy.deepcopy(cfg)
    c["ground"]["axle_friction"] = 1e-3
    s = drag_test.run(c)
    assert s["ratio_sideways_over_forward"] > 1


def test_anisotropy_check_catches_wheel_turned_90deg(cfg, monkeypatch):
    # Planted fault: axle along the body instead of across it. The wheel then
    # rolls sideways, so the ratio must fall below 1 and the check must fail.
    real = mb.build_mjcf

    def turned(c=None, drag_rig=False):
        xml = real(c, drag_rig)
        return xml.replace('type="hinge" axis="0 1 0"', 'type="hinge" axis="1 0 0"').replace(
            'zaxis="0 1 0"', 'zaxis="1 0 0"')

    monkeypatch.setattr(mb, "build_mjcf", turned)
    c = copy.deepcopy(cfg)
    c["ground"]["axle_friction"] = 1e-3
    assert drag_test.run(c)["ratio_sideways_over_forward"] < 1
