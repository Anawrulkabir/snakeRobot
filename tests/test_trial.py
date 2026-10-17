"""Tests for the lattice arena and trial setup, each with a planted fault."""
import copy
import math

import numpy as np
import pytest

import snake.model_builder as mb
import snake.trial as tr
from snake import arena as arena_mod
from snake import config as cfgmod


@pytest.fixture
def setup():
    cfg = cfgmod.load()
    mc = copy.deepcopy(cfgmod.load("metrics.yaml"))
    return cfg, cfgmod.load("arena.yaml"), mc


def test_hexagonal_lattice_nearest_neighbour_is_spacing(setup):
    _, arena, _ = setup
    for dn in ("sparse", "medium", "dense"):
        p = arena_mod.post_centres(arena, dn, 0.7)
        d = arena_mod.spacing(arena, dn, 0.7)
        dist = np.linalg.norm(p[:, None] - p[None], axis=2) + np.eye(len(p)) * 1e9
        assert dist.min(axis=1) == pytest.approx(np.full(len(p), d), rel=1e-9)
        assert p[:, 0].min() >= arena["lattice"]["post_diameter_m"] / 2 - 1e-12


def init_only(cfg, arena, mc, dn, seed, A=59.5, xi=0.58):
    m0 = copy.deepcopy(mc)
    m0["success"]["max_cycles"] = 0
    return tr.run_lattice_trial(cfg, arena, m0, dn, A, xi, 0.125, "paper", 0.75, seed)


@pytest.mark.parametrize("dn,A,xi", [("medium", 59.5, 0.58), ("dense", 84.0, 1.02)])
def test_start_pose_clear_of_posts_and_aimed(setup, dn, A, xi):
    # Lattice diagnosis (b): 17/50 medium and 5/50 dense starts overlapped posts.
    cfg, arena, mc = setup
    for seed in range(30):
        r = init_only(cfg, arena, mc, dn, seed, A, xi)
        assert r["initial_post_contacts"] == 0
        assert r["initial_body_front_x_m"] == pytest.approx(arena["start"]["head_x_m"], abs=1e-9)
        assert abs(r["initial_body_axis_deg"]) <= arena["start"]["heading_noise_deg"] + 1e-6


def test_start_check_catches_head_yaw_placement(setup, monkeypatch):
    # Planted fault: the old placement (head segment's yaw = heading, head pin at head_x).
    cfg, arena, mc = setup

    def old(m, d, c, angles, jq, heading, front_x, y0):
        d.qpos[jq] = angles
        d.qpos[m.joint("root_x").qposadr[0]] = front_x
        d.qpos[m.joint("root_y").qposadr[0]] = y0
        d.qpos[m.joint("root_yaw").qposadr[0]] = heading
        tr.mujoco.mj_forward(m, d)

    monkeypatch.setattr(tr, "place_body", old)
    hits = sum(init_only(cfg, arena, mc, "medium", s)["initial_post_contacts"] > 0 for s in range(30))
    assert hits > 0


def short_trial(cfg, arena, mc, mu):
    a = copy.deepcopy(arena)
    a["lattice"]["post_friction"] = mu
    m0 = copy.deepcopy(mc)
    m0["success"]["max_cycles"] = 2
    return tr.run_lattice_trial(cfg, a, m0, "dense", 84.0, 1.02, 0.25, "paper", 0.75, seed=4)


def test_post_friction_changes_result(setup):
    # Lattice diagnosis (d): post friction 0 and 0.3 gave identical results.
    cfg, arena, mc = setup
    lo, hi = short_trial(cfg, arena, mc, 0.05), short_trial(cfg, arena, mc, 0.8)
    assert lo["collisions"] > 0
    assert abs(lo["final_com_dx_m"] - hi["final_com_dx_m"]) > 1e-4


def test_friction_check_catches_missing_priority(setup, monkeypatch):
    # Planted fault: posts without contact priority (the capsules' default
    # friction then overrides the configured value, as before the fix).
    cfg, arena, mc = setup
    real = mb.build_mjcf
    monkeypatch.setattr(mb, "build_mjcf", lambda *a, **k: real(*a, **k).replace(' priority="2"', ""))
    lo, hi = short_trial(cfg, arena, mc, 0.05), short_trial(cfg, arena, mc, 0.8)
    assert abs(lo["final_com_dx_m"] - hi["final_com_dx_m"]) < 1e-12


def passive_trial(cfg, arena, mc, model, coeff):
    c = copy.deepcopy(cfg)
    c["joint"]["passive_model"], c["joint"]["passive_coeff"] = model, coeff
    m0 = copy.deepcopy(mc)
    m0["success"]["max_cycles"] = 1
    # G = 1.5 on open floor: wide free ranges, so the passive element dominates tracking.
    return tr.run_lattice_trial(c, arena, m0, "open", 53.666667, 0.82, 0.25, "paper", 1.5, seed=2)


def test_passive_element_pulls_joints_toward_alpha(setup):
    cfg, arena, mc = setup
    free = passive_trial(cfg, arena, mc, "none", 0.0)["tracking_rms_rad"]
    held = passive_trial(cfg, arena, mc, "quadratic_alpha", 0.5)["tracking_rms_rad"]
    assert held < 0.8 * free


def test_passive_check_catches_sign_flip(setup, monkeypatch):
    # Planted fault: the passive torque pushes away from alpha.
    cfg, arena, mc = setup
    free = passive_trial(cfg, arena, mc, "none", 0.0)["tracking_rms_rad"]
    real = tr.passive_torque
    monkeypatch.setattr(tr, "passive_torque", lambda z, a, c, m: -real(z, a, c, m))
    # The anti-restoring torque makes the model blow up; MuJoCo resets the
    # state silently, and the trial must report it rather than carry on.
    with pytest.raises(FloatingPointError):
        passive_trial(cfg, arena, mc, "quadratic_alpha", 0.5)
    flipped = passive_trial(cfg, arena, mc, "quadratic_alpha", 0.02)["tracking_rms_rad"]
    assert not flipped < 0.8 * free


def test_joint_frictionloss_reaches_model(setup):
    cfg = copy.deepcopy(setup[0])
    cfg["joint"]["frictionloss"] = 0.0233
    m = mb.build_model(cfg)
    assert m.dof_frictionloss[m.joint("j1").dofadr[0]] == pytest.approx(0.0233)
