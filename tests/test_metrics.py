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


# ---- jam, success, collisions (CLAUDE.md 5.5, 9) ----

def pinned(T=40.0, f=0.125, sway=0.05, dt=0.01):
    """A robot pinned between posts: it wiggles in place with no net progress."""
    t = np.arange(0, T, dt)
    return t, np.c_[0.001 * np.sin(0.3 * t), sway * np.sin(2 * math.pi * f * t)]


def test_jam_flags_pinned_robot():
    f = 0.125
    t, xy = pinned(f=f)
    jammed, t_jam = metrics.detect_jam(t, xy, f, threshold=0.01, min_cycles=3)
    assert jammed and t_jam is not None


def test_jam_does_not_flag_free_robot():
    f = 0.125
    t, xy = wiggle(0.012, 0.3, f, T=60)       # 0.096 m per cycle, with sway
    assert metrics.detect_jam(t, xy, f, threshold=0.01, min_cycles=3) == (False, None)


def test_jam_ignores_short_stall():
    # Free, stalled for 2 cycles (< 3), free again: not a jam.
    f, dt = 0.125, 0.01
    t = np.arange(0, 80, dt)
    v = np.where((t > 30) & (t < 30 + 2 / f), 0.0, 0.012)
    x = np.cumsum(v) * dt
    xy = np.c_[x, 0.05 * np.sin(2 * math.pi * f * t)]
    assert metrics.detect_jam(t, xy, f, threshold=0.01, min_cycles=3)[0] is False


def test_jam_check_catches_inverted_threshold(monkeypatch):
    # Planted fault: comparing with > instead of <. The pinned robot must then
    # not be flagged, which shows the jam test above depends on the comparison.
    f = 0.125
    t, xy = pinned(f=f)
    real = metrics.displacement_over_last_cycle
    monkeypatch.setattr(metrics, "displacement_over_last_cycle", lambda *a: 1.0 - real(*a))
    assert metrics.detect_jam(t, xy, f, threshold=0.01, min_cycles=3)[0] is False


def test_first_crossing():
    t = np.arange(0, 10, 0.01)
    head = np.c_[0.1 * t, np.zeros_like(t)]
    assert metrics.first_crossing(t, head, (0.5, 0), (1, 0)) == pytest.approx(5.0, abs=0.011)
    assert metrics.first_crossing(t, head, (0.5, 0), (1, 0), T=4.0) is None
    # Planted fault: a line normal pointing backwards counts the start as a crossing.
    assert metrics.first_crossing(t, head, (0.5, 0), (-1, 0)) == 0.0


def test_collision_count_debounces_chatter():
    t = np.arange(0, 2, 0.001)
    c = np.zeros_like(t, bool)
    c[(t > 0.2) & (t < 0.5)] = True
    c[(t > 0.302) & (t < 0.305)] = False       # 3 ms flicker: same collision
    c[(t > 1.0) & (t < 1.2)] = True            # a separate collision
    assert metrics.count_collisions(t, c[:, None], min_gap=0.05) == 2
    # Planted fault: no debounce counts the flicker as an extra collision.
    assert metrics.count_collisions(t, c[:, None], min_gap=0.0) == 3
