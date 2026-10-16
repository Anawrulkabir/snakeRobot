"""Tests for snake/metrics.py on synthetic trajectories with known answers."""
import math

import numpy as np
import pytest

from snake import metrics


def wiggle(v, heading, freq, sway=0.03, T=10.0, dt=1e-3):
    """Straight-line travel at speed v along heading, plus lateral sway at the gait frequency."""
    t = np.arange(0, T, dt)
    u = np.array([math.cos(heading), math.sin(heading)])
    n = np.array([-u[1], u[0]])
    xy = np.outer(v * t, u) + np.outer(sway * np.sin(2 * math.pi * freq * t), n)
    return t, xy


def test_displacement_per_cycle_known():
    f, v, h = 0.5, 0.02, 0.7
    t, xy = wiggle(v, h, f)
    fwd, net = metrics.displacement_per_cycle(t, xy, f, 1, 3, h)
    assert fwd == pytest.approx(v / f, rel=1e-6)
    assert net == pytest.approx(v / f, rel=1e-6)


def test_displacement_sign_catches_backwards_travel():
    # Planted fault: travelling backwards must give negative forward displacement.
    f, h = 0.5, 0.3
    t, xy = wiggle(-0.02, h, f)
    fwd, net = metrics.displacement_per_cycle(t, xy, f, 1, 3, h)
    assert fwd < 0 < net


def test_sway_does_not_leak_into_displacement():
    # Sampling at whole cycles removes sway; sampling at half cycles would not.
    f, h = 0.5, 0.0
    t, xy = wiggle(0.0, h, f, sway=0.05)
    _, net = metrics.displacement_per_cycle(t, xy, f, 1, 3, h)
    assert net < 1e-9


def test_heading_drift_straight_and_turning():
    f = 0.5
    t, xy = wiggle(0.02, 0.0, f)
    assert metrics.heading_drift_per_cycle(t, xy, f, 0, 4) == pytest.approx(0.0, abs=1e-9)
    # Planted fault: a circular path turning at w rad/s must show w / f per cycle.
    w = 0.05
    t = np.arange(0, 10, 1e-3)
    xy = np.c_[np.sin(w * t), 1 - np.cos(w * t)]
    drift = metrics.heading_drift_per_cycle(t, xy, f, 0, 4)
    assert drift == pytest.approx(w / f, rel=1e-3)


def test_summary_stats():
    s = metrics.summary_stats([-3, 1, 2])
    assert s["peak"] == 3 and s["mean"] == pytest.approx(2.0)


def test_mean_ci95_known():
    m, h = metrics.mean_ci95([1.0, 2.0, 3.0])
    assert m == 2.0
    assert h == pytest.approx(4.302652729749464 * 1.0 / math.sqrt(3), rel=1e-6)


def test_mean_body_heading_ignores_swing():
    # Axis swinging +-40 deg about 0.5 rad averages to 0.5 rad.
    f = 0.5
    t = np.arange(0, 10, 1e-3)
    ang = 0.5 + math.radians(40) * np.sin(2 * math.pi * f * t)
    axis = np.c_[np.cos(ang), np.sin(ang)]
    assert metrics.mean_body_heading(t, axis, f, 1, 3) == pytest.approx(0.5, abs=1e-3)
    # Planted fault: a reversed axis (head and tail swapped) reads pi away.
    h = metrics.mean_body_heading(t, -axis, f, 1, 3)
    assert abs(math.remainder(h - 0.5, 2 * math.pi)) == pytest.approx(math.pi, abs=1e-3)
