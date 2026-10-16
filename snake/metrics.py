"""Locomotion metrics (CLAUDE.md 5.5). Pure numpy, no MuJoCo, so each can be unit-tested.

Jam detection, success and collision counts come with the arena (milestone 4).
"""
import numpy as np


def cycle_window(t, freq, skip_cycles, n_cycles):
    """Boolean mask of samples in cycles [skip_cycles, skip_cycles + n_cycles)."""
    period = 1.0 / freq
    return (t >= skip_cycles * period) & (t < (skip_cycles + n_cycles) * period + 1e-12)


def displacement_per_cycle(t, xy, freq, skip_cycles, n_cycles, heading):
    """CoM displacement per gait cycle over a whole number of cycles.

    Returns (forward, net): forward is along the initial heading (radians),
    net is the straight-line distance. Both are per cycle, in metres.
    Sampling at whole cycles removes the within-cycle lateral sway.
    """
    period = 1.0 / freq
    t0, t1 = skip_cycles * period, (skip_cycles + n_cycles) * period
    p0 = np.array([np.interp(t0, t, xy[:, k]) for k in range(2)])
    p1 = np.array([np.interp(t1, t, xy[:, k]) for k in range(2)])
    d = p1 - p0
    u = np.array([np.cos(heading), np.sin(heading)])
    return float(d @ u) / n_cycles, float(np.linalg.norm(d)) / n_cycles


def mean_body_heading(t, axis_xy, freq, skip_cycles, n_cycles):
    """Direction (radians) of the tail-to-head axis, averaged over whole cycles.

    The head's own yaw swings with the wave, so it is not the travel axis.
    """
    w = cycle_window(t, freq, skip_cycles, n_cycles)
    v = axis_xy[w].mean(axis=0)
    return float(np.arctan2(v[1], v[0]))


def heading_drift_per_cycle(t, xy, freq, skip_cycles, n_cycles):
    """Change in CoM travel direction per cycle (radians), from cycle-sampled positions.

    A non-integer number of waves on the body makes an open-loop serpenoid
    turn slowly; this reports how much.
    """
    period = 1.0 / freq
    pts = np.array([[np.interp((skip_cycles + k) * period, t, xy[:, j]) for j in range(2)]
                    for k in range(n_cycles + 1)])
    steps = np.diff(pts, axis=0)
    ang = np.unwrap(np.arctan2(steps[:, 1], steps[:, 0]))
    if len(ang) < 2:
        return 0.0
    return float((ang[-1] - ang[0]) / (len(ang) - 1))


def summary_stats(x):
    """Mean, 95th percentile and peak of |x| (CLAUDE.md 5.5 torque statistics)."""
    a = np.abs(np.asarray(x, dtype=float))
    return {"mean": float(a.mean()), "p95": float(np.percentile(a, 95)), "peak": float(a.max())}


def mean_ci95(values):
    """Mean and 95% confidence half-width (Student t) across trials."""
    from scipy import stats
    v = np.asarray(values, dtype=float)
    n = len(v)
    if n < 2:
        return float(v.mean()), float("nan")
    half = stats.t.ppf(0.975, n - 1) * v.std(ddof=1) / np.sqrt(n)
    return float(v.mean()), float(half)
