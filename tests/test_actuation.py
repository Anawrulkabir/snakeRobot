"""Tests for implementation A (snake/actuation.py), each with a planted fault.

The expected behaviours are the paper's own descriptions of G
(Wang et al. 2023, pp. 13-16; paper_notes.md 1.4).
"""

import copy
import math

import mujoco
import numpy as np
import pytest

import snake.actuation as act
from snake import config as cfgmod
from snake.cable_geometry import exact_length
from snake.model_builder import build_model

A = math.radians(53.666667)
DEG = math.radians(1)


@pytest.fixture
def cfg():
    return cfgmod.load()


@pytest.fixture
def geom(cfg):
    return act.geometry(cfg)


def rng(alpha, G, geom):
    return act.free_range(alpha, G, A, *geom)


# ---- the inverse of Eq. S1 ----


def test_inverse_exact_round_trip(geom):
    Lc, Lj, _ = geom
    for z in np.linspace(-1.4, 1.4, 29):
        assert act.inverse_exact(exact_length(z, Lc, Lj, "l"), "l", Lc, Lj, math.pi / 2) == pytest.approx(z, abs=1e-9)
        assert act.inverse_exact(exact_length(z, Lc, Lj, "r"), "r", Lc, Lj, math.pi / 2) == pytest.approx(z, abs=1e-9)


# ---- the paper's descriptions of G ----


@pytest.mark.parametrize("alpha_deg", [-50, -20, 0, 20, 50])
def test_G0_tracks_suggested_angle(geom, alpha_deg):
    # p. 13: at G = 0 "joint angles can precisely track the suggested angles".
    lo, hi = rng(math.radians(alpha_deg), 0.0, geom)
    assert lo == pytest.approx(math.radians(alpha_deg), abs=1e-9)
    assert hi == pytest.approx(math.radians(alpha_deg), abs=1e-9)


def test_G05_directional(geom):
    # pp. 13-14: at G = 0.5, for alpha > 0 the joint may bend further (zeta >= alpha)
    # but not less; mirror for alpha < 0; zeta = 0 at alpha = 0.
    a = math.radians(30)
    lo, hi = rng(a, 0.5, geom)
    assert lo == pytest.approx(a, abs=1e-9) and hi > a + DEG
    lo, hi = rng(-a, 0.5, geom)
    assert hi == pytest.approx(-a, abs=1e-9) and lo < -a - DEG
    lo, hi = rng(0.0, 0.5, geom)
    assert lo == pytest.approx(0, abs=1e-9) and hi == pytest.approx(0, abs=1e-9)


def test_G075_hybrid(geom):
    # pp. 15-16: at G = 0.75, bidirectionally compliant for alpha in (-0.5A, 0.5A),
    # directionally compliant otherwise.
    for frac in (-0.4, 0.0, 0.3):
        lo, hi = rng(frac * A, 0.75, geom)
        assert lo < frac * A - 0.1 * DEG and hi > frac * A + 0.1 * DEG
    for frac in (0.6, 1.0):
        lo, hi = rng(frac * A, 0.75, geom)
        assert lo == pytest.approx(frac * A, abs=1e-9) and hi > frac * A + DEG


def test_G1_directional_only_at_extremes(geom):
    # p. 14: at G = 1 both cables are lengthened, except at alpha = +-A where
    # the joint is only directionally compliant (zeta >= A at alpha = A).
    lo, hi = rng(A, 1.0, geom)
    assert lo == pytest.approx(A, abs=1e-9) and hi > A
    lo, hi = rng(0.5 * A, 1.0, geom)
    assert lo < 0.5 * A - DEG and hi > 0.5 * A + DEG


def test_compliance_increases_with_G(geom):
    # p. 13: "increasing G leads to more compliance". The free range never shrinks.
    for a in np.linspace(-A, A, 21):
        widths = [np.subtract(*rng(a, G, geom)[::-1]) for G in np.arange(0, 1.76, 0.25)]
        assert all(w2 >= w1 - 1e-12 for w1, w2 in zip(widths, widths[1:]))


