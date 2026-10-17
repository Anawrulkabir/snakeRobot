"""Tests for snake/model_builder.py against docs/model_plan.md.

Each physics check is paired with a planted fault it must catch (CLAUDE.md 9).
"""

import copy
import math

import mujoco
import numpy as np
import pytest

from snake import config as cfgmod
from snake.cable_geometry import exact_length
from snake.model_builder import build_mjcf, build_model


@pytest.fixture
def cfg():
    return cfgmod.load()


def max_cable_error(model, cfg, angle_sign=1.0):
    """Largest |tendon length - Eq. S1| over joints, sides and angles in [-80, 80] deg.

    angle_sign = -1 plants a sign-convention fault in the comparison.
    """
    Lc, Lj = cfg["cable"]["half_spacing"], cfg["cable"]["joint_offset"]
    data = mujoco.MjData(model)
    worst = 0.0
    for deg in np.linspace(-80, 80, 33):
        q = math.radians(deg)
        data.qpos[:] = 0
        for i in range(1, cfg["body"]["n_segments"]):
            data.qpos[model.joint(f"j{i}").qposadr[0]] = q
        mujoco.mj_forward(model, data)
        for i in range(1, cfg["body"]["n_segments"]):
            for side in ("l", "r"):
                sim = data.ten_length[model.tendon(f"cable{i}_{side}").id]
                ref = exact_length(angle_sign * q, Lc, Lj, side)
                worst = max(worst, abs(sim - ref))
    return worst


def test_structure(cfg):
    m = build_model(cfg)
    n = cfg["body"]["n_segments"]
    assert m.nbody == 2 * n + 1  # segments + wheels + world
    extra = {"none": 0, "slide": n - 1, "rollpitch": 2 * (n - 1)}[cfg["body"]["vertical_compliance"]]
    assert m.nv == 4 + (n - 1) + n + extra  # planar root + yaw joints + axles + load-model DOF
    assert m.nu == n - 1
    assert m.ntendon == 2 * (n - 1)
    for i in range(1, n):
        assert np.allclose(m.jnt_axis[m.joint(f"j{i}").id], [0, 0, 1])
        assert m.jnt_range[m.joint(f"j{i}").id][1] == pytest.approx(math.radians(cfg["joint"]["hard_limit_deg"]))


def test_total_mass(cfg):
    # Head: shell + hardware + electronics. Others: shell + hardware + servos.
    m, n = cfg["mass"], cfg["body"]["n_segments"]
    expected = n * (m["shell"] + m["hardware"]) + m["head_electronics"] + (n - 1) * m["servos_per_joint"] * m["servo"]
    assert build_model(cfg).body_subtreemass[1] == pytest.approx(expected)


def test_cable_lengths_match_eq_s1(cfg):
    # The tendon geometry reproduces the paper's exact-length formula,
    # including its sign convention (alpha > 0 lengthens the left cable).
    assert max_cable_error(build_model(cfg), cfg) < 1e-9


def test_cable_check_catches_sign_flip(cfg):
    # Planted fault: the opposite angle convention must be detected.
    assert max_cable_error(build_model(cfg), cfg, angle_sign=-1.0) > 1e-3


def test_cable_check_catches_misplaced_sites(cfg):
    # Planted fault: geometry built with a different L_c than the formula uses.
    bad = copy.deepcopy(cfg)
    bad["cable"]["half_spacing"] *= 1.2
    assert max_cable_error(build_model(bad), cfg) > 1e-4


def settle(model, seconds=1.0):
    data = mujoco.MjData(model)
    for _ in range(int(seconds / model.opt.timestep)):
        mujoco.mj_step(model, data)
    return data


def contact_pairs(model, data):
    return {(model.geom(c.geom1).name, model.geom(c.geom2).name) for c in data.contact[: data.ncon]}


def test_rests_on_wheels_only(cfg):
    m = build_model(cfg)
    d = settle(m)
    pairs = contact_pairs(m, d)
    n = cfg["body"]["n_segments"]
    assert pairs == {("floor", f"wheel{i}_tyre") for i in range(n)}
    # Sinks into the floor by under 1 mm (soft-contact penetration).
    assert abs(d.qpos[m.joint("root_z").qposadr[0]]) < 1e-3
    assert np.allclose(d.qvel, 0, atol=1e-3)


def body_clearance(model, data):
    """Lowest point of any body capsule above the floor (m).

    The floor and body capsules are in contact groups that never collide, so
    a body sunk into the floor would produce no contact at all. Clearance is
    therefore checked geometrically.
    """
    lows = [
        data.geom_xpos[g][2] - model.geom_size[g][0] for g in range(model.ngeom) if model.geom(g).name.endswith("_body")
    ]
    return min(lows)


def test_body_clears_floor(cfg):
    m = build_model(cfg)
    d = settle(m)
    assert body_clearance(m, d) > 0


def test_clearance_check_catches_low_body(cfg, monkeypatch):
    # Planted fault: ride_height below the capsule radius, with the builder's
    # guard switched off so the bad model can be built.
    import snake.model_builder as mb

    monkeypatch.setattr(mb, "_check", lambda c: None)
    bad = copy.deepcopy(cfg)
    bad["body"]["ride_height"] = bad["body"]["segment_width"] / 2 - 0.005
    bad["ground"]["wheel_radius"] = 0.005
    m = mb.build_model(bad)
    d = settle(m)
    assert body_clearance(m, d) < 0


def test_builder_rejects_low_ride_height(cfg):
    bad = copy.deepcopy(cfg)
    bad["body"]["ride_height"] = bad["body"]["segment_width"] / 2
    with pytest.raises(ValueError):
        build_mjcf(bad)


def test_planar_under_sideways_push(cfg):
    # No roll or pitch DOF exists, so a sideways shove on the tail must leave
    # every segment level (z axis of every body stays vertical).
    m = build_model(cfg)
    d = mujoco.MjData(m)
    tail = m.body(f"seg{cfg['body']['n_segments'] - 1}").id
    for k in range(500):
        d.xfrc_applied[tail] = [0, 2.0, 0, 0, 0, 0] if k < 100 else 0
        mujoco.mj_step(m, d)
    for b in (m.body(f"seg{i}").id for i in range(cfg["body"]["n_segments"])):
        z_axis = d.xmat[b].reshape(3, 3)[:, 2]
        assert np.allclose(z_axis, [0, 0, 1], atol=1e-9)


def test_invalid_geometry_rejected(cfg):
    bad = copy.deepcopy(cfg)
    bad["cable"]["joint_offset"] = cfg["body"]["segment_pitch"]  # no room for the segment
    with pytest.raises(ValueError):
        build_mjcf(bad)
    bad = copy.deepcopy(cfg)
    bad["cable"]["half_spacing"] = cfg["body"]["segment_width"]  # anchor outside the body
    with pytest.raises(ValueError):
        build_mjcf(bad)


def test_servo_torque_capped(cfg):
    m = build_model(cfg)
    stall = cfg["servo"]["stall_torque"]
    assert np.allclose(m.actuator_forcerange, [[-stall, stall]] * m.nu)