def test_narrative_check_catches_sign_flip(geom, monkeypatch):
    # Planted fault: flip the sign of alpha in Eq. 3's lengthened branch
    # (l0 * (g - alpha) for the left cable instead of l0 * (g + alpha)).
    def flipped(alpha, G, A_, Lc, Lj, l0):
        g = (2 * G - 1) * A_
        Ll = (
            exact_length(alpha, Lc, Lj, "l")
            if alpha <= -g
            else exact_length(-A_ * min(1, 2 * G - 1), Lc, Lj, "l") + l0 * (g - alpha)
        )
        Lr = (
            exact_length(alpha, Lc, Lj, "r")
            if alpha >= g
            else exact_length(A_ * min(1, 2 * G - 1), Lc, Lj, "r") + l0 * (g + alpha)
        )
        return Ll, Lr

    monkeypatch.setattr(act, "commanded_lengths", flipped)
    a = math.radians(30)
    lo, hi = act.free_range(a, 0.5, A, *geom)
    # The G = 0.5 property (bend further only) no longer holds.
    assert not (lo == pytest.approx(a, abs=1e-9) and hi > a + DEG)


def test_no_cable_commanded_shorter_than_exact(geom):
    # paper_notes 1.6: with l0 >= R, Eq. 3 never asks for a cable shorter than exact,
    # so the suggested angle always lies inside the free range.
    for G in (0, 0.25, 0.5, 0.75, 1.0, 1.5):
        for a in np.linspace(-A, A, 41):
            lo, hi = rng(a, G, geom)
            assert lo <= a + 1e-9 and hi >= a - 1e-9


# ---- G4: independence from anchor offsets ----


@pytest.mark.parametrize("scale", [0.5, 0.75, 1.5])
def test_free_range_independent_of_anchor_offsets(cfg, scale):
    # With the anchor angle (L_c / L_j) and l0 / R fixed, Eq. 3 is identical
    # in joint-angle space, so implementation A's free ranges must not change.
    base = act.geometry(cfg)
    c = copy.deepcopy(cfg)
    c["cable"]["half_spacing"] *= scale
    c["cable"]["joint_offset"] *= scale
    scaled = act.geometry(c)
    for G in (0, 0.5, 0.75, 1.0, 1.5):
        for a in np.linspace(-A, A, 17):
            assert act.free_range(a, G, A, *scaled) == pytest.approx(act.free_range(a, G, A, *base), abs=1e-12)


def test_anchor_check_catches_unscaled_l0(cfg):
    # Planted fault: halve the offsets but keep l0 in mm (not scaled with R).
    # The free ranges must then differ, which is why l0 is stored as l0 / R.
    Lc, Lj, l0 = act.geometry(cfg)
    a = 0.3
    assert act.free_range(a, 0.75, A, Lc / 2, Lj / 2, l0) != pytest.approx(
        act.free_range(a, 0.75, A, Lc, Lj, l0), abs=1e-6
    )


# ---- boundary torque ----


def test_boundary_torque_inside_zero_outside_restoring_capped():
    k, c, cap = 10.0, 0.05, 0.2
    assert act.boundary_torque(0.1, 5.0, -0.2, 0.2, k, c, cap) == 0.0
    t = act.boundary_torque(0.21, 0.0, -0.2, 0.2, k, c, cap)
    assert t == pytest.approx(-0.1) and t < 0
    t = act.boundary_torque(-0.21, 0.0, -0.2, 0.2, k, c, cap)
    assert t == pytest.approx(0.1) and t > 0
    assert act.boundary_torque(1.0, 0.0, -0.2, 0.2, k, c, cap) == -cap


def test_boundary_damping_one_sided():
    # Cables only pull: moving back into the range gets no damping torque.
    assert act.boundary_torque(0.21, -1.0, -0.2, 0.2, 10.0, 0.05, 0.2) == pytest.approx(-0.1)
    assert act.boundary_torque(0.21, +1.0, -0.2, 0.2, 10.0, 0.05, 0.2) == pytest.approx(-0.15)


# ---- in simulation: a pushed joint stops at its free-range boundary ----


def push_joint(cfg, G, alpha, push, seconds=3.0):
    """Hold the snake in place (root slides locked by large damping), command
    a constant suggested angle alpha at every joint, and push joint 3 with a
    constant external torque. Returns the joint's final angle.

    Gravity is off, so the wheels carry no load and ground friction cannot
    take part of the push: this isolates the joint law. A little joint
    damping lets the floating chain settle; it does not change the static
    balance push = k * overshoot."""
    c = copy.deepcopy(cfg)
    c["servo"]["actuation"] = "compliance_A"
    c["joint"]["damping"] = 0.02
    m = build_model(c)
    m.opt.gravity[:] = 0
    for nm in ("root_x", "root_y", "root_yaw"):
        m.dof_damping[m.joint(nm).dofadr[0]] = 1e3
    d = mujoco.MjData(m)
    law = act.ComplianceA(c, G, A)
    jq = [m.joint(f"j{i}").qposadr[0] for i in range(1, m.nu + 1)]
    jv = [m.joint(f"j{i}").dofadr[0] for i in range(1, m.nu + 1)]
    d.qpos[jq] = alpha
    mujoco.mj_forward(m, d)
    j3 = m.joint("j3").dofadr[0]
    while d.time < seconds:
        d.ctrl[:] = law.torques(
            [alpha] * m.nu, d.qpos[jq], d.qvel[jv], m.opt.timestep, act.effective_inertias(m, d, jv)
        )
        d.qfrc_applied[:] = 0
        d.qfrc_applied[j3] = push
        mujoco.mj_step(m, d)
    return d.qpos[m.joint("j3").qposadr[0]]


@pytest.mark.parametrize("G", [0.0, 0.5, 0.75, 1.0])
def test_pushed_joint_settles_at_boundary(cfg, G):
    # A push of half the stall torque moves the joint to its free-range
    # boundary, plus the overshoot push / k from the boundary stiffness.
    # Only cable boundaries are checked; a boundary at the mechanical stop
    # (90 deg) is a different constraint.
    alpha = 0.4 * A
    lo, hi = act.free_range(alpha, G, A, *act.geometry(cfg))
    k = cfg["servo"]["boundary_stiffness"]
    push = 0.1
    hard = math.radians(cfg["joint"]["hard_limit_deg"])
    if hi < hard:
        assert push_joint(cfg, G, alpha, +push) == pytest.approx(hi + push / k, abs=0.05 * DEG)
    if lo > -hard:
        assert push_joint(cfg, G, alpha, -push) == pytest.approx(lo - push / k, abs=0.05 * DEG)


def test_push_check_catches_swapped_boundaries(cfg, monkeypatch):
    # Planted fault: zeta_min and zeta_max swapped in the controller.
    real = act.free_range
    monkeypatch.setattr(act, "free_range", lambda *a, **k: real(*a, **k)[::-1])
    alpha, G = 0.4 * A, 0.75
    monkeypatch.undo()
    lo, hi = act.free_range(alpha, G, A, *act.geometry(cfg))
    monkeypatch.setattr(act, "free_range", lambda *a, **k: real(*a, **k)[::-1])
    z_up = push_joint(cfg, G, alpha, +0.1)
    assert z_up != pytest.approx(hi + 0.1 / cfg["servo"]["boundary_stiffness"], abs=0.3 * DEG)


def test_boundary_damping_stable_at_1ms(cfg):
    # At G = 0 every joint sits on its boundary. With explicit damping the
    # pushed joint oscillated at 500 Hz at dt = 1 ms (c dt / I_eff = 2.6-3.9).
    # With the implicit form it settles to the static balance push / k (the
    # remaining +-0.02 deg is the floating chain's slow ~2.7 Hz swing).
    alpha = 0.4 * A
    z = [push_joint(cfg, 0.0, alpha, 0.1, s) - alpha for s in (3.0, 3.5, 4.0)]
    assert max(z) - min(z) < 0.05 * DEG
    assert sum(z) / 3 == pytest.approx(0.1 / cfg["servo"]["boundary_stiffness"], abs=0.05 * DEG)


def test_stability_check_catches_explicit_damping(cfg, monkeypatch):
    # Planted fault: plain explicit damping (no implicit correction).
    monkeypatch.setattr(act, "implicit_damping", lambda c, dt, inertia: c)
    alpha = 0.4 * A
    z = [push_joint(cfg, 0.0, alpha, 0.1, s) - alpha for s in (3.0, 3.5, 4.0)]
    settled = max(z) - min(z) < 0.05 * DEG and abs(sum(z) / 3 - 0.1 / cfg["servo"]["boundary_stiffness"]) < 0.05 * DEG
    assert not settled


def test_simulated_trial_independent_of_anchor_offsets(cfg):
    # G4 item 3, in simulation: implementation A only sees the free ranges,
    # so halving the anchor offsets (with l0 scaled by R) must not change the
    # locomotion. A short trial at G = 0.75 is compared step for step.
    from snake.sim import run_trial

    gait = cfgmod.load("gait.yaml")["wave"]
    base = run_trial(cfg, gait, 0.25, 1, seed=7, G=0.75)
    c = copy.deepcopy(cfg)
    c["cable"]["half_spacing"] *= 0.5
    c["cable"]["joint_offset"] *= 0.5
    half = run_trial(c, gait, 0.25, 1, seed=7, G=0.75)
    assert np.allclose(base["com_xy"], half["com_xy"], atol=1e-9)


def test_tight_spool_matches_drive_reach(geom):
    # Same law as scripts/drive_reach.py 'tight': taut at 0, slack elsewhere.
    # drive_reach run 20261016T175804Z_162cbe0 (A = 53.7 deg): free range at
    # alpha = A/2 is [24.4, 31.5] deg and at alpha = A is [45.8, 90] deg.
    Lc, Lj, l0 = geom
    lo, hi = act.free_range(0.0, None, A, Lc, Lj, l0, law="tight_spool")
    assert lo == pytest.approx(0, abs=1e-9) and hi == pytest.approx(0, abs=1e-9)
    lo, hi = act.free_range(A / 2, None, A, Lc, Lj, l0, law="tight_spool")
    assert math.degrees(lo) == pytest.approx(24.4, abs=0.05) and math.degrees(hi) == pytest.approx(31.5, abs=0.05)
    lo, hi = act.free_range(A, None, A, Lc, Lj, l0, law="tight_spool")
    assert math.degrees(lo) == pytest.approx(45.8, abs=0.05) and math.degrees(hi) == pytest.approx(90.0, abs=0.05)
    # Planted fault: slope taken as l0 instead of L_c gives a different range.
    with pytest.raises(AssertionError):
        Ll = 2 * Lj + l0 * (A / 2)
        assert math.degrees(act.inverse_exact(Ll, "l", Lc, Lj, math.pi / 2)) == pytest.approx(31.5, abs=0.05)


# Passive element about alpha (Fahad 2026-10-17).
@pytest.mark.parametrize("model", ["quadratic_alpha", "linear_alpha"])
def test_passive_torque_restores_toward_alpha(model):
    a = math.radians(15)
    assert act.passive_torque(a, a, 0.5, model) == 0.0
    assert act.passive_torque(a + 0.3, a, 0.5, model) < 0
    assert act.passive_torque(a - 0.3, a, 0.5, model) > 0
    # Centred on alpha, not on straight: zero torque at zeta = alpha != 0, nonzero at 0.
    assert act.passive_torque(0.0, a, 0.5, model) > 0


def test_passive_quadratic_magnitude_matches_fit():
    # tau = c e^2: doubling the deflection quadruples the torque.
    t1 = act.passive_torque(0.2, 0.0, 0.3, "quadratic_alpha")
    t2 = act.passive_torque(0.4, 0.0, 0.3, "quadratic_alpha")
    assert t1 == pytest.approx(-0.3 * 0.04)
    assert t2 == pytest.approx(4 * t1)
